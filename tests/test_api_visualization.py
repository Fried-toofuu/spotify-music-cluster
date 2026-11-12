"""Artifact-serving endpoints with deterministic software fixtures."""

import copy

import pytest
from fastapi.testclient import TestClient

from spotify_cluster.api.app import create_app
from spotify_cluster.research import build_comparison, save_comparison
from spotify_cluster.visualization import build_visualization, save_visualization


def _metadata(bundle_parts):
    metadata, _profiles, _numerics = bundle_parts
    metadata = copy.deepcopy(metadata)
    metadata["deployment_profile"] = "spotify-f9-robust-kmeans-k2-v1"
    metadata["model_origin"] = "new_deployment_refit"
    return metadata


def _prepare(tmp_path, pipeline, matrix, bundle_parts, mode="points"):
    metadata = _metadata(bundle_parts)
    payload, checks = build_visualization(
        pipeline,
        metadata,
        matrix,
        mode=mode,
        per_cluster_cap=20,
        seed=7,
        occupancy_bins=4,
        occupancy_min_count=2,
    )
    save_visualization(tmp_path / f"viz-{mode}", payload, checks)
    research_payload, research_checks = build_comparison(pipeline, metadata, matrix)
    save_comparison(tmp_path / "research", research_payload, research_checks)
    return metadata


def _client(software_service, tmp_path, metadata, mode="points", *, research=True):
    software_service._metadata["model_id"] = metadata["model_id"]
    software_service._profiles["model_id"] = metadata["model_id"]
    software_service._metadata["dataset_sha256"] = metadata["dataset_sha256"]
    software_service._metadata["prepared_fingerprint"] = metadata[
        "prepared_fingerprint"
    ]
    app = create_app(
        tmp_path,
        service_factory=lambda _: software_service,
        visualization_dir=tmp_path / f"viz-{mode}",
        research_dir=tmp_path / "research" if research else None,
    )
    return TestClient(app)


def test_points_meta_and_payload(
    software_service, tmp_path, pipeline, matrix, bundle_parts
):
    metadata = _prepare(tmp_path, pipeline, matrix, bundle_parts)
    with _client(software_service, tmp_path, metadata) as client:
        meta = client.get("/api/v1/visualization/meta")
        assert meta.status_code == 200
        body = meta.json()
        assert body["available"] is True
        assert body["model_id"] == metadata["model_id"]
        assert body["views"] == {"points": True, "density": True}
        assert body["sample"]["size"] > 0
        assert body["pca"]["n_components"] == 3
        points = client.get("/api/v1/visualization/points")
        assert points.status_code == 200
        payload = points.json()
        assert payload["model_id"] == metadata["model_id"]
        assert payload["view"] == "points"
        assert len(payload["points"]["x"]) == payload["sample"]["size"]
        assert len(payload["points"]["cluster"]) == payload["sample"]["size"]
        assert all(len(row) == 9 for row in payload["points"]["raw_features"])
        assert "scaler_center" not in points.text
        assert "scaler_scale" not in points.text
        occupancy = client.get("/api/v1/visualization/occupancy")
        assert occupancy.status_code == 200
        assert occupancy.json()["view"] == "density"
        assert occupancy.json()["occupancy"]["cells"]


def test_neighbors_and_bounds(
    software_service, tmp_path, pipeline, matrix, bundle_parts
):
    metadata = _prepare(tmp_path, pipeline, matrix, bundle_parts)
    with _client(software_service, tmp_path, metadata) as client:
        response = client.get("/api/v1/visualization/neighbors?index=2&k=4")
        assert response.status_code == 200
        body = response.json()
        assert body["point"]["index"] == 2
        assert len(body["neighbors"]) == 4
        assert all(entry["index"] != 2 for entry in body["neighbors"])
        assert body["distance_definition"].startswith("Euclidean distance")
        assert (
            client.get("/api/v1/visualization/neighbors?index=9999").status_code == 422
        )
        assert (
            client.get("/api/v1/visualization/neighbors?index=0&k=99").status_code
            == 422
        )
        assert client.get("/api/v1/visualization/neighbors?index=-1").status_code == 422


