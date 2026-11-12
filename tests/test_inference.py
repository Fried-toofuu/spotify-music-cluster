import json
import subprocess
import sys

import numpy as np
import pandas as pd
import pytest
from sklearn.cluster import KMeans
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import RobustScaler

from spotify_cluster.config import F9
from spotify_cluster.inference import InferenceService, input_matrix


def test_single_batch_distances_and_no_runtime_io(
    artifact, matrix, pipeline, monkeypatch
):
    service = InferenceService(artifact)

    def forbidden(*args, **kwargs):
        pytest.fail("Inference attempted training or CSV access")

    monkeypatch.setattr(KMeans, "fit", forbidden)
    monkeypatch.setattr(RobustScaler, "fit", forbidden)
    monkeypatch.setattr(Pipeline, "fit", forbidden)
    monkeypatch.setattr(pd, "read_csv", forbidden)
    tracks = [dict(zip(reversed(F9), reversed(row), strict=True)) for row in matrix[:3]]
    results = service.predict_batch(tracks)
    assert service.predict_one(tracks[0]) == results[0]
    scaled = (matrix[:3] - pipeline[0].center_) / pipeline[0].scale_
    distances = np.linalg.norm(
        scaled[:, None] - pipeline[1].cluster_centers_[None], axis=2
    )
    np.testing.assert_allclose([r["distances"] for r in results], distances)
    assert [r["cluster_id"] for r in results] == distances.argmin(axis=1).tolist()
    for result in results:
        assert result["profile"]["cluster_id"] == result["cluster_id"]
        assert "not probabilities" in result["limitation"]
    results[0]["profile"]["count"] = -1
    assert service.predict_one(tracks[0])["profile"]["count"] > 0


@pytest.mark.parametrize(
    "value",
    [
        True,
        np.bool_(False),
        "0.5",
        None,
        np.nan,
        np.inf,
        -np.inf,
        complex(1, 0),
        [],
        1.1,
        -0.1,
    ],
)
def test_reject_invalid_features(matrix, value):
    track = dict(zip(F9, matrix[0], strict=True))
    track["energy"] = value
    with pytest.raises(ValueError):
        input_matrix([track])


@pytest.mark.parametrize(
    "fault", ["missing", "extra", "empty", "dimension", "negative-tempo"]
)
def test_schema_and_tempo(matrix, fault):
    track = dict(zip(F9, matrix[0], strict=True))
    tracks = [track]
    if fault == "missing":
        del track["energy"]
    elif fault == "extra":
        track["track_genre"] = "forbidden-input"
    elif fault == "empty":
        tracks = []
    elif fault == "dimension":
        tracks = matrix
    else:
        track["tempo"] = -1
    with pytest.raises(ValueError):
        input_matrix(tracks)


def test_zero_tempo_and_unbounded_loudness(matrix):
    track = dict(zip(F9, matrix[0], strict=True))
    track.update(tempo=0, loudness=5)
    assert input_matrix([track])[0, 4] == 0


def test_clean_process_inference_without_dataset(artifact, matrix, tmp_path):
    track = dict(zip(F9, matrix[0].tolist(), strict=True))
    code = (
        "import json,sys; from pathlib import Path; "
        "from spotify_cluster.inference import InferenceService; "
        "s=InferenceService(Path(sys.argv[1])); "
        "print(json.dumps(s.predict_batch([json.loads(sys.argv[2])]*2)))"
    )
    process = subprocess.run(
        [sys.executable, "-I", "-c", code, str(artifact), json.dumps(track)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
    )
    results = json.loads(process.stdout)
    expected = InferenceService(artifact).predict_one(track)
    assert results == [expected, expected]
