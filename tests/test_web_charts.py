"""Aggregate tables and Plotly figures; software fixtures are not evidence."""

import pytest
from plotly.graph_objects import Figure

from spotify_cluster.config import F9
from spotify_cluster.web import charts, figures


def test_distribution_counts_shares(web_responses):
    frame = charts.distribution(web_responses["clusters"])
    assert frame.to_dict("list") == {
        "Cluster": ["Cluster 0", "Cluster 1"],
        "Tracks": [5, 5],
        "Share (%)": [50.0, 50.0],
    }


@pytest.mark.parametrize("feature", F9)
@pytest.mark.parametrize("statistic", ["Mean", "Median"])
def test_comparison_values_units(feature, statistic, web_responses):
    data = web_responses["clusters"]
    data["clusters"]["0"]["mean"][feature] = 0.1234
    data["clusters"]["0"]["median"][feature] = 0.2345
    frame = charts.comparison(data, feature, statistic)
    assert frame.iloc[0]["Value"] == data["clusters"]["0"][statistic.lower()][feature]
    table = charts.profile_table(data, statistic)
    assert table[table.Feature == feature.title()].iloc[0]["Unit"] == charts.unit(
        feature
    )
    assert charts.unit(feature) == {"tempo": "BPM", "loudness": "dB"}.get(
        feature, "0–1"
    )
    assert list(frame) == ["Cluster", "Value"]


def test_optional_spread_and_profile_selection(web_responses):
    data = web_responses["clusters"]
    data["clusters"]["1"].pop("std")
    frame = charts.detail_table(data, "Cluster 1")
    assert frame.Std.isna().all() and len(frame) == 9
    assert set(frame.Feature) == {f.title() for f in F9}
    with pytest.raises(ValueError):
        charts.selected_profiles(data, "private-path")
    with pytest.raises(ValueError):
        charts.comparison(data, "pca", "Mean")


def test_distribution_figure_uses_only_aggregate_values(web_responses):
    figure = figures.distribution_figure(web_responses["clusters"])
    assert isinstance(figure, Figure)
    assert list(figure.data[0].x) == [5, 5]
    assert list(figure.data[0].y) == ["Cluster 0", "Cluster 1"]
    assert list(figure.data[0].text) == ["5 · 50.00%", "5 · 50.00%"]
    assert list(figure.data[0].marker.color) == ["#147D73", "#7055B9"]
    assert list(figure.layout.xaxis.range) == pytest.approx([0, 6.6])
    assert figure.layout.paper_bgcolor == "#FFFFFF"
    assert figure.layout.plot_bgcolor == "#FFFFFF"


def test_comparison_figure_units_and_zero_baseline(web_responses):
    data = web_responses["clusters"]
    figure = figures.comparison_figure(data, "instrumentalness", "Mean", "Cluster 1")
    assert list(figure.data[0].x) == ["Cluster 1"]
    assert list(figure.data[0].y) == [0.5]
    assert list(figure.layout.yaxis.range) == [0, 1]
    data["clusters"]["0"]["mean"]["loudness"] = -20.0
    data["clusters"]["1"]["mean"]["loudness"] = -5.0
    figure = figures.comparison_figure(data, "loudness", "Mean")
    low, high = figure.layout.yaxis.range
    assert low <= -20.0 and high >= -5.0
    assert figure.layout.yaxis.title.text == "Loudness (dB)"
    assert figure.layout.yaxis.zeroline is True


def test_distance_figure_marks_the_nearest_centroid(web_responses):
    prediction = web_responses["predict"]
    figure = figures.distances_figure(prediction)
    assert list(figure.data[0].x) == prediction["distances"]
    assert list(figure.data[0].y) == ["Cluster 0", "Cluster 1"]
    colors = list(figure.data[0].marker.color)
    nearest = prediction["cluster_id"]
    assert colors[nearest] == ["#147D73", "#7055B9"][nearest]
    assert colors[1 - nearest] == "#7B8896"
    assert figure.layout.margin.l == 92
    assert "probability" not in figure.layout.xaxis.title.text.lower()


def test_contribution_and_comparison_figures(web_responses):
    profiles = web_responses["clusters"]
    contributions = figures.contributions_figure(profiles)
    assert contributions.data[0].orientation == "h"
    assert contributions.data[0].y[0] == "Instrumentalness"
    assert contributions.data[0].x[0] == pytest.approx(1.0)
    assert list(contributions.layout.xaxis.range) == [0, 1]
    research = figures.research_figure(web_responses["comparison"])
    f5 = web_responses["comparison"]["comparisons"]["f5_kmeans_vs_deployment_f9_kmeans"]
    gmm = web_responses["comparison"]["comparisons"]["f9_kmeans_vs_f9_gmm"]
    assert list(research.data[0].x) == [f5["ari"], gmm["ari"]]
    assert list(research.layout.xaxis.range) == [-1.05, 1.05]
    assert "not quality" in research.layout.xaxis.title.text.lower()


def test_empty_figures_are_explicit():
    figure = figures.empty_figure("Nothing yet.")
    assert isinstance(figure, Figure)
    assert figure.layout.annotations[0].text == "Nothing yet."
