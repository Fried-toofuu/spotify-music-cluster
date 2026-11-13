# ruff: noqa: E501  (embedded HTML)
"""Presentation and event logic, independently testable without a Gradio server."""

import html

import gradio as gr
import pandas as pd

from spotify_cluster.config import DATASET_LICENSE, F9

from . import charts, figures
from .api_client import APIError, number

EMPTY = "Refresh live data to load verified aggregates from the API."
CAVEAT = (
    "Clusters describe acoustic similarity; they are not verified music genres or "
    "mood labels. Centroid distances are not probabilities."
)
DISTANCE_NOTE = (
    "Smaller means closer to that centroid. Euclidean distances in fitted "
    "RobustScaler-transformed F9 space; distances are not probabilities."
)
AUDIO_NOTE = (
    "This form reads nine numerical acoustic descriptors. It does not accept MP3 "
    "files, audio uploads or Spotify URLs."
)
REPO = "https://github.com/Fried-toofuu/spotify-music-cluster"
DOC_LINKS = {
    "methodology": f"{REPO}/blob/main/docs/NOTEBOOK_AUDIT.md",
    "architecture": f"{REPO}/blob/main/docs/ARCHITECTURE.md",
    "model": f"{REPO}/blob/main/docs/MODEL_SERVING.md",
    "visualization": f"{REPO}/blob/main/docs/VISUALIZATION.md",
}
CLEARED_PREDICTION_STATUS = "Submit features to request a real API prediction."
DATASET_URL = DATASET_LICENSE["url"]
SYNTHETIC_EXAMPLE = [0.72, 0.61, 0.38, 0.44, 118.5, -9.2, 0.05, 0.81, 0.13]
HELP = {
    "acousticness": "Estimated acoustic character of the recording.",
    "danceability": "Rhythm-based suitability for dancing.",
    "energy": "Perceptual intensity and activity descriptor.",
    "valence": "Musical positiveness descriptor; not a verified mood label.",
    "tempo": "Estimated tempo in beats per minute; zero is allowed.",
    "loudness": "Overall loudness in decibels; any finite value is accepted.",
    "speechiness": "Presence of spoken words.",
    "instrumentalness": "Estimated absence of vocals; not a binary vocal detector.",
    "liveness": "Estimated presence of an audience in the recording.",
}
BRAND_MARK = """
<svg class="obs-brand-mark" viewBox="0 0 40 40" role="img" aria-label="Acoustic Observatory mark">
  <circle cx="20" cy="20" r="15.5" fill="none" stroke="var(--obs-teal)"/>
  <circle cx="20" cy="20" r="8.5" fill="none" stroke="var(--obs-violet)"/>
  <circle cx="20" cy="20" r="2.6" fill="var(--obs-teal)"/>
  <circle cx="33.5" cy="12" r="1.8" fill="var(--obs-amber)"/>
</svg>
"""
HERO = """
<div class="obs-hero">
  <span class="obs-kicker">An instrument for acoustic discovery</span>
  <h1>Music, mapped by sound.</h1>
  <p>Explore 89,741 canonical Spotify tracks by acoustic similarity.
  Inspect a sample or test nine descriptors.</p>
  <div class="obs-hero-meta">
    <span class="obs-note obs-mono">F9 · RobustScaler · K-Means / K2</span>
  </div>
</div>
"""


def e(value):
    return html.escape(str(value), quote=True)


def count(value):
    return f"{int(value):,}"


def pct(value):
    return f"{value:.2%}"


def feature_value(value, feature):
    return f"{value:,.1f}" if feature in ("tempo", "loudness") else f"{value:.4f}"


def brandbar_html(*, ready=False, warning=False):
    return f"""
<div class="obs-brandbar">
  <div class="obs-brand">{BRAND_MARK}
    <div>
      <div class="obs-brand-name">Acoustic Observatory</div>
      <div class="obs-brand-sub">Spotify Music Clustering</div>
    </div>
  </div>
</div>
"""


def footer_html(model=None):
    identity = ""
    if model:
        identity = (
            f"<span>Model <code>{e(model['model_id'])}</code> · "
            "Historical equivalence <strong>NOT VERIFIED</strong></span>"
        )
    return f"""
<div class="obs-provenance">
  <span>Dataset: <a href="{e(DATASET_URL)}" target="_blank" rel="noopener noreferrer">
  Spotify Tracks Dataset (Maharshi Pandya)</a> · ODbL 1.0 · no track identifiers
  distributed with the visualization sample.</span>
  {identity}
  <span><a href="{e(DOC_LINKS["methodology"])}" target="_blank" rel="noopener noreferrer">
  Methodology</a> · <a href="{e(DOC_LINKS["visualization"])}" target="_blank"
  rel="noopener noreferrer">Visualization pipeline</a></span>
</div>
"""


