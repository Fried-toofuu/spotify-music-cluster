import importlib
import json

import pytest
from fastapi.testclient import TestClient

from spotify_cluster.api.app import create_app, resolve_model_dir
from spotify_cluster.api.dependencies import get_service
from spotify_cluster.config import F9


def test_health_metadata_profiles_and_openapi(api_client):
    health = api_client.get("/api/v1/health")
    assert health.status_code == 200
    assert health.json() == {
        "service": "spotify-music-clustering-web",
        "version": "0.1.0",
        "status": "ready",
        "model_loaded": True,
    }
    model = api_client.get("/api/v1/model").json()
    assert model["model_id"] == "software-fixture-only"
    assert model["features"] == list(F9)
    assert model["model_origin"] == "new_deployment_refit"
    assert model["historical_equivalence"] == "not_verified"
    assert model["modeling_pca"] is None
    assert model["algorithm"] == "KMeans"
    assert model["scaler"] == "RobustScaler"
    assert "PRIVATE-METADATA-MARKER" not in json.dumps(model)
    profiles = api_client.get("/api/v1/clusters").json()
    assert profiles["model_id"] == model["model_id"]
    assert set(profiles["clusters"]) == {"0", "1"}
    assert "instrumentalness" in profiles["interpretation"]
    for profile in profiles["clusters"].values():
        for stat in ("mean", "median", "std", "q1", "q3", "iqr"):
            assert set(profile[stat]) == set(F9)
    assert api_client.get("/docs").status_code == 200
    spec = api_client.get("/openapi.json").json()
    assert set(spec["paths"]) == {
        "/api/v1/health",
        "/api/v1/model",
        "/api/v1/clusters",
        "/api/v1/predict",
        "/api/v1/predict/batch",
    }
    assert spec["components"]["schemas"]["Track"]["additionalProperties"] is False


def test_model_loads_once_and_clears_on_shutdown(software_service, tmp_path, api_track):
    calls = []

    def load(path):
        calls.append(path)
        return software_service

    app = create_app(tmp_path, service_factory=load)
    assert not calls
    for expected_loads in (1, 2):
        with TestClient(app) as client:
            assert len(calls) == expected_loads
            for _ in range(2):
                assert client.get("/api/v1/health").status_code == 200
                assert client.post("/api/v1/predict", json=api_track).status_code == 200
                assert app.state.inference_service is software_service
            assert len(calls) == expected_loads
        assert app.state.inference_service is None


@pytest.mark.parametrize(
    "route", ["health", "model", "clusters", "predict", "predict/batch"]
)
def test_unavailable_runtime_state(api_client, api_track, route):
    api_client.app.state.inference_service = None
    if route == "predict":
        response = api_client.post(f"/api/v1/{route}", json=api_track)
    elif route == "predict/batch":
        response = api_client.post(f"/api/v1/{route}", json={"tracks": [api_track]})
    else:
        response = api_client.get(f"/api/v1/{route}")
    assert response.status_code == 503
    assert response.json() == {"detail": "Model service unavailable"}


@pytest.mark.parametrize("fault", ["missing", "checksum"])
def test_fail_fast_artifact(tmp_path, fault, monkeypatch):
    import joblib

    def no_deserialization(*args, **kwargs):
        pytest.fail("Unverified model must not be deserialized")

    monkeypatch.setattr(joblib, "load", no_deserialization)
    if fault == "checksum":
        (tmp_path / "model_bundle.joblib").write_bytes(b"corrupted software fixture")
        (tmp_path / "verification_report.json").write_text(
            json.dumps(
                {
                    "manual_scaling": "PASS",
                    "nearest_centroid": "PASS",
                    "checksums": {"model_bundle.joblib": "incorrect"},
                }
            )
        )
    app = create_app(tmp_path)
    with pytest.raises(RuntimeError, match="Model initialization failed") as error:
        with TestClient(app):
            pytest.fail("Invalid artifact reached serving state")
    assert str(tmp_path) not in str(error.value)
    assert app.state.inference_service is None


@pytest.mark.parametrize("fault", ["identity", "schema", "origin", "historical"])
def test_fail_fast_incompatible_service(software_service, tmp_path, fault):
    if fault == "identity":
        software_service._profiles["model_id"] = "different-model"
    elif fault == "schema":
        software_service._metadata["features"] = list(reversed(F9))
    elif fault == "origin":
        software_service._metadata["model_origin"] = "software-test-only"
    else:
        software_service._metadata["historical_equivalence"] = "verified"
    with pytest.raises(RuntimeError, match="Model initialization failed"):
        with TestClient(
            create_app(tmp_path, service_factory=lambda _: software_service)
        ):
            pytest.fail("Incompatible service reached readiness")


def test_dependency_override_is_explicit_and_restored(
    api_client, api_track, software_service
):
    api_client.app.state.inference_service = None
    api_client.app.dependency_overrides[get_service] = lambda: software_service
    try:
        assert api_client.post("/api/v1/predict", json=api_track).status_code == 200
    finally:
        api_client.app.dependency_overrides.clear()
    assert api_client.get("/api/v1/health").status_code == 503


def test_import_never_loads_model(monkeypatch):
    from spotify_cluster import inference

    def forbidden(*args, **kwargs):
        pytest.fail("Module import loaded model")

    monkeypatch.setattr(inference, "load_bundle", forbidden)
    import spotify_cluster.api.app as module

    importlib.reload(module)


def test_deterministic_model_path(monkeypatch, tmp_path):
    from pathlib import Path

    monkeypatch.delenv("SPOTIFY_MODEL_DIR", raising=False)
    monkeypatch.chdir(tmp_path)
    expected = Path(__file__).resolve().parents[1] / "artifacts" / "deployment-v1"
    assert resolve_model_dir() == expected
    monkeypatch.setenv("SPOTIFY_MODEL_DIR", str(tmp_path))
    assert resolve_model_dir() == tmp_path
    monkeypatch.setenv("SPOTIFY_MODEL_DIR", "relative/path")
    with pytest.raises(ValueError, match="absolute"):
        resolve_model_dir()


def test_sanitized_internal_error(
    api_client, api_track, software_service, monkeypatch, caplog
):
    def broken(track):
        raise RuntimeError("PRIVATE-PAYLOAD-OR-PATH")

    monkeypatch.setattr(software_service, "predict_one", broken)
    with TestClient(api_client.app, raise_server_exceptions=False) as client:
        response = client.post("/api/v1/predict", json=api_track)
    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error"}
    assert "PRIVATE-PAYLOAD-OR-PATH" not in caplog.text
    assert "RuntimeError" in caplog.text
