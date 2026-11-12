"""Local Gradio entry point. Browser → Gradio → HTTP → FastAPI."""

import os
from pathlib import Path

import gradio as gr

from spotify_cluster.config import F9

from . import figures
from .api_client import APIClient
from .assets import ASSET_DIR
from .components import (
    AUDIO_NOTE,
    DISTANCE_NOTE,
    EMPTY,
    HELP,
    HERO,
    Handlers,
    brandbar_html,
    footer_html,
    prediction_empty_html,
    status_html,
)
from .explorer import create_explorer
from .theme import CSS, theme

TAB_NAMES = (
    "Overview",
    "Cluster Explorer",
    "Predict Cluster",
    "Research & Methodology",
)


def _scroll_result_on_submit():
    return """(...args) => {
      let attempts = 0;
      const reveal = () => {
        const target =
          document.querySelector('#prediction-result .obs-prediction') ||
          document.querySelector('#prediction-result .obs-card');
        if (!target) {
          attempts += 1;
          if (attempts < 20) window.setTimeout(reveal, 200);
          return;
        }
        const reduce = window.matchMedia(
          '(prefers-reduced-motion: reduce)'
        ).matches;
        target.scrollIntoView({
          behavior: reduce ? 'auto' : 'smooth', block: 'start'
        });
      };
      [1200, 2400, 3600].forEach((delay) => window.setTimeout(reveal, delay));
      return args;
    }"""


def _jump(label):
    return (
        "() => { const buttons = Array.from(document.querySelectorAll("
        "'.tab-nav button, button[role=\"tab\"]')); "
        "const match = buttons.find((button) => "
        "button.textContent.trim().toLowerCase().startsWith(" + repr(label) + ")); "
        "if (match) match.click(); }"
    )


def plot(**kwargs):
    return gr.Plot(
        show_label=False,
        container=False,
        buttons=[],
        elem_classes=["obs-chart"],
        **kwargs,
    )


def table(**kwargs):
    return gr.Dataframe(
        interactive=False,
        buttons=[],
        elem_classes=["obs-table"],
        **kwargs,
    )


def _noop():
    return None


