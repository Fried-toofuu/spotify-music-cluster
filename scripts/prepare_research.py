"""Prepare the controlled training-population comparison artifact offline."""

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
from pathlib import Path

from threadpoolctl import threadpool_limits

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from spotify_cluster.config import DEPLOYMENT_V1  # noqa: E402
from spotify_cluster.data import load_dataset  # noqa: E402
from spotify_cluster.model_store import load_bundle  # noqa: E402
from spotify_cluster.research import build_comparison, save_comparison  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Fit documented comparison models on the full canonical training "
            "population. No Holdout is opened and the deployment model is unchanged."
        )
    )
    parser.add_argument("--dataset", required=True, type=Path)
    parser.add_argument("--model-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    prepared, dataset_info = load_dataset(args.dataset)
    pipeline, metadata, _profiles = load_bundle(args.model_dir)
    if (
        metadata.get("dataset_sha256") != dataset_info["dataset_sha256"]
        or metadata.get("prepared_fingerprint") != prepared.fingerprint
        or metadata.get("training_sample_count") != len(prepared.matrix)
        or metadata.get("deployment_profile") != DEPLOYMENT_V1.identifier
        or metadata.get("model_origin") != "new_deployment_refit"
    ):
        raise ValueError("Model bundle does not match the authorized dataset snapshot")
    with threadpool_limits(limits=1):
        payload, checks = build_comparison(pipeline, metadata, prepared.matrix)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(
        tempfile.mkdtemp(prefix=args.output.name + ".partial-", dir=args.output.parent)
    )
    staging.rmdir()
    try:
        save_comparison(staging, payload, checks)
        staging.rename(args.output)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    f5 = payload["comparisons"]["f5_kmeans_vs_deployment_f9_kmeans"]
    gmm = payload["comparisons"]["f9_kmeans_vs_f9_gmm"]
    print(
        {
            "status": "PASS",
            "output": str(args.output),
            "model_id": payload["model_id"],
            "population": payload["population"]["training_sample_count"],
            "f5_vs_f9_ari": round(f5["ari"], 6),
            "f9_kmeans_vs_gmm_ari": round(gmm["ari"], 6),
            "mean_max_responsibility": round(gmm["mean_max_responsibility"], 6),
            "holdout_evaluated": False,
            "historical_equivalence": "NOT VERIFIED",
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
