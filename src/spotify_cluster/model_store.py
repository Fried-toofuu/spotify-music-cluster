"""Trusted-local joblib persistence. Checksums detect damage, not malicious authors."""

import json
import platform
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import joblib
import numpy as np
import pandas as pd
import scipy
import sklearn
import threadpoolctl
from sklearn.cluster import KMeans
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import RobustScaler
from sklearn.utils.validation import check_is_fitted

from .config import (
    DEPLOYMENT_V1,
    EXPECTED_SHA256,
    F9,
    PREPARATION_VERSION,
    SCALER_PARAMS,
    TRACK_COUNT,
    DeploymentProfile,
)
from .data import sha256_file
from .verification import verify_sample

_MODEL_FILENAME = "model_bundle.joblib"
_CHECKSUMMED_FILENAMES = (
    _MODEL_FILENAME,
    "metadata.json",
    "cluster_profiles.json",
)


def environment() -> dict:
    return {
        "python": platform.python_version(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scipy": scipy.__version__,
        "scikit_learn": sklearn.__version__,
        "joblib": joblib.__version__,
        "threadpoolctl": threadpoolctl.__version__,
    }


def new_model_id() -> str:
    return "spotify-f9-robust-k2-" + uuid4().hex


def make_metadata(
    pipeline: Pipeline,
    model_id: str,
    data_identity: dict,
    *,
    reconstruction_status: str,
    profile: DeploymentProfile | None = None,
) -> dict:
    """Keep provenance explicit, including software fixtures versus real research."""
    metadata = {
        **data_identity,
        "schema_version": 1,
        "model_id": model_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "features": list(F9),
        "scaler_params": pipeline.named_steps["scaler"].get_params(),
        "kmeans_params": pipeline.named_steps["kmeans"].get_params(),
        "number_of_clusters": 2,
        "modeling_pca": None,
        "environment": environment(),
        "reconstruction_status": reconstruction_status,
        "historical_equivalence": "NOT VERIFIED",
        "holdout_evaluated": False,
        "execution": {"thread_limit": 1, "scope": "offline"},
        "cluster_counts": np.bincount(
            pipeline.named_steps["kmeans"].labels_, minlength=2
        ).tolist(),
    }
    metadata["cluster_shares"] = (
        np.asarray(metadata["cluster_counts"]) / metadata["training_sample_count"]
    ).tolist()
    if profile is not None:
        metadata.update(
            {
                "training_profile": profile.name,
                "deployment_profile": profile.identifier,
                "model_origin": (
                    "software-test-only"
                    if reconstruction_status == "software-test-only"
                    else "new_deployment_refit"
                ),
                "configuration_provenance": dict(profile.provenance),
            }
        )
    return metadata


def _json_value(value):
    return json.loads(json.dumps(value, allow_nan=False))


def _validate(pipeline: Pipeline, metadata: dict, profiles: dict) -> None:
    if metadata.get("schema_version") != 1 or metadata.get("features") != list(F9):
        raise ValueError("Incompatible metadata schema or F9 order")
    if not isinstance(metadata.get("model_id"), str) or not metadata["model_id"]:
        raise ValueError("Missing model identity")
    if metadata.get("environment") != environment():
        raise ValueError(
            "Model environment mismatch; recreate the recorded environment"
        )
    if metadata.get("historical_equivalence") != "NOT VERIFIED":
        raise ValueError("Unsupported historical-equivalence claim")
    if metadata.get("holdout_evaluated") is not False:
        raise ValueError("Holdout evaluation is outside this model contract")
    status = metadata.get("reconstruction_status")
    if status not in ("reconstructed", "software-test-only", "new_deployment_refit"):
        raise ValueError("Unrecognized reconstruction status")
    if status == "reconstructed" and (
        metadata.get("dataset_sha256") != EXPECTED_SHA256
        or metadata.get("training_sample_count") != TRACK_COUNT
        or metadata.get("preparation_version") != PREPARATION_VERSION
        or not metadata.get("final_configuration_evidence")
    ):
        raise ValueError("Incomplete production model provenance")
    if status == "new_deployment_refit":
        if (
            metadata.get("dataset_sha256") != EXPECTED_SHA256
            or metadata.get("training_sample_count") != TRACK_COUNT
            or metadata.get("preparation_version") != PREPARATION_VERSION
            or metadata.get("training_profile") != DEPLOYMENT_V1.name
            or metadata.get("model_origin") != "new_deployment_refit"
            or not isinstance(metadata.get("prepared_fingerprint"), str)
            or len(metadata["prepared_fingerprint"]) != 64
        ):
            raise ValueError("Incomplete deployment model provenance")
    if "training_profile" in metadata:
        if (
            metadata["training_profile"] != DEPLOYMENT_V1.name
            or metadata.get("deployment_profile") != DEPLOYMENT_V1.identifier
            or metadata.get("configuration_provenance")
            != dict(DEPLOYMENT_V1.provenance)
            or metadata.get("kmeans_params") != dict(DEPLOYMENT_V1.kmeans_params)
            or metadata.get("scaler_params")
            != _json_value(dict(DEPLOYMENT_V1.scaler_params))
        ):
            raise ValueError("Deployment recipe or configuration provenance mismatch")
    if type(pipeline) is not Pipeline or list(pipeline.named_steps) != [
        "scaler",
        "kmeans",
    ]:
        raise ValueError("Expected exactly RobustScaler followed by KMeans, no PCA")
    scaler, estimator = pipeline.named_steps.values()
    if type(scaler) is not RobustScaler or type(estimator) is not KMeans:
        raise ValueError("Incorrect estimator types")
    check_is_fitted(scaler)
    check_is_fitted(estimator)
    if _json_value(scaler.get_params()) != _json_value(SCALER_PARAMS):
        raise ValueError("Incorrect RobustScaler configuration")
    for key, actual in (
        ("scaler_params", scaler.get_params()),
        ("kmeans_params", estimator.get_params()),
    ):
        if metadata.get(key) != _json_value(actual):
            raise ValueError(f"Metadata {key} differs from fitted bundle")
    if (
        metadata.get("number_of_clusters") != 2
        or metadata.get("modeling_pca") is not None
        or estimator.n_clusters != 2
        or np.shape(estimator.cluster_centers_) != (2, 9)
        or np.shape(scaler.center_) != (9,)
        or np.shape(scaler.scale_) != (9,)
        or scaler.n_features_in_ != 9
        or estimator.n_features_in_ != 9
    ):
        raise ValueError("Incompatible fitted dimensions")
    if (
        np.shape(estimator.labels_) != (metadata.get("training_sample_count"),)
        or estimator.n_iter_ >= estimator.max_iter
    ):
        raise ValueError("Incompatible fitted training state")
    if (
        not np.isfinite(estimator.cluster_centers_).all()
        or not np.isfinite(scaler.center_).all()
        or not np.isfinite(scaler.scale_).all()
        or (scaler.scale_ <= 0).any()
    ):
        raise ValueError("Invalid fitted numerical state")
    counts = metadata.get("cluster_counts")
    if (
        not isinstance(counts, list)
        or len(counts) != 2
        or any(type(n) is not int or n <= 0 for n in counts)
        or sum(counts) != metadata.get("training_sample_count")
        or counts != np.bincount(estimator.labels_, minlength=2).tolist()
    ):
        raise ValueError("Inconsistent cluster totals")
    if "cluster_shares" in metadata and not np.allclose(
        metadata["cluster_shares"],
        np.asarray(counts) / sum(counts),
        rtol=1e-12,
        atol=1e-12,
    ):
        raise ValueError("Inconsistent cluster shares")
    if profiles.get("model_id") != metadata["model_id"]:
        raise ValueError("Cluster-profile model identity mismatch")
    if set(profiles.get("clusters", {})) != {"0", "1"}:
        raise ValueError("Incorrect cluster-profile mapping")
    for label, count in enumerate(counts):
        profile = profiles["clusters"][str(label)]
        if (
            profile.get("count") != count
            or profile.get("cluster_id") != label
            or not np.isclose(profile.get("share", -1), count / sum(counts))
        ):
            raise ValueError("Inconsistent profile count, share or label")
        for stat in ("mean", "median", "std", "q1", "q3", "iqr"):
            values = profile.get(stat, {})
            if set(values) != set(F9) or not np.isfinite(list(values.values())).all():
                raise ValueError("Invalid raw-unit profile statistics")


def _write_json(path: Path, value: dict) -> None:
    path.write_text(
        json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )


def save_bundle(
    output: Path,
    pipeline: Pipeline,
    metadata: dict,
    profiles: dict,
    numerical_report: dict,
    verification_sample: dict | None = None,
) -> dict:
    """Create a new directory; partial writes are never a valid bundle."""
    metadata, profiles = _json_value(metadata), _json_value(profiles)
    _validate(pipeline, metadata, profiles)
    if "training_profile" in metadata and verification_sample is None:
        raise ValueError("Deployment export requires a verification sample")
    if verification_sample is not None:
        verification_sample = _json_value(verification_sample)
        verify_sample(pipeline, verification_sample, metadata["model_id"])
    if any(
        numerical_report.get(key) != "PASS"
        for key in ("manual_scaling", "nearest_centroid")
    ):
        raise ValueError(
            "Independent numerical verification required before serialization"
        )
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    model_path = output / _MODEL_FILENAME
    joblib.dump({"features": F9, "pipeline": pipeline}, model_path)
    metadata["artifact_sha256"] = sha256_file(model_path)
    _write_json(output / "cluster_profiles.json", profiles)
    metadata["profile_sha256"] = sha256_file(output / "cluster_profiles.json")
    filenames = list(_CHECKSUMMED_FILENAMES)
    if verification_sample is not None:
        _write_json(output / "verification_sample.json", verification_sample)
        metadata["verification_sample_sha256"] = sha256_file(
            output / "verification_sample.json"
        )
        filenames.append("verification_sample.json")
    _write_json(output / "metadata.json", metadata)
    report = {
        **numerical_report,
        "model_id": metadata["model_id"],
        "checksums": {name: sha256_file(output / name) for name in filenames},
    }
    if verification_sample is not None:
        report["stored_sample"] = "PASS"
    _write_json(output / "verification_report.json", report)
    load_bundle(output)
    return report


def load_bundle(output: Path) -> tuple[Pipeline, dict, dict]:
    """Load only an operator-trusted local directory; never an uploaded joblib file."""
    output = Path(output)
    report = json.loads(
        (output / "verification_report.json").read_text(encoding="utf-8")
    )
    if not isinstance(report, dict) or any(
        report.get(key) != "PASS" for key in ("manual_scaling", "nearest_centroid")
    ):
        raise ValueError("Bundle lacks successful numerical verification")
    checksums = report.get("checksums")
    if not isinstance(checksums, dict):
        raise ValueError("Bundle lacks artifact checksums")
    for name in _CHECKSUMMED_FILENAMES:
        if sha256_file(output / name) != checksums.get(name):
            raise ValueError(f"Artifact checksum mismatch: {name}")
    metadata = json.loads((output / "metadata.json").read_text(encoding="utf-8"))
    profiles = json.loads(
        (output / "cluster_profiles.json").read_text(encoding="utf-8")
    )
    if metadata.get("environment") != environment():
        raise ValueError("Model environment mismatch; refused before deserialization")
    if metadata.get("artifact_sha256") != checksums[_MODEL_FILENAME] or metadata.get(
        "model_id"
    ) != report.get("model_id"):
        raise ValueError("Bundle identity or checksum mismatch")
    if (
        "profile_sha256" in metadata or "training_profile" in metadata
    ) and metadata.get("profile_sha256") != checksums["cluster_profiles.json"]:
        raise ValueError("Profile checksum mismatch")
    sample = None
    if "training_profile" in metadata or "verification_sample_sha256" in metadata:
        sample_path = output / "verification_sample.json"
        if (
            report.get("stored_sample") != "PASS"
            or sha256_file(sample_path) != checksums.get("verification_sample.json")
            or checksums.get("verification_sample.json")
            != metadata.get("verification_sample_sha256")
        ):
            raise ValueError("Verification sample checksum or status mismatch")
        sample = json.loads(sample_path.read_text(encoding="utf-8"))
    bundle = joblib.load(output / _MODEL_FILENAME)
    if not isinstance(bundle, dict) or bundle.get("features") != F9:
        raise ValueError("Incorrect bundle feature schema")
    pipeline = bundle.get("pipeline")
    _validate(pipeline, metadata, profiles)
    if sample is not None:
        verify_sample(pipeline, sample, metadata["model_id"])
    return pipeline, metadata, profiles
