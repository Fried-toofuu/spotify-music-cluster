"""Offline PCA visualization artifacts; never a clustering or evaluation step."""

from __future__ import annotations

import json
import platform
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from sklearn.decomposition import PCA
from sklearn.pipeline import Pipeline

from .config import (
    DATASET_LICENSE,
    DEPLOYMENT_V1,
    F9,
    VISUALIZATION_KIND,
    VISUALIZATION_LIMITATIONS,
    VISUALIZATION_OCCUPANCY_BINS,
    VISUALIZATION_OCCUPANCY_MIN_COUNT,
    VISUALIZATION_PCA_COMPONENTS,
    VISUALIZATION_PER_CLUSTER_CAP,
    VISUALIZATION_SCHEMA_VERSION,
    VISUALIZATION_SEED,
)
from .data import sha256_file, validate_matrix

_ARTIFACT = "visualization.json"
_REPORT = "verification_report.json"
_FORBIDDEN_KEYS = frozenset(
    {
        "track_id",
        "artists",
        "album_name",
        "track_name",
        "popularity",
        "duration_ms",
        "explicit",
        "key",
        "mode",
        "time_signature",
        "track_genre",
        "row_positions",
        "verification_sample",
    }
)
_COORDINATE_DECIMALS = 6
_FEATURE_DECIMALS = 8
_PROJECTION_TOLERANCE = 2e-6


