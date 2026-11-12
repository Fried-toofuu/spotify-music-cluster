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


def safe_reason(value):
    if not isinstance(value, str) or not value:
        return "Optional data unavailable"
    return " ".join(value.split())[:200]


def features_valid(values):
    if not isinstance(values, dict) or set(values) != set(F9):
        return False
    if not all(number(values[name]) for name in F9):
        return False
    return (
        all(0 <= values[name] <= 1 for name in F9 if name not in ("tempo", "loudness"))
        and values["tempo"] >= 0
    )


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
        if not features_valid(values):
            return False
    return True


def pca_view_valid(data):
    if not isinstance(data, dict):
        return False
    ratios = data.get("explained_variance_ratio")
    cumulative = data.get("cumulative_explained_variance")
    if (
        not isinstance(ratios, list)
        or len(ratios) != 3
        or not isinstance(cumulative, list)
        or len(cumulative) != 3
        or not all(number(value, minimum=0, maximum=1) for value in ratios)
        or not all(number(value, minimum=0, maximum=1) for value in cumulative)
    ):
        return False
    if ratios != sorted(ratios, reverse=True):
        return False
    if not math.isclose(sum(ratios), cumulative[-1], rel_tol=0, abs_tol=1e-12):
        return False
    return isinstance(data.get("scope"), str) and bool(data["scope"])


def population_valid(data):
    if not isinstance(data, dict):
        return False
    counts = data.get("cluster_counts")
    shares = data.get("cluster_shares")
    total = data.get("training_sample_count")
    if (
        type(total) is not int
        or total < 1
        or not isinstance(counts, list)
        or len(counts) != 2
        or not all(type(value) is int and value > 0 for value in counts)
        or sum(counts) != total
        or not isinstance(shares, list)
        or len(shares) != 2
        or not all(number(value, minimum=0, maximum=1) for value in shares)
    ):
        return False
    return all(
        math.isclose(share, count / total, rel_tol=0, abs_tol=1e-8)
        for share, count in zip(shares, counts, strict=True)
    )


def sample_valid(data):
    if not isinstance(data, dict):
        return False
    counts = data.get("cluster_counts")
    population = data.get("population_cluster_counts")
    size = data.get("size")
    return (
        isinstance(data.get("policy"), str)
        and bool(data["policy"])
        and type(data.get("seed")) is int
        and type(data.get("per_cluster_cap")) is int
        and type(size) is int
        and size >= 0
        and isinstance(data.get("proportions_disclosure"), str)
        and isinstance(counts, list)
        and len(counts) == 2
        and all(type(value) is int and value >= 0 for value in counts)
        and sum(counts) == size
        and isinstance(population, list)
        and len(population) == 2
        and all(type(value) is int and value > 0 for value in population)
    )


def license_valid(data):
    return (
        isinstance(data, dict)
        and data.get("license") == "ODbL 1.0"
        and all(
            isinstance(data.get(key), str) and data[key]
            for key in ("name", "url", "redistribution")
        )
    )


def occupancy_valid(data):
    if not isinstance(data, dict):
        return False
    cells = data.get("cells")
    minimum = data.get("min_cell_count")
    if (
        type(data.get("bins")) is not int
        or data["bins"] < 4
        or type(minimum) is not int
        or minimum < 1
        or not isinstance(cells, list)
        or not cells
        or not isinstance(data.get("definition"), str)
        or not isinstance(data.get("x_range"), list)
        or len(data["x_range"]) != 2
        or not isinstance(data.get("y_range"), list)
        or len(data["y_range"]) != 2
        or not all(number(value) for value in data["x_range"] + data["y_range"])
    ):
        return False
    for cell in cells:
        if (
            not isinstance(cell, dict)
            or not number(cell.get("x"))
            or not number(cell.get("y"))
            or type(cell.get("count")) is not int
            or cell["count"] < minimum
            or not number(cell.get("cluster1_share"), minimum=0, maximum=1)
            or not number(cell.get("mean_instrumentalness"), minimum=0, maximum=1)
        ):
            return False
    return True


