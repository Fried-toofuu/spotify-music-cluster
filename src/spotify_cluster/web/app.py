"""Local Gradio entry point. Browser → Gradio → HTTP → FastAPI."""

import os
from pathlib import Path

import gradio as gr

from spotify_cluster.config import F9

from .api_client import APIClient
from .charts import unit
from .components import (
    CAVEAT,
    DISTANCE_NOTE,
    EMPTY,
    HELP,
    METHODOLOGY,
    Handlers,
)

CSS = """
.gradio-container {
  --page: #141b18; --surface: #1c2621; --ink: #edf5f0; --muted: #b5c8bd;
  --accent: #69d6a0; --line: #3d5146; --radius: 12px;
  --space-sm: 8px; --space-md: 16px; --space-lg: 24px; --space-xl: 32px;
  max-width: 1200px; width: 100%; min-width: 0;
  margin: auto; padding: var(--space-lg);
  background: var(--page); color: var(--ink); font-variant-numeric: tabular-nums;
}
.metrics { display: grid; grid-template-columns: repeat(5,minmax(0,1fr));
  gap: var(--space-md); margin: var(--space-md) 0 var(--space-lg); }
.metric { background: var(--surface); border: 1px solid var(--line);
  border-radius: var(--radius); padding: var(--space-lg) var(--space-md); }
.metric strong { display: block; font-size: 1.45rem; font-weight: 650;
  overflow-wrap: anywhere; color: var(--ink); }
.metric span { display: block; margin-top: var(--space-sm); color: var(--muted); }
#hero { padding: var(--space-xl) 0 var(--space-md); }
#hero h1 { font-size: clamp(1.8rem,4vw,2.7rem); line-height: 1.15; }
#hero p { color: var(--muted); }
#scientific-caveat { border-left: 3px solid var(--accent); padding: var(--space-md);
  background: var(--surface); border-radius: var(--radius); }
.gradio-container button { min-height: 44px; }
.gradio-container :focus-visible {
  outline: 2px solid var(--accent); outline-offset: 2px; }
.gradio-container .prose { overflow-wrap: anywhere; }
.gradio-container .app { padding: 0; min-width: 0; }
.gradio-container .chart img {
  display: block; width: 100%; max-width: 620px; margin: 0 auto; }
.gradio-container [role=tabpanel] { min-width: 0; max-width: 100%; }
@media(max-width: 768px) { .metrics { grid-template-columns: repeat(2,minmax(0,1fr)); }
  .gradio-container { padding: var(--space-md); }
  .metric:last-child { grid-column: 1 / -1; } }
"""


def theme():
    # Local system fonts; the same dark palette also covers OS light preference.
    return gr.themes.Base(
        primary_hue="green",
        secondary_hue="blue",
        neutral_hue="slate",
        font=["system-ui", "sans-serif"],
        font_mono=["monospace"],
    ).set(
        body_background_fill="#141b18",
        body_background_fill_dark="#141b18",
        body_text_color="#edf5f0",
        body_text_color_dark="#edf5f0",
        body_text_color_subdued="#b5c8bd",
        body_text_color_subdued_dark="#b5c8bd",
        block_background_fill="#1c2621",
        block_background_fill_dark="#1c2621",
        block_border_color="#3d5146",
        block_border_color_dark="#3d5146",
        input_background_fill="#141b18",
        input_background_fill_dark="#141b18",
        button_primary_background_fill="#69d6a0",
        button_primary_background_fill_dark="#69d6a0",
        button_primary_text_color="#102319",
        button_primary_text_color_dark="#102319",
    )


def plot(**kwargs):
    # Native BarPlot keeps stale bars on data updates in Gradio 6.31; Plot
    # re-encodes a fresh Matplotlib figure for every value change instead.
    return gr.Plot(
        show_label=False,
        container=False,
        buttons=[],
        format="png",
        elem_classes=["chart"],
        **kwargs,
    )


