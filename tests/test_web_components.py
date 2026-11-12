"""Presentation correctness against software-only API responses."""

from types import SimpleNamespace

import pytest
from plotly.graph_objects import Figure

from spotify_cluster.config import F9
from spotify_cluster.web.components import (
    SYNTHETIC_EXAMPLE,
    Handlers,
    insight,
    payload,
    prediction_card_html,
    preview_payload,
    research_narrative_html,
    selection_html,
)


def event(index):
    return SimpleNamespace(index=index)


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


def test_refresh_returns_every_panel(web_client, web_responses):
    result = Handlers(web_client).refresh()
    assert len(result) == 20
    state, brandbar, status, overview, note, facts, finding, population = result[:8]
    (
        identity,
        disclosure,
        explorer,
        detail,
        research,
        contrib,
        comparison,
        archived,
        prediction_status,
        prediction,
        distance_plot,
        distance_table,
    ) = result[8:]
    assert state["model"]["model_id"] == "software-fixture-only"
    assert "Acoustic Observatory" in brandbar and "obs-live" not in brandbar
    assert "API ready" in status and "loaded" in status
    assert overview["view"] == "points"
    assert (
        overview["sample"]["size"] == 1
    )  # every fourth point of the four-point fixture
    assert "Preview plots every fourth" in note
    assert "10 tracks" in facts and "NOT VERIFIED" in facts
    assert "100.00%" in finding and "not prediction accuracy" in finding
    assert "Cluster 0" in population
    assert "software-fixture-only" in identity
    assert "Plotted sample" in disclosure and "4 tracks" in disclosure
    assert explorer["view"] == "points"
    assert "Sample inspector" in detail
    assert "Research &amp; methodology" in research
    assert "Archived historical" in research
    assert isinstance(contrib, Figure)
    assert isinstance(comparison, Figure)
    assert len(archived) == 3
    assert set(archived["Metric"]) == {
        "Holdout Silhouette",
        "Holdout Davies–Bouldin",
        "Holdout Calinski–Harabasz",
    }
    assert "Submit features" in prediction_status
    assert "Awaiting a feature vector" in prediction
    assert distance_plot.layout.annotations[0].text == (
        "Submit a feature vector to see distances."
    )
    assert list(distance_table.columns) == ["Cluster", "Distance"]


def test_load_explorer_and_point_selection(web_client, web_responses):
    handlers = Handlers(web_client)
    state = handlers.refresh()[0]
    payload_value, disclosure, placeholder = handlers.load_explorer(state)
    assert payload_value["view"] == "points"
    assert "Plotted sample" in disclosure
    assert "Sample inspector" in placeholder
    selected = handlers.explorer_select(state, event(0))
    assert "Sample #0" in selected
    assert "Nearest sampled tracks" in selected
    assert "not screen distance" in selected
    failed = handlers.explorer_select(state, event(1))
    assert "Could not complete" in failed
    assert 'class="obs-card obs-selection-error" data-sample="1"' in failed
    assert "Explorer Guide" in handlers.explorer_select(None, event(0))


def test_clear_selection_returns_mode_appropriate_guide_without_neighbor_request(
    web_client, monkeypatch
):
    import gradio as gr

    handlers = Handlers(web_client)
    state = handlers.refresh()[0]

    def forbidden(*args):
        raise AssertionError("Clearing selection must not request neighbors")

    monkeypatch.setattr(web_client, "visualization_neighbors", forbidden)
    for mode, expected in [
        ("density", "Read population density"),
        ("3d", "Pick a sample"),
        ("2d", "Pick a sample"),
    ]:
        cleared = handlers.explorer_select(
            state, gr.EventData(None, {"index": None, "view": mode})
        )
        assert expected in cleared
        assert "obs-selected-track" not in cleared


def test_research_disclosure_preserves_identity_and_evidence(web_responses):
    markup = research_narrative_html(
        web_responses["comparison"], web_responses["clusters"]
    )
    assert markup.index("Research Findings") < markup.index("Model Comparison")
    assert markup.index("Model Comparison") < markup.index(
        "Methodology and Reproducibility"
    )
    assert 'class="obs-research-layer">' in markup
    assert "NOT VERIFIED" in markup and "Holdout" in markup
    assert "Adjusted Rand Index" in markup and "not quality" in markup
    assert "Supporting figures and exact archived evidence" in markup