def point_arrays_valid(data, size):
    if not isinstance(data, dict):
        return False
    x, y, z = data.get("x"), data.get("y"), data.get("z")
    cluster, rows = data.get("cluster"), data.get("raw_features")
    if not all(isinstance(value, list) for value in (x, y, z, cluster, rows)):
        return False
    if not all(len(value) == size for value in (x, y, z, cluster, rows)):
        return False
    if not all(number(value) for value in (*x, *y, *z)):
        return False
    if not all(type(value) is int and value in (0, 1) for value in cluster):
        return False
    for row in rows:
        if (
            not isinstance(row, list)
            or len(row) != 9
            or not all(number(value) for value in row)
            or not features_valid(dict(zip(F9, row, strict=True)))
        ):
            return False
    return True


def views_valid(data, mode):
    views = data.get("views")
    return (
        isinstance(views, dict)
        and set(views) == {"points", "density"}
        and type(views["points"]) is bool
        and type(views["density"]) is bool
        and views["points"] is (mode == "points")
        and views["density"] is True
    )


def research_valid(data):
    comparisons = data.get("comparisons")
    archived = data.get("archived_evidence")
    population = data.get("population")
    if (
        not identity(data)
        or data.get("schema_version") != 1
        or data.get("artifact_kind") != "training-population-comparison"
        or data.get("features") != list(F9)
        or data.get("holdout_evaluated") is not False
        or data.get("historical_equivalence") != "NOT VERIFIED"
        or not population_valid(population)
        or not license_valid(data.get("license"))
        or not isinstance(comparisons, dict)
        or set(comparisons)
        != {"f5_kmeans_vs_deployment_f9_kmeans", "f9_kmeans_vs_f9_gmm"}
        or not isinstance(archived, dict)
    ):
        return False
    f5 = comparisons["f5_kmeans_vs_deployment_f9_kmeans"]
    gmm = comparisons["f9_kmeans_vs_f9_gmm"]
    total = population["training_sample_count"]
    for comparison in (f5, gmm):
        if (
            not isinstance(comparison, dict)
            or comparison.get("identical_track_ids") is not True
            or not number(comparison.get("ari"), minimum=-1, maximum=1)
        ):
            return False
    return not (
        sum(f5.get("f5_cluster_counts", [])) != total
        or sum(f5.get("deployment_cluster_counts", [])) != total
        or sum(gmm.get("gmm_hard_cluster_counts", [])) != total
        or not number(gmm.get("mean_max_responsibility"), minimum=0.5, maximum=1)
        or not number(gmm.get("mean_entropy_nats"), minimum=0)
        or archived.get("status") != "ARCHIVED; NOT RECOMPUTED; HOLDOUT CLOSED"
        or archived.get("label") != "Archived historical FULL research evidence"
        or not number(archived.get("holdout_silhouette"))
    )


def _components_valid(components):
    if not isinstance(components, list) or len(components) != 3:
        return False
    if not all(
        isinstance(row, list) and len(row) == 9 and all(number(v) for v in row)
        for row in components
    ):
        return False
    return all(
        math.isclose(
            sum(components[i][k] * components[j][k] for k in range(9)),
            1.0 if i == j else 0.0,
            rel_tol=0,
            abs_tol=1e-8,
        )
        for i in range(3)
        for j in range(3)
    )


def _point_valid(point):
    return (
        isinstance(point, dict)
        and type(point.get("index")) is int
        and point["index"] >= 0
        and type(point.get("cluster")) is int
        and point["cluster"] in (0, 1)
        and isinstance(point.get("coordinates"), list)
        and len(point["coordinates"]) == 3
        and all(number(value) for value in point["coordinates"])
        and features_valid(point.get("features"))
    )


