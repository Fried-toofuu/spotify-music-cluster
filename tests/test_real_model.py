"""Opt-in private dataset checks; default public software tests never need the CSV."""

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
from scipy.optimize import linear_sum_assignment

from spotify_cluster.config import DEPLOYMENT_V1, F9, TRACK_COUNT
from spotify_cluster.data import load_dataset, sha256_file
from spotify_cluster.inference import InferenceService
from spotify_cluster.model_store import load_bundle
from spotify_cluster.training import cluster_profiles, verify_numerics
from spotify_cluster.verification import verify_sample

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "artifacts" / "deployment-v1"
NOTEBOOK_HASH = "76a31ac55e385238761d7decbc5117cede6f1ad8a2c9285504e80c4a2526b178"


@pytest.fixture(scope="module")
def real_model(request):
    if not request.config.getoption("--run-real-model"):
        pytest.skip("Private dataset/model verification requires --run-real-model")
    prepared, identity = load_dataset(ROOT / "dataset.csv")
    pipeline, metadata, profiles = load_bundle(ARTIFACT)
    sample = json.loads((ARTIFACT / "verification_sample.json").read_text())
    return prepared, identity, pipeline, metadata, profiles, sample


def test_real_population_recipe_profiles_and_math(real_model):
    prepared, identity, pipeline, metadata, profiles, sample = real_model
    assert prepared.matrix.shape == (TRACK_COUNT, 9)
    assert metadata["dataset_sha256"] == identity["dataset_sha256"]
    assert metadata["prepared_fingerprint"] == identity["prepared_fingerprint"]
    assert metadata["model_origin"] == "new_deployment_refit"
    assert metadata["historical_equivalence"] == "NOT VERIFIED"
    assert metadata["holdout_evaluated"] is False
    assert metadata["kmeans_params"] == dict(DEPLOYMENT_V1.kmeans_params)
    assert sum(metadata["cluster_counts"]) == TRACK_COUNT
    assert verify_numerics(pipeline, prepared.matrix)["manual_scaling"] == "PASS"
    assert cluster_profiles(pipeline, prepared.matrix, metadata["model_id"]) == profiles
    positions = sample["row_positions"]
    np.testing.assert_array_equal(sample["raw_f9"], prepared.matrix[positions])
    verify_sample(pipeline, sample, metadata["model_id"])
    scaled = pipeline[0].transform(prepared.matrix)
    labels = pipeline.predict(prepared.matrix)
    a, b = scaled[labels == 0], scaled[labels == 1]
    independent = len(a) * len(b) / TRACK_COUNT * (a.mean(axis=0) - b.mean(axis=0)) ** 2
    np.testing.assert_allclose(
        list(profiles["feature_contributions"]["between_ss"].values()),
        independent,
        rtol=1e-10,
        atol=1e-8,
    )
    assert sha256_file(ROOT / "Spotify_Music_Clustering_Final.ipynb") == NOTEBOOK_HASH


def test_real_single_batch_profile_order_without_fitting(real_model, monkeypatch):
    _, _, pipeline, metadata, _, sample = real_model
    import pandas as pd
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import RobustScaler

    def forbidden(*args, **kwargs):
        pytest.fail("Inference attempted to fit or read the dataset")

    monkeypatch.setattr(KMeans, "fit", forbidden)
    monkeypatch.setattr(RobustScaler, "fit", forbidden)
    monkeypatch.setattr(pd, "read_csv", forbidden)
    service = InferenceService(ARTIFACT)
    rows = sample["raw_f9"][::-1]
    tracks = [dict(zip(reversed(F9), reversed(row), strict=True)) for row in rows]
    results = service.predict_batch(tracks)
    assert service.predict_one(tracks[0]) == results[0]
    assert [result["cluster_id"] for result in results] == sample["predictions"][::-1]
    np.testing.assert_allclose(
        [r["distances"] for r in results], sample["distances"][::-1]
    )
    for result in results:
        assert result["model_id"] == metadata["model_id"]
        assert result["profile"]["cluster_id"] == result["cluster_id"]
    np.testing.assert_array_equal(
        pipeline.predict(rows), [r["cluster_id"] for r in results]
    )


def test_real_clean_process_without_csv_or_network(real_model, tmp_path):
    code = """
import builtins, json, socket, sys
from pathlib import Path
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import RobustScaler
def forbidden(*args, **kwargs):
    raise RuntimeError("Dataset, network or training access is forbidden")
pd.read_csv = forbidden
KMeans.fit = forbidden
RobustScaler.fit = forbidden
socket.socket.connect = forbidden
socket.create_connection = forbidden
original_open = builtins.open
def guarded_open(file, *args, **kwargs):
    if str(file).endswith((".csv", ".ipynb")):
        forbidden()
    return original_open(file, *args, **kwargs)
builtins.open = guarded_open
from spotify_cluster.inference import InferenceService
from spotify_cluster.config import F9
artifact = Path(sys.argv[1])
sample = json.loads((artifact / "verification_sample.json").read_text())
tracks = [dict(zip(F9, row)) for row in sample["raw_f9"]]
service = InferenceService(artifact)
results = service.predict_batch(tracks)
assert service.predict_one(tracks[0]) == results[0]
assert [r["cluster_id"] for r in results] == sample["predictions"]
print(json.dumps({"status": "PASS", "model_id": results[0]["model_id"]}))
"""
    result = subprocess.run(
        [sys.executable, "-I", "-c", code, str(ARTIFACT)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(result.stdout)["status"] == "PASS"


def test_real_sequential_reconstruction(real_model, tmp_path):
    prepared, identity, original, metadata, _, sample = real_model
    output = tmp_path / "controlled-reconstruction"
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "export_model.py"),
            "--dataset",
            str(ROOT / "dataset.csv"),
            "--output",
            str(output),
            "--profile",
            "deployment-v1",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    reloaded, repeated_metadata, _ = load_bundle(output)
    assert (
        json.loads(result.stdout.splitlines()[-1])["model_id"]
        == repeated_metadata["model_id"]
    )
    assert verify_numerics(reloaded, prepared.matrix)["nearest_centroid"] == "PASS"
    np.testing.assert_array_equal(original[0].center_, reloaded[0].center_)
    np.testing.assert_array_equal(original[0].scale_, reloaded[0].scale_)
    distances = np.linalg.norm(
        original[1].cluster_centers_[:, None] - reloaded[1].cluster_centers_[None],
        axis=2,
    )
    rows, columns = linear_sum_assignment(distances)
    np.testing.assert_allclose(
        original[1].cluster_centers_[rows],
        reloaded[1].cluster_centers_[columns],
        rtol=1e-12,
        atol=1e-12,
    )
    mapping = np.empty(2, dtype=int)
    mapping[rows] = columns
    np.testing.assert_array_equal(
        mapping[original.predict(prepared.matrix)], reloaded.predict(prepared.matrix)
    )
    np.testing.assert_array_equal(
        np.asarray(metadata["cluster_counts"])[rows],
        np.asarray(repeated_metadata["cluster_counts"])[columns],
    )
    np.testing.assert_array_equal(
        mapping[np.asarray(sample["predictions"])], reloaded.predict(sample["raw_f9"])
    )
    assert repeated_metadata["model_id"] != metadata["model_id"]
