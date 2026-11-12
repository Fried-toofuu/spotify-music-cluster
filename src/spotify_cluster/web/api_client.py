"""Small HTTP boundary; never imports model serving or reads local artifacts."""

import math
import os
import re

import httpx

from spotify_cluster.config import F9


class APIError(Exception):
    """A sanitized message suitable for the interface."""


MALFORMED = "The API returned an unexpected response. Check backend compatibility."


def number(value, *, minimum=None, maximum=None):
    try:
        finite = type(value) in (int, float) and math.isfinite(value)
    except OverflowError:
        return False
    return (
        finite
        and (minimum is None or value >= minimum)
        and (maximum is None or value <= maximum)
    )


def identity(data):
    value = data.get("model_id")
    return isinstance(value, str) and bool(re.fullmatch(r"[a-zA-Z0-9_-]{1,160}", value))


def profile_valid(data, label):
    if not isinstance(data, dict):
        return False
    if (
        type(data.get("cluster_id")) is not int
        or data["cluster_id"] != label
        or type(data.get("count")) is not int
        or data["count"] < 1
        or not number(data.get("share"), minimum=0, maximum=1)
    ):
        return False
    for stat in ("mean", "median", "std", "q1", "q3", "iqr"):
        values = data.get(stat)
        if values is None and stat not in ("mean", "median"):
            continue
        if not isinstance(values, dict) or any(not number(values.get(f)) for f in F9):
            return False
    return True


def validate_response(kind, data):
    """Validate consumed fields while allowing additive backend fields."""
    if not isinstance(data, dict):
        raise APIError(MALFORMED)
    if kind == "health":
        valid = data.get("status") == "ready" and data.get("model_loaded") is True
    elif kind == "model":
        valid = (
            identity(data)
            and data.get("features") == list(F9)
            and data.get("algorithm") == "KMeans"
            and data.get("scaler") == "RobustScaler"
            and type(data.get("number_of_clusters")) is int
            and data["number_of_clusters"] == 2
            and type(data.get("training_sample_count")) is int
            and data["training_sample_count"] > 0
            and "modeling_pca" in data
            and data["modeling_pca"] is None
            and data.get("historical_equivalence") == "not_verified"
        )
    elif kind == "clusters":
        profiles = data.get("clusters")
        valid = (
            identity(data)
            and data.get("units") == "raw F9"
            and isinstance(profiles, dict)
            and set(profiles) == {"0", "1"}
            and all(profile_valid(profiles[str(i)], i) for i in (0, 1))
        )
        if valid:
            total = sum(p["count"] for p in profiles.values())
            valid = all(
                math.isclose(p["share"], p["count"] / total, abs_tol=1e-8)
                for p in profiles.values()
            )
        contributions = data.get("feature_contributions")
        if contributions is not None:
            shares = (
                contributions.get("shares") if isinstance(contributions, dict) else None
            )
            valid = (
                valid
                and isinstance(shares, dict)
                and all(number(shares.get(f), minimum=0, maximum=1) for f in F9)
            )
    elif kind == "predict":
        distances = data.get("distances")
        label = data.get("cluster_id")
        valid = (
            identity(data)
            and type(label) is int
            and label in (0, 1)
            and isinstance(distances, list)
            and len(distances) == 2
            and all(number(d, minimum=0) for d in distances)
            and profile_valid(data.get("profile"), label)
            and data.get("distance_definition")
            == "Euclidean distance to centroids [0, 1] in fitted RobustScaler space"
            and data.get("historical_equivalence") == "not_verified"
        )
    else:
        raise ValueError("Unknown response kind")
    if not valid:
        raise APIError(MALFORMED)
    return data


class APIClient:
    def __init__(self, base_url=None, *, transport=None):
        url = base_url or os.environ.get(
            "SPOTIFY_API_BASE_URL", "http://127.0.0.1:8000"
        )
        parsed = httpx.URL(url)
        if (
            parsed.scheme not in ("http", "https")
            or not parsed.host
            or parsed.userinfo
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("Configure an HTTP(S) API base URL without credentials")
        self.base_url = str(parsed).rstrip("/")
        self.transport = transport

    def _request(self, method, route, kind, payload=None):
        try:
            with httpx.Client(
                timeout=httpx.Timeout(15, connect=3),
                transport=self.transport,
                trust_env=False,
                follow_redirects=False,
            ) as client:
                response = client.request(
                    method, self.base_url + "/api/v1/" + route, json=payload
                )
            response.raise_for_status()
        except httpx.TimeoutException:
            raise APIError("The API timed out. Please try again.") from None
        except httpx.HTTPStatusError as exc:
            messages = {
                422: (
                    "The API rejected these features. Check all nine values and ranges."
                ),
                503: "The model service is unavailable. Start the backend and retry.",
            }
            raise APIError(
                messages.get(
                    exc.response.status_code, "The API request failed. Please retry."
                )
            ) from None
        except httpx.RequestError:
            raise APIError(
                "Cannot connect to the API. Start the backend, then refresh or retry."
            ) from None
        try:
            data = response.json()
        except ValueError:
            raise APIError(MALFORMED) from None
        return validate_response(kind, data)

    def health(self):
        return self._request("GET", "health", "health")

    def model(self):
        return self._request("GET", "model", "model")

    def clusters(self):
        return self._request("GET", "clusters", "clusters")

    def predict(self, features):
        return self._request("POST", "predict", "predict", features)