def _neighbor_valid(entry):
    return _point_valid(entry) and number(entry.get("distance"), minimum=0)


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
    elif kind == "viz_meta":
        if data.get("available") is False:
            return {"available": False, "reason": safe_reason(data.get("reason"))}
        valid = (
            data.get("available") is True
            and data.get("schema_version") == 1
            and data.get("artifact_kind") == "pca-cluster-space"
            and data.get("artifact_mode") in ("points", "aggregate")
            and identity(data)
            and data.get("features") == list(F9)
            and data.get("historical_equivalence") == "NOT VERIFIED"
            and population_valid(data.get("population"))
            and sample_valid(data.get("sample"))
            and pca_view_valid(data.get("pca"))
            and views_valid(data, data.get("artifact_mode"))
            and license_valid(data.get("license"))
        )
        if valid:
            pca = data["pca"]
            valid = (
                _components_valid(pca.get("components"))
                and isinstance(pca.get("fit_representation"), str)
                and isinstance(pca.get("sign_convention"), str)
            )
    elif kind == "viz_points":
        sample = data.get("sample")
        size = sample.get("size") if isinstance(sample, dict) else None
        valid = (
            identity(data)
            and data.get("view") == "points"
            and data.get("features") == list(F9)
            and data.get("historical_equivalence") == "NOT VERIFIED"
            and population_valid(data.get("population"))
            and sample_valid(sample)
            and pca_view_valid(data.get("pca"))
            and type(size) is int
            and size >= 2
            and point_arrays_valid(data.get("points"), size)
            and occupancy_valid(data.get("occupancy"))
        )
        if valid:
            cluster = data["points"]["cluster"]
            valid = sample["cluster_counts"] == [cluster.count(0), cluster.count(1)]
    elif kind == "viz_occupancy":
        valid = (
            identity(data)
            and data.get("view") == "density"
            and data.get("features") == list(F9)
            and data.get("historical_equivalence") == "NOT VERIFIED"
            and population_valid(data.get("population"))
            and pca_view_valid(data.get("pca"))
            and occupancy_valid(data.get("occupancy"))
        )
    elif kind == "neighbors":
        point = data.get("point")
        neighbors = data.get("neighbors")
        valid = (
            identity(data)
            and type(data.get("sample_size")) is int
            and data["sample_size"] > 0
            and isinstance(data.get("distance_definition"), str)
            and isinstance(point, dict)
            and _point_valid(point)
            and isinstance(neighbors, list)
            and 1 <= len(neighbors) <= 12
            and all(_neighbor_valid(entry) for entry in neighbors)
            and data.get("historical_equivalence") == "NOT VERIFIED"
        )
        if valid:
            distances = [entry["distance"] for entry in neighbors]
            valid = distances == sorted(distances) and all(
                entry["index"] != point["index"] for entry in neighbors
            )
    elif kind == "research":
        if data.get("available") is False:
            return {"available": False, "reason": safe_reason(data.get("reason"))}
        valid = data.get("available") is True and research_valid(data)
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
            if kind == "predict":
                rejected = "The API rejected these features. Check all nine values."
            elif kind == "neighbors":
                rejected = "The selected point is outside the visualization sample."
            else:
                rejected = "The API rejected this request. Check submitted values."
            messages = {
                404: "The requested visualization or research data is unavailable.",
                422: rejected,
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

    def visualization_meta(self):
        return self._request("GET", "visualization/meta", "viz_meta")

    def visualization_points(self):
        return self._request("GET", "visualization/points", "viz_points")

    def visualization_occupancy(self):
        return self._request("GET", "visualization/occupancy", "viz_occupancy")

    def visualization_neighbors(self, index, k=8):
        if type(index) is not int or index < 0:
            raise ValueError("Point index must be a nonnegative integer")
        if type(k) is not int or not 1 <= k <= 12:
            raise ValueError("Neighbor count must be between 1 and 12")
        result = self._request(
            "GET", f"visualization/neighbors?index={index}&k={k}", "neighbors"
        )
        if result["point"]["index"] != index:
            raise APIError(MALFORMED)
        return result

    def research(self):
        return self._request("GET", "research/comparison", "research")