def status_html(ready, message, warnings=None):
    warnings = warnings or []
    klass = "obs-live" if ready else "obs-live offline"
    loading = not ready and message.startswith("Loading")
    label = "Connecting" if loading else "API ready" if ready else "API unavailable"
    if loading:
        klass = "obs-live connecting"
    extra = ""
    if warnings:
        extra = (
            '<div class="obs-note" style="margin-top:8px">Partial data: '
            + " ".join(e(item) for item in warnings)
            + "</div>"
        )
    return (
        f'<div class="obs-api-status" role="status" aria-live="polite">'
        f'<span class="{klass}" title="{e(message)}">{label}</span>'
        + (
            f'<span class="obs-note">{e(message)} The service may be waking up; '
            "try Refresh live data shortly.</span>"
            if not ready
            else ""
        )
        + f"{extra}</div>"
    )


def summary(model):
    """Compact metric strip retained for compatibility with older callers."""
    metrics = [
        (count(model["training_sample_count"]), "Training tracks"),
        (str(model["number_of_clusters"]), "Acoustic clusters"),
        (model["algorithm"], "Algorithm"),
        (f"F{len(model['features'])}", "Representation"),
        (model["scaler"], "Preprocessing"),
    ]
    return (
        '<div class="metrics">'
        + "".join(
            f'<div class="metric"><strong>{e(value)}</strong>'
            f"<span>{e(label)}</span></div>"
            for value, label in metrics
        )
        + "</div>"
    )


def insight(profiles):
    feature, share = charts.largest_contribution(profiles)
    if feature is None:
        return "### Separation diagnostic\nNot available from this API response."
    return (
        f"### {pct(share)} · {feature.title()}\n"
        "Share of between-cluster sum of squares in fitted RobustScaler space. "
        "This measures internal separation in the training population, "
        "not prediction accuracy."
    )


def interpretation(data, selection):
    profiles = charts.selected_profiles(data, selection)
    lines = [
        f"**Cluster {p['cluster_id']}** · {count(p['count'])} tracks · "
        f"{pct(p['share'])} of training population · "
        f"mean instrumentalness {p['mean']['instrumentalness']:.4f}."
        for p in profiles
    ]
    selected = charts.selected_profiles(data)
    a, b = selected
    if a["mean"]["instrumentalness"] != b["mean"]["instrumentalness"]:
        high, low = sorted(
            (a, b), key=lambda p: p["mean"]["instrumentalness"], reverse=True
        )
        lines.append(
            f"In this model, Cluster {high['cluster_id']} has higher mean "
            f"instrumentalness than Cluster {low['cluster_id']}. "
            "Label meanings belong to this fitted artifact "
            "and can change after a refit."
        )
    return "\n\n".join(lines)


def fact_sheet_html(model, profiles, viz_meta=None):
    shares = [profiles["clusters"][str(i)]["share"] for i in (0, 1)]
    counts = [profiles["clusters"][str(i)]["count"] for i in (0, 1)]
    viz = "Not provisioned"
    if viz_meta and viz_meta.get("available"):
        if viz_meta.get("artifact_mode") == "points":
            size = (viz_meta.get("sample") or {}).get("size", 0)
            viz = f"PCA points · {count(size)} sampled tracks"
        else:
            viz = "Aggregate density only"
    rows = [
        ("Training population", f"{count(model['training_sample_count'])} tracks"),
        ("Clusters", f"{model['number_of_clusters']} acoustic groups"),
        ("Representation", f"F{len(model['features'])} · no modeling PCA"),
        ("Preprocessing", "RobustScaler · median / IQR"),
        ("Algorithm", "K-Means · K = 2"),
        ("Deployment profile", e(model.get("deployment_profile", "not recorded"))),
        ("Historical equivalence", "NOT VERIFIED"),
        ("Visualization", e(viz)),
    ]
    body = "".join(
        f"<div class='obs-fact'><dt>{e(a)}</dt><dd>{b}</dd></div>" for a, b in rows
    )
    return f"""
<div class="obs-card">
  <span class="obs-kicker">Model fact sheet</span>
  <h3>One fitted acoustic partition</h3>
  <dl class="obs-facts">{body}</dl>
  <p class="obs-footnote">Cluster 0 holds {count(counts[0])} tracks ({pct(shares[0])});
  Cluster 1 holds {count(counts[1])} tracks ({pct(shares[1])}). Labels are arbitrary
  fitted groups, not genres.</p>
</div>
"""


def finding_html(profiles):
    feature, share = charts.largest_contribution(profiles)
    if feature is None:
        return (
            '<div class="obs-card obs-finding"><span class="obs-kicker">Finding</span>'
            '<p class="obs-muted">Separation diagnostics unavailable.</p></div>'
        )
    p0 = profiles["clusters"]["0"]["mean"][feature]
    p1 = profiles["clusters"]["1"]["mean"][feature]
    higher = 0 if p0 >= p1 else 1
    label = (
        "instrumental versus less-instrumental"
        if feature == "instrumentalness"
        else "strongly separated along this feature"
    )
    return f"""
<div class="obs-card obs-finding">
  <span class="obs-kicker">Dominant signal</span>
  <div class="obs-big">{pct(share)} <small>of between-cluster SS</small></div>
  <h3>{e(feature.title())}</h3>
  <p class="obs-bar"><span style="width:{min(100, max(0, share * 100)):.1f}%"></span></p>
  <p>The deployed partition is largely <strong>{e(label)}</strong>. Cluster
  {higher} has the higher raw mean ({feature_value(max(p0, p1), feature)} vs
  {feature_value(min(p0, p1), feature)}).</p>
  <p class="obs-footnote">Between-cluster sum of squares in fitted RobustScaler
  space. This is internal training-population separation, <strong>not prediction accuracy</strong>. Instrumentalness dominates because its interquartile range is
  small, so RobustScaler amplifies that dimension.</p>
</div>
"""


