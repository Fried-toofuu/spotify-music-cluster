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
