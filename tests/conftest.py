"""Synthetic software fixtures only; never Spotify research evidence."""

import numpy as np
import pandas as pd
import pytest

from spotify_cluster.config import F9, PREPARATION_VERSION
from spotify_cluster.model_store import make_metadata, new_model_id, save_bundle
from spotify_cluster.training import cluster_profiles, train_model, verify_numerics

pytest_plugins = ["api_fixtures"]


def pytest_addoption(parser):
    parser.addoption(
        "--run-real-web",
        action="store_true",
        help="Opt in to owned Gradio/FastAPI HTTP integration; no refit",
    )
    parser.addoption(
        "--run-real-api",
        action="store_true",
        help="Opt in to private deployment-model API tests; no dataset access or refit",
    )
    parser.addoption(
        "--run-real-model",
        action="store_true",
        help="Opt in to private model tests and one sequential reconstruction",
    )


@pytest.fixture
def matrix():
    rng = np.random.default_rng(42)
    values = rng.uniform(0.1, 0.9, size=(40, 9))
    values[:, 4] *= 200
    values[:, 5] *= -30
    values[:20, 7] = 0
    values[20:, 7] = 1
    return values


@pytest.fixture
def params():
    # Explicit test settings, not recovered historical final-refit parameters.
    return dict(
        n_clusters=2,
        init="k-means++",
        n_init=5,
        max_iter=300,
        tol=1e-4,
        algorithm="lloyd",
        random_state=42,
        copy_x=True,
        verbose=0,
    )


@pytest.fixture
def raw(matrix):
    frame = pd.DataFrame(matrix, columns=F9)
    frame["track_id"] = [f"test-{i:03d}" for i in range(len(frame))]
    frame["track_genre"] = "software-fixture"
    return frame


@pytest.fixture
def pipeline(matrix, params):
    return train_model(matrix, params)


@pytest.fixture
def bundle_parts(matrix, pipeline):
    model_id = new_model_id()
    metadata = make_metadata(
        pipeline,
        model_id,
        {
            "dataset_sha256": "software-fixture",
            "prepared_fingerprint": "software-fixture",
            "preparation_version": PREPARATION_VERSION,
            "training_sample_count": len(matrix),
        },
        reconstruction_status="software-test-only",
    )
    profiles = cluster_profiles(pipeline, matrix, model_id)
    return metadata, profiles, verify_numerics(pipeline, matrix)


@pytest.fixture
def artifact(tmp_path, pipeline, bundle_parts):
    path = tmp_path / "software-test-model"
    save_bundle(path, pipeline, *bundle_parts)
    return path