def population_html(profiles):
    p0 = profiles["clusters"]["0"]
    p1 = profiles["clusters"]["1"]
    return f"""
<div class="obs-card">
  <span class="obs-kicker">Population balance</span>
  <h3>Two acoustic groups</h3>
  <div class="obs-split" role="img" aria-label="Cluster 0 {pct(p0["share"])}; Cluster 1 {pct(p1["share"])}">
    <span class="c0" style="width:{p0["share"] * 100:.2f}%"></span>
    <span class="c1" style="width:{p1["share"] * 100:.2f}%"></span>
  </div>
  <p><span class="obs-badge c0"><span class="swatch"></span>Cluster 0</span>
  {count(p0["count"])} tracks · {pct(p0["share"])}</p>
  <p><span class="obs-badge c1"><span class="swatch"></span>Cluster 1</span>
  {count(p1["count"])} tracks · {pct(p1["share"])}</p>
  <p class="obs-footnote">Stable cluster colors are used across every view.
  Stratified Explorer samples do not preserve these proportions.</p>
</div>
"""


def identity_html(model):
    return f"""
<div class="obs-card tight">
  <span class="obs-kicker">Identity</span>
  <p class="obs-mono" style="margin:6px 0 8px;overflow-wrap:anywhere">{e(model["model_id"])}</p>
  <p class="obs-footnote">Deployment profile <code>{e(model.get("deployment_profile"))}</code>
  · origin {e(model.get("model_origin"))} · no modeling PCA. This is a separately
  approved deployment refit, not the historical final estimator. Historical
  equivalence is <strong>NOT VERIFIED</strong>.</p>
</div>
"""


def overview_note_html(viz_meta):
    if not viz_meta or not viz_meta.get("available"):
        reason = (viz_meta or {}).get(
            "reason", "Visualization artifact not provisioned"
        )
        return (
            '<div class="obs-card tight"><span class="obs-kicker">Visualization</span>'
            f'<p class="obs-muted" style="margin:6px 0 0">{e(reason)}. '
            "The profile tables and research sections remain available.</p></div>"
        )
    if viz_meta.get("artifact_mode") == "points":
        return (
            '<div class="obs-card tight"><span class="obs-kicker">Visualization</span>'
            '<p class="obs-muted" style="margin:6px 0 0">Preview plots every fourth '
            "point of the verified sample. Open the Cluster Explorer for all points, "
            "nearest-neighbor inspection in fitted scaled F9 space and exact tables.</p></div>"
        )
    return (
        '<div class="obs-card tight"><span class="obs-kicker">Visualization</span>'
        '<p class="obs-muted" style="margin:6px 0 0">This deployment serves aggregate '
        "density only: individual coordinates are not distributed. No aggregate cell "
        "represents a single track.</p></div>"
    )


def explorer_disclosure_html(viz_meta):
    if not viz_meta:
        return EMPTY
    if not viz_meta.get("available"):
        return e(viz_meta.get("reason", "Visualization unavailable."))
    if viz_meta.get("artifact_mode") == "points":
        sample = viz_meta.get("sample") or {}
        counts = sample.get("cluster_counts") or [0, 0]
        return (
            f"<strong>Plotted sample:</strong> {count(sample.get('size', 0))} tracks "
            f"({count(counts[0])} / {count(counts[1])}); equal-cap stratified sample, "
            "so plotted proportions are not population proportions. PCA is fitted on "
            "the full training population for visualization only; assignments come from "
            "the deployed F9 model. Sample points carry no track identifiers. "
            "Coordinates are not model training coordinates."
        )
    return (
        "Aggregate density only. Individual coordinates are not distributed; cells "
        "contain at least the configured minimum number of training tracks and are "
        "never labeled as individual tracks."
    )


def preview_payload(points_response, stride=4):
    """A smaller, explicitly labeled preview of the same verified sample."""
    if not points_response or points_response.get("view") != "points":
        return points_response
    source = points_response["points"]
    points = {
        key: list(source[key])[::stride]
        for key in ("x", "y", "z", "cluster", "raw_features")
    }
    sample = dict(points_response["sample"])
    sample["size"] = len(points["x"])
    sample["cluster_counts"] = [
        points["cluster"].count(0),
        points["cluster"].count(1),
    ]
    sample["policy"] = (
        f"Overview preview: every {stride}th point of the verified stratified sample"
    )
    sample["proportions_disclosure"] = (
        "Preview plotted proportions are not population proportions"
    )
    result = dict(points_response)
    result["points"] = points
    result["sample"] = sample
    return result


