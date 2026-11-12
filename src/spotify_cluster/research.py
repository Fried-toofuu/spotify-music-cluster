"""Controlled training-population comparisons; no Holdout, no model selection."""

from __future__ import annotations

import json
import platform
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score
from sklearn.mixture import GaussianMixture
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .config import (
    DATASET_LICENSE,
    DEPLOYMENT_V1,
    F5,
    F9,
    RESEARCH_KIND,
    RESEARCH_SCHEMA_VERSION,
)
from .data import sha256_file, validate_matrix
from .visualization import reject_record_identifiers

_ARTIFACT = "comparison.json"
_REPORT = "verification_report.json"
ARCHIVED_HISTORICAL_EVIDENCE = {
    "label": "Archived historical FULL research evidence",
    "source": (
        "Original executed notebook ARCHIVED record; frozen historical "
        "F9/Robust/KMeans/K2 estimator"
    ),
    "scope": (
        "One-time historical Holdout evaluation on a deterministic 3,000-track "
        "sample; already closed"
    ),
    "status": "ARCHIVED; NOT RECOMPUTED; HOLDOUT CLOSED",
    "holdout_silhouette": 0.6076945989627338,
    "holdout_davies_bouldin": 0.6323066464652578,
    "holdout_calinski_harabasz": 3750.5583111569226,
    "warning": (
        "These historical-estimator metrics do not describe deployment-v1 and "
        "must never be attached to deployment predictions. Historical estimator "
        "equivalence remains NOT VERIFIED."
    ),
}
_LIMITATIONS = (
    "These comparisons are new exploratory development calculations on the full "
    "canonical training population, not model selection and not an independent "
    "evaluation. Adjusted Rand Index measures partition agreement, not quality. "
    "Do not compare Silhouette values across different feature geometries. The "
    "historical Holdout remains closed. Historical final-estimator equivalence "
    "is NOT VERIFIED."
)


