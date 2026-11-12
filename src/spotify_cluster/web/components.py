"""Presentation and event logic, independently testable without a Gradio server."""

import html

from spotify_cluster.config import F9

from . import charts
from .api_client import APIError, number

EMPTY = "Refresh live data to load verified aggregates from the API."
CAVEAT = (
    "Clusters describe acoustic similarity; "
    "they are not verified music genres or mood labels."
)
DISTANCE_NOTE = (
    "Smaller means closer to that centroid. Euclidean distances in fitted "
    "RobustScaler-transformed F9 space; distances are not probabilities."
)
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


def summary(model):
    metrics = [
        (f"{model['training_sample_count']:,}", "Training tracks"),
        (str(model["number_of_clusters"]), "Acoustic clusters"),
        (model["algorithm"], "Algorithm"),
        (f"F{len(model['features'])}", "Representation"),
        (model["scaler"], "Preprocessing"),
    ]
    return (
        '<div class="metrics">'
        + "".join(
            f'<div class="metric"><strong>{html.escape(value)}</strong>'
            f"<span>{label}</span></div>"
            for value, label in metrics
        )
        + "</div>"
    )


def insight(profiles):
    contributions = profiles.get("feature_contributions")
    if not contributions:
        return "### Separation diagnostic\nNot available from this API response."
    shares = contributions["shares"]
    dominant = max(F9, key=lambda f: shares[f])
    return (
        f"### {shares[dominant]:.3%} · {dominant.title()}\n"
        "Share of between-cluster sum of squares in fitted RobustScaler space. "
        "This measures internal separation in the training population, "
        "not prediction accuracy."
    )


def interpretation(data, selection):
    profiles = charts.selected_profiles(data, selection)
    lines = [
        f"**Cluster {p['cluster_id']}** · {p['count']:,} tracks · {p['share']:.2%} "
        "of training population · "
        f"mean instrumentalness {p['mean']['instrumentalness']:.4f}."
        for p in profiles
    ]
    a, b = charts.selected_profiles(data)
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


def prediction_text(result):
    p = result["profile"]
    return (
        f"## Cluster {result['cluster_id']}\n"
        "Current cluster mean instrumentalness: "
        f"**{p['mean']['instrumentalness']:.4f}**. "
        f"Mean energy: **{p['mean']['energy']:.4f}**. "
        f"Mean valence: **{p['mean']['valence']:.4f}**.\n\n"
        f"**{p['count']:,} tracks · {p['share']:.2%}** of training population. "
        "These aggregate descriptors do not establish a genre or listening mood.\n\n"
        f"Model: `{result['model_id']}`\n\n"
        "Historical equivalence: **NOT VERIFIED**."
    )


class Handlers:
    def __init__(self, client):
        self.client = client

    def explore(self, data, selection, feature, statistic):
        if not data:
            return EMPTY, None, None, None
        profiles = data["profiles"]
        return (
            interpretation(profiles, selection),
            charts.comparison_figure(profiles, feature, statistic, selection),
            charts.profile_table(profiles, statistic, selection),
            charts.detail_table(profiles, selection),
        )

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
            data = {"model": model, "profiles": profiles}
            return (
                data,
                "**API ready** · Live verified aggregates loaded.",
                summary(model),
                charts.distribution_figure(profiles),
                charts.distribution(profiles).round(3),
                insight(profiles),
                f"Model: `{model['model_id']}` · "
                "Historical equivalence: **NOT VERIFIED**",
            )
        except APIError as exc:
            return (
                None,
                str(exc),
                "",
                None,
                None,
                EMPTY,
                "No live model metadata loaded.",
            )

    def predict(self, data, *values):
        try:
            result = self.client.predict(payload(values))
            if data and result["model_id"] != data["model"]["model_id"]:
                raise APIError(
                    "The backend model changed. Refresh live data before predicting."
                )
            return (
                "**Prediction received from the API.**",
                prediction_text(result),
                charts.distances_figure(result),
                charts.distances(result),
            )
        except (APIError, ValueError) as exc:
            return str(exc), "No prediction available.", None, None


METHODOLOGY = """
## Research & Methodology
### Why cluster music?
Unsupervised clustering explores acoustic relationships without using genre labels
as targets. The live interface groups numerical acoustic descriptors, not audio files.

### Dataset and preparation
The Kaggle Spotify Tracks Dataset (Maharshi Pandya) contains 114,000 original rows.
Track-ID deduplication yields 89,741 canonical unique tracks in the authorized snapshot.
Numeric features are checked for finite values and valid domains. Text and genre
metadata do not enter the nine-feature modeling matrix.

**Exact F9 order:** acousticness, danceability, energy, valence, tempo, loudness,
speechiness, instrumentalness, liveness. RobustScaler centers each feature using its
median and scales by its interquartile range; the fitted scaler and centroids stay
paired in one Pipeline.

### Research comparisons and the deployed model
The final notebook studies K-Means and Gaussian Mixture Models, F5 and F9 feature
representations, scaling comparisons and PCA exploration. The deployed model is a
separately authorized **deployment-v1 refit: K-Means, K=2, F9, RobustScaler, no PCA**,
trained on all 89,741 canonical tracks.

Deployment-v1 explicitly adopts k-means++ initialization, n_init=20, max_iter=300,
tol=0.0001, Lloyd algorithm and seed 42. These deployment settings do not establish
the historical final estimator's undocumented optimizer settings.

### Archived evidence
The notebook records a historical FULL candidate study and a one-time Holdout
evaluation. Those are archived research evidence, not a new evaluation of deployment-v1.
The Holdout remains closed. **Historical model equivalence is NOT VERIFIED.**

### What the results can and cannot say
- Cluster IDs are arbitrary; use the current artifact's profiles to interpret them.
- Instrumentalness dominates the current scaled-space separation diagnostic.
- There is no verified genre accuracy, calibrated probability or fresh independent
  deployment Holdout score. Centroid distances are not confidence percentages.
- This app accepts numerical acoustic features only; MP3 analysis, Spotify URLs and
  fabricated music recommendations are unsupported.
- The API exposes aggregate statistics, not verified per-track PCA or t-SNE
  coordinates. Those scatterplots are deliberately omitted.
"""
