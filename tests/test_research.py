"""Software-fixture checks for controlled research comparisons."""

import copy
import json

import numpy as np
import pytest

from spotify_cluster.config import DEPLOYMENT_V1, F9
from spotify_cluster.research import (
    ARCHIVED_HISTORICAL_EVIDENCE,
    build_comparison,
    load_comparison,
    save_comparison,
    verify_comparison,
)


def metadata_for(bundle_parts):
    metadata, _profiles, _numerics = bundle_parts
    metadata = copy.deepcopy(metadata)
    metadata["deployment_profile"] = DEPLOYMENT_V1.identifier
    metadata["model_origin"] = "new_deployment_refit"
    return metadata


def test_comparison_is_controlled_and_holdout_free(pipeline, matrix, bundle_parts):
    metadata = metadata_for(bundle_parts)
    payload, checks = build_comparison(pipeline, metadata, matrix)
    assert checks["holdout_not_evaluated"] == "PASS"
    assert payload["holdout_evaluated"] is False
    assert payload["historical_equivalence"] == "NOT VERIFIED"
    assert payload["population"]["training_sample_count"] == len(matrix)
    f5 = payload["comparisons"]["f5_kmeans_vs_deployment_f9_kmeans"]
    gmm = payload["comparisons"]["f9_kmeans_vs_f9_gmm"]
    assert f5["identical_track_ids"] is True
    assert gmm["identical_track_ids"] is True
    assert -1 <= f5["ari"] <= 1 and -1 <= gmm["ari"] <= 1
    assert sum(f5["deployment_cluster_counts"]) == len(matrix)
    assert sum(f5["f5_cluster_counts"]) == len(matrix)
    assert sum(gmm["gmm_hard_cluster_counts"]) == len(matrix)
    assert 0.5 <= gmm["mean_max_responsibility"] <= 1
    assert gmm["mean_entropy_nats"] >= 0
    assert f5["f5_features"] == [
        "acousticness",
        "danceability",
        "energy",
        "valence",
        "tempo",
    ]
    assert payload["features"] == list(F9)
    assert payload["archived_evidence"]["status"] == (
        "ARCHIVED; NOT RECOMPUTED; HOLDOUT CLOSED"
    )
    assert (
        payload["archived_evidence"]["holdout_silhouette"]
        == (ARCHIVED_HISTORICAL_EVIDENCE["holdout_silhouette"])
    )
    assert "holdout_silhouette" not in json.dumps(payload["population"])


def test_comparison_does_not_change_deployment_partition(
    pipeline, matrix, bundle_parts
):
    metadata = metadata_for(bundle_parts)
    before = pipeline.predict(matrix)
    payload, _ = build_comparison(pipeline, metadata, matrix)
    assert np.array_equal(before, pipeline.predict(matrix))
    assert payload["population"]["cluster_counts"] == metadata["cluster_counts"]


def test_comparison_roundtrip_and_tamper(tmp_path, pipeline, matrix, bundle_parts):
    metadata = metadata_for(bundle_parts)
    payload, checks = build_comparison(pipeline, metadata, matrix)
    save_comparison(tmp_path / "research", payload, checks)
    assert (
        load_comparison(tmp_path / "research", expected_model_id=payload["model_id"])[
            "model_id"
        ]
        == payload["model_id"]
    )
    with pytest.raises(ValueError, match="identity mismatch"):
        load_comparison(tmp_path / "research", expected_model_id="other-model")
    with pytest.raises(ValueError, match="fingerprint mismatch"):
        load_comparison(
            tmp_path / "research",
            expected_model_id=payload["model_id"],
            expected_dataset_sha256=payload["dataset_sha256"],
            expected_fingerprint="different-fingerprint",
        )
    path = tmp_path / "research" / "comparison.json"
    path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="checksum mismatch"):
        load_comparison(tmp_path / "research")


def test_invalid_or_identifier_payload_is_rejected(pipeline, matrix, bundle_parts):
    metadata = metadata_for(bundle_parts)
    payload, _ = build_comparison(pipeline, metadata, matrix)
    leaked = copy.deepcopy(payload)
    leaked["track_id"] = ["not allowed"]
    with pytest.raises(ValueError, match="record field"):
        verify_comparison(leaked)
    holdout = copy.deepcopy(payload)
    holdout["holdout_evaluated"] = True
    with pytest.raises(ValueError, match="Holdout"):
        verify_comparison(holdout)
    ari = copy.deepcopy(payload)
    ari["comparisons"]["f5_kmeans_vs_deployment_f9_kmeans"]["ari"] = 1.5
    with pytest.raises(ValueError, match="Adjusted Rand Index"):
        verify_comparison(ari)
    labels = copy.deepcopy(payload)
    labels["archived_evidence"]["status"] = "LIVE"
    with pytest.raises(ValueError, match="Archived evidence"):
        verify_comparison(labels)