def create_app(client=None):
    handlers = Handlers(client or APIClient())
    with gr.Blocks(title="Spotify Music Clustering", analytics_enabled=False) as app:
        state = gr.State(None, time_to_live=3600)
        gr.Markdown(
            "# Spotify Music Clustering\n"
            "Explore acoustic patterns with unsupervised machine learning",
            elem_id="hero",
        )
        gr.Markdown(CAVEAT, elem_id="scientific-caveat")
        with gr.Row():
            status = gr.Markdown("Live predictions require the FastAPI backend.")
            refresh = gr.Button("Refresh live data", size="sm", scale=0)
        with gr.Tabs(overflow_behavior="wrap"):
            with gr.Tab("Overview"):
                gr.Markdown(
                    "## The acoustic landscape\n"
                    "An unsupervised learning project that groups Spotify tracks using "
                    "acoustic descriptors. Acoustic clustering, "
                    "not genre classification."
                )
                metrics = gr.HTML("")
                with gr.Row():
                    with gr.Column(scale=3, min_width=280):
                        dist = plot()
                        dist_table = gr.Dataframe(
                            headers=["Cluster", "Tracks", "Share (%)"],
                            interactive=False,
                            label="Population and share",
                            buttons=[],
                        )
                    with gr.Column(scale=2, min_width=260):
                        insight = gr.Markdown(EMPTY)
                        gr.Markdown(
                            "### Read the profiles, not the label\n"
                            "Cluster numbers identify fitted centroids. Their acoustic "
                            "meaning comes from this model's aggregate statistics."
                        )
                identity = gr.Markdown("No live model metadata loaded.")
            with gr.Tab("Predict Cluster"):
                gr.Markdown(
                    "## Where does your feature vector belong?\n"
                    "Enter all nine raw acoustic descriptors. "
                    "MP3 and Spotify URL analysis are unsupported."
                )
                inputs = []
                with gr.Row():
                    with gr.Column(min_width=280):
                        for f in F9[:4]:
                            inputs.append(
                                gr.Slider(
                                    0,
                                    1,
                                    value=0.5,
                                    step=0.001,
                                    label=f.title(),
                                    info=HELP[f],
                                )
                            )
                    with gr.Column(min_width=280):
                        for f in F9[4:]:
                            if f in ("tempo", "loudness"):
                                inputs.append(
                                    gr.Number(
                                        label=f"{f.title()} ({unit(f)})",
                                        value=120 if f == "tempo" else -10,
                                        minimum=0 if f == "tempo" else None,
                                        info=HELP[f],
                                    )
                                )
                            else:
                                inputs.append(
                                    gr.Slider(
                                        0,
                                        1,
                                        value=0.5,
                                        step=0.001,
                                        label=f.title(),
                                        info=HELP[f],
                                    )
                                )
                gr.Examples(
                    examples=[[0.72, 0.61, 0.38, 0.44, 118.5, -9.2, 0.05, 0.81, 0.13]],
                    inputs=inputs,
                    cache_examples=False,
                    label="Illustrative, synthetic input example · not a real track",
                    example_labels=["Load synthetic F9 example"],
                )
                submit = gr.Button("Predict Cluster", variant="primary")
                prediction_status = gr.Markdown(
                    "Submit features to request a live prediction."
                )
                with gr.Row():
                    with gr.Column(min_width=280):
                        prediction = gr.Markdown("No prediction yet.")
                    with gr.Column(min_width=280):
                        distance_plot = plot()
                        distance_table = gr.Dataframe(
                            headers=["Cluster", "Distance"],
                            interactive=False,
                            label="Exact centroid distances",
                            buttons=[],
                        )
                gr.Markdown(DISTANCE_NOTE)
            with gr.Tab("Cluster Explorer"):
                gr.Markdown(
                    "## Compare the current acoustic profiles\n"
                    "Raw feature units; training aggregates only."
                )
                with gr.Row():
                    selection = gr.Dropdown(
                        ["Compare Both", "Cluster 0", "Cluster 1"],
                        value="Compare Both",
                        label="Cluster selection",
                        min_width=220,
                    )
                    feature = gr.Dropdown(
                        [(f.title(), f) for f in F9],
                        value="instrumentalness",
                        label="Acoustic feature",
                        min_width=220,
                    )
                    statistic = gr.Radio(
                        ["Mean", "Median"], value="Mean", label="Statistic"
                    )
                profile_text = gr.Markdown(EMPTY)
                compare_plot = plot(elem_id="feature-comparison")
                compare_table = gr.Dataframe(
                    interactive=False,
                    label="Nine-feature comparison",
                    buttons=[],
                    elem_id="feature-table",
                )
                with gr.Accordion(
                    "Detailed cluster statistics",
                    open=False,
                ):
                    details = gr.Dataframe(
                        interactive=False,
                        label="Raw-unit aggregate statistics",
                        buttons=[],
                    )
                    gr.Markdown(
                        "Std is sample standard deviation (ddof=1). "
                        "Missing optional statistics appear blank."
                    )
            with gr.Tab("Research & Methodology"):
                gr.Markdown(METHODOLOGY)

        overview_outputs = [state, status, metrics, dist, dist_table, insight, identity]
        app.load(handlers.refresh, outputs=overview_outputs, api_name="refresh")
        refresh.click(
            handlers.refresh, outputs=overview_outputs, api_name="refresh_live_data"
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
            [state, *inputs],
            [prediction_status, prediction, distance_plot, distance_table],
            api_name="predict_cluster",
            concurrency_limit=1,
        )
    return app


def launch_options():
    # Gradio treats allowed_paths=[] as a fallback to this environment variable.
    if os.environ.get("GRADIO_ALLOWED_PATHS"):
        raise ValueError("Remove GRADIO_ALLOWED_PATHS before starting this local app")
    # No input/output component serves files. Block the working tree explicitly too.
    return dict(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
        inbrowser=False,
        show_error=False,
        allowed_paths=[],
        blocked_paths=[str(Path.cwd())],
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
