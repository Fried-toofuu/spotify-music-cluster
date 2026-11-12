"""Software-fixture checks for the visualization export contract."""

import copy
import json

import numpy as np
import pytest

from spotify_cluster.config import DEPLOYMENT_V1, F9
from spotify_cluster.visualization import (
    build_visualization,
    load_visualization,
    neighbours,
    occupancy_view,
    points_view,
    public_meta,
    save_visualization,
    verify_visualization,
)


def metadata_for(bundle_parts):
    metadata, _profiles, _numerics = bundle_parts
    metadata = copy.deepcopy(metadata)
    metadata["deployment_profile"] = DEPLOYMENT_V1.identifier
    metadata["model_origin"] = "new_deployment_refit"
    return metadata


def build(pipeline, matrix, metadata, **kwargs):
    options = dict(
        mode="points",
        per_cluster_cap=20,
        seed=7,
        occupancy_bins=4,
        occupancy_min_count=2,
    )
    options.update(kwargs)
    return build_visualization(pipeline, metadata, matrix, **options)


def test_points_artifact_is_deterministic_and_self_verifying(
    pipeline, matrix, bundle_parts
):
    metadata = metadata_for(bundle_parts)
    first, checks = build(pipeline, matrix, metadata)
    second, _ = build(pipeline, matrix, metadata)
    assert checks["pca_projection_recomputed"] == "PASS"
    assert sum(first["sample"]["cluster_counts"]) == len(first["points"]["x"])
    assert all(0 < count <= 20 for count in first["sample"]["cluster_counts"])
    assert first["views"] == {"points": True, "density": True}
    assert np.isfinite(first["points"]["x"]).all()
    assert first["pca"]["n_components"] == 3
    assert (
        first["pca"]["explained_variance_ratio"]
        == second["pca"]["explained_variance_ratio"]
    )
    assert first["points"] == second["points"]
    assert first["occupancy"] == second["occupancy"]
    verify_visualization(first, expected_model_id=metadata["model_id"])


def test_aggregate_artifact_has_no_point_level_data(pipeline, matrix, bundle_parts):
    metadata = metadata_for(bundle_parts)
    payload, _ = build(pipeline, matrix, metadata, mode="aggregate")
    assert payload["artifact_mode"] == "aggregate"
    assert "points" not in payload
    assert payload["sample"]["size"] == 0
    assert payload["views"] == {"points": False, "density": True}
    assert payload["occupancy"]["cells"]
    serialized = json.dumps(payload)
    for identifier in (
        "track_id",
        "artists",
        "album_name",
        "track_name",
        "raw_features",
    ):
        assert identifier not in serialized
    verify_visualization(payload)


def test_tampered_or_mismatched_artifact_is_rejected(
    tmp_path, pipeline, matrix, bundle_parts
):
    metadata = metadata_for(bundle_parts)
    payload, checks = build(pipeline, matrix, metadata)
    save_visualization(tmp_path / "viz", payload, checks)
    assert (
        load_visualization(tmp_path / "viz", expected_model_id=payload["model_id"])[
            "model_id"
        ]
        == payload["model_id"]
    )
    with pytest.raises(ValueError, match="identity mismatch"):
        load_visualization(tmp_path / "viz", expected_model_id="different-model")
    path = tmp_path / "viz" / "visualization.json"
    path.write_text(path.read_text(encoding="utf-8") + " ", encoding="utf-8")
    with pytest.raises(ValueError, match="checksum mismatch"):
        load_visualization(tmp_path / "viz")


def test_identifier_fields_and_bad_coordinates_are_rejected(
    pipeline, matrix, bundle_parts
):
    metadata = metadata_for(bundle_parts)
    payload, _ = build(pipeline, matrix, metadata)
    leaked = copy.deepcopy(payload)
    leaked["track_id"] = ["not", "allowed"]
    with pytest.raises(ValueError, match="record field"):
        verify_visualization(leaked)
    shifted = copy.deepcopy(payload)
    shifted["points"]["x"][0] += 0.01
    with pytest.raises(ValueError, match="do not recompute"):
        verify_visualization(shifted)
    bad_mode = copy.deepcopy(payload)
    bad_mode["artifact_mode"] = "aggregate"
    with pytest.raises(ValueError, match="views"):
        verify_visualization(bad_mode)


def test_neighbours_use_scaled_space_and_exclude_the_query(
    pipeline, matrix, bundle_parts
):
    metadata = metadata_for(bundle_parts)
    payload, _ = build(pipeline, matrix, metadata)
    result = neighbours(payload, 3, 5)
    assert result["point"]["index"] == 3
    indices = [entry["index"] for entry in result["neighbors"]]
    assert len(indices) == 5 and 3 not in indices
    distances = [entry["distance"] for entry in result["neighbors"]]
    assert distances == sorted(distances)
    features = np.asarray(payload["points"]["raw_features"])
    center = np.asarray(payload["points"]["scaler_center"])
    scale = np.asarray(payload["points"]["scaler_scale"])
    scaled = (features - center) / scale
    manual = np.linalg.norm(scaled - scaled[3], axis=1)
    manual[3] = np.inf
    expected = np.argsort(manual, kind="stable")[:5]
    assert indices == [int(index) for index in expected]
    with pytest.raises(ValueError, match="outside"):
        neighbours(payload, 999)
    aggregate, _ = build(pipeline, matrix, metadata, mode="aggregate")
    with pytest.raises(ValueError, match="track-level"):
        neighbours(aggregate, 0)


def test_public_views_exclude_private_scaler_state(pipeline, matrix, bundle_parts):
    metadata = metadata_for(bundle_parts)
    payload, _ = build(pipeline, matrix, metadata)
    meta = public_meta(payload)
    assert "points" not in meta
    assert "scaler_center" not in json.dumps(meta)
    view = points_view(payload)
    assert view["view"] == "points"
    assert len(view["points"]["raw_features"]) == view["sample"]["size"]
    aggregate, _ = build(pipeline, matrix, metadata, mode="aggregate")
    density = occupancy_view(aggregate)
    assert density["view"] == "density"
    assert "points" not in density
    with pytest.raises(ValueError, match="aggregate mode"):
        points_view(aggregate)


def test_visualization_does_not_mutate_the_fitted_model(pipeline, matrix, bundle_parts):
    metadata = metadata_for(bundle_parts)
    before = pipeline.predict(matrix)
    build(pipeline, matrix, metadata)
    assert np.array_equal(before, pipeline.predict(matrix))
    assert metadata["features"] == list(F9)
    assert metadata["modeling_pca"] is None
