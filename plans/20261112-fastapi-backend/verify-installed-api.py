"""Run with a clean wheel Python in isolated mode outside the source checkout."""

import builtins
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from fastapi.testclient import TestClient
from sklearn.cluster import KMeans
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import RobustScaler

import spotify_cluster
from spotify_cluster.api.app import create_app, resolve_model_dir
from spotify_cluster.config import F9


def forbidden(*args, **kwargs):
    raise RuntimeError("Training or raw data access forbidden in installed API")


for cls in (KMeans, RobustScaler, Pipeline):
    for method in ("fit", "fit_predict", "fit_transform"):
        if hasattr(cls, method):
            setattr(cls, method, forbidden)
pd.read_csv = forbidden
original_open = builtins.open
original_path_open = Path.open


def guarded_open(file, *args, **kwargs):
    if str(file).endswith((".csv", ".ipynb")):
        forbidden()
    return original_open(file, *args, **kwargs)


def guarded_path_open(path, *args, **kwargs):
    if path.suffix in (".csv", ".ipynb"):
        forbidden()
    return original_path_open(path, *args, **kwargs)


builtins.open = guarded_open
Path.open = guarded_path_open
artifact = Path(sys.argv[1]).resolve()
assert "site-packages" in spotify_cluster.__file__
os.environ.pop("SPOTIFY_MODEL_DIR", None)
try:
    resolve_model_dir()
except ValueError:
    pass
else:
    raise AssertionError("Installed wheel must require explicit model configuration")
os.environ["SPOTIFY_MODEL_DIR"] = str(artifact)
sample = json.loads((artifact / "verification_sample.json").read_text())
tracks = [dict(zip(F9, row, strict=True)) for row in sample["raw_f9"]]
with TestClient(create_app()) as client:
    assert client.get("/api/v1/health").status_code == 200
    assert client.get("/api/v1/model").json()["model_id"] == sample["model_id"]
    assert client.get("/api/v1/clusters").json()["model_id"] == sample["model_id"]
    response = client.post("/api/v1/predict/batch", json={"tracks": tracks})
    assert response.status_code == 200
    results = response.json()["predictions"]
    np.testing.assert_array_equal(
        [r["cluster_id"] for r in results], sample["predictions"]
    )
    np.testing.assert_allclose(
        [r["distances"] for r in results], sample["distances"], rtol=1e-9, atol=1e-7
    )
    assert client.post("/api/v1/predict", json=tracks[0]).status_code == 200
    assert client.get("/docs").status_code == 200
    assert client.get("/openapi.json").status_code == 200
print(
    json.dumps(
        {
            "status": "PASS",
            "installed_from": "site-packages",
            "model_id": sample["model_id"],
            "verified_records": len(results),
            "no_training_or_dataset_access": True,
            "wheel_requires_explicit_model_dir": True,
        }
    )
)
