"""Presentation correctness against software-only API responses."""

import pytest

from spotify_cluster.config import F9
from spotify_cluster.web.components import Handlers, insight, payload, prediction_text


def test_exact_payload_and_domains(api_track):
    assert payload(list(api_track.values())) == api_track
    assert tuple(payload(list(api_track.values()))) == F9
    values = list(api_track.values())
    values[4], values[5] = 0, 100
    assert payload(values)["loudness"] == 100


@pytest.mark.parametrize(
    "index,value,match",
    [
        (0, -0.1, "between"),
        (7, 1.1, "between"),
        (4, -1, "Tempo"),
        (5, None, "finite"),
        (1, True, "finite"),
        (2, "0.5", "finite"),
        (3, float("inf"), "finite"),
        (8, float("nan"), "finite"),
        (5, 10**400, "finite"),
    ],
)
def test_invalid_input(index, value, match, api_track):
    values = list(api_track.values())
    values[index] = value
    with pytest.raises(ValueError, match=match):
        payload(values)


def test_incomplete_payload():
    with pytest.raises(ValueError, match="nine"):
        payload([0])


def test_refresh_predict_and_explore(web_client, web_responses, api_track):
    handlers = Handlers(web_client)
    state, status, summary, distribution, table, diagnostic, identity = (
        handlers.refresh()
    )
    assert "ready" in status and "10" in summary
    assert "software-fixture-only" in identity
    assert [p.get_width() for p in distribution.axes[0].patches] == [5.0, 5.0]
    assert table["Share (%)"].tolist() == [50.0, 50.0]
    assert "100.000%" in diagnostic and "not prediction accuracy" in diagnostic
    feedback, result, distances, exact = handlers.predict(state, *api_track.values())
    assert "received" in feedback and "software-fixture-only" in result
    assert "Cluster 0" in result
    assert [p.get_height() for p in distances.axes[0].patches] == web_responses[
        "predict"
    ]["distances"]
    assert exact["Cluster"].tolist() == ["Cluster 0", "Cluster 1"]
    text, chart, table, details = handlers.explore(
        state, "Cluster 1", "tempo", "Median"
    )
    assert "Cluster 1" in text and len(chart.axes[0].patches) == 1
    assert chart.axes[0].get_ylabel() == "Tempo (BPM)"
    assert list(table) == ["Feature", "Cluster 1", "Unit"]
    assert len(details) == 9


def test_profile_meaning_follows_current_profiles(web_client, web_responses):
    profiles = web_responses["clusters"]["clusters"]
    profiles["0"]["mean"]["instrumentalness"] = 0.9
    profiles["1"]["mean"]["instrumentalness"] = 0.1
    handlers = Handlers(web_client)
    state = handlers.refresh()[0]
    assert (
        "Cluster 0 has higher"
        in handlers.explore(state, "Compare Both", "instrumentalness", "Mean")[0]
    )


def test_identity_mismatch_and_population(web_client, web_responses, api_track):
    handlers = Handlers(web_client)
    state = handlers.refresh()[0]
    web_responses["predict"]["model_id"] = "changed-model"
    result = handlers.predict(state, *api_track.values())
    assert "model changed" in result[0] and result[2:] == (None, None)
    web_responses["model"]["training_sample_count"] += 1
    result = handlers.refresh()
    assert result[0] is None and "disagree" in result[1]
    web_responses["model"]["model_id"] = "another-model"
    assert handlers.refresh()[0] is None


def test_offline_and_invalid_clear_outputs(api_track):
    import httpx

    from spotify_cluster.web.api_client import APIClient

    def refuse(request):
        raise httpx.ConnectError("PRIVATE", request=request)

    handlers = Handlers(APIClient(transport=httpx.MockTransport(refuse)))
    refresh = handlers.refresh()
    assert refresh[0] is None and "Cannot connect" in refresh[1]
    result = handlers.predict(None, *api_track.values())
    assert "Cannot connect" in result[0] and result[2:] == (None, None)
    assert "nine" in handlers.predict(None, 0)[0]
    assert handlers.explore(None, "Compare Both", "tempo", "Mean")[1:] == (
        None,
        None,
        None,
    )


def test_missing_diagnostic_and_prediction_identity(web_responses):
    assert "Not available" in insight({})
    text = prediction_text(web_responses["predict"])
    assert web_responses["predict"]["model_id"] in text
    assert "NOT VERIFIED" in text and "50.00%" in text
