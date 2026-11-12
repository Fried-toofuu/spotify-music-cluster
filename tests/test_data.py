import numpy as np
import pandas as pd
import pytest

from spotify_cluster.config import F9
from spotify_cluster.data import load_dataset, prepare_tracks


def test_canonical_order_bridge_and_original_preservation(raw):
    original = raw.copy(deep=True)
    duplicate = raw.iloc[[0]].copy()
    duplicate["track_id"] = " test-000 "
    duplicate["track_genre"] = " a-first "
    duplicate["acousticness"] += 1e-9  # Notebook tolerance allows this difference.
    joined = pd.concat([raw, duplicate], ignore_index=True)
    result = prepare_tracks(joined)
    assert len(result.tracks) == len(raw)
    assert len(result.genre_bridge) == len(raw) + 1
    assert result.tracks.track_id.tolist() == sorted(raw.track_id)
    np.testing.assert_array_equal(result.matrix, result.tracks.loc[:, F9].to_numpy())
    assert result.matrix[0, 0] == duplicate.acousticness.iloc[0]
    assert "track_genre" not in result.tracks
    assert result.fingerprint == prepare_tracks(joined).fingerprint
    pd.testing.assert_frame_equal(raw, original)


def test_missing_genre_does_not_drop_acoustic_track(raw):
    raw.loc[0, "track_genre"] = None
    result = prepare_tracks(raw)
    assert len(result.matrix) == len(raw)
    assert len(result.genre_bridge) == len(raw) - 1


@pytest.mark.parametrize("value", [None, "", "   "])
def test_missing_identifier(raw, value):
    raw.loc[0, "track_id"] = value
    with pytest.raises(ValueError, match="Missing track_id"):
        prepare_tracks(raw)


def test_missing_required_column(raw):
    with pytest.raises(ValueError, match="columns"):
        prepare_tracks(raw.drop(columns="energy"))


@pytest.mark.parametrize("value", ["invalid", np.nan, np.inf, True, -1, 1.01])
def test_numeric_validation(raw, value):
    raw["energy"] = raw["energy"].astype(object)
    raw.loc[0, "energy"] = value
    with pytest.raises((ValueError, TypeError)):
        prepare_tracks(raw)


def test_conflicting_duplicate(raw):
    duplicate = raw.iloc[[0]].copy()
    duplicate["energy"] = 0
    with pytest.raises(ValueError, match="conflict"):
        prepare_tracks(pd.concat([raw, duplicate]))


def test_fingerprint_tracks_actual_vector(raw):
    before = prepare_tracks(raw)
    raw.loc[0, "energy"] = 0
    assert before.fingerprint != prepare_tracks(raw).fingerprint


def test_wrong_dataset_bytes_rejected_before_read(tmp_path):
    csv = tmp_path / "wrong.csv"
    csv.write_text("not the authorized snapshot")
    with pytest.raises(ValueError, match="SHA-256"):
        load_dataset(csv)
