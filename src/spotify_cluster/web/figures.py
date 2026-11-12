"""Interactive Plotly figures over verified aggregate values."""

from __future__ import annotations

from plotly import graph_objects as go

from spotify_cluster.config import F9

from . import charts
from .theme import CLUSTER_COLORS, TOKENS

INK = TOKENS["ink"]
INK_2 = TOKENS["ink_2"]
MUTED = TOKENS["muted"]
LINE = TOKENS["line"]
SURFACE = TOKENS["surface_3"]
AMBER = TOKENS["amber"]
TEAL = TOKENS["teal"]


def _base(height=320, *, title=None, showlegend=False):
    figure = go.Figure()
    figure.update_layout(
        template=None,
        height=height,
        autosize=True,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(
            family="Inter, Segoe UI, system-ui, sans-serif", color=INK_2, size=12
        ),
        margin=dict(l=8, r=18, t=44, b=38),
        title=dict(
            text=title,
            x=0,
            xanchor="left",
            font=dict(size=13, color=INK, family="Inter, Segoe UI, sans-serif"),
        )
        if title
        else None,
        showlegend=showlegend,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            x=0,
            font=dict(size=12, color=MUTED),
            bgcolor="rgba(0,0,0,0)",
        ),
        hoverlabel=dict(
            bgcolor=SURFACE,
            bordercolor=TOKENS["line_strong"],
            font=dict(color=INK, size=12),
        ),
        bargap=0.42,
        transition=dict(duration=0),
    )
    figure.update_xaxes(
        automargin=True,
        gridcolor=LINE,
        zerolinecolor=TOKENS["line_strong"],
        linecolor=LINE,
        tickfont=dict(color=MUTED, size=12),
        title_font=dict(color=MUTED, size=12),
    )
    figure.update_yaxes(
        automargin=True,
        gridcolor=LINE,
        zerolinecolor=TOKENS["line_strong"],
        linecolor=LINE,
        tickfont=dict(color=MUTED, size=12),
        title_font=dict(color=MUTED, size=12),
    )
    return figure


def empty_figure(message: str) -> go.Figure:
    figure = _base(220)
    figure.update_layout(
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        annotations=[
            dict(
                text=message,
                x=0.5,
                y=0.5,
                xref="paper",
                yref="paper",
                showarrow=False,
                font=dict(color=MUTED, size=12),
            )
        ],
    )
    return figure


def distribution_figure(profiles: dict) -> go.Figure:
    selected = charts.selected_profiles(profiles)
    labels = [charts.cluster_name(p["cluster_id"]) for p in selected]
    counts = [p["count"] for p in selected]
    colors = [CLUSTER_COLORS[p["cluster_id"]] for p in selected]
    text = [f"{p['count']:,} · {p['share']:.2%}" for p in selected]
    figure = _base(300, title="Training population by cluster")
    figure.add_bar(
        x=counts,
        y=labels,
        orientation="h",
        marker=dict(color=colors, line=dict(color=TOKENS["surface_1"], width=1)),
        text=text,
        textposition="outside",
        cliponaxis=False,
        textfont=dict(color=INK, size=12),
        hovertemplate=(
            "<b>%{y}</b><br>Training tracks: %{x:,}"
            "<br>Share of population: %{text}<extra></extra>"
        ),
    )
    figure.update_layout(bargap=0.38)
    figure.update_xaxes(title="Training tracks", rangemode="tozero")
    figure.update_yaxes(autorange="reversed", title=None)
    top = max(counts)
    figure.update_xaxes(range=[0, top * 1.32 if top else 1])
    return figure


def contributions_figure(profiles: dict) -> go.Figure:
    contributions = profiles.get("feature_contributions") or {}
    shares = contributions.get("shares") or {}
    between = contributions.get("between_ss") or {}
    if not shares:
        return empty_figure("Separation diagnostic unavailable for this response.")
    ordered = sorted(F9, key=lambda name: shares.get(name, 0), reverse=True)
    values = [shares.get(name, 0) for name in ordered]
    dominant = ordered[0]
    colors = [AMBER if name == dominant else TOKENS["muted"] for name in ordered]
    figure = _base(340, title="Share of between-cluster sum of squares")
    figure.add_bar(
        x=values,
        y=[name.title() for name in ordered],
        orientation="h",
        marker=dict(color=colors, line=dict(color=TOKENS["surface_1"], width=1)),
        text=[f"{value:.2%}" for value in values],
        textposition="auto",
        insidetextanchor="end",
        cliponaxis=False,
        textfont=dict(color=INK, size=12),
        insidetextfont=dict(color="#04110f", size=12),
        customdata=[between.get(name, 0) for name in ordered],
        hovertemplate=(
            "<b>%{y}</b><br>Share: %{x:.3%}"
            "<br>Between-cluster SS: %{customdata:.1f}"
            "<br><i>Fitted RobustScaler space</i><extra></extra>"
        ),
    )
    figure.update_layout(bargap=0.36)
    figure.update_xaxes(
        title="Share of between-cluster SS", range=[0, 1], tickformat=".0%"
    )
    figure.update_yaxes(autorange="reversed", title=None, automargin=True)
    figure.update_xaxes(automargin=True)
    figure.add_annotation(
        text="Training-population separation.<br>Not prediction accuracy.",
        xref="paper",
        yref="paper",
        x=0,
        y=-0.22,
        showarrow=False,
        font=dict(color=MUTED, size=12),
        xanchor="left",
    )
    figure.update_layout(margin=dict(l=8, r=18, t=44, b=58))
    return figure