def create_app(client=None):
    handlers = Handlers(client or APIClient())
    with gr.Blocks(
        title="Acoustic Observatory · Spotify Music Clustering",
        analytics_enabled=False,
    ) as app:
        state = gr.State(None, time_to_live=3600)
        with gr.Row(elem_classes=["obs-brandrow"]):
            brandbar = gr.HTML(brandbar_html(), container=False, padding=False)
            refresh = gr.Button(
                "Refresh live data", size="sm", scale=0, variant="secondary"
            )
        status = gr.HTML(
            status_html(False, "Loading live aggregates…"),
            container=False,
            padding=False,
        )

        with gr.Tabs(overflow_behavior="wrap") as tabs:
            with gr.Tab("Overview"):
                gr.HTML(HERO, container=False, padding=False)
                with gr.Row(elem_id="overview-grid"):
                    with gr.Column(scale=5, min_width=320):
                        overview_space = create_explorer("overview-space", compact=True)
                        overview_note = gr.HTML("", container=False, padding=False)
                        gr.HTML(
                            '<div class="obs-card tight"><span class="obs-kicker">'
                            'How to read this space</span><p class="obs-footnote">'
                            "Each point is a sampled track in a visualization-only "
                            "PCA projection. Color is the deployed cluster assignment. "
                            "Hover for acoustic descriptors; open the Cluster Explorer "
                            "to pick a sample and inspect its nearest neighbours in "
                            "fitted RobustScaler F9 space.</p></div>",
                            container=False,
                            padding=False,
                        )
                    with gr.Column(scale=3, min_width=290):
                        fact_sheet = gr.HTML("", container=False, padding=False)
                        finding = gr.HTML("", container=False, padding=False)
                        population = gr.HTML("", container=False, padding=False)
                gr.HTML(
                    """
<div class="obs-section">
  <div class="obs-section-head">
    <h2>Three ways in</h2>
    <span class="obs-note">Start with the map, test a vector,
    or read the evidence.</span>
  </div>
  <div class="obs-grid-3">
    <div class="obs-card obs-entry">
      <span class="obs-kicker">01 · Explore</span>
      <h3>Walk the cluster space</h3>
      <p>Switch between PCA 2D, PCA 3D and aggregate density; filter clusters;
      inspect a sampled track and its nearest neighbours in fitted scaled F9 space.</p>
      <span class="obs-entry-link">Open Cluster Explorer →</span>
    </div>
    <div class="obs-card obs-entry">
      <span class="obs-kicker">02 · Test</span>
      <h3>Score an acoustic vector</h3>
      <p>Submit nine raw descriptors to the real FastAPI endpoint. Read the assigned
      cluster, both centroid distances and the current profile — never a fake
      probability.</p>
      <span class="obs-entry-link">Open Predict Cluster →</span>
    </div>
    <div class="obs-card obs-entry">
      <span class="obs-kicker">03 · Read</span>
      <h3>Follow the research</h3>
      <p>Trace the authorized dataset, F5/F9 representations, K-Means and GMM
      comparisons, archived historical evidence and the limits of the deployed
      model.</p>
      <span class="obs-entry-link">Open Research →</span>
    </div>
  </div>
</div>
"""
                )
                with gr.Row(elem_classes=["obs-nav-actions"]):
                    go_explore = gr.Button("Cluster Explorer", variant="secondary")
                    go_predict = gr.Button("Predict Cluster", variant="secondary")
                    go_research = gr.Button("Research", variant="secondary")
                overview_identity = gr.HTML("", container=False, padding=False)

            with gr.Tab("Cluster Explorer"):
                gr.Markdown(
                    "## Read the acoustic space\n"
                    "Pick points, filter clusters and compare the fitted profiles. "
                    "The map is a visualization projection; the model's assignments "
                    "come from the deployed F9 representation."
                )
                explorer_plot = create_explorer("explorer-space")
                explorer_disclosure = gr.HTML(EMPTY, container=False, padding=False)
                with gr.Row(elem_id="explorer-panels"):
                    with gr.Column(scale=5, min_width=320):
                        explorer_detail = gr.HTML(
                            "",
                            container=False,
                            padding=False,
                            elem_id="explorer-detail",
                        )
                    with gr.Column(scale=4, min_width=300):
                        gr.Markdown("### Compare acoustic profiles")
                        with gr.Row():
                            selection = gr.Dropdown(
                                ["Compare Both", "Cluster 0", "Cluster 1"],
                                value="Compare Both",
                                label="Cluster selection",
                                min_width=160,
                            )
                            feature = gr.Dropdown(
                                [(value.title(), value) for value in F9],
                                value="instrumentalness",
                                label="Acoustic feature",
                                min_width=160,
                            )
                            statistic = gr.Radio(
                                ["Mean", "Median"], value="Mean", label="Statistic"
                            )
                        profile_text = gr.Markdown(EMPTY)
                        compare_plot = plot(
                            value=figures.empty_figure(
                                "Refresh live data to compare profiles."
                            )
                        )
                        compare_table = table(
                            label="Nine-feature comparison",
                            elem_id="feature-table",
                        )
                        with gr.Accordion("Detailed aggregate statistics", open=False):
                            details = table(label="Raw-unit aggregate statistics")
                            gr.Markdown(
                                "Std is sample standard deviation (ddof=1). Missing "
                                "optional statistics appear blank. Values describe the "
                                "training population, not a genre or a listener mood."
                            )
                gr.Markdown(
                    "**How to read the panel:** the browser never fits a model. "
                    "Cluster assignments and point inspection come from the FastAPI "
                    "service. Nearest-neighbour distances are computed in fitted "
                    "RobustScaler F9 space, not from screen distance.",
                    elem_id="explorer-footnote",
                )

            with gr.Tab("Predict Cluster"):
                with gr.Row(elem_id="predict-grid"):
                    with gr.Column(scale=5, min_width=320, elem_id="predict-form"):
                        gr.Markdown(
                            "## Where does this vector belong?\n"
                            "Enter all nine raw acoustic descriptors. " + AUDIO_NOTE
                        )
                        with gr.Accordion("Core acoustic character", open=True):
                            acousticness = gr.Slider(
                                0,
                                1,
                                value=0.7,
                                step=0.001,
                                label="Acousticness · 0–1",
                                info=HELP["acousticness"],
                            )
                            instrumentalness = gr.Slider(
                                0,
                                1,
                                value=0.01,
                                step=0.001,
                                label="Instrumentalness · 0–1",
                                info=HELP["instrumentalness"],
                            )
                            speechiness = gr.Slider(
                                0,
                                1,
                                value=0.05,
                                step=0.001,
                                label="Speechiness · 0–1",
                                info=HELP["speechiness"],
                            )
                            liveness = gr.Slider(
                                0,
                                1,
                                value=0.12,
                                step=0.001,
                                label="Liveness · 0–1",
                                info=HELP["liveness"],
                            )
                        with gr.Accordion("Rhythm, energy and dynamics", open=True):
                            danceability = gr.Slider(
                                0,
                                1,
                                value=0.6,
                                step=0.001,
                                label="Danceability · 0–1",
                                info=HELP["danceability"],
                            )
                            energy = gr.Slider(
                                0,
                                1,
                                value=0.65,
                                step=0.001,
                                label="Energy · 0–1",
                                info=HELP["energy"],
                            )
                            valence = gr.Slider(
                                0,
                                1,
                                value=0.45,
                                step=0.001,
                                label="Valence · 0–1",
                                info=HELP["valence"],
                            )
                            tempo = gr.Number(
                                label="Tempo · BPM",
                                value=120,
                                minimum=0,
                                info=HELP["tempo"],
                            )
                            loudness = gr.Number(
                                label="Loudness · dB",
                                value=-9.0,
                                info=HELP["loudness"],
                            )
                        with gr.Row(elem_id="predict-action"):
                            example = gr.Button(
                                "Load illustrative F9 vector", variant="secondary"
                            )
                            submit = gr.Button(
                                "Predict cluster",
                                variant="primary",
                                elem_id="predict-submit",
                            )
                        gr.Markdown(
                            "The example is explicitly synthetic and is only loaded "
                            "into the form; no result appears until the FastAPI "
                            "endpoint returns one."
                        )
                    with gr.Column(scale=5, min_width=320):
                        prediction_status = gr.Markdown(
                            "Submit features to request a real API prediction."
                        )
                        prediction = gr.HTML(
                            prediction_empty_html(),
                            container=False,
                            padding=False,
                            elem_id="prediction-result",
                        )
                        distance_plot = plot(
                            value=figures.empty_figure(
                                "Submit a feature vector to see distances."
                            )
                        )
                        distance_table = table(
                            headers=["Cluster", "Distance"],
                            label="Exact centroid distances",
                        )
                        gr.Markdown(DISTANCE_NOTE)
                gr.HTML(
                    '<div class="obs-card tight"><span class="obs-kicker">Model '
                    'boundary</span><p class="obs-footnote">This is unsupervised '
                    "acoustic clustering, not genre classification. The cluster label "
                    "is arbitrary; the current profile is the interpretation. The "
                    "deployed model is a separate refit and historical equivalence "
                    "remains <strong>NOT VERIFIED</strong>.</p></div>",
                    container=False,
                    padding=False,
                )

            with gr.Tab("Research & Methodology"):
                research_html = gr.HTML(
                    '<div class="obs-card"><span class="obs-kicker">Research</span>'
                    '<p class="obs-muted">Refresh live data to load verified '
                    "research evidence.</p></div>",
                    container=False,
                    padding=False,
                )
                gr.Markdown(
                    "### Figures\n"
                    "The contribution chart shows internal between-cluster separation "
                    "in fitted scaled space; the agreement chart compares partitions "
                    "on identical rows. Neither is a quality leaderboard."
                )
                research_plot = plot(
                    value=figures.empty_figure(
                        "Refresh live data to load contributions."
                    )
                )
                research_comparison_plot = plot(
                    value=figures.empty_figure("Refresh live data to load comparisons.")
                )
                archived_table = table(label="Archived historical evidence · closed")
                gr.Markdown(
                    "Values above are shown only when served by the research artifact. "
                    "No historical Holdout evaluation is rerun, extended or attached "
                    "to deployment predictions.",
                    elem_id="research-footnote",
                )

        gr.HTML(footer_html(), container=False, padding=False)

        refresh_outputs = [
            state,
            brandbar,
            status,
            overview_space,
            overview_note,
            fact_sheet,
            finding,
            population,
            overview_identity,
            explorer_disclosure,
            explorer_plot,
            explorer_detail,
            research_html,
            research_plot,
            research_comparison_plot,
            archived_table,
        ]
        app.load(
            handlers.refresh,
            outputs=refresh_outputs,
            api_name="refresh",
        )
        refresh.click(
            handlers.refresh,
            outputs=refresh_outputs,
            api_name="refresh_live_data",
        )
        tabs.select(
            handlers.load_explorer,
            [state],
            [explorer_plot, explorer_disclosure, explorer_detail],
            api_visibility="private",
        )
        explorer_plot.select(
            handlers.explorer_select,
            [state],
            [explorer_detail],
            api_visibility="private",
        )
        for trigger in (
            state.change,
            selection.change,
            feature.change,
            statistic.change,
        ):
            trigger(
                handlers.explore,
                [state, selection, feature, statistic],
                [profile_text, compare_plot, compare_table, details],
                api_visibility="private",
            )
        submit.click(
            handlers.predict,
            [
                state,
                acousticness,
                danceability,
                energy,
                valence,
                tempo,
                loudness,
                speechiness,
                instrumentalness,
                liveness,
            ],
            [prediction_status, prediction, distance_plot, distance_table],
            api_name="predict_cluster",
            concurrency_limit=1,
            js=_scroll_result_on_submit(),
        )
        example.click(
            handlers.example,
            outputs=[
                acousticness,
                danceability,
                energy,
                valence,
                tempo,
                loudness,
                speechiness,
                instrumentalness,
                liveness,
            ],
            api_visibility="private",
        )
        go_explore.click(_noop, js=_jump("cluster explorer"))
        go_predict.click(_noop, js=_jump("predict cluster"))
        go_research.click(_noop, js=_jump("research"))
    return app


