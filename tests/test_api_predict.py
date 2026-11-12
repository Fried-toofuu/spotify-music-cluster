def test_single_delegation_and_profile(api_client, api_track, software_service):
    response = api_client.post(
        "/api/v1/predict", json=dict(reversed(list(api_track.items())))
    )
    assert response.status_code == 200
    result = response.json()
    assert result["model_id"] == "software-fixture-only"
    assert result["cluster_id"] == 0
    assert result["distances"] == [0.25, 0.75]
    assert result["profile"]["cluster_id"] == result["cluster_id"]
    assert "Euclidean" in result["distance_definition"]
    assert "not probabilities" in result["limitation"]
    assert software_service.calls == [("one", [api_track])]
    assert list(software_service.calls[0][1][0]) == list(api_track)


def test_batch_is_one_ordered_operation_and_matches_single(
    api_client, api_track, software_service
):
    other = {**api_track, "instrumentalness": 0.9}
    tracks = [other, api_track, other]
    response = api_client.post("/api/v1/predict/batch", json={"tracks": tracks})
    assert response.status_code == 200
    results = response.json()["predictions"]
    assert [result["cluster_id"] for result in results] == [1, 0, 1]
    assert software_service.calls == [("batch", tracks)]
    for track, result in zip(tracks, results, strict=True):
        assert api_client.post("/api/v1/predict", json=track).json() == result


def test_single_record_and_max_batch(api_client, api_track):
    for size in (1, 100):
        response = api_client.post(
            "/api/v1/predict/batch", json={"tracks": [api_track] * size}
        )
        assert response.status_code == 200
        assert len(response.json()["predictions"]) == size


def test_inference_domains_allow_zero_tempo_and_positive_loudness(
    api_client, api_track
):
    assert (
        api_client.post(
            "/api/v1/predict", json={**api_track, "tempo": 0, "loudness": 5}
        ).status_code
        == 200
    )
