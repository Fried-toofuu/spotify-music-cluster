import numpy as np
import pytest
from sklearn.cluster import KMeans
from sklearn.preprocessing import RobustScaler

from spotify_cluster.config import final_kmeans_params
from spotify_cluster.training import cluster_profiles, train_model, verify_numerics


def test_selected_pipeline_and_profiles(matrix, pipeline):
    assert list(pipeline.named_steps) == ["scaler", "kmeans"]
    assert type(pipeline[0]) is RobustScaler
    assert type(pipeline[1]) is KMeans
    assert pipeline[1].n_clusters == 2
    assert pipeline[0].center_.shape == (9,)
    assert pipeline[1].cluster_centers_.shape == (2, 9)
    profiles = cluster_profiles(pipeline, matrix, "test")
    assert sum(p["count"] for p in profiles["clusters"].values()) == len(matrix)
    for label in range(2):
        selected = matrix[pipeline.predict(matrix) == label]
        profile = profiles["clusters"][str(label)]
        np.testing.assert_allclose(
            list(profile["mean"].values()), selected.mean(axis=0)
        )
        np.testing.assert_allclose(
            list(profile["std"].values()), selected.std(axis=0, ddof=1)
        )
    assert verify_numerics(pipeline, matrix)["nearest_centroid"] == "PASS"


def test_repeat_fitting_and_zero_iqr(matrix, params):
    matrix[:, 0] = 0.5
    first = train_model(matrix, params)
    second = train_model(matrix, params)
    assert first[0].scale_[0] == 1
    verify_numerics(first, matrix)
    np.testing.assert_allclose(first[0].center_, second[0].center_)
    np.testing.assert_allclose(first[0].scale_, second[0].scale_)
    # Match each centroid by distance, then compare the corresponding labels.
    match = np.linalg.norm(
        first[1].cluster_centers_[:, None] - second[1].cluster_centers_[None, :], axis=2
    ).argmin(axis=1)
    assert len(set(match)) == 2
    np.testing.assert_allclose(
        first[1].cluster_centers_, second[1].cluster_centers_[match]
    )
    np.testing.assert_array_equal(match[first.predict(matrix)], second.predict(matrix))


def test_training_requires_complete_configuration(matrix):
    with pytest.raises(ValueError, match="explicit"):
        train_model(matrix, {"n_clusters": 2})


def test_no_export_without_final_parameter_evidence():
    with pytest.raises(RuntimeError, match="BLOCKED"):
        final_kmeans_params()
