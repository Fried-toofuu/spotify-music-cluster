import json

import pytest


@pytest.mark.parametrize(
    "field,value",
    [
        ("energy", True),
        ("energy", "0.5"),
        ("energy", None),
        ("energy", -0.1),
        ("energy", 1.01),
        ("energy", []),
        ("tempo", -1),
        ("tempo", "120"),
        ("loudness", False),
        ("energy", {"value": 0.5}),
    ],
)
def test_invalid_numeric_domains(api_client, api_track, software_service, field, value):
    response = api_client.post("/api/v1/predict", json={**api_track, field: value})
    assert response.status_code == 422
    assert not software_service.calls


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
@pytest.mark.parametrize("field", ["energy", "tempo", "loudness"])
def test_nonfinite_json_is_sanitized_422(api_client, api_track, value, field):
    response = api_client.post(
        "/api/v1/predict",
        content=json.dumps({**api_track, field: value}),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 422
    assert all(
        "input" not in error and "ctx" not in error
        for error in response.json()["detail"]
    )


@pytest.mark.parametrize(
    "fault", ["missing", "extra", "empty", "nested", "list", "null", "malformed"]
)
def test_invalid_structure(api_client, api_track, fault):
    payload = api_track.copy()
    if fault == "missing":
        payload.pop("energy")
    elif fault == "extra":
        payload["unexpected"] = "PRIVATE-INPUT-MARKER"
    elif fault == "empty":
        payload = {}
    elif fault == "nested":
        payload = {"track": api_track}
    elif fault == "list":
        payload = [api_track]
    elif fault == "null":
        payload = None
    response = api_client.post(
        "/api/v1/predict",
        content="{broken" if fault == "malformed" else json.dumps(payload),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 422
    assert "PRIVATE-INPUT-MARKER" not in response.text


@pytest.mark.parametrize(
    "fault", ["empty", "oversize", "mixed", "missing", "extra", "wrong-container"]
)
def test_invalid_batch(api_client, api_track, software_service, fault):
    payload = {"tracks": [api_track]}
    if fault == "empty":
        payload["tracks"] = []
    elif fault == "oversize":
        payload["tracks"] *= 101
    elif fault == "mixed":
        payload["tracks"].append({**api_track, "energy": "PRIVATE-INPUT-MARKER"})
    elif fault == "missing":
        payload = {}
    elif fault == "extra":
        payload["model_dir"] = "PRIVATE-INPUT-MARKER"
    else:
        payload["tracks"] = api_track
    response = api_client.post("/api/v1/predict/batch", json=payload)
    assert response.status_code == 422
    assert "PRIVATE-INPUT-MARKER" not in response.text
    assert not software_service.calls


def test_no_upload_sample_dataset_or_cors_surface(api_client):
    for path in (
        "/api/v1/train",
        "/api/v1/upload",
        "/api/v1/data",
        "/verification_sample.json",
    ):
        assert api_client.get(path).status_code == 404
    response = api_client.options(
        "/api/v1/predict",
        headers={
            "Origin": "https://untrusted.example",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert "access-control-allow-origin" not in response.headers


def test_oversized_request_body_is_rejected(api_client):
    response = api_client.post(
        "/api/v1/predict",
        content=b"x" * (70 * 1024),
        headers={"content-type": "application/json"},
    )
    assert response.status_code == 413
    assert response.json() == {"detail": "Request body too large"}