def _meter_rows(distances, nearest):
    top = max(distances) or 1
    rows = []
    for label, value in enumerate(distances):
        width = max(2.0, 100 * value / top)
        klass = f"c{label}"
        rows.append(
            f'<div class="obs-meter-row"><span>{e(charts.cluster_name(label))}</span>'
            f'<span class="track {klass}"><span style="width:{width:.1f}%"></span></span>'
            f'<span class="value">{value:.4f}<small>'
            f"{'nearest' if label == nearest else 'distance'}</small></span></div>"
        )
    return "".join(rows)


def _distinguishing(profiles):
    if not profiles:
        return []
    a, b = profiles["clusters"]["0"], profiles["clusters"]["1"]
    ranked = []
    for feature in F9:
        left, right = a["mean"][feature], b["mean"][feature]
        scale = max(abs(left), abs(right), 1e-9)
        ranked.append((abs(left - right) / scale, feature, left, right))
    ranked.sort(reverse=True)
    return ranked[:2]


def prediction_card_html(result, profiles=None, submitted=None):
    label = result["cluster_id"]
    profile = result["profile"]
    other = None
    if profiles and str(1 - label) in profiles.get("clusters", {}):
        other = profiles["clusters"][str(1 - label)]
    meters = _meter_rows(result["distances"], label)
    submitted_block = ""
    if submitted:
        items = "".join(
            f"<div class='obs-feature'><dt>{e(name)}</dt>"
            f"<dd>{feature_value(submitted[name], name)}</dd></div>"
            for name in F9
        )
        submitted_block = f"""
  <details class="obs-footnote" style="margin-top:10px">
    <summary>Submitted F9 vector (the values this card describes)</summary>
    <dl class="obs-feature-grid">{items}</dl>
  </details>"""
    comparisons = ""
    if other:
        parts = []
        for _score, feature, _left, _right in _distinguishing(profiles):
            current_value = profile["mean"][feature]
            other_value = other["mean"][feature]
            direction = "higher" if current_value > other_value else "lower"
            parts.append(
                f"mean {e(feature)} "
                f"{feature_value(current_value, feature)} vs "
                f"{feature_value(other_value, feature)} in Cluster {1 - label} "
                f"({direction})"
            )
        comparisons = (
            '<p class="obs-footnote">Current cluster profile: '
            + "; ".join(parts)
            + ". These are raw-unit training aggregates, not a musical genre.</p>"
        )
    return f"""
<div class="obs-card obs-prediction c{label}">
  <div class="obs-result-head">
    <div>
      <span class="obs-kicker">Nearest centroid</span>
      <h2>Cluster {label}</h2>
      <div class="obs-result-meta">{count(profile["count"])} training tracks ·
      {pct(profile["share"])} of the training population</div>
    </div>
    <span class="obs-verdict">Nearest wins · not a probability</span>
  </div>
  <div class="obs-meter">{meters}</div>
  <p class="obs-footnote">The smaller Euclidean distance determines the assignment.
  Distances are not confidence scores and are not converted to probabilities.</p>
  {comparisons}
  {submitted_block}
  <details class="obs-footnote" style="margin-top:10px">
    <summary>Model identity and scientific limits</summary>
    <p class="obs-mono" style="overflow-wrap:anywhere">{e(result["model_id"])}</p>
    <p>Deployment profile {e(result.get("deployment_profile"))} · historical
    equivalence <strong>NOT VERIFIED</strong>. The historical Holdout remains closed;
    no deployment Holdout score is claimed.</p>
    <p>{e(result["limitation"])}</p>
  </details>
</div>
"""


def prediction_empty_html():
    return (
        '<div class="obs-card"><span class="obs-kicker">Result</span>'
        "<h3>Awaiting a feature vector</h3>"
        '<p class="obs-muted">Enter nine acoustic descriptors and submit. The server '
        "performs scaling and inference; the browser never assigns the cluster.</p></div>"
    )


def cleared_prediction_outputs():
    return (
        CLEARED_PREDICTION_STATUS,
        prediction_empty_html(),
        figures.empty_figure("Submit a feature vector to see distances."),
        pd.DataFrame(columns=["Cluster", "Distance"]),
    )


def error_card_html(message, *, sample_index=None):
    attributes = (
        f'class="obs-card obs-selection-error" data-sample="{e(sample_index)}"'
        if sample_index is not None
        else 'class="obs-card"'
    )
    return (
        f'<div {attributes} data-tone="error"><span class="obs-kicker">Could not complete</span>'
        f'<p class="obs-muted" style="margin:6px 0 0">{e(message)}</p></div>'
    )