def test_explore_changes_with_feature_and_statistic(web_client, web_responses):
    handlers = Handlers(web_client)
    state = handlers.refresh()[0]
    text, chart, table, details = handlers.explore(
        state, "Cluster 1", "tempo", "Median"
    )
    assert "Cluster 1" in text
    assert isinstance(chart, Figure)
    assert list(chart.data[0].x) == ["Cluster 1"]
    assert chart.layout.yaxis.title.text == "Tempo (BPM)"
    assert list(table) == ["Feature", "Cluster 1", "Unit"]
    assert len(details) == 9
    empty = handlers.explore(None, "Compare Both", "tempo", "Mean")
    assert empty[1].layout.annotations[0].text == "Refresh live data first."
    assert empty[2:] == (None, None)


def test_prediction_and_stale_clearing(web_client, web_responses, api_track):
    handlers = Handlers(web_client)
    state = handlers.refresh()[0]
    feedback, card, chart, exact = handlers.predict(state, *api_track.values())
    assert "received" in feedback
    assert "Cluster 0" in card and "software-fixture-only" in card
    assert "probability" in card.lower() and "confidence" in card.lower()
    assert isinstance(chart, Figure)
    assert exact["Cluster"].tolist() == ["Cluster 0", "Cluster 1"]
    web_responses["predict"]["model_id"] = "changed-model"
    feedback, card, chart, exact = handlers.predict(state, *api_track.values())
    assert "model changed" in feedback
    assert "Could not complete" in card
    assert chart is None and exact is None


def test_identity_mismatch_and_offline(web_client, web_responses):
    handlers = Handlers(web_client)
    state = handlers.refresh()[0]
    assert state
    web_responses["model"]["training_sample_count"] += 1
    result = handlers.refresh()
    assert result[0] is None and "disagree" in result[2]
    web_responses["model"]["model_id"] = "another-model"
    assert handlers.refresh()[0] is None

    import httpx

    from spotify_cluster.web.api_client import APIClient

    def refuse(request):
        raise httpx.ConnectError("PRIVATE", request=request)

    offline = Handlers(APIClient(transport=httpx.MockTransport(refuse)))
    result = offline.refresh()
    assert result[0] is None and "Cannot connect" in result[2]
    assert "Could not complete" in offline.predict(None, 0)[1]
    empty = offline.explore(None, "Compare Both", "tempo", "Mean")
    assert empty[1].layout.annotations[0].text == "Refresh live data first."
    assert empty[2:] == (None, None)


def test_preview_payload_is_explicit(web_responses):
    source = web_responses["points"]
    preview = preview_payload(source, stride=2)
    assert preview["sample"]["size"] == 2
    assert preview["sample"]["policy"].startswith("Overview preview")
    assert "not population proportions" in preview["sample"]["proportions_disclosure"]
    assert len(preview["points"]["x"]) == 2
    assert source["sample"]["size"] == 4


def test_prediction_card_uses_current_profile(web_responses):
    result = web_responses["predict"]
    card = prediction_card_html(result, web_responses["clusters"])
    assert "Cluster 0" in card
    assert "nearest" in card.lower()
    assert "not a probability" in card.lower()
    assert "instrumentalness" in card


def test_selection_html_escapes_and_uses_real_features(web_responses):
    result = web_responses["neighbors"]
    markup = selection_html(result)
    assert "Sample #0" in markup
    assert "Nearest sampled tracks" in markup
    assert "0.2000" in markup
    assert "Cluster 0" in markup


def test_insight_follows_current_profiles(web_responses):
    assert "100.00%" in insight(web_responses["clusters"])
    assert "not available" in insight({}).lower()


def test_missing_contributions_never_become_zero_evidence(web_responses):
    profiles = web_responses["clusters"]
    profiles.pop("feature_contributions")
    html = research_narrative_html(
        {"available": False, "reason": "not provisioned"}, profiles
    )
    assert "Separation diagnostic unavailable" in html
    assert "drives 0.00%" not in html
    assert "0 tracks" not in html


def test_example_clears_stale_prediction(web_client):
    result = Handlers(web_client).load_example()
    assert len(result) == 13
    assert result[:9] == tuple(SYNTHETIC_EXAMPLE)
    assert "Submit features" in result[9]
    assert "Awaiting a feature vector" in result[10]
    assert result[11].layout.annotations[0].text == (
        "Submit a feature vector to see distances."
    )
    assert list(result[12].columns) == ["Cluster", "Distance"]


def test_offline_does_not_fabricate_research(api_track):
    import httpx

    from spotify_cluster.web.api_client import APIClient

    def refuse(request):
        raise httpx.ConnectError("PRIVATE", request=request)

    result = Handlers(APIClient(transport=httpx.MockTransport(refuse))).refresh()
    assert len(result) == 20
    research_html = result[12]
    assert "Research evidence unavailable" in research_html
    assert "drives 0.00%" not in research_html
    assert "0 tracks" not in research_html