def launch_options():
    # Gradio treats allowed_paths=[] as a fallback to this environment variable.
    if os.environ.get("GRADIO_ALLOWED_PATHS"):
        raise ValueError("Remove GRADIO_ALLOWED_PATHS before starting this local app")
    cwd = Path.cwd().resolve()
    if ASSET_DIR.resolve().is_relative_to(cwd):
        raise ValueError("The browser-asset directory must sit outside the checkout")
    host = os.environ.get("SPOTIFY_WEB_HOST", "127.0.0.1")
    if host not in ("127.0.0.1", "localhost", "0.0.0.0", "::1"):
        raise ValueError(
            "SPOTIFY_WEB_HOST must be loopback or 0.0.0.0; terminate TLS at a proxy"
        )
    try:
        port = int(os.environ.get("SPOTIFY_WEB_PORT", "7860"))
    except ValueError:
        raise ValueError("SPOTIFY_WEB_PORT must be an integer") from None
    if not 1 <= port <= 65535:
        raise ValueError("SPOTIFY_WEB_PORT must be between 1 and 65535")
    return dict(
        server_name=host,
        server_port=port,
        share=False,
        inbrowser=False,
        show_error=False,
        allowed_paths=[],
        blocked_paths=[str(cwd)],
        theme=theme(),
        css=CSS,
        run_history=False,
        footer_links=[],
        enable_monitoring=False,
        mcp_server=False,
        ssr_mode=False,
        max_file_size=1,
        strict_cors=True,
    )


def main():
    create_app().launch(**launch_options())


if __name__ == "__main__":
    main()