def selection_html(result):
    point = result["point"]
    feature_items = "".join(
        f"<div class='obs-feature'><dt>{e(name)}</dt>"
        f"<dd>{feature_value(value, name)}</dd></div>"
        for name, value in point["features"].items()
    )
    rows = "".join(
        f"<tr><td data-label='Sample'>#{entry['index']}</td>"
        f"<td data-label='Cluster'><span class='obs-badge c{entry['cluster']}'>"
        f"<span class='swatch'></span>Cluster {entry['cluster']}</span></td>"
        f"<td data-label='Instrumentalness'>{feature_value(entry['features']['instrumentalness'], 'instrumentalness')}</td>"
        f"<td data-label='Energy'>{feature_value(entry['features']['energy'], 'energy')}</td>"
        f"<td data-label='Distance'>{entry['distance']:.4f}</td></tr>"
        for entry in result["neighbors"]
    )
    coordinates = ", ".join(f"{value:+.2f}" for value in point["coordinates"])
    return f"""
<div class="obs-card obs-selected-track" data-sample="{point["index"]}">
  <span class="obs-kicker">Selected sample</span>
  <h3>Sample #{point["index"]} · Cluster {point["cluster"]}</h3>
  <p class="obs-footnote">PCA coordinates ({coordinates}) are visualization
  coordinates, not model training distances. No track identifiers are stored.</p>
  <dl class="obs-feature-grid">{feature_items}</dl>
  <h4 style="margin:14px 0 4px">Nearest sampled tracks</h4>
  <p class="obs-footnote" style="margin:0 0 8px">Computed in the fitted
  RobustScaler F9 space, not screen distance. Distances are not probabilities.</p>
  <table class="obs-neighbors">
    <thead><tr><th>Sample</th><th>Cluster</th><th>Instr.</th><th>Energy</th><th>Distance</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
</div>
"""


def selection_placeholder_html(viz_meta=None):
    if (
        viz_meta
        and viz_meta.get("available")
        and viz_meta.get("artifact_mode") == "aggregate"
    ):
        return (
            '<div class="obs-card obs-guide"><span class="obs-kicker">Explorer Guide</span>'
            "<h3>Read population density</h3><p>Each cell summarizes training tracks. "
            "Color encodes track count on a logarithmic scale. Hover a cell for its "
            'count, Cluster 1 share and mean instrumentalness.</p><p class="obs-footnote">'
            "Aggregate mode does not expose individual points. Compare raw-unit "
            "profiles below; sample proportions never stand for population proportions.</p></div>"
        )
    return (
        '<div class="obs-card obs-guide"><span class="obs-kicker">Explorer Guide</span>'
        "<h3>Pick a sample, follow the sound</h3>"
        "<p>Select a point to open the Sample inspector: nine raw descriptors and "
        "nearest sampled tracks in fitted RobustScaler F9 space.</p>"
        "<p>Use Both to compare clusters, or isolate Cluster 0 or Cluster 1. "
        "Drag to pan in 2D or orbit in 3D. Reset view restores the camera.</p>"
        '<p class="obs-footnote">PCA is visualization only. Sample numbers are local '
        "indices, never Spotify track IDs. The stratified sample does not show "
        "natural population proportions.</p></div>"
    )