def test_aggregate_only_artifact_hides_points(
    software_service, tmp_path, pipeline, matrix, bundle_parts
):
    metadata = _prepare(tmp_path, pipeline, matrix, bundle_parts, mode="aggregate")
    with _client(software_service, tmp_path, metadata, mode="aggregate") as client:
        meta = client.get("/api/v1/visualization/meta").json()
        assert meta["available"] is True
        assert meta["artifact_mode"] == "aggregate"
        assert meta["views"] == {"points": False, "density": True}
        assert client.get("/api/v1/visualization/points").status_code == 404
        assert client.get("/api/v1/visualization/occupancy").status_code == 200
        assert client.get("/api/v1/visualization/neighbors?index=0").status_code == 404
        text = client.get("/api/v1/visualization/occupancy").text
        assert "raw_features" not in text
        assert "track_id" not in text


def test_missing_artifacts_are_reported_not_fatal(
    software_service, tmp_path, pipeline, matrix, bundle_parts
):
    metadata = _prepare(tmp_path, pipeline, matrix, bundle_parts)
    software_service._metadata["dataset_sha256"] = metadata["dataset_sha256"]
    software_service._metadata["prepared_fingerprint"] = metadata[
        "prepared_fingerprint"
    ]
    app = create_app(
        tmp_path,
        service_factory=lambda _: software_service,
        visualization_dir=None,
        research_dir=None,
    )
    with TestClient(app) as client:
        assert client.get("/api/v1/health").status_code == 200
        meta = client.get("/api/v1/visualization/meta")
        assert meta.status_code == 200
        assert meta.json()["available"] is False
        assert meta.json()["reason"]
        assert client.get("/api/v1/visualization/points").status_code == 404
        research = client.get("/api/v1/research/comparison")
        assert research.status_code == 200
        assert research.json()["available"] is False


def test_mismatched_artifact_identity_is_unavailable(
    software_service, tmp_path, pipeline, matrix, bundle_parts
):
    metadata = _prepare(tmp_path, pipeline, matrix, bundle_parts)
    software_service._metadata["model_id"] = metadata["model_id"]
    software_service._profiles["model_id"] = metadata["model_id"]
    software_service._metadata["dataset_sha256"] = "different-dataset"
    software_service._metadata["prepared_fingerprint"] = metadata[
        "prepared_fingerprint"
    ]
    app = create_app(
        tmp_path,
        service_factory=lambda _: software_service,
        visualization_dir=tmp_path / "viz-points",
        research_dir=tmp_path / "research",
    )
    with TestClient(app) as client:
        meta = client.get("/api/v1/visualization/meta").json()
        assert meta["available"] is False
        assert str(tmp_path) not in meta["reason"]
        assert client.get("/api/v1/research/comparison").json()["available"] is False


def test_research_endpoint(software_service, tmp_path, pipeline, matrix, bundle_parts):
    metadata = _prepare(tmp_path, pipeline, matrix, bundle_parts)
    with _client(software_service, tmp_path, metadata) as client:
        response = client.get("/api/v1/research/comparison")
        assert response.status_code == 200
        body = response.json()
        assert body["available"] is True
        assert body["model_id"] == metadata["model_id"]
        assert body["holdout_evaluated"] is False
        assert body["archived_evidence"]["status"] == (
            "ARCHIVED; NOT RECOMPUTED; HOLDOUT CLOSED"
        )
        assert "holdout_silhouette" in body["archived_evidence"]
        assert set(body["comparisons"]) == {
            "f5_kmeans_vs_deployment_f9_kmeans",
            "f9_kmeans_vs_f9_gmm",
        }


def test_gzip_for_large_points(
    software_service, tmp_path, pipeline, matrix, bundle_parts
):
    metadata = _prepare(tmp_path, pipeline, matrix, bundle_parts)
    with _client(software_service, tmp_path, metadata) as client:
        response = client.get(
            "/api/v1/visualization/points",
            headers={"Accept-Encoding": "gzip"},
        )
        assert response.status_code == 200
        assert response.headers.get("content-encoding") == "gzip"


@pytest.mark.parametrize("path", ["visualization/meta", "research/comparison"])
def test_unavailable_artifact_skips_without_dataset_identity(
    software_service, tmp_path, path
):
    app = create_app(tmp_path, service_factory=lambda _: software_service)
    with TestClient(app) as client:
        response = client.get(f"/api/v1/{path}")
        assert response.status_code == 200
        assert response.json()["available"] is False
