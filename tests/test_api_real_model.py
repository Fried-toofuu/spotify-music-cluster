"""Opt-in private bundle integration; never loads CSV, notebook or refits."""

import json
from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient

from spotify_cluster.api.app import create_app
from spotify_cluster.config import F9
from spotify_cluster.inference import InferenceService


def test_real_api_matches_verified_sample_without_training_or_data(
    request, monkeypatch
):
    if not request.config.getoption("--run-real-api"):
        pytest.skip("Private API verification requires --run-real-api (no refit)")
    import pandas as pd
    from sklearn.cluster import KMeans
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import RobustScaler

    def forbidden(*args, **kwargs):
        pytest.fail("API attempted model fitting or raw dataset/notebook access")

    for cls in (KMeans, RobustScaler, Pipeline):
        for method in ("fit", "fit_predict", "fit_transform"):
            if hasattr(cls, method):
                monkeypatch.setattr(cls, method, forbidden)
    monkeypatch.setattr(pd, "read_csv", forbidden)
    original_open = Path.open

    def guarded_open(path, *args, **kwargs):
        if path.suffix in (".csv", ".ipynb"):
            forbidden()
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded_open)
    artifact = Path(__file__).resolve().parents[1] / "artifacts" / "deployment-v1"
    sample = json.loads((artifact / "verification_sample.json").read_text())
    metadata = json.loads((artifact / "metadata.json").read_text())
    profiles = json.loads((artifact / "cluster_profiles.json").read_text())
    loads = []

    def load(path):
        loads.append(path)
        return InferenceService(path)

    tracks = [
        dict(zip(reversed(F9), reversed(row), strict=True)) for row in sample["raw_f9"]
    ]
    with TestClient(create_app(artifact, service_factory=load)) as client:
        assert client.get("/api/v1/health").json()["model_loaded"] is True
        public = client.get("/api/v1/model").json()
        assert public["model_id"] == metadata["model_id"] == sample["model_id"]
        assert public["features"] == list(F9)
        assert public["historical_equivalence"] == "not_verified"
        aggregate = client.get("/api/v1/clusters").json()
        assert aggregate["model_id"] == metadata["model_id"]
        assert aggregate["clusters"] == profiles["clusters"]
        assert aggregate["feature_contributions"] == profiles["feature_contributions"]
        response = client.post("/api/v1/predict/batch", json={"tracks": tracks})
        assert response.status_code == 200
        results = response.json()["predictions"]
        np.testing.assert_array_equal(
            [r["cluster_id"] for r in results], sample["predictions"]
        )
        np.testing.assert_allclose(
            [r["distances"] for r in results], sample["distances"], rtol=1e-9, atol=1e-7
        )
        for track, expected in zip(tracks, results, strict=True):
            response = client.post("/api/v1/predict", json=track)
            assert response.status_code == 200
            single = response.json()
            np.testing.assert_allclose(
                single.pop("distances"), expected["distances"], rtol=1e-9, atol=1e-7
            )
            assert single == {k: v for k, v in expected.items() if k != "distances"}
            assert (
                expected["profile"] == profiles["clusters"][str(expected["cluster_id"])]
            )
        assert loads == [artifact]


def test_public_metadata_accessors_are_defensive(artifact):
    """Software bundle fixture checks the public read-only service boundary."""
    service = InferenceService(artifact)
    original = service.metadata
    changed = service.metadata
    changed["features"].reverse()
    assert service.metadata == original
    profiles = service.profiles
    profiles["clusters"]["0"]["count"] = -1
    assert service.profiles["clusters"]["0"]["count"] > 0