def visualization_responses(model_id):
    """Small, internally consistent visualization doubles; not research evidence."""
    population = {
        "training_sample_count": 10,
        "cluster_counts": [5, 5],
        "cluster_shares": [0.5, 0.5],
    }
    sample = {
        "policy": "software fixture sample",
        "seed": 42,
        "per_cluster_cap": 2,
        "size": 4,
        "cluster_counts": [2, 2],
        "population_cluster_counts": [5, 5],
        "proportions_disclosure": "not population proportions",
    }
    pca = {
        "n_components": 3,
        "fit_representation": "software fixture scaled F9",
        "explained_variance_ratio": [0.5, 0.3, 0.1],
        "cumulative_explained_variance": [0.5, 0.8, 0.9],
        "components": [
            [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        ],
        "sign_convention": "software fixture",
        "scope": "visualization only",
    }
    license_value = {
        "name": "Spotify Tracks Dataset (Maharshi Pandya, Kaggle)",
        "license": "ODbL 1.0",
        "url": "https://www.kaggle.com/datasets/maharshipandya/-spotify-tracks-dataset",
        "redistribution": "software fixture disclosure",
    }
    occupancy = {
        "definition": "software fixture aggregate",
        "bins": 4,
        "min_cell_count": 2,
        "x_range": [-1.0, 1.0],
        "y_range": [-1.0, 1.0],
        "cells": [
            {
                "x": 0.0,
                "y": 0.0,
                "count": 4,
                "cluster1_share": 0.5,
                "mean_instrumentalness": 0.5,
            }
        ],
    }
    rows = [
        [0.2, 0.5, 0.6, 0.5, 120.0, -8.0, 0.05, 0.0, 0.1],
        [0.3, 0.4, 0.5, 0.4, 100.0, -9.0, 0.06, 0.1, 0.2],
        [0.7, 0.6, 0.4, 0.3, 130.0, -7.0, 0.04, 0.9, 0.3],
        [0.8, 0.7, 0.3, 0.2, 140.0, -6.0, 0.03, 1.0, 0.4],
    ]
    points = {
        "x": [-0.8, -0.6, 0.5, 0.7],
        "y": [0.1, 0.2, -0.1, -0.3],
        "z": [0.0, 0.1, 0.2, 0.3],
        "cluster": [0, 0, 1, 1],
        "raw_features": rows,
    }
    pca_view = {
        "explained_variance_ratio": pca["explained_variance_ratio"],
        "cumulative_explained_variance": pca["cumulative_explained_variance"],
        "scope": pca["scope"],
    }
    return {
        "meta": {
            "available": True,
            "schema_version": 1,
            "artifact_kind": "pca-cluster-space",
            "artifact_mode": "points",
            "model_id": model_id,
            "deployment_profile": "spotify-f9-robust-kmeans-k2-v1",
            "dataset_sha256": "software-fixture",
            "prepared_fingerprint": "software-fixture",
            "preparation_version": "software-fixture",
            "created_at": "2026-01-01T00:00:00+00:00",
            "features": list(F9),
            "population": population,
            "pca": pca,
            "sample": sample,
            "views": {"points": True, "density": True},
            "software": {"python": "3.12"},
            "license": license_value,
            "limitations": "software fixture limitations",
            "historical_equivalence": "NOT VERIFIED",
            "model_origin": "new_deployment_refit",
        },
        "points": {
            "model_id": model_id,
            "view": "points",
            "features": list(F9),
            "pca": pca_view,
            "population": population,
            "sample": sample,
            "points": points,
            "occupancy": occupancy,
            "limitations": "software fixture limitations",
            "historical_equivalence": "NOT VERIFIED",
        },
        "occupancy": {
            "model_id": model_id,
            "view": "density",
            "features": list(F9),
            "pca": pca_view,
            "population": population,
            "occupancy": occupancy,
            "limitations": "software fixture limitations",
            "historical_equivalence": "NOT VERIFIED",
        },
        "neighbors": {
            "model_id": model_id,
            "selection": "software fixture neighbors",
            "distance_definition": "Euclidean distance in software fixture space",
            "sample_size": 4,
            "point": {
                "index": 0,
                "cluster": 0,
                "coordinates": [-0.8, 0.1, 0.0],
                "features": dict(zip(F9, rows[0], strict=True)),
            },
            "neighbors": [
                {
                    "index": 1,
                    "cluster": 0,
                    "coordinates": [-0.6, 0.2, 0.1],
                    "features": dict(zip(F9, rows[1], strict=True)),
                    "distance": 0.2,
                }
            ],
            "historical_equivalence": "NOT VERIFIED",
        },
        "comparison": {
            "available": True,
            "schema_version": 1,
            "artifact_kind": "training-population-comparison",
            "created_at": "2026-01-01T00:00:00+00:00",
            "model_id": model_id,
            "deployment_profile": "spotify-f9-robust-kmeans-k2-v1",
            "dataset_sha256": "software-fixture",
            "prepared_fingerprint": "software-fixture",
            "preparation_version": "software-fixture",
            "features": list(F9),
            "population": population,
            "scope": "software fixture comparison",
            "comparisons": {
                "f5_kmeans_vs_deployment_f9_kmeans": {
                    "definition": "software fixture",
                    "identical_track_ids": True,
                    "f5_features": list(F9[:5]),
                    "f5_recipe": {},
                    "deployment_recipe": {},
                    "ari": 0.1,
                    "f5_cluster_counts": [5, 5],
                    "deployment_cluster_counts": [5, 5],
                    "interpretation": "software fixture",
                },
                "f9_kmeans_vs_f9_gmm": {
                    "definition": "software fixture",
                    "identical_track_ids": True,
                    "representation": "software fixture",
                    "gmm_recipe": {},
                    "ari": -0.1,
                    "gmm_hard_cluster_counts": [5, 5],
                    "mean_max_responsibility": 0.9,
                    "mean_entropy_nats": 0.2,
                    "soft_assignment_definition": "software fixture",
                    "interpretation": "software fixture",
                },
            },
            "archived_evidence": {
                "label": "Archived historical FULL research evidence",
                "source": "software fixture",
                "scope": "software fixture",
                "status": "ARCHIVED; NOT RECOMPUTED; HOLDOUT CLOSED",
                "holdout_silhouette": 0.6,
                "holdout_davies_bouldin": 0.63,
                "holdout_calinski_harabasz": 3750.0,
                "warning": "software fixture",
            },
            "software": {"python": "3.12"},
            "license": license_value,
            "limitations": "software fixture limitations",
            "historical_equivalence": "NOT VERIFIED",
            "holdout_evaluated": False,
        },
    }


@pytest.fixture
def web_responses(api_client, api_track):
    """HTTP contract responses from the deterministic software-only API double."""
    responses = {
        "health": api_client.get("/api/v1/health").json(),
        "model": api_client.get("/api/v1/model").json(),
        "clusters": api_client.get("/api/v1/clusters").json(),
        "predict": api_client.post("/api/v1/predict", json=api_track).json(),
    }
    responses.update(visualization_responses(responses["model"]["model_id"]))
    return responses


@pytest.fixture
def web_client(web_responses):
    import httpx

    from spotify_cluster.web.api_client import APIClient

    return APIClient(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(
                200, json=web_responses[request.url.path.rsplit("/", 1)[-1]]
            )
        )
    )
