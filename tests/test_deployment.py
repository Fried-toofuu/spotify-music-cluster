"""Deployment recipe and artifact changes use synthetic software fixtures here."""

import json
import subprocess
import sys
from dataclasses import FrozenInstanceError
from pathlib import Path

import joblib
import numpy as np
import pytest

from spotify_cluster.config import DEPLOYMENT_V1, F9, training_profile
from spotify_cluster.model_store import load_bundle, make_metadata, save_bundle
from spotify_cluster.training import cluster_profiles, train_model, verify_numerics
from spotify_cluster.verification import make_verification_sample, verify_sample


def test_approved_profile_is_explicit_and_immutable():
    profile = training_profile("deployment-v1")
    assert profile.identifier == "spotify-f9-robust-kmeans-k2-v1"
    assert profile.features == F9
    assert dict(profile.kmeans_params) == {
        "n_clusters": 2,
        "init": "k-means++",
        "n_init": 20,
        "max_iter": 300,
        "tol": 1e-4,
        "random_state": 42,
        "algorithm": "lloyd",
        "copy_x": True,
        "verbose": 0,
    }
    assert dict(profile.scaler_params) == {
        "with_centering": True,
        "with_scaling": True,
        "quantile_range": (25.0, 75.0),
        "copy": True,
        "unit_variance": False,
    }
    with pytest.raises(TypeError):
        profile.kmeans_params["n_init"] = 10
    with pytest.raises(FrozenInstanceError):
        profile.identifier = "changed"
    with pytest.raises(RuntimeError, match="BLOCKED"):
        training_profile("historical-final-refit")
    with pytest.raises(ValueError, match="Unsupported"):
        training_profile("unknown")


@pytest.fixture
def deployment_parts(matrix):
    profile = DEPLOYMENT_V1
    pipeline = train_model(matrix, dict(profile.kmeans_params))
    metadata = make_metadata(
        pipeline,
        "software-deployment",
        {
            "training_sample_count": len(matrix),
            "dataset_sha256": "software-fixture",
        },
        reconstruction_status="software-test-only",
        profile=profile,
    )
    profiles = cluster_profiles(pipeline, matrix, metadata["model_id"])
    sample = make_verification_sample(pipeline, matrix, metadata["model_id"], size=12)
    return pipeline, metadata, profiles, verify_numerics(pipeline, matrix), sample


def test_profile_provenance_and_sample_round_trip(tmp_path, deployment_parts):
    pipeline, metadata, profiles, report, sample = deployment_parts
    assert metadata["historical_equivalence"] == "NOT VERIFIED"
    assert metadata["holdout_evaluated"] is False
    assert metadata["configuration_provenance"]["n_init"].endswith("cell 82")
    assert "default" in metadata["configuration_provenance"]["max_iter"]
    output = tmp_path / "fixture"
    save_bundle(output, pipeline, metadata, profiles, report, sample)
    loaded, saved, saved_profiles = load_bundle(output)
    assert saved["training_profile"] == "deployment-v1"
    assert saved["profile_sha256"]
    assert saved["verification_sample_sha256"]
    assert saved_profiles["model_id"] == saved["model_id"]
    verify_sample(
        loaded,
        json.loads((output / "verification_sample.json").read_text()),
        saved["model_id"],
    )
    np.testing.assert_array_equal(
        loaded.predict(sample["raw_f9"]), sample["predictions"]
    )


@pytest.mark.parametrize("fault", ["predictions", "distances", "model_id", "features"])
def test_invalid_verification_samples(deployment_parts, fault):
    pipeline, metadata, _, _, sample = deployment_parts
    if fault == "predictions":
        sample["predictions"][0] = 1 - sample["predictions"][0]
    elif fault == "distances":
        sample["distances"][0][0] += 1
    elif fault == "model_id":
        sample["model_id"] = "wrong"
    else:
        sample["features"].reverse()
    with pytest.raises(ValueError, match="mismatch"):
        verify_sample(pipeline, sample, metadata["model_id"])


def test_sample_corruption_rejected_before_unpickle(
    tmp_path, deployment_parts, monkeypatch
):
    pipeline, metadata, profiles, report, sample = deployment_parts
    output = tmp_path / "fixture"
    save_bundle(output, pipeline, metadata, profiles, report, sample)
    with (output / "verification_sample.json").open("ab") as stream:
        stream.write(b"corrupt")

    def forbidden(*args, **kwargs):
        pytest.fail("Corrupt sample reached model deserialization")

    monkeypatch.setattr(joblib, "load", forbidden)
    with pytest.raises(ValueError, match="checksum"):
        load_bundle(output)


def test_profile_requires_sample_and_frozen_parameters(tmp_path, deployment_parts):
    pipeline, metadata, profiles, report, sample = deployment_parts
    with pytest.raises(ValueError, match="requires a verification sample"):
        save_bundle(tmp_path / "no-sample", pipeline, metadata, profiles, report)
    pipeline[1].max_iter = 400
    metadata["kmeans_params"]["max_iter"] = 400
    with pytest.raises(ValueError, match="recipe"):
        save_bundle(
            tmp_path / "wrong-recipe", pipeline, metadata, profiles, report, sample
        )


def test_feature_contributions_match_two_group_identity(matrix, pipeline):
    profiles = cluster_profiles(pipeline, matrix, "fixture")
    scaled = pipeline[0].transform(matrix)
    labels = pipeline.predict(matrix)
    a, b = scaled[labels == 0], scaled[labels == 1]
    independent = len(a) * len(b) / len(matrix) * (a.mean(axis=0) - b.mean(axis=0)) ** 2
    shares = profiles["feature_contributions"]["shares"]
    np.testing.assert_allclose(list(shares.values()), independent / independent.sum())
    assert np.isclose(sum(shares.values()), 1)


def test_unsupported_cli_profile_fails_without_dataset(tmp_path):
    script = Path(__file__).resolve().parents[1] / "scripts" / "export_model.py"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--profile",
            "unknown",
            "--dataset",
            "missing.csv",
            "--output",
            str(tmp_path / "invalid"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert "invalid choice" in result.stderr
    assert not (tmp_path / "invalid").exists()
