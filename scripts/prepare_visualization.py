"""Prepare one offline PCA visualization artifact from authorized inputs."""

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
from pathlib import Path

from threadpoolctl import threadpool_limits

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from spotify_cluster.config import (  # noqa: E402
    DEPLOYMENT_V1,
    VISUALIZATION_PER_CLUSTER_CAP,
    VISUALIZATION_SEED,
)
from spotify_cluster.data import load_dataset  # noqa: E402
from spotify_cluster.model_store import load_bundle  # noqa: E402
from spotify_cluster.visualization import (  # noqa: E402
    build_visualization,
    save_visualization,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Project the trusted deployment model's training population into a "
            "visualization-only PCA artifact. No clustering is fitted."
        )
    )
    parser.add_argument("--dataset", required=True, type=Path)
    parser.add_argument("--model-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--mode",
        choices=("points", "aggregate"),
        default="points",
        help="points is private/local only; aggregate is the approved public fallback",
    )
    parser.add_argument(
        "--per-cluster-cap", type=int, default=VISUALIZATION_PER_CLUSTER_CAP
    )
    parser.add_argument("--seed", type=int, default=VISUALIZATION_SEED)
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
        payload, checks = build_visualization(
            pipeline,
            metadata,
            prepared.matrix,
            mode=args.mode,
            per_cluster_cap=args.per_cluster_cap,
            seed=args.seed,
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(
        tempfile.mkdtemp(prefix=args.output.name + ".partial-", dir=args.output.parent)
    )
    staging.rmdir()
    try:
        report = save_visualization(staging, payload, checks)
        staging.rename(args.output)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    print(
        {
            "status": "PASS",
            "output": str(args.output),
            "artifact_mode": payload["artifact_mode"],
            "model_id": payload["model_id"],
            "sample_size": report["sample_size"],
            "population": payload["population"]["training_sample_count"],
            "explained_variance": payload["pca"]["explained_variance_ratio"],
            "sample_policy": payload["sample"]["policy"],
            "historical_equivalence": "NOT VERIFIED",
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