def comparison_figure(
    profiles: dict,
    feature: str,
    statistic: str,
    selection: str = "Compare Both",
) -> go.Figure:
    if feature not in F9 or statistic not in ("Mean", "Median"):
        raise ValueError("Choose a supported feature and statistic.")
    selected = charts.selected_profiles(profiles, selection)
    labels = [charts.cluster_name(p["cluster_id"]) for p in selected]
    values = [p[statistic.lower()][feature] for p in selected]
    colors = [CLUSTER_COLORS[p["cluster_id"]] for p in selected]
    unit = charts.unit(feature)
    figure = _base(320, title=f"{feature.title()} · {statistic}")
    figure.add_bar(
        x=labels,
        y=values,
        marker=dict(color=colors, line=dict(color=TOKENS["surface_1"], width=1)),
        width=0.48,
        text=[_format_feature(value, feature) for value in values],
        textposition="outside",
        cliponaxis=False,
        textfont=dict(color=INK, size=12),
        customdata=[[p["count"], p["share"]] for p in selected],
        hovertemplate=(
            "<b>%{x}</b><br>"
            + f"{feature.title()}: %{{y}} {unit}"
            + "<br>Training tracks: %{customdata[0]:,}"
            + "<br>Population share: %{customdata[1]:.2%}<extra></extra>"
        ),
    )
    figure.update_yaxes(title=f"{feature.title()} ({unit})")
    if feature in ("tempo", "loudness"):
        low, high = min(0.0, *values), max(0.0, *values)
        pad = max((high - low) * 0.18, 0.05 * max(abs(high), abs(low), 1.0))
        figure.update_yaxes(
            range=[low - (pad if low < 0 else 0), high + pad],
            zeroline=True,
            zerolinecolor=TOKENS["line_strong"],
        )
    else:
        figure.update_yaxes(range=[0, 1])
    figure.update_xaxes(title=None)
    return figure


def distances_figure(prediction: dict) -> go.Figure:
    labels = ["Cluster 0", "Cluster 1"]
    values = list(prediction["distances"])
    nearest = prediction["cluster_id"]
    colors = [
        CLUSTER_COLORS[index] if index == nearest else TOKENS["line_strong"]
        for index in (0, 1)
    ]
    figure = _base(280, title="Distance to each fitted centroid")
    figure.add_bar(
        x=values,
        y=labels,
        orientation="h",
        marker=dict(color=colors, line=dict(color=TOKENS["surface_1"], width=1)),
        text=[f"{value:.4f}" for value in values],
        textposition="outside",
        cliponaxis=False,
        textfont=dict(color=INK, size=12),
        hovertemplate="<b>%{y}</b><br>Euclidean distance: %{x:.4f}<extra></extra>",
    )
    figure.update_layout(bargap=0.4, margin=dict(l=92, r=24, t=44, b=48))
    figure.update_xaxes(
        title="Euclidean distance in transformed F9 space",
        rangemode="tozero",
        automargin=True,
    )
    figure.update_yaxes(autorange="reversed", title=None, automargin=True)
    top = max(values)
    figure.update_xaxes(range=[0, top * 1.22 if top else 1])
    return figure


def research_figure(comparison: dict) -> go.Figure:
    f5 = comparison["comparisons"]["f5_kmeans_vs_deployment_f9_kmeans"]
    gmm = comparison["comparisons"]["f9_kmeans_vs_f9_gmm"]
    labels = [
        "F5 K-Means vs deployed F9 K-Means",
        "F9 K-Means vs F9 GMM hard partition",
    ]
    values = [f5["ari"], gmm["ari"]]
    figure = _base(280, title="Partition agreement (Adjusted Rand Index)")
    figure.add_bar(
        x=values,
        y=labels,
        orientation="h",
        marker=dict(
            color=[TOKENS["line_strong"], AMBER],
            line=dict(color=TOKENS["surface_1"], width=1),
        ),
        text=[f"{value:+.3f}" for value in values],
        textposition="outside",
        cliponaxis=False,
        textfont=dict(color=INK, size=12),
        hovertemplate="<b>%{y}</b><br>ARI: %{x:+.4f}<extra></extra>",
    )
    figure.update_layout(bargap=0.42, margin=dict(l=8, r=30, t=44, b=58))
    figure.update_xaxes(
        title="Adjusted Rand Index (agreement, not quality)", range=[-1.05, 1.05]
    )
    figure.update_yaxes(autorange="reversed", title=None, automargin=True)
    figure.update_xaxes(automargin=True)
    figure.add_annotation(
        text="Identical rows; ARI measures partition agreement, not model quality.",
        xref="paper",
        yref="paper",
        x=0,
        y=-0.24,
        showarrow=False,
        font=dict(color=MUTED, size=12),
        xanchor="left",
    )
    return figure


def _format_feature(value: float, feature: str) -> str:
    return f"{value:.1f}" if feature in ("tempo", "loudness") else f"{value:.4f}"
