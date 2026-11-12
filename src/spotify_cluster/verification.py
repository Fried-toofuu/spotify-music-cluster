"""Private deterministic sample evidence and independent centroid arithmetic."""

import numpy as np
from sklearn.pipeline import Pipeline

from .config import F9
from .data import validate_matrix


def make_verification_sample(
    pipeline: Pipeline, matrix: np.ndarray, model_id: str, size: int = 32
) -> dict:
    """Select equally spaced canonical positions; store no identifiers or metadata."""
    matrix = validate_matrix(matrix)
    if type(size) is not int or size < 1:
        raise ValueError("Verification sample size must be a positive integer")
    positions = np.linspace(0, len(matrix) - 1, min(size, len(matrix)), dtype=int)
    selected = matrix[positions]
    scaled = pipeline.named_steps["scaler"].transform(selected)
    centers = pipeline.named_steps["kmeans"].cluster_centers_
    squared = np.square(scaled[:, None, :] - centers[None, :, :]).sum(axis=2)
    sample = {
        "model_id": model_id,
        "features": list(F9),
        "selection": "Equally spaced canonical positions, including endpoints",
        "row_positions": positions.tolist(),
        "raw_f9": selected.tolist(),
        "predictions": pipeline.predict(selected).tolist(),
        "distances": pipeline.transform(selected).tolist(),
        "squared_distances": squared.tolist(),
        "scope": "Training consistency only; no independent Holdout evaluation",
    }
    verify_sample(pipeline, sample, model_id)
    return sample


def verify_sample(pipeline: Pipeline, sample: dict, model_id: str) -> None:
    """Check saved expectations against NumPy arithmetic and model predictions."""
    if sample.get("model_id") != model_id or sample.get("features") != list(F9):
        raise ValueError("Verification sample identity or schema mismatch")
    matrix = validate_matrix(sample.get("raw_f9", []))
    positions = sample.get("row_positions", [])
    if (
        len(positions) != len(matrix)
        or len(set(positions)) != len(positions)
        or any(
            type(p) is not int or not 0 <= p < len(pipeline[-1].labels_)
            for p in positions
        )
    ):
        raise ValueError("Invalid verification sample positions")
    scaler, estimator = pipeline.named_steps.values()
    scaled = (matrix - scaler.center_) / scaler.scale_
    squared = np.square(
        scaled[:, None, :] - estimator.cluster_centers_[None, :, :]
    ).sum(axis=2)
    distances = np.sqrt(squared)
    labels = squared.argmin(axis=1)
    try:
        np.testing.assert_array_equal(sample.get("predictions"), labels)
        np.testing.assert_array_equal(
            sample.get("predictions"), estimator.labels_[positions]
        )
        np.testing.assert_array_equal(pipeline.predict(matrix), labels)
        np.testing.assert_array_equal(estimator.predict(scaled), labels)
        for name, expected in (
            ("distances", distances),
            ("squared_distances", squared),
        ):
            actual = np.asarray(sample.get(name), dtype=float)
            if actual.shape != expected.shape:
                raise ValueError("Verification sample distance dimensions mismatch")
            np.testing.assert_allclose(actual, expected, rtol=1e-9, atol=1e-7)
        np.testing.assert_allclose(
            pipeline.transform(matrix), distances, rtol=1e-9, atol=1e-7
        )
    except AssertionError as exc:
        raise ValueError(
            "Verification sample predictions or distances mismatch"
        ) from exc
