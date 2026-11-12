"""Export an explicitly approved deployment recipe; historical identity stays gated."""

import argparse
import json
from pathlib import Path

from spotify_cluster.config import training_profile
from spotify_cluster.data import load_dataset
from spotify_cluster.model_store import make_metadata, new_model_id, save_bundle
from spotify_cluster.training import cluster_profiles, train_model, verify_numerics
from spotify_cluster.verification import make_verification_sample


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--profile",
        choices=("deployment-v1", "historical-final-refit"),
        default="historical-final-refit",
        help="Select deployment-v1 explicitly; omission retains the historical gate",
    )
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output already exists; choose a new versioned directory")
    try:
        prepared, identity = load_dataset(args.dataset)
        print(json.dumps({"dataset": identity, "matrix_shape": prepared.matrix.shape}))
        profile = training_profile(args.profile)
        pipeline = train_model(prepared.matrix, dict(profile.kmeans_params))
        model_id = new_model_id()
        metadata = make_metadata(
            pipeline,
            model_id,
            identity,
            reconstruction_status="new_deployment_refit",
            profile=profile,
        )
        report = verify_numerics(pipeline, prepared.matrix)
        profiles = cluster_profiles(pipeline, prepared.matrix, model_id)
        sample = make_verification_sample(pipeline, prepared.matrix, model_id)
        save_bundle(args.output, pipeline, metadata, profiles, report, sample)
        print(
            json.dumps(
                {
                    "model_id": model_id,
                    "profile": profile.identifier,
                    "output": str(args.output.resolve()),
                    "cluster_counts": metadata["cluster_counts"],
                    "historical_equivalence": metadata["historical_equivalence"],
                }
            )
        )
    except (ValueError, RuntimeError, OSError) as exc:
        parser.exit(2, f"{exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
