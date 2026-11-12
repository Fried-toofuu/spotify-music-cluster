"""Aggregate tables and static figures; no observations or projection coordinates."""

import pandas as pd
from matplotlib.figure import Figure

from spotify_cluster.config import F9

COLORS = {"Cluster 0": "#69d6a0", "Cluster 1": "#8ebcff"}
SURFACE = "#1c2621"
INK = "#edf5f0"
MUTED = "#b5c8bd"
LINE = "#3d5146"


def unit(feature):
    return {"tempo": "BPM", "loudness": "dB"}.get(feature, "0–1")


def selected_profiles(data, selection="Compare Both"):
    if selection not in ("Compare Both", "Cluster 0", "Cluster 1"):
        raise ValueError("Choose Cluster 0, Cluster 1 or Compare Both.")
    labels = (0, 1) if selection == "Compare Both" else (int(selection[-1]),)
    return [data["clusters"][str(i)] for i in labels]


def distribution(data):
    return pd.DataFrame(
        [
            {
                "Cluster": f"Cluster {p['cluster_id']}",
                "Tracks": p["count"],
                "Share (%)": p["share"] * 100,
            }
            for p in selected_profiles(data)
        ]
    )


def comparison(data, feature, statistic, selection="Compare Both"):
    if feature not in F9 or statistic not in ("Mean", "Median"):
        raise ValueError("Choose a supported feature and statistic.")
    return pd.DataFrame(
        [
            {
                "Cluster": f"Cluster {p['cluster_id']}",
                "Value": p[statistic.lower()][feature],
            }
            for p in selected_profiles(data, selection)
        ]
    )


def profile_table(data, statistic, selection="Compare Both"):
    if statistic not in ("Mean", "Median"):
        raise ValueError("Choose Mean or Median.")
    profiles = selected_profiles(data, selection)
    rows = []
    for f in F9:
        row = {"Feature": f.title()}
        for p in profiles:
            row[f"Cluster {p['cluster_id']}"] = round(p[statistic.lower()][f], 4)
        row["Unit"] = unit(f)
        rows.append(row)
    return pd.DataFrame(rows)


def detail_table(data, selection="Compare Both"):
    rows = []
    for p in selected_profiles(data, selection):
        for f in F9:
            row = {
                "Cluster": f"Cluster {p['cluster_id']}",
                "Feature": f.title(),
                "Unit": unit(f),
            }
            for stat in ("mean", "median", "std", "q1", "q3", "iqr"):
                values = p.get(stat)
                row[stat.upper() if stat in ("q1", "q3", "iqr") else stat.title()] = (
                    round(values[f], 4) if values else None
                )
            rows.append(row)
    return pd.DataFrame(rows)


def distances(prediction):
    return pd.DataFrame(
        {"Cluster": ["Cluster 0", "Cluster 1"], "Distance": prediction["distances"]}
    )


def _axes(width, height, *, horizontal=False):
    figure = Figure(figsize=(width, height), dpi=150)
    figure.patch.set_facecolor(SURFACE)
    axes = figure.add_subplot()
    axes.set_facecolor(SURFACE)
    axes.spines[["top", "right"]].set_visible(False)
    for side in ("left", "bottom"):
        axes.spines[side].set_color(LINE)
    axes.tick_params(colors=MUTED, labelsize=9.5)
    axes.grid(axis="x" if horizontal else "y", color=LINE, linewidth=0.6, alpha=0.7)
    axes.set_axisbelow(True)
    return figure, axes


def _title(axes, text):
    axes.set_title(text, color=INK, fontsize=11, loc="left")


def _label(value, feature=None):
    return f"{value:.1f}" if feature in ("tempo", "loudness") else f"{value:.4f}"


def _finish(figure):
    figure.tight_layout()
    return figure


def distribution_figure(data):
    """Horizontal bars; NativePlot could not apply post-render data updates."""
    profiles = selected_profiles(data)
    labels = [f"Cluster {p['cluster_id']}" for p in profiles]
    counts = [p["count"] for p in profiles]
    figure, axes = _axes(4.6, 2.9, horizontal=True)
    axes.barh(labels, counts, color=[COLORS[label] for label in labels], height=0.55)
    axes.invert_yaxis()
    axes.set_xlabel("Training tracks", color=MUTED, fontsize=10)
    _title(axes, "Training population by cluster")
    top = max(counts)
    axes.set_xlim(0, top * 1.32)
    for profile, label in zip(profiles, labels, strict=True):
        axes.text(
            profile["count"] + top * 0.02,
            label,
            f"{profile['count']:,} · {profile['share']:.2%}",
            va="center",
            color=INK,
            fontsize=10,
        )
    return _finish(figure)


def comparison_figure(data, feature, statistic, selection="Compare Both"):
    if feature not in F9 or statistic not in ("Mean", "Median"):
        raise ValueError("Choose a supported feature and statistic.")
    profiles = selected_profiles(data, selection)
    labels = [f"Cluster {p['cluster_id']}" for p in profiles]
    values = [p[statistic.lower()][feature] for p in profiles]
    figure, axes = _axes(4.6, 2.9)
    bars = axes.bar(
        labels, values, color=[COLORS[label] for label in labels], width=0.5
    )
    _title(axes, f"{feature.title()} · {statistic}")
    axes.set_ylabel(f"{feature.title()} ({unit(feature)})", color=MUTED, fontsize=10)
    if feature in ("tempo", "loudness"):
        low, high = min(0.0, *values), max(0.0, *values)
        pad = max((high - low) * 0.18, 0.05 * max(abs(high), abs(low), 1.0))
        axes.set_ylim(low - (pad if low < 0 else 0), high + pad)
    else:
        axes.set_ylim(0, 1)
    span = axes.get_ylim()[1] - axes.get_ylim()[0]
    for bar, value in zip(bars, values, strict=True):
        above = value >= 0
        axes.text(
            bar.get_x() + bar.get_width() / 2,
            value + (span * 0.02 if above else -span * 0.02),
            _label(value, feature),
            ha="center",
            va="bottom" if above else "top",
            color=INK,
            fontsize=10,
        )
    return _finish(figure)


def distances_figure(prediction):
    labels = ["Cluster 0", "Cluster 1"]
    values = list(prediction["distances"])
    figure, axes = _axes(4.6, 2.9)
    bars = axes.bar(
        labels, values, color=[COLORS[label] for label in labels], width=0.5
    )
    _title(axes, "Centroid distances")
    axes.set_ylabel("Euclidean distance (transformed F9)", color=MUTED, fontsize=10)
    top = max(values)
    axes.set_ylim(0, top * 1.18 if top else 1)
    for bar, value in zip(bars, values, strict=True):
        axes.text(
            bar.get_x() + bar.get_width() / 2,
            value + axes.get_ylim()[1] * 0.02,
            f"{value:.4f}",
            ha="center",
            va="bottom",
            color=INK,
            fontsize=10,
        )
    return _finish(figure)
