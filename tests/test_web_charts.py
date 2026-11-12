"""Aggregate-only chart data checks; software fixtures are not research evidence."""

import pytest

from spotify_cluster.config import F9
from spotify_cluster.web import charts


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


def test_figures_use_only_aggregate_values(web_responses):
    from matplotlib.figure import Figure

    data = web_responses["clusters"]
    distribution = charts.distribution_figure(data)
    assert isinstance(distribution, Figure)
    (axis,) = distribution.axes
    assert [p.get_width() for p in axis.patches] == [5.0, 5.0]
    assert [t.get_text() for t in axis.get_yticklabels()] == [
        "Cluster 0",
        "Cluster 1",
    ]
    assert any("50.00%" in t.get_text() for t in axis.texts)
    comparison = charts.comparison_figure(data, "instrumentalness", "Mean", "Cluster 1")
    (axis,) = comparison.axes
    assert len(axis.patches) == 1
    assert axis.get_ylabel() == "Instrumentalness (0–1)"
    assert axis.get_title(loc="left") == "Instrumentalness · Mean"
    data["clusters"]["0"]["mean"]["loudness"] = -20.0
    data["clusters"]["1"]["mean"]["loudness"] = -5.0
    (axis,) = charts.comparison_figure(data, "loudness", "Mean").axes
    assert axis.get_ylim()[0] <= -20.0 and axis.get_ylim()[1] >= -5.0
    assert axis.get_ylabel() == "Loudness (dB)"
    (axis,) = charts.distances_figure(web_responses["predict"]).axes
    assert [p.get_height() for p in axis.patches] == pytest.approx(
        web_responses["predict"]["distances"]
    )