def research_narrative_html(research, profiles, viz_meta=None):
    feature, share = charts.largest_contribution(profiles)
    p0 = profiles["clusters"]["0"]["mean"]
    p1 = profiles["clusters"]["1"]["mean"]
    if feature is None or share is None:
        dominant_block = """
<div class="obs-card obs-section">
  <span class="obs-kicker">03 · Dominant finding</span>
  <h3>Separation diagnostic unavailable</h3>
  <p class="obs-muted">The current API response does not include between-cluster
  feature contributions. The F9 profiles and archived research evidence remain
  available; no percentage or dominant feature is fabricated.</p>
</div>
"""
    else:
        driver_note = (
            "Because instrumentalness has a small interquartile range, RobustScaler "
            "amplifies it, so the partition is largely an instrumental versus "
            "less-instrumental split."
            if feature == "instrumentalness"
            else f"The partition is strongly separated along {feature}."
        )
        dominant_block = f"""
<div class="obs-card obs-section">
  <span class="obs-kicker">03 · Dominant finding</span>
  <h3>{e(feature.title())} drives {share:.2%} of the between-cluster separation</h3>
  <p>Cluster 0's raw mean is {feature_value(p0[feature], feature)}; Cluster 1's is
  {feature_value(p1[feature], feature)}. {driver_note} The archived research
  reported high seed stability for this selected configuration; this application
  does not recompute that diagnostic. The artifact's separation is dominated by
  this feature. It is not a genre classifier and its separation diagnostic is
  not accuracy.</p>
  <p class="obs-footnote">Share of between-cluster sum of squares in fitted
  RobustScaler space, computed from this artifact's training assignments.</p>
</div>
"""
    if research and research.get("available"):
        f5 = research["comparisons"]["f5_kmeans_vs_deployment_f9_kmeans"]
        gmm = research["comparisons"]["f9_kmeans_vs_f9_gmm"]
        comparison = f"""
<div class="obs-grid-2 obs-section">
  <div class="obs-card">
    <span class="obs-kicker">Controlled comparison · identical rows</span>
    <h3>F5 StandardScaler vs deployed F9 RobustScaler</h3>
    <div class="obs-big" style="color:var(--obs-teal)">{f5["ari"]:+.3f} <small>Adjusted Rand Index</small></div>
    <p>The F5 K-Means partition and the deployed F9 K-Means partition agree at
    ARI {f5["ari"]:+.3f} on all {count(research["population"]["training_sample_count"])}
    identical tracks. ARI measures partition agreement, not quality, and no
    Silhouette values are compared across different feature geometries.</p>
    <p class="obs-footnote">F5 recipe: StandardScaler + K-Means (k-means++, n_init=20,
    max_iter=300, seed 42). This is a new development computation, not a claim to
    reproduce the archived historical F5 baseline.</p>
  </div>
  <div class="obs-card">
    <span class="obs-kicker">Hard vs soft assignments</span>
    <h3>K-Means vs a Gaussian mixture</h3>
    <div class="obs-big" style="color:var(--obs-violet)">{gmm["ari"]:+.3f} <small>ARI between hard partitions</small></div>
    <p>On the identical fitted RobustScaler F9 representation, a diagonal-covariance
    GMM reaches mean maximum responsibility
    {gmm["mean_max_responsibility"]:.3f} and mean entropy
    {gmm["mean_entropy_nats"]:.3f} nats. Responsibilities are posterior component
    weights; the hard GMM partition uses argmax. K-Means instead minimizes squared
    centroid distance.</p>
    <p class="obs-footnote">Low agreement is an informative result: the two models
    answer different questions. Neither is selected by this comparison.</p>
  </div>
</div>
"""
    else:
        reason = (research or {}).get(
            "reason", "Research comparison artifact not provisioned"
        )
        comparison = f"""
<div class="obs-card obs-section"><span class="obs-kicker">Controlled comparison</span>
<h3>Comparison artifact unavailable</h3>
<p class="obs-muted">{e(reason)}. The deployment evidence above remains available;
no comparison metric is fabricated.</p></div>
"""
    archived = (research or {}).get("archived_evidence")
    if archived:
        archived_block = f"""
<p class="obs-footnote">Archived historical metrics are available in the
Supporting figures and exact archived evidence section below. They remain one-time,
closed evidence of the historical estimator.</p>
<p class="obs-footnote" style="margin-top:8px">{e(archived["warning"])}</p>
"""
    else:
        archived_block = (
            '<p class="obs-muted">Archived historical evidence is not available from '
            "this backend. The Holdout remains closed; no value is invented.</p>"
        )
    return f"""
<div id="research-overview">
<span class="obs-kicker">Research &amp; methodology</span>
<h2>What this partition can — and cannot — say</h2>
<p>This is an <strong>unsupervised</strong> study. No genre label is used as a
target, so there is no accuracy score to report. The model groups numerical
acoustic descriptors by similarity; the meaning of a cluster comes from the
current artifact's raw-unit profiles, not from its numeric label.</p>


<h2>Research Findings</h2>
{dominant_block}
<details class="obs-research-layer" open>
  <summary>Model Comparison</summary>
  {comparison}
</details>
<details class="obs-research-layer">
  <summary>Methodology and Reproducibility</summary>
<div class="obs-grid-2 obs-section">
  <div class="obs-card">
    <span class="obs-kicker">01 · Data</span>
    <h3>One authorized snapshot</h3>
    <p>The Kaggle Spotify Tracks Dataset (Maharshi Pandya) supplies 114,000 raw
    rows. Track-ID deduplication leaves <strong>89,741 canonical tracks</strong>
    across 114 reported genres. Genre and text metadata are kept out of the F9
    modeling matrix. The CSV is verified by SHA-256 before any offline artifact
    is prepared; the raw file is never served by this application.</p>
    <p class="obs-footnote">Dataset license: ODbL 1.0. Track-level derived
    coordinates remain private by default; a public deployment uses the
    aggregate-only artifact unless redistribution is explicitly approved.</p>
  </div>
  <div class="obs-card">
    <span class="obs-kicker">02 · Representation</span>
    <h3>F9, scaled, without PCA</h3>
    <p><code>acousticness, danceability, energy, valence, tempo, loudness,
    speechiness, instrumentalness, liveness</code> in that exact order. RobustScaler
    centers each feature at its median and scales by its interquartile range. The
    fitted scaler and K-Means centroids remain paired in one Pipeline; PCA is
    visualisation only and is never used to fit or assign clusters.</p>
    <p class="obs-footnote">The historical notebook also studied an F5 baseline,
    StandardScaler, PCA projections and GMM candidates.</p>
  </div>
</div>

<div class="obs-card obs-section">
  <span class="obs-kicker">04 · Historical evidence vs deployed model</span>
  <h3>Two identities, never one score</h3>
  <p>The archived FULL research evidence below belongs to the <em>historical</em>
  frozen F9/Robust/K2 estimator and its one-time Holdout. The deployed model is a
  separately approved refit on all canonical tracks. It is <strong>not verified
  equivalent</strong> to the historical estimator, and the historical Holdout is
  closed: it was not reopened, rerun or extended for this application.</p>
  {archived_block}
  <p class="obs-footnote" style="margin-top:10px">Deployment-v1 training
  population: {count(profiles["clusters"]["0"]["count"] + profiles["clusters"]["1"]["count"])}
  tracks, cluster counts {count(profiles["clusters"]["0"]["count"])} /
  {count(profiles["clusters"]["1"]["count"])}. A full-population refit has no fresh
  independent Holdout score.</p>
</div>


<div class="obs-card obs-section">
  <span class="obs-kicker">05 · Limits and reproducibility</span>
  <h3>What not to conclude</h3>
  <ul>
    <li>Cluster IDs are arbitrary and can swap after a refit; use the current
    profiles to interpret them.</li>
    <li>Descriptions are acoustic, not perceptual or cultural; no listening study
    established validity.</li>
    <li>Centroid distances are Euclidean distances in fitted scaled space, not
    probabilities or confidence scores.</li>
    <li>Track-disjoint cohorts are not artist-disjoint; the training population is
    not an independent evaluation.</li>
    <li>The archived historical metrics cannot be attached to deployment
    predictions. Historical equivalence remains <strong>NOT VERIFIED</strong>.</li>
  </ul>
  <p class="obs-footnote">Methodology:
  <a href="{e(DOC_LINKS["methodology"])}" target="_blank" rel="noopener noreferrer">Notebook audit</a>
  · <a href="{e(DOC_LINKS["architecture"])}" target="_blank" rel="noopener noreferrer">Architecture</a>
  · <a href="{e(DOC_LINKS["model"])}" target="_blank" rel="noopener noreferrer">Model serving</a>
  · <a href="{e(DOC_LINKS["visualization"])}" target="_blank" rel="noopener noreferrer">Visualization pipeline</a>.</p>
</div>
</details>
</div>
"""