def _software() -> dict:
    return {
        "python": platform.python_version(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scikit_learn": sklearn.__version__,
    }


def build_comparison(
    pipeline: Pipeline, metadata: dict, matrix: np.ndarray
) -> tuple[dict, dict]:
    """Fit only documented comparison models on identical rows and representation."""
    matrix = validate_matrix(matrix)
    if metadata.get("features") != list(F9):
        raise ValueError("Model metadata feature order mismatch")
    if metadata.get("training_sample_count") != len(matrix):
        raise ValueError("Comparison matrix does not match the model population")
    if metadata.get("prepared_fingerprint") is None:
        raise ValueError("Model metadata lacks a preparation fingerprint")
    deployment_labels = pipeline.predict(matrix)
    counts = np.bincount(deployment_labels, minlength=2)
    if counts.tolist() != metadata.get("cluster_counts"):
        raise ValueError("Deployment labels differ from model metadata")
    scaled = pipeline.named_steps["scaler"].transform(matrix)
    f5_positions = [F9.index(name) for name in F5]
    f5_scaler = StandardScaler()
    f5_matrix = f5_scaler.fit_transform(matrix[:, f5_positions])
    f5_params = dict(
        n_clusters=2,
        init="k-means++",
        n_init=20,
        max_iter=300,
        tol=1e-4,
        random_state=42,
        algorithm="lloyd",
    )
    f5_labels = KMeans(**f5_params).fit_predict(f5_matrix)
    f5_counts = np.bincount(f5_labels, minlength=2)
    gmm_params = dict(
        n_components=2,
        covariance_type="diag",
        random_state=42,
        n_init=3,
        max_iter=300,
        tol=1e-3,
        reg_covar=1e-6,
    )
    gmm = GaussianMixture(**gmm_params)
    gmm.fit(scaled)
    probabilities = gmm.predict_proba(scaled)
    gmm_labels = probabilities.argmax(axis=1)
    gmm_counts = np.bincount(gmm_labels, minlength=2)
    if not np.allclose(probabilities.sum(axis=1), 1, rtol=0, atol=1e-9):
        raise ValueError("GMM responsibilities do not sum to one")
    entropy = -(probabilities * np.log(np.clip(probabilities, 1e-12, 1))).sum(axis=1)
    f5_ari = float(adjusted_rand_score(deployment_labels, f5_labels))
    gmm_ari = float(adjusted_rand_score(deployment_labels, gmm_labels))
    payload = {
        "schema_version": RESEARCH_SCHEMA_VERSION,
        "artifact_kind": RESEARCH_KIND,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "model_id": metadata["model_id"],
        "deployment_profile": metadata.get("deployment_profile"),
        "dataset_sha256": metadata.get("dataset_sha256"),
        "prepared_fingerprint": metadata["prepared_fingerprint"],
        "preparation_version": metadata.get("preparation_version"),
        "features": list(F9),
        "population": {
            "training_sample_count": int(len(matrix)),
            "cluster_counts": counts.tolist(),
            "cluster_shares": (counts / len(matrix)).tolist(),
        },
        "scope": (
            "New exploratory development comparison on the full canonical "
            "training population; identical row order; not model selection; "
            "no Holdout and no deployment change"
        ),
        "comparisons": {
            "f5_kmeans_vs_deployment_f9_kmeans": {
                "definition": (
                    "F5 StandardScaler K-Means partition compared with the "
                    "deployed F9 RobustScaler K-Means partition on identical rows"
                ),
                "identical_track_ids": True,
                "f5_features": list(F5),
                "f5_recipe": {
                    "scaler": "StandardScaler fitted on the full training population",
                    "kmeans": f5_params,
                    "provenance": (
                        "New development recipe for this comparison; it is not "
                        "asserted to reproduce the archived historical F5 baseline"
                    ),
                },
                "deployment_recipe": {
                    "features": list(F9),
                    "scaler": "RobustScaler",
                    "kmeans": dict(metadata["kmeans_params"]),
                },
                "ari": f5_ari,
                "f5_cluster_counts": f5_counts.tolist(),
                "deployment_cluster_counts": counts.tolist(),
                "interpretation": (
                    "A low Adjusted Rand Index indicates that scaler and feature "
                    "geometry change the partition substantially. ARI is not a "
                    "quality score and does not rank the representations."
                ),
            },
            "f9_kmeans_vs_f9_gmm": {
                "definition": (
                    "Deployed F9 RobustScaler K-Means hard assignments compared "
                    "with a diagonal-covariance Gaussian mixture on the identical "
                    "fitted scaled representation and rows"
                ),
                "identical_track_ids": True,
                "representation": (
                    "Identical RobustScaler-transformed F9 matrix used by the "
                    "deployed K-Means model"
                ),
                "gmm_recipe": gmm_params,
                "ari": gmm_ari,
                "gmm_hard_cluster_counts": gmm_counts.tolist(),
                "mean_max_responsibility": float(probabilities.max(axis=1).mean()),
                "mean_entropy_nats": float(entropy.mean()),
                "soft_assignment_definition": (
                    "Responsibilities are posterior component weights. The hard "
                    "GMM partition uses argmax responsibility; K-Means instead "
                    "minimizes squared centroid distance."
                ),
                "interpretation": (
                    "K-Means and a mixture model answer different questions. "
                    "Partition agreement is informative even when it is low; "
                    "neither model is selected by this comparison."
                ),
            },
        },
        "archived_evidence": ARCHIVED_HISTORICAL_EVIDENCE,
        "software": _software(),
        "license": dict(DATASET_LICENSE),
        "limitations": _LIMITATIONS,
        "historical_equivalence": "NOT VERIFIED",
        "holdout_evaluated": False,
    }
    checks = {
        "identical_rows": "PASS",
        "responsibilities_normalized": "PASS",
        "ari_in_bounds": "PASS",
        "counts_sum_to_population": "PASS",
        "holdout_not_evaluated": "PASS",
        "no_record_identifiers": "PASS",
        "scope": "Development comparison only; no Holdout, no deployment change",
        "historical_equivalence": "NOT VERIFIED",
    }
    verify_comparison(payload)
    return payload, checks


def verify_comparison(
    payload: dict,
    *,
    expected_model_id: str | None = None,
    expected_dataset_sha256: str | None = None,
    expected_fingerprint: str | None = None,
) -> None:
    if not isinstance(payload, dict):
        raise ValueError("Research comparison must be an object")
    reject_record_identifiers(payload)
    if payload.get("schema_version") != RESEARCH_SCHEMA_VERSION:
        raise ValueError("Unsupported research comparison schema")
    if payload.get("artifact_kind") != RESEARCH_KIND:
        raise ValueError("Unsupported research comparison kind")
    if not isinstance(payload.get("model_id"), str) or not payload["model_id"]:
        raise ValueError("Missing research model identity")
    if expected_model_id is not None and payload["model_id"] != expected_model_id:
        raise ValueError("Research comparison model identity mismatch")
    if (
        expected_dataset_sha256 is not None
        and payload.get("dataset_sha256") != expected_dataset_sha256
    ):
        raise ValueError("Research comparison dataset identity mismatch")
    if (
        expected_fingerprint is not None
        and payload.get("prepared_fingerprint") != expected_fingerprint
    ):
        raise ValueError("Research comparison preparation fingerprint mismatch")
    if payload.get("deployment_profile") != DEPLOYMENT_V1.identifier:
        raise ValueError("Research comparison deployment profile mismatch")
    if payload.get("features") != list(F9):
        raise ValueError("Research comparison feature order mismatch")
    if payload.get("historical_equivalence") != "NOT VERIFIED":
        raise ValueError("Unsupported historical-equivalence claim")
    if payload.get("holdout_evaluated") is not False:
        raise ValueError("Research comparison must not evaluate Holdout")
    population = payload.get("population", {})
    total = population.get("training_sample_count")
    counts = population.get("cluster_counts")
    if (
        type(total) is not int
        or not isinstance(counts, list)
        or len(counts) != 2
        or sum(counts) != total
    ):
        raise ValueError("Invalid research population totals")
    comparisons = payload.get("comparisons", {})
    if set(comparisons) != {
        "f5_kmeans_vs_deployment_f9_kmeans",
        "f9_kmeans_vs_f9_gmm",
    }:
        raise ValueError("Missing controlled comparisons")
    f5 = comparisons["f5_kmeans_vs_deployment_f9_kmeans"]
    gmm = comparisons["f9_kmeans_vs_f9_gmm"]
    for name, comparison in (("f5", f5), ("gmm", gmm)):
        ari = comparison.get("ari")
        if type(ari) not in (int, float) or not -1 <= ari <= 1:
            raise ValueError(f"Invalid {name} Adjusted Rand Index")
        if comparison.get("identical_track_ids") is not True:
            raise ValueError(f"{name} comparison must use identical rows")
    if (
        sum(f5.get("f5_cluster_counts", [])) != total
        or sum(f5.get("deployment_cluster_counts", [])) != total
        or sum(gmm.get("gmm_hard_cluster_counts", [])) != total
    ):
        raise ValueError("Comparison cluster counts do not sum to the population")
    confidence = gmm.get("mean_max_responsibility")
    entropy = gmm.get("mean_entropy_nats")
    if (
        type(confidence) not in (int, float)
        or not 0.5 <= confidence <= 1
        or type(entropy) not in (int, float)
        or entropy < 0
    ):
        raise ValueError("Invalid soft-assignment diagnostics")
    archived = payload.get("archived_evidence", {})
    if (
        archived.get("status") != "ARCHIVED; NOT RECOMPUTED; HOLDOUT CLOSED"
        or archived.get("label") != "Archived historical FULL research evidence"
    ):
        raise ValueError("Archived evidence must stay clearly labeled")
    license_value = payload.get("license", {})
    if license_value.get("license") != "ODbL 1.0":
        raise ValueError("Missing dataset license disclosure")


def save_comparison(output: Path, payload: dict, checks: dict) -> dict:
    output = Path(output)
    verify_comparison(payload)
    output.mkdir(parents=True, exist_ok=False)
    path = output / _ARTIFACT
    path.write_text(
        json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    report = {
        "status": "PASS",
        "artifact": _ARTIFACT,
        "checksums": {_ARTIFACT: sha256_file(path)},
        "model_id": payload["model_id"],
        "dataset_sha256": payload["dataset_sha256"],
        "prepared_fingerprint": payload["prepared_fingerprint"],
        "created_at": payload["created_at"],
        "checks": checks,
        "scope": "Development comparison only; no Holdout, no deployment change",
        "historical_equivalence": "NOT VERIFIED",
    }
    (output / _REPORT).write_text(
        json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    load_comparison(
        output,
        expected_model_id=payload["model_id"],
        expected_dataset_sha256=payload["dataset_sha256"],
    )
    return report


def load_comparison(
    output: Path,
    *,
    expected_model_id: str | None = None,
    expected_dataset_sha256: str | None = None,
    expected_fingerprint: str | None = None,
) -> dict:
    output = Path(output)
    report = json.loads((output / _REPORT).read_text(encoding="utf-8"))
    if report.get("status") != "PASS":
        raise ValueError("Research artifact lacks successful validation")
    checksums = report.get("checksums")
    if not isinstance(checksums, dict):
        raise ValueError("Research artifact lacks checksums")
    if sha256_file(output / _ARTIFACT) != checksums.get(_ARTIFACT):
        raise ValueError("Research artifact checksum mismatch")
    payload = json.loads((output / _ARTIFACT).read_text(encoding="utf-8"))
    verify_comparison(
        payload,
        expected_model_id=expected_model_id,
        expected_dataset_sha256=expected_dataset_sha256,
        expected_fingerprint=expected_fingerprint,
    )
    for key in ("model_id", "dataset_sha256", "prepared_fingerprint"):
        if report.get(key) != payload.get(key):
            raise ValueError(f"Research report identity mismatch: {key}")
    return payload