def _software() -> dict:
    return {
        "python": platform.python_version(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scikit_learn": sklearn.__version__,
    }


def _rounded(values, decimals: int) -> list:
    return np.round(np.asarray(values, dtype=np.float64), decimals).tolist()


def _stratified_indices(
    labels: np.ndarray, per_cluster_cap: int, seed: int
) -> tuple[np.ndarray, list[int]]:
    if type(per_cluster_cap) is not int or per_cluster_cap < 1:
        raise ValueError("per_cluster_cap must be a positive integer")
    rng = np.random.default_rng(seed)
    chosen = []
    counts = []
    for label in (0, 1):
        positions = np.flatnonzero(labels == label)
        if not len(positions):
            raise ValueError("Visualization requires two populated clusters")
        take = min(per_cluster_cap, len(positions))
        selected = rng.choice(positions, size=take, replace=False)
        selected.sort()
        chosen.append(selected)
        counts.append(int(take))
    return np.sort(np.concatenate(chosen)), counts


def _fix_pca_signs(components: np.ndarray, coordinates: np.ndarray) -> None:
    """Deterministic sign convention so projections are stable across runs."""
    for index in range(components.shape[0]):
        anchor = int(np.argmax(np.abs(components[index])))
        if components[index, anchor] < 0:
            components[index] *= -1
            coordinates[:, index] *= -1


def _occupancy(
    coordinates: np.ndarray,
    labels: np.ndarray,
    instrumentalness: np.ndarray,
    bins: int,
    min_count: int,
) -> dict:
    if type(bins) is not int or bins < 4:
        raise ValueError("Occupancy bins must be an integer of at least 4")
    if type(min_count) is not int or min_count < 1:
        raise ValueError("Occupancy minimum count must be a positive integer")
    x, y = coordinates[:, 0], coordinates[:, 1]
    x_edges = np.linspace(float(x.min()), float(x.max()), bins + 1)
    y_edges = np.linspace(float(y.min()), float(y.max()), bins + 1)
    ix = np.clip(np.searchsorted(x_edges, x, side="right") - 1, 0, bins - 1)
    iy = np.clip(np.searchsorted(y_edges, y, side="right") - 1, 0, bins - 1)
    flat = ix * bins + iy
    size = bins * bins
    counts = np.bincount(flat, minlength=size)
    cluster1 = np.bincount(flat, weights=(labels == 1), minlength=size)
    inst_sum = np.bincount(flat, weights=instrumentalness, minlength=size)
    cells = []
    for cell in range(size):
        count = int(counts[cell])
        if count < min_count:
            continue
        row, column = divmod(cell, bins)
        cells.append(
            {
                "x": round(float((x_edges[row] + x_edges[row + 1]) / 2), 6),
                "y": round(float((y_edges[column] + y_edges[column + 1]) / 2), 6),
                "count": count,
                "cluster1_share": round(float(cluster1[cell] / count), 6),
                "mean_instrumentalness": round(float(inst_sum[cell] / count), 6),
            }
        )
    return {
        "definition": (
            "Aggregate PC1/PC2 occupancy over the full training population; "
            "individual tracks are not represented in aggregate mode"
        ),
        "bins": bins,
        "min_cell_count": min_count,
        "x_range": [round(float(x.min()), 6), round(float(x.max()), 6)],
        "y_range": [round(float(y.min()), 6), round(float(y.max()), 6)],
        "cells": cells,
    }


def build_visualization(
    pipeline: Pipeline,
    metadata: dict,
    matrix: np.ndarray,
    *,
    mode: str = "points",
    per_cluster_cap: int = VISUALIZATION_PER_CLUSTER_CAP,
    seed: int = VISUALIZATION_SEED,
    occupancy_bins: int = VISUALIZATION_OCCUPANCY_BINS,
    occupancy_min_count: int = VISUALIZATION_OCCUPANCY_MIN_COUNT,
) -> tuple[dict, dict]:
    """Project the fitted deployment representation; never fit a new clusterer."""
    if mode not in ("points", "aggregate"):
        raise ValueError("Visualization mode must be points or aggregate")
    matrix = validate_matrix(matrix)
    if metadata.get("features") != list(F9):
        raise ValueError("Model metadata feature order mismatch")
    if metadata.get("training_sample_count") != len(matrix):
        raise ValueError("Visualization matrix does not match the model population")
    if metadata.get("prepared_fingerprint") is None:
        raise ValueError("Model metadata lacks a preparation fingerprint")
    scaler = pipeline.named_steps["scaler"]
    estimator = pipeline.named_steps["kmeans"]
    labels = pipeline.predict(matrix)
    if not np.array_equal(labels, estimator.labels_):
        raise ValueError("Visualization assignments differ from fitted model labels")
    counts = np.bincount(labels, minlength=2)
    if counts.tolist() != metadata.get("cluster_counts"):
        raise ValueError("Visualization cluster totals differ from model metadata")
    scaled = scaler.transform(matrix)
    pca = PCA(
        n_components=VISUALIZATION_PCA_COMPONENTS,
        svd_solver="full",
        random_state=seed,
    )
    coordinates = pca.fit_transform(scaled)
    components = pca.components_.copy()
    _fix_pca_signs(components, coordinates)
    explained = pca.explained_variance_ratio_.tolist()
    cumulative = np.cumsum(pca.explained_variance_ratio_).tolist()
    reconstructed = (scaled - pca.mean_) @ components.T
    if not np.allclose(reconstructed, coordinates, rtol=0, atol=1e-9):
        raise ValueError("PCA projection recomputation failed")
    if not np.allclose(components @ components.T, np.eye(len(components)), atol=1e-9):
        raise ValueError("PCA components are not orthonormal")
    if not (
        np.isfinite(coordinates).all()
        and np.isfinite(components).all()
        and np.isfinite(pca.mean_).all()
    ):
        raise ValueError("Nonfinite PCA state")
    indices = None
    if mode == "points":
        indices, sample_counts = _stratified_indices(labels, per_cluster_cap, seed)
        repeated, repeated_counts = _stratified_indices(labels, per_cluster_cap, seed)
        if not np.array_equal(indices, repeated) or sample_counts != repeated_counts:
            raise ValueError("Stratified sampling is not deterministic")
        sample = {
            "policy": (
                "Deterministic stratified sample per cluster, equal caps, "
                "seed recorded below; sorted by canonical row order"
            ),
            "seed": seed,
            "per_cluster_cap": per_cluster_cap,
            "size": int(len(indices)),
            "cluster_counts": sample_counts,
            "population_cluster_counts": counts.tolist(),
            "proportions_disclosure": (
                "Stratified plotted proportions are not population proportions"
            ),
        }
    else:
        sample = {
            "policy": "aggregate_only",
            "seed": seed,
            "per_cluster_cap": per_cluster_cap,
            "size": 0,
            "cluster_counts": [0, 0],
            "population_cluster_counts": counts.tolist(),
            "proportions_disclosure": (
                "No track-level points are distributed in aggregate mode"
            ),
        }
    instrumentalness = matrix[:, F9.index("instrumentalness")]
    payload = {
        "schema_version": VISUALIZATION_SCHEMA_VERSION,
        "artifact_kind": VISUALIZATION_KIND,
        "artifact_mode": mode,
        "model_id": metadata["model_id"],
        "deployment_profile": metadata.get("deployment_profile"),
        "dataset_sha256": metadata.get("dataset_sha256"),
        "prepared_fingerprint": metadata["prepared_fingerprint"],
        "preparation_version": metadata.get("preparation_version"),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "features": list(F9),
        "population": {
            "training_sample_count": int(len(matrix)),
            "cluster_counts": counts.tolist(),
            "cluster_shares": (counts / len(matrix)).tolist(),
        },
        "pca": {
            "n_components": int(VISUALIZATION_PCA_COMPONENTS),
            "fit_representation": (
                "RobustScaler-transformed F9 fitted on the full canonical "
                "training population"
            ),
            "explained_variance_ratio": explained,
            "cumulative_explained_variance": cumulative,
            "components": np.round(components, 12).tolist(),
            "mean": np.round(pca.mean_, 12).tolist(),
            "sign_convention": (
                "Each component is flipped so its largest absolute loading is "
                "positive; this changes display signs only"
            ),
            "scope": (
                "Visualization-only projection; not used by the deployed model, "
                "not the model training coordinates and not an independent evaluation"
            ),
        },
        "sample": sample,
        "occupancy": _occupancy(
            coordinates, labels, instrumentalness, occupancy_bins, occupancy_min_count
        ),
        "views": {"points": mode == "points", "density": True},
        "software": _software(),
        "license": dict(DATASET_LICENSE),
        "limitations": VISUALIZATION_LIMITATIONS,
        "historical_equivalence": metadata.get("historical_equivalence"),
        "model_origin": metadata.get("model_origin"),
    }
    if mode == "points":
        sample_features = matrix[indices]
        payload["points"] = {
            "x": _rounded(coordinates[indices, 0], _COORDINATE_DECIMALS),
            "y": _rounded(coordinates[indices, 1], _COORDINATE_DECIMALS),
            "z": _rounded(coordinates[indices, 2], _COORDINATE_DECIMALS),
            "cluster": labels[indices].astype(int).tolist(),
            "raw_features": _rounded(sample_features, _FEATURE_DECIMALS),
            "scaler_center": np.round(scaler.center_, 12).tolist(),
            "scaler_scale": np.round(scaler.scale_, 12).tolist(),
        }
    checks = {
        "cluster_assignments_match_deployment_model": "PASS",
        "population_counts_match_metadata": "PASS",
        "feature_domains": "PASS",
        "pca_projection_recomputed": "PASS",
        "pca_components_orthonormal": "PASS",
        "sampling_deterministic": "PASS",
        "no_record_identifiers": "PASS",
        "scope": "Offline visualization export; no training, refit or Holdout",
        "historical_equivalence": "NOT VERIFIED",
    }
    verify_visualization(payload)
    return payload, checks


def reject_record_identifiers(value, path="root") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in _FORBIDDEN_KEYS:
                raise ValueError(f"Visualization artifact exposes record field: {key}")
            reject_record_identifiers(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            reject_record_identifiers(child, f"{path}[{index}]")


def _finite_vector(value, length: int, name: str) -> np.ndarray:
    array = np.asarray(value, dtype=np.float64)
    if array.shape != (length,) or not np.isfinite(array).all():
        raise ValueError(f"Invalid {name} vector")
    return array


def verify_visualization(
    payload: dict,
    *,
    expected_model_id: str | None = None,
    expected_dataset_sha256: str | None = None,
    expected_fingerprint: str | None = None,
) -> None:
    if not isinstance(payload, dict):
        raise ValueError("Visualization payload must be an object")
    reject_record_identifiers(payload)
    if payload.get("schema_version") != VISUALIZATION_SCHEMA_VERSION:
        raise ValueError("Unsupported visualization schema version")
    if payload.get("artifact_kind") != VISUALIZATION_KIND:
        raise ValueError("Unsupported visualization artifact kind")
    if not isinstance(payload.get("model_id"), str) or not payload["model_id"]:
        raise ValueError("Missing visualization model identity")
    if expected_model_id is not None and payload["model_id"] != expected_model_id:
        raise ValueError("Visualization model identity mismatch")
    for key, expected in (
        ("dataset_sha256", expected_dataset_sha256),
        ("prepared_fingerprint", expected_fingerprint),
    ):
        if expected is not None and payload.get(key) != expected:
            raise ValueError(f"Visualization {key} mismatch")
    if payload.get("deployment_profile") != DEPLOYMENT_V1.identifier:
        raise ValueError("Visualization deployment profile mismatch")
    if payload.get("features") != list(F9):
        raise ValueError("Visualization feature order mismatch")
    if payload.get("historical_equivalence") != "NOT VERIFIED":
        raise ValueError("Unsupported historical-equivalence claim")
    population = payload.get("population", {})
    counts = population.get("cluster_counts")
    total = population.get("training_sample_count")
    if (
        not isinstance(counts, list)
        or len(counts) != 2
        or any(type(value) is not int or value < 1 for value in counts)
        or type(total) is not int
        or sum(counts) != total
    ):
        raise ValueError("Invalid visualization population totals")
    pca = payload.get("pca", {})
    ratios = pca.get("explained_variance_ratio")
    cumulative = pca.get("cumulative_explained_variance")
    if (
        not isinstance(ratios, list)
        or len(ratios) != VISUALIZATION_PCA_COMPONENTS
        or not isinstance(cumulative, list)
        or len(cumulative) != VISUALIZATION_PCA_COMPONENTS
        or any(not 0 <= value <= 1 for value in ratios)
        or any(not 0 <= value <= 1 for value in cumulative)
        or ratios != sorted(ratios, reverse=True)
    ):
        raise ValueError("Invalid PCA explained variance")
    if not np.allclose(np.cumsum(ratios), cumulative, rtol=0, atol=1e-12):
        raise ValueError("Inconsistent cumulative explained variance")
    components = np.asarray(pca.get("components"), dtype=np.float64)
    mean = _finite_vector(pca.get("mean"), len(F9), "PCA mean")
    if components.shape != (VISUALIZATION_PCA_COMPONENTS, len(F9)):
        raise ValueError("Invalid PCA component dimensions")
    if not np.isfinite(components).all() or not np.allclose(
        components @ components.T, np.eye(len(components)), atol=1e-8
    ):
        raise ValueError("PCA components are not finite and orthonormal")
    occupancy = payload.get("occupancy", {})
    cells = occupancy.get("cells")
    minimum = occupancy.get("min_cell_count")
    if not isinstance(cells, list) or not cells or type(minimum) is not int:
        raise ValueError("Invalid aggregate occupancy grid")
    for cell in cells:
        count = cell.get("count")
        share = cell.get("cluster1_share")
        average = cell.get("mean_instrumentalness")
        if (
            type(count) is not int
            or count < minimum
            or not _is_number(share, 0, 1)
            or not _is_number(average, 0, 1)
            or not np.isfinite([cell.get("x"), cell.get("y")]).all()
        ):
            raise ValueError("Invalid aggregate occupancy cell")
    views = payload.get("views")
    if views != {
        "points": payload.get("artifact_mode") == "points",
        "density": True,
    }:
        raise ValueError("Inconsistent visualization views")
    if payload.get("artifact_mode") == "points":
        points = payload.get("points", {})
        x = np.asarray(points.get("x"), dtype=np.float64)
        y = np.asarray(points.get("y"), dtype=np.float64)
        z = np.asarray(points.get("z"), dtype=np.float64)
        cluster = np.asarray(points.get("cluster"))
        sample = payload.get("sample", {})
        size = sample.get("size")
        if (
            not isinstance(size, int)
            or size < 2
            or x.shape != (size,)
            or y.shape != (size,)
            or z.shape != (size,)
            or cluster.shape != (size,)
        ):
            raise ValueError("Invalid visualization point dimensions")
        if not (np.isfinite(x).all() and np.isfinite(y).all() and np.isfinite(z).all()):
            raise ValueError("Nonfinite visualization coordinates")
        if not set(cluster.tolist()) <= {0, 1}:
            raise ValueError("Invalid visualization cluster assignments")
        sample_counts = [int((cluster == label).sum()) for label in (0, 1)]
        if sample_counts != sample.get("cluster_counts"):
            raise ValueError("Sample cluster counts mismatch")
        if size != sum(sample_counts):
            raise ValueError("Sample size mismatch")
        features = np.asarray(points.get("raw_features"), dtype=np.float64)
        if features.shape != (size, len(F9)):
            raise ValueError("Invalid visualization feature dimensions")
        features = validate_matrix(features)
        center = _finite_vector(points.get("scaler_center"), len(F9), "scaler center")
        scale = _finite_vector(points.get("scaler_scale"), len(F9), "scaler scale")
        if (scale <= 0).any():
            raise ValueError("Invalid RobustScaler scale")
        scaled = (features - center) / scale
        expected = (scaled - mean) @ components.T
        if not np.allclose(
            expected,
            np.column_stack([x, y, z]),
            rtol=0,
            atol=_PROJECTION_TOLERANCE,
        ):
            raise ValueError("Coordinates do not recompute from the recorded PCA")
    elif payload.get("artifact_mode") == "aggregate":
        if "points" in payload:
            raise ValueError("Aggregate artifact must not expose track-level points")
        if payload.get("sample", {}).get("size") != 0:
            raise ValueError("Aggregate artifact must not claim a point sample")
    else:
        raise ValueError("Unsupported visualization mode")
    license_value = payload.get("license", {})
    if license_value.get("license") != "ODbL 1.0" or not license_value.get(
        "redistribution"
    ):
        raise ValueError("Missing dataset license disclosure")


def _is_number(value, low: float, high: float) -> bool:
    return type(value) in (int, float) and np.isfinite(value) and low <= value <= high


def save_visualization(output: Path, payload: dict, checks: dict) -> dict:
    output = Path(output)
    verify_visualization(payload)
    output.mkdir(parents=True, exist_ok=False)
    path = output / _ARTIFACT
    path.write_text(
        json.dumps(payload, indent=1, allow_nan=False) + "\n", encoding="utf-8"
    )
    report = {
        "status": "PASS",
        "artifact": _ARTIFACT,
        "checksums": {_ARTIFACT: sha256_file(path)},
        "model_id": payload["model_id"],
        "dataset_sha256": payload["dataset_sha256"],
        "prepared_fingerprint": payload["prepared_fingerprint"],
        "artifact_mode": payload["artifact_mode"],
        "sample_size": payload["sample"].get("size", 0),
        "created_at": payload["created_at"],
        "checks": checks,
        "scope": "Offline visualization export; no training, refit or Holdout",
        "historical_equivalence": "NOT VERIFIED",
    }
    (output / _REPORT).write_text(
        json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    load_visualization(
        output,
        expected_model_id=payload["model_id"],
        expected_dataset_sha256=payload["dataset_sha256"],
        expected_fingerprint=payload["prepared_fingerprint"],
    )
    return report


def load_visualization(
    output: Path,
    *,
    expected_model_id: str | None = None,
    expected_dataset_sha256: str | None = None,
    expected_fingerprint: str | None = None,
) -> dict:
    output = Path(output)
    report = json.loads((output / _REPORT).read_text(encoding="utf-8"))
    if report.get("status") != "PASS":
        raise ValueError("Visualization artifact lacks successful validation")
    checksums = report.get("checksums")
    if not isinstance(checksums, dict):
        raise ValueError("Visualization artifact lacks checksums")
    if sha256_file(output / _ARTIFACT) != checksums.get(_ARTIFACT):
        raise ValueError("Visualization checksum mismatch")
    payload = json.loads((output / _ARTIFACT).read_text(encoding="utf-8"))
    verify_visualization(
        payload,
        expected_model_id=expected_model_id,
        expected_dataset_sha256=expected_dataset_sha256,
        expected_fingerprint=expected_fingerprint,
    )
    for key in ("model_id", "dataset_sha256", "prepared_fingerprint", "artifact_mode"):
        if report.get(key) != payload.get(key):
            raise ValueError(f"Visualization report identity mismatch: {key}")
    if report.get("sample_size") != payload["sample"].get("size", 0):
        raise ValueError("Visualization report sample size mismatch")
    return payload


def public_meta(payload: dict) -> dict:
    """Small, presentation-safe metadata; no point coordinates or scaler state."""
    meta = {
        key: payload[key]
        for key in (
            "schema_version",
            "artifact_kind",
            "artifact_mode",
            "model_id",
            "deployment_profile",
            "dataset_sha256",
            "prepared_fingerprint",
            "preparation_version",
            "created_at",
            "features",
            "population",
            "pca",
            "sample",
            "views",
            "software",
            "license",
            "limitations",
            "historical_equivalence",
            "model_origin",
        )
    }
    meta["pca"] = {
        key: payload["pca"][key]
        for key in (
            "n_components",
            "fit_representation",
            "explained_variance_ratio",
            "cumulative_explained_variance",
            "components",
            "sign_convention",
            "scope",
        )
    }
    return meta


def points_view(payload: dict) -> dict:
    if payload.get("artifact_mode") != "points":
        raise ValueError("Track-level points are unavailable in aggregate mode")
    return {
        "model_id": payload["model_id"],
        "view": "points",
        "features": payload["features"],
        "pca": {
            "explained_variance_ratio": payload["pca"]["explained_variance_ratio"],
            "cumulative_explained_variance": payload["pca"][
                "cumulative_explained_variance"
            ],
            "scope": payload["pca"]["scope"],
        },
        "population": payload["population"],
        "sample": payload["sample"],
        "points": {
            key: payload["points"][key]
            for key in ("x", "y", "z", "cluster", "raw_features")
        },
        "occupancy": payload["occupancy"],
        "limitations": payload["limitations"],
        "historical_equivalence": payload["historical_equivalence"],
    }


def occupancy_view(payload: dict) -> dict:
    return {
        "model_id": payload["model_id"],
        "view": "density",
        "features": payload["features"],
        "pca": {
            "explained_variance_ratio": payload["pca"]["explained_variance_ratio"],
            "cumulative_explained_variance": payload["pca"][
                "cumulative_explained_variance"
            ],
            "scope": payload["pca"]["scope"],
        },
        "population": payload["population"],
        "occupancy": payload["occupancy"],
        "limitations": payload["limitations"],
        "historical_equivalence": payload["historical_equivalence"],
    }


def neighbours(payload: dict, index: int, k: int = 8) -> dict:
    """Nearest sampled tracks in fitted scaled F9 space; bounded O(n) per query."""
    if payload.get("artifact_mode") != "points":
        raise ValueError("Nearest neighbors require a track-level artifact")
    if type(index) is not int or type(k) is not int:
        raise ValueError("Point index and neighbor count must be integers")
    if not 1 <= k <= 12:
        raise ValueError("Neighbor count must be between 1 and 12")
    points = payload["points"]
    size = len(points["x"])
    if not 0 <= index < size:
        raise ValueError("Point index is outside the visualization sample")
    features = np.asarray(points["raw_features"], dtype=np.float64)
    center = np.asarray(points["scaler_center"], dtype=np.float64)
    scale = np.asarray(points["scaler_scale"], dtype=np.float64)
    scaled = (features - center) / scale
    distances = np.linalg.norm(scaled - scaled[index], axis=1)
    order = np.argsort(distances, kind="stable")
    order = [int(position) for position in order if int(position) != index][:k]
    coordinates = np.column_stack([points["x"], points["y"], points["z"]])
    cluster = points["cluster"]

    def describe(position: int, distance: float | None = None) -> dict:
        entry = {
            "index": position,
            "cluster": int(cluster[position]),
            "coordinates": [float(value) for value in coordinates[position]],
            "features": {
                name: float(features[position, column])
                for column, name in enumerate(F9)
            },
        }
        if distance is not None:
            entry["distance"] = float(distance)
        return entry

    return {
        "model_id": payload["model_id"],
        "selection": "Nearest neighbors in fitted RobustScaler F9 space",
        "distance_definition": (
            "Euclidean distance in fitted RobustScaler-transformed F9 space; "
            "not screen distance and not a probability"
        ),
        "sample_size": size,
        "point": describe(index),
        "neighbors": [
            describe(position, float(distances[position])) for position in order
        ],
        "historical_equivalence": payload["historical_equivalence"],
    }