def archived_table(research):
    if not research or not research.get("available"):
        return pd.DataFrame(columns=["Evidence", "Metric", "Value", "Status"])
    archived = research["archived_evidence"]
    return pd.DataFrame(
        [
            {
                "Evidence": archived["label"],
                "Metric": "Holdout Silhouette",
                "Value": archived["holdout_silhouette"],
                "Status": "Archived · one-time · closed",
            },
            {
                "Evidence": archived["label"],
                "Metric": "Holdout Davies–Bouldin",
                "Value": archived["holdout_davies_bouldin"],
                "Status": "Archived · one-time · closed",
            },
            {
                "Evidence": archived["label"],
                "Metric": "Holdout Calinski–Harabasz",
                "Value": archived["holdout_calinski_harabasz"],
                "Status": "Archived · one-time · closed",
            },
        ]
    )


def payload(values):
    if len(values) != len(F9):
        raise ValueError("Enter all nine acoustic features.")
    result = {}
    for feature, value in zip(F9, values, strict=True):
        if not number(value):
            raise ValueError(f"{feature.title()} must be a finite number.")
        if feature == "tempo" and value < 0:
            raise ValueError("Tempo must be zero or greater (BPM).")
        if feature not in ("tempo", "loudness") and not 0 <= value <= 1:
            raise ValueError(f"{feature.title()} must be between 0 and 1.")
        result[feature] = float(value)
    return result


