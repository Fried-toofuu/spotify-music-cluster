"""HTTP transport/software-double checks, not scientific model evidence."""

import json

import httpx
import pytest

from spotify_cluster.web.api_client import APIClient, APIError


@pytest.mark.parametrize("route", ["health", "model", "clusters", "predict"])
def test_http_contract(route, web_responses, api_track):
    def respond(request):
        assert str(request.url) == f"http://127.0.0.1:8000/api/v1/{route}"
        assert request.method == ("POST" if route == "predict" else "GET")
        if route == "predict":
            assert json.loads(request.content) == api_track
        return httpx.Response(200, json=web_responses[route])

    client = APIClient(transport=httpx.MockTransport(respond))
    result = (
        getattr(client, route)(api_track)
        if route == "predict"
        else getattr(client, route)()
    )
    assert result == web_responses[route]


@pytest.mark.parametrize(
    "status,phrase",
    [(422, "rejected"), (500, "failed"), (503, "unavailable"), (302, "failed")],
)
def test_status_sanitization(status, phrase):
    client = APIClient(
        transport=httpx.MockTransport(
            lambda _: httpx.Response(status, text="SECRET path and private features")
        )
    )
    with pytest.raises(APIError, match=phrase) as error:
        client.health()
    assert "SECRET" not in str(error.value)


@pytest.mark.parametrize(
    "error,phrase",
    [
        (httpx.ConnectError, "Cannot connect"),
        (httpx.ReadTimeout, "timed out"),
        (httpx.ConnectTimeout, "timed out"),
    ],
)
def test_transport_errors(error, phrase):
    def respond(request):
        raise error("SECRET backend path", request=request)

    client = APIClient(transport=httpx.MockTransport(respond))
    with pytest.raises(APIError, match=phrase) as exc:
        client.health()
    assert "SECRET" not in str(exc.value)


@pytest.mark.parametrize("route", ["health", "model", "clusters", "predict"])
@pytest.mark.parametrize("body", [[], None, {}, {"model_id": "bad"}])
def test_malformed_responses(route, body, api_track):
    client = APIClient(
        transport=httpx.MockTransport(
            lambda _: httpx.Response(200, content=json.dumps(body))
        )
    )
    with pytest.raises(APIError, match="unexpected response"):
        getattr(client, route)(api_track) if route == "predict" else getattr(
            client, route
        )()


def test_invalid_json():
    client = APIClient(
        transport=httpx.MockTransport(
            lambda _: httpx.Response(200, text="SECRET not JSON")
        )
    )
    with pytest.raises(APIError, match="unexpected response"):
        client.health()


@pytest.mark.parametrize("mutation", ["distances", "profile", "identity", "units"])
def test_invalid_prediction_fields(mutation, web_responses, api_track):
    result = web_responses["predict"]
    if mutation == "distances":
        result["distances"] = [-1, float("nan")]
    elif mutation == "profile":
        result["profile"]["cluster_id"] = 1 - result["cluster_id"]
    elif mutation == "identity":
        result["model_id"] = "<script>SECRET</script>"
    else:
        result["distance_definition"] = "probabilities"
    client = APIClient(
        transport=httpx.MockTransport(
            lambda _: httpx.Response(200, content=json.dumps(result))
        )
    )
    with pytest.raises(APIError):
        client.predict(api_track)


def test_configuration_and_redirect_boundary(monkeypatch):
    monkeypatch.setenv("SPOTIFY_API_BASE_URL", "http://localhost:8123")
    assert APIClient().base_url == "http://localhost:8123"
    for url in (
        "file:///private",
        "https://name:secret@example.org",
        "http://x/?url=secret",
    ):
        with pytest.raises(ValueError):
            APIClient(url)


def test_optional_statistics(web_responses, web_client):
    for p in web_responses["clusters"]["clusters"].values():
        for stat in ("std", "q1", "q3", "iqr"):
            p.pop(stat)
    web_responses["clusters"].pop("feature_contributions")
    assert web_client.clusters()["clusters"]["0"]["mean"]


def test_visualization_and_research_contract(web_client):
    meta = web_client.visualization_meta()
    assert meta["available"] is True
    assert meta["artifact_mode"] == "points"
    points = web_client.visualization_points()
    assert len(points["points"]["x"]) == points["sample"]["size"] == 4
    assert web_client.visualization_occupancy()["view"] == "density"
    neighbors = web_client.visualization_neighbors(0, 1)
    assert neighbors["point"]["index"] == 0
    assert neighbors["neighbors"][0]["index"] == 1
    research = web_client.research()
    assert research["available"] is True
    assert research["holdout_evaluated"] is False
    assert research["archived_evidence"]["status"].startswith("ARCHIVED")


def test_optional_artifact_unavailable(web_responses, web_client):
    web_responses["meta"] = {"available": False, "reason": "not provisioned"}
    web_responses["comparison"] = {"available": False, "reason": "not provisioned"}
    assert web_client.visualization_meta() == {
        "available": False,
        "reason": "not provisioned",
    }
    assert web_client.research() == {"available": False, "reason": "not provisioned"}


@pytest.mark.parametrize(
    "mutation,kind",
    [
        ("components", "meta"),
        ("features", "points"),
        ("cluster", "points"),
        ("sorted", "neighbors"),
        ("holdout", "comparison"),
        ("license", "comparison"),
    ],
)
def test_invalid_optional_payloads(mutation, kind, web_responses, web_client):
    if mutation == "components":
        web_responses["meta"]["pca"]["components"][0][0] = 0.5
    elif mutation == "features":
        web_responses["points"]["points"]["raw_features"][0].pop()
    elif mutation == "cluster":
        web_responses["points"]["points"]["cluster"][0] = 7
    elif mutation == "sorted":
        web_responses["neighbors"]["neighbors"] = [
            {
                **web_responses["neighbors"]["neighbors"][0],
                "index": 2,
                "distance": 3.0,
            },
            {
                **web_responses["neighbors"]["neighbors"][0],
                "index": 3,
                "distance": 1.0,
            },
        ]
    elif mutation == "holdout":
        web_responses["comparison"]["holdout_evaluated"] = True
    else:
        web_responses["comparison"]["license"]["license"] = "unknown"
    call = {
        "meta": web_client.visualization_meta,
        "points": web_client.visualization_points,
        "neighbors": lambda: web_client.visualization_neighbors(0),
        "comparison": web_client.research,
    }[kind]
    with pytest.raises(APIError, match="unexpected response"):
        call()


def test_neighbor_identity_and_bounds(web_responses, web_client):
    with pytest.raises(APIError):
        web_client.visualization_neighbors(1)
    with pytest.raises(ValueError):
        web_client.visualization_neighbors(-1)
    with pytest.raises(ValueError):
        web_client.visualization_neighbors(0, 13)
