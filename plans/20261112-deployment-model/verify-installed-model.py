"""Verify real installed-wheel inference with training and acquisition denied."""

import argparse
import builtins
import io
import json
import socket
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import RobustScaler

import spotify_cluster
from spotify_cluster.config import DEPLOYMENT_V1, F9
from spotify_cluster.inference import InferenceService


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts", type=Path, required=True)
    args = parser.parse_args()

    def forbidden(*args, **kwargs):
        raise RuntimeError("Dataset, notebook, network and fitting access denied")

    def guard(original):
        def guarded(file, *args, **kwargs):
            if str(file).lower().endswith((".csv", ".ipynb")):
                forbidden()
            return original(file, *args, **kwargs)

        return guarded

    builtins.open = guard(builtins.open)
    io.open = guard(io.open)
    pd.read_csv = forbidden
    socket.socket.connect = forbidden
    socket.socket.connect_ex = forbidden
    socket.create_connection = forbidden
    KMeans.fit = forbidden
    RobustScaler.fit = forbidden
    Pipeline.fit = forbidden

    assert not list(Path.cwd().glob("*.csv"))
    assert not list(Path.cwd().glob("*.ipynb"))
    sample = json.loads((args.artifacts / "verification_sample.json").read_text())
    service = InferenceService(args.artifacts)
    tracks = [dict(zip(F9, row, strict=True)) for row in sample["raw_f9"]]
    results = service.predict_batch(tracks)
    assert service.predict_one(tracks[0]) == results[0]
    np.testing.assert_array_equal(
        [r["cluster_id"] for r in results], sample["predictions"]
    )
    np.testing.assert_allclose([r["distances"] for r in results], sample["distances"])
    reverse = service.predict_batch(tracks[::-1])
    assert reverse == results[::-1]
    for result in results:
        assert result["model_id"] == sample["model_id"]
        assert result["deployment_profile"] == DEPLOYMENT_V1.identifier
        assert result["profile"]["cluster_id"] == result["cluster_id"]
        assert result["historical_equivalence"] == "NOT VERIFIED"
    invalid = dict(tracks[0], energy=True)
    try:
        service.predict_one(invalid)
    except ValueError:
        pass
    else:
        raise AssertionError("Real model accepted a boolean descriptor")
    print(
        json.dumps(
            {
                "status": "PASS",
                "model_id": sample["model_id"],
                "sample_records": len(results),
                "single_inference": "PASS",
                "batch_order": "PASS",
                "distances": "PASS",
                "profiles": "PASS",
                "strict_validation": "PASS",
                "dataset_notebook_network_fitting_denied": True,
                "package_import_path": spotify_cluster.__file__,
            }
        )
    )


if __name__ == "__main__":
    main()