class Handlers:
    def __init__(self, client):
        self.client = client

    def refresh(self):
        try:
            self.client.health()
            model = self.client.model()
            profiles = self.client.clusters()
            if model["model_id"] != profiles["model_id"] or model[
                "training_sample_count"
            ] != sum(p["count"] for p in profiles["clusters"].values()):
                raise APIError(
                    "API model and profiles disagree. Refresh after backend restart."
                )
        except APIError as exc:
            return self._offline(str(exc))
        warnings = []
        viz_meta = None
        viz_points = None
        viz_density = None
        try:
            viz_meta = self.client.visualization_meta()
            if viz_meta.get("available") is False:
                warnings.append(viz_meta["reason"])
            else:
                if viz_meta["model_id"] != model["model_id"]:
                    raise APIError(
                        "Visualization belongs to another model. Refresh after restart."
                    )
                if viz_meta["views"]["points"]:
                    viz_points = self.client.visualization_points()
                    if viz_points["model_id"] != model["model_id"]:
                        raise APIError("Visualization model identity mismatch.")
                else:
                    viz_density = self.client.visualization_occupancy()
                    if viz_density["model_id"] != model["model_id"]:
                        raise APIError("Visualization model identity mismatch.")
        except APIError as exc:
            viz_meta = {"available": False, "reason": str(exc)}
            viz_points = None
            viz_density = None
            warnings.append(str(exc))
        try:
            research = self.client.research()
            if research.get("available") and research["model_id"] != model["model_id"]:
                research = {
                    "available": False,
                    "reason": "Research comparison belongs to another model.",
                }
        except APIError as exc:
            research = {"available": False, "reason": str(exc)}
        data = {
            "model": model,
            "profiles": profiles,
            "viz_meta": viz_meta,
            "viz_points": viz_points,
            "viz_density": viz_density,
            "research": research,
        }
        overview = preview_payload(viz_points) if viz_points else viz_density
        explorer = viz_points or viz_density
        handoff = "Live verified aggregates loaded."
        if warnings:
            handoff += " Optional visualization data is partially unavailable."
        comparison_figure = (
            figures.research_figure(research)
            if research.get("available")
            else figures.empty_figure("Research comparison artifact not provisioned.")
        )
        return (
            data,
            brandbar_html(ready=True, warning=bool(warnings)),
            status_html(True, handoff, warnings),
            overview,
            overview_note_html(viz_meta),
            fact_sheet_html(model, profiles, viz_meta),
            finding_html(profiles),
            population_html(profiles),
            identity_html(model),
            explorer_disclosure_html(viz_meta),
            explorer,
            selection_placeholder_html(viz_meta),
            research_narrative_html(research, profiles, viz_meta),
            figures.contributions_figure(profiles),
            comparison_figure,
            archived_table(research),
            *cleared_prediction_outputs(),
        )

    def _offline(self, message):
        return (
            None,
            brandbar_html(ready=False),
            status_html(False, message),
            None,
            '<div class="obs-card tight"><span class="obs-kicker">Visualization</span>'
            '<p class="obs-muted" style="margin:6px 0 0">Start the FastAPI backend and '
            "refresh to load verified aggregates.</p></div>",
            '<div class="obs-card"><span class="obs-kicker">Model fact sheet</span>'
            f'<p class="obs-muted">{e(message)}</p></div>',
            '<div class="obs-card obs-finding"><span class="obs-kicker">Finding</span>'
            '<p class="obs-muted">Live separation diagnostics are unavailable.</p></div>',
            '<div class="obs-card"><span class="obs-kicker">Population</span>'
            '<p class="obs-muted">Live cluster shares are unavailable.</p></div>',
            "",
            EMPTY,
            None,
            selection_placeholder_html(None),
            '<div class="obs-card"><span class="obs-kicker">Research</span>'
            '<h3>Research evidence unavailable</h3><p class="obs-muted">Start the '
            "FastAPI backend and refresh. No comparison, archived metric or cluster "
            "statistic is substituted while the backend is offline.</p></div>",
            figures.empty_figure("Backend offline."),
            figures.empty_figure("Backend offline."),
            archived_table(None),
            *cleared_prediction_outputs(),
        )

    def explore(self, data, selection, feature, statistic):
        if not data:
            return EMPTY, figures.empty_figure("Refresh live data first."), None, None
        profiles = data["profiles"]
        return (
            interpretation(profiles, selection),
            figures.comparison_figure(profiles, feature, statistic, selection),
            charts.profile_table(profiles, statistic, selection),
            charts.detail_table(profiles, selection),
        )

    def load_explorer(self, data):
        if not data:
            return None, EMPTY, selection_placeholder_html(None)
        viz_meta = data.get("viz_meta")
        payload_value = data.get("viz_points") or data.get("viz_density")
        return (
            payload_value,
            explorer_disclosure_html(viz_meta),
            selection_placeholder_html(viz_meta),
        )

    def explorer_select(self, data, evt: gr.EventData):
        if not data or not data.get("viz_points"):
            return selection_placeholder_html((data or {}).get("viz_meta"))
        index = getattr(evt, "index", None)
        if index is None:
            mode = getattr(evt, "_data", {}).get("view")
            meta = (
                {"available": True, "artifact_mode": "aggregate"}
                if mode == "density"
                else data.get("viz_meta")
            )
            return selection_placeholder_html(meta)
        if type(index) is not int or index < 0:
            return error_card_html(
                "The selected point is outside the sample.", sample_index=index
            )
        try:
            result = self.client.visualization_neighbors(index, 8)
            if result["model_id"] != data["model"]["model_id"]:
                raise APIError(
                    "The backend model changed. Refresh live data before inspecting."
                )
            return selection_html(result)
        except (APIError, ValueError) as exc:
            return error_card_html(str(exc), sample_index=index)

    def predict(self, data, *values):
        try:
            features = payload(values)
            result = self.client.predict(features)
            if data and result["model_id"] != data["model"]["model_id"]:
                raise APIError(
                    "The backend model changed. Refresh live data before predicting."
                )
            return (
                "**Prediction received from the API.**",
                prediction_card_html(result, (data or {}).get("profiles"), features),
                figures.distances_figure(result),
                charts.distances(result),
            )
        except (APIError, ValueError) as exc:
            return (
                str(exc),
                error_card_html(str(exc)),
                None,
                None,
            )

    def load_example(self):
        return (*SYNTHETIC_EXAMPLE, *cleared_prediction_outputs())
