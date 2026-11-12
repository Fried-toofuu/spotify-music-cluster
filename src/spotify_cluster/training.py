"""Offline fitting and training-consistency checks; never independent evaluation."""

import warnings

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.exceptions import ConvergenceWarning
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import RobustScaler
from threadpoolctl import threadpool_limits

from .config import F9, SCALER_PARAMS
from .data import validate_matrix

_REQUIRED_KMEANS_PARAMS = frozenset(
    {
        "n_clusters",
        "init",
        "n_init",
        "max_iter",
        "tol",
        "algorithm",
        "random_state",
        "copy_x",
        "verbose",
    }
)


def train_model(matrix: np.ndarray, kmeans_params: dict) -> Pipeline:
    """Fit explicit settings; the caller owns provenance and population."""
    matrix = validate_matrix(matrix)
    if (
        set(kmeans_params) != _REQUIRED_KMEANS_PARAMS
        or kmeans_params["n_clusters"] != 2
    ):
        raise ValueError("An explicit, complete K=2 configuration is required")
    pipeline = Pipeline(
        [
            ("scaler", RobustScaler(**SCALER_PARAMS)),
            ("kmeans", KMeans(**kmeans_params)),
        ]
    )
    with warnings.catch_warnings(), threadpool_limits(limits=1):
        warnings.simplefilter("error", ConvergenceWarning)
        pipeline.fit(matrix)
    estimator = pipeline.named_steps["kmeans"]
    if estimator.n_iter_ >= estimator.max_iter:
        raise ValueError("K-Means reached the iteration limit; convergence unverified")
    if estimator.cluster_centers_.shape != (2, 9):
        raise ValueError("Unexpected centroid dimensions")
    if not np.isfinite(estimator.cluster_centers_).all():
        raise ValueError("Nonfinite fitted centroids")
    if set(pipeline.predict(matrix)) != {0, 1}:
        raise ValueError("Training did not produce two populated clusters")
    return pipeline


def cluster_profiles(pipeline: Pipeline, matrix: np.ndarray, model_id: str) -> dict:
    """Describe actual assignments in raw units; std is sample std (ddof=1)."""
    matrix = validate_matrix(matrix)
    labels = pipeline.predict(matrix)
    profiles = {}
    for label in range(2):
        frame = pd.DataFrame(matrix[labels == label], columns=F9)
        if frame.empty:
            raise ValueError("Cannot profile an empty cluster")
        count = len(frame)
        q1, q3 = frame.quantile(0.25), frame.quantile(0.75)
        stats = {
            "mean": frame.mean(),
            "median": frame.median(),
            "std": frame.std(ddof=1).fillna(0),
            "q1": q1,
            "q3": q3,
            "iqr": q3 - q1,
        }
        profiles[str(label)] = {
            "cluster_id": label,
            "count": count,
            "share": count / len(matrix),
            **{key: value.to_dict() for key, value in stats.items()},
        }
    scaled = pipeline.named_steps["scaler"].transform(matrix)
    mean_all = scaled.mean(axis=0)
    contributions = np.zeros(len(F9))
    for label in range(2):
        group = scaled[labels == label]
        contributions += len(group) * (group.mean(axis=0) - mean_all) ** 2
    if contributions.sum() <= 0:
        raise ValueError("No between-cluster separation to profile")
    return {
        "model_id": model_id,
        "units": "raw F9",
        "std_ddof": 1,
        "singleton_std": 0,
        "clusters": profiles,
        "feature_contributions": {
            "definition": (
                "Per-feature between-cluster sum of squares "
                "in fitted RobustScaler space"
            ),
            "population": "all training assignments; no Holdout evaluation",
            "between_ss": dict(zip(F9, contributions.tolist(), strict=True)),
            "shares": dict(
                zip(F9, (contributions / contributions.sum()).tolist(), strict=True)
            ),
        },
    }


def verify_numerics(pipeline: Pipeline, matrix: np.ndarray) -> dict:
    """Independently check quantiles, zero-IQR handling, SSE and nearest centroids."""
    matrix = validate_matrix(matrix)
    scaler, estimator = pipeline.named_steps.values()
    median = np.median(matrix, axis=0)
    q1, q3 = np.percentile(matrix, [25, 75], axis=0)
    scale = q3 - q1
    scale[scale < 10 * np.finfo(scale.dtype).eps] = 1
    manual = (matrix - median) / scale
    np.testing.assert_allclose(scaler.center_, median, rtol=1e-12, atol=1e-12)
    np.testing.assert_allclose(scaler.scale_, scale, rtol=1e-12, atol=1e-12)
    np.testing.assert_allclose(scaler.transform(matrix), manual, rtol=1e-12, atol=1e-12)
    distances = np.linalg.norm(
        manual[:, None, :] - estimator.cluster_centers_[None, :, :], axis=2
    )
    labels = pipeline.predict(matrix)
    np.testing.assert_array_equal(labels, distances.argmin(axis=1))
    np.testing.assert_allclose(
        pipeline.transform(matrix), distances, rtol=1e-9, atol=1e-7
    )
    sse = float(np.square(manual - estimator.cluster_centers_[labels]).sum())
    np.testing.assert_allclose(sse, estimator.inertia_, rtol=1e-8, atol=1e-6)
    return {
        "manual_scaling": "PASS",
        "nearest_centroid": "PASS",
        "sse": sse,
        "verified_rows": len(matrix),
        "historical_equivalence": "NOT VERIFIED",
        "scope": "Training consistency only; no independent Holdout evaluation",
    }
