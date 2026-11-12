import json
import subprocess
import sys

import joblib
import numpy as np
import pytest
from sklearn.preprocessing import StandardScaler

from spotify_cluster.data import sha256_file
from spotify_cluster.model_store import load_bundle, save_bundle


def test_round_trip_and_fresh_process(artifact, matrix, pipeline, tmp_path):
    loaded, metadata, profiles = load_bundle(artifact)
    np.testing.assert_array_equal(loaded.predict(matrix), pipeline.predict(matrix))
    assert metadata["model_id"] == profiles["model_id"]
    inputs = tmp_path / "inputs.json"
    inputs.write_text(json.dumps(matrix.tolist()))
    code = (
        "import json,sys,numpy as np; "
        "from pathlib import Path; "
        "from spotify_cluster.model_store import load_bundle; "
        "p,m,c=load_bundle(Path(sys.argv[1])); "
        "print(json.dumps(p.predict(np.array(json.loads(Path(sys.argv[2]).read_text()))).tolist()))"
    )
    result = subprocess.run(
        [sys.executable, "-I", "-c", code, str(artifact), str(inputs)],
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(result.stdout) == pipeline.predict(matrix).tolist()


@pytest.mark.parametrize(
    "name", ["model_bundle.joblib", "metadata.json", "cluster_profiles.json"]
)
def test_corruption_rejected_before_unpickle(artifact, name, monkeypatch):
    with (artifact / name).open("ab") as stream:
        stream.write(b"corruption")

    def forbidden(*args, **kwargs):
        pytest.fail("Corrupted bundle reached unsafe deserialization")

    monkeypatch.setattr(joblib, "load", forbidden)
    with pytest.raises(ValueError, match="checksum"):
        load_bundle(artifact)


def test_environment_mismatch_before_unpickle(artifact, monkeypatch):
    path = artifact / "metadata.json"
    metadata = json.loads(path.read_text())
    metadata["environment"]["scikit_learn"] = "incompatible"
    path.write_text(json.dumps(metadata))
    report_path = artifact / "verification_report.json"
    report = json.loads(report_path.read_text())
    report["checksums"]["metadata.json"] = sha256_file(path)
    report_path.write_text(json.dumps(report))

    def forbidden(*args, **kwargs):
        pytest.fail("Incompatible environment reached deserialization")

    monkeypatch.setattr(joblib, "load", forbidden)
    with pytest.raises(ValueError, match="environment mismatch"):
        load_bundle(artifact)


def test_no_overwrite(artifact, pipeline, bundle_parts):
    with pytest.raises(FileExistsError):
        save_bundle(artifact, pipeline, *bundle_parts)


@pytest.mark.parametrize(
    "fault", ["schema", "params", "count", "profile", "type", "production"]
)
def test_inconsistent_bundle_rejected(tmp_path, pipeline, bundle_parts, fault):
    metadata, profiles, report = bundle_parts
    if fault == "schema":
        metadata["features"].reverse()
    elif fault == "params":
        metadata["kmeans_params"]["n_init"] += 1
    elif fault == "count":
        metadata["training_sample_count"] += 1
    elif fault == "profile":
        profiles["model_id"] = "wrong-model"
    elif fault == "type":
        pipeline.steps[0] = ("scaler", StandardScaler())
    elif fault == "production":
        metadata["reconstruction_status"] = "reconstructed"
    with pytest.raises(ValueError):
        save_bundle(tmp_path / "invalid", pipeline, metadata, profiles, report)


@pytest.mark.parametrize("fault", ["scale-shape", "labels", "convergence"])
def test_invalid_fitted_state_rejected(tmp_path, pipeline, bundle_parts, fault):
    if fault == "scale-shape":
        pipeline[0].scale_ = pipeline[0].scale_[:1]
    elif fault == "labels":
        pipeline[1].labels_ = pipeline[1].labels_[:1]
    else:
        pipeline[1].n_iter_ = pipeline[1].max_iter
    with pytest.raises(ValueError, match="fitted"):
        save_bundle(tmp_path / "invalid-state", pipeline, *bundle_parts)


def test_failed_numerical_report_rejected_before_unpickle(artifact, monkeypatch):
    report_path = artifact / "verification_report.json"
    report = json.loads(report_path.read_text())
    report["nearest_centroid"] = "FAIL"
    report_path.write_text(json.dumps(report))

    def forbidden(*args, **kwargs):
        pytest.fail("Failed numerical verification reached deserialization")

    monkeypatch.setattr(joblib, "load", forbidden)
    with pytest.raises(ValueError, match="numerical verification"):
        load_bundle(artifact)
