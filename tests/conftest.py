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


@pytest.fixture
def web_responses(api_client, api_track):
    """HTTP contract responses from the deterministic software-only API double."""
    return {
        "health": api_client.get("/api/v1/health").json(),
        "model": api_client.get("/api/v1/model").json(),
        "clusters": api_client.get("/api/v1/clusters").json(),
        "predict": api_client.post("/api/v1/predict", json=api_track).json(),
    }


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
