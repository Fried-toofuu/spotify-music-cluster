# ruff: noqa: E501  (long CSS declarations)
"""Acoustic Observatory design tokens, Gradio theme and application CSS."""

from __future__ import annotations

import gradio as gr

TOKENS = {
    "bg": "#F7F9FC",
    "surface_1": "#FFFFFF",
    "surface_2": "#F0F3F7",
    "surface_3": "#E8EDF3",
    "ink": "#17212B",
    "ink_2": "#556270",
    "muted": "#596775",
    "line": "#E0E6ED",
    "line_strong": "#7B8896",
    "teal": "#147D73",
    "teal_dim": "#10665E",
    "violet": "#7055B9",
    "amber": "#8A5B10",
    "danger": "#B42335",
    "success": "#147D59",
    "on_accent": "#FFFFFF",
    "density_low": "#5D9F96",
    "density_mid": "#3D9589",
    "density_high": "#247F74",
    "cluster_0": "#147D73",
    "cluster_1": "#7055B9",
}
CLUSTER_COLORS = {0: TOKENS["cluster_0"], 1: TOKENS["cluster_1"]}
CLUSTER_SYMBOLS = {0: "circle", 1: "diamond"}
CLUSTER_NAMES = {0: "Cluster 0", 1: "Cluster 1"}


def theme() -> gr.Theme:
    base = gr.themes.Base(
        primary_hue="teal",
        secondary_hue="violet",
        neutral_hue="slate",
        font=[
            "Inter",
            "Segoe UI Variable",
            "Segoe UI",
            "system-ui",
            "sans-serif",
        ],
        font_mono=["JetBrains Mono", "Cascadia Code", "Consolas", "monospace"],
    )
    light_values = dict(
        body_background_fill=TOKENS["bg"],
        body_text_color=TOKENS["ink"],
        body_text_color_subdued=TOKENS["ink_2"],
        background_fill_primary=TOKENS["bg"],
        background_fill_secondary=TOKENS["surface_1"],
        block_background_fill=TOKENS["surface_1"],
        block_border_color=TOKENS["line"],
        block_border_width="1px",
        block_radius="14px",
        panel_background_fill=TOKENS["surface_1"],
        panel_border_color=TOKENS["line"],
        input_background_fill=TOKENS["surface_2"],
        input_border_color=TOKENS["line_strong"],
        input_border_color_focus=TOKENS["teal"],
        input_placeholder_color=TOKENS["muted"],
        button_primary_background_fill=TOKENS["teal"],
        button_primary_background_fill_hover=TOKENS["teal_dim"],
        button_primary_text_color=TOKENS["on_accent"],
        button_secondary_background_fill=TOKENS["surface_2"],
        button_secondary_background_fill_hover=TOKENS["surface_3"],
        button_secondary_text_color=TOKENS["ink"],
        button_secondary_border_color=TOKENS["line_strong"],
        checkbox_background_color_selected=TOKENS["teal"],
        slider_color=TOKENS["teal"],
        color_accent=TOKENS["teal"],
        color_accent_soft=TOKENS["surface_3"],
        link_text_color=TOKENS["teal"],
        link_text_color_hover=TOKENS["ink"],
        link_text_color_visited=TOKENS["violet"],
        table_border_color=TOKENS["line"],
        table_even_background_fill=TOKENS["surface_1"],
        table_odd_background_fill=TOKENS["surface_2"],
        code_background_fill=TOKENS["surface_3"],
        border_color_primary=TOKENS["line"],
        loader_color=TOKENS["teal"],
        shadow_drop="0 1px 2px rgba(23,33,43,.10)",
        shadow_drop_lg="0 18px 48px rgba(23,33,43,.10)",
        block_shadow="none",
    )

    # Gradio can receive a host-provided theme preference. Its compatibility slots
    # share the light values; there is no second palette or application theme state.
    values = base.to_dict()["theme"] | light_values
    dark_values = {
        key: values[key.removesuffix("_dark")]
        for key in values
        if key.endswith("_dark") and key.removesuffix("_dark") in values
    }
    return base.set(**light_values, **dark_values)


def css_tokens() -> str:
    return "; ".join(
        f"--obs-{key.replace('_', '-')}: {value}" for key, value in TOKENS.items()
    )


LIGHT_HEAD = """<meta name="color-scheme" content="light">
<script>
// Gradio mounts before custom head scripts on some clients. Enforce the same
// light appearance for initial, host-supplied and subsequent system preferences.
const observatoryUrl = new URL(window.location.href);
observatoryUrl.searchParams.set('__theme', 'light');
history.replaceState(history.state, '', observatoryUrl);
const keepObservatoryLight = () => {
  if (document.body.classList.contains('dark')) document.body.classList.remove('dark');
};
keepObservatoryLight();
new MutationObserver(keepObservatoryLight).observe(document.body, {
  attributes: true, attributeFilter: ['class']
});
</script>"""


CSS = """
:root { color-scheme: only light; --obs-display: "Iowan Old Style", "Palatino Linotype",
  "Book Antiqua", Palatino, Georgia, serif;
  --obs-ui: "Inter", "Segoe UI Variable", "Segoe UI", system-ui, -apple-system, sans-serif;
  --obs-mono: "JetBrains Mono", "Cascadia Code", "SFMono-Regular", Consolas, monospace; }
html, body { background: var(--obs-bg) !important; color-scheme: only light !important; }
body { margin: 0; }
/* The app shell owns width and rhythm so every view shares one grid. */
.gradio-container {
  --obs-space-1: 4px; --obs-space-2: 8px; --obs-space-3: 12px;
  --obs-space-4: 16px; --obs-space-5: 24px; --obs-space-6: 32px;
  --obs-duration: 180ms; --obs-ease: ease-out;
  --obs-radius: 14px; --obs-radius-sm: 9px;
  max-width: 1280px !important; width: 100%; min-width: 0; margin: 0 auto;
  padding: 0 24px 72px; background: var(--obs-bg) !important;
  color: var(--obs-ink); font-family: var(--obs-ui); font-size: 16px;
  line-height: 1.6; font-variant-numeric: tabular-nums;
}
footer, .built-with, .show-api { display: none !important; }
.prose { color: var(--obs-ink-2); max-width: 100%; overflow-wrap: anywhere; }
.prose h1, .prose h2, .prose h3, .prose h4 {
  font-family: var(--obs-display); color: var(--obs-ink); letter-spacing: -.015em;
  line-height: 1.15; }
.prose h2 { font-size: clamp(1.55rem, 2.6vw, 2.1rem); margin: 1.8em 0 .55em; }
.prose h3 { font-size: 1.18rem; margin: 1.5em 0 .4em; }
.prose h4 { font-size: .95rem; font-family: var(--obs-ui); letter-spacing: .04em;
  text-transform: uppercase; color: var(--obs-muted); }
.prose a { color: var(--obs-teal); text-underline-offset: 3px; }
.prose strong { color: var(--obs-ink); }
.prose code { background: var(--obs-surface-3); color: var(--obs-ink);
  border: 1px solid var(--obs-line); border-radius: 5px; padding: .12em .38em;
  font-family: var(--obs-mono); font-size: .84em; }
.prose ul, .prose ol { padding-left: 1.2em; }
.prose li { margin: .28em 0; }
.prose hr { border: 0; border-top: 1px solid var(--obs-line); margin: 2em 0; }

/* Brand bar and hero */
.obs-brandbar { display: flex; align-items: center; justify-content: space-between;
  gap: 16px; flex-wrap: wrap; padding: 20px 0 18px;
  border-bottom: 1px solid var(--obs-line); }
.obs-brand { display: flex; align-items: center; gap: 12px; }
.obs-brand-mark { width: 34px; height: 34px; flex: 0 0 auto; }
.obs-brand-name { font-family: var(--obs-display); font-size: 1.02rem;
  letter-spacing: .08em; text-transform: uppercase; color: var(--obs-ink); }
.obs-brand-sub { font-family: var(--obs-mono); font-size: .8rem; color: var(--obs-muted);
  letter-spacing: .12em; text-transform: uppercase; }
.obs-brand-right { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.obs-live { display: inline-flex; align-items: center; gap: 8px; padding: 6px 11px;
  border: 1px solid var(--obs-line-strong); border-radius: 999px;
  font-family: var(--obs-mono); font-size: .8rem; letter-spacing: .06em;
  color: var(--obs-ink-2); background: var(--obs-surface-1); }
.obs-live::before { content: ""; width: 7px; height: 7px; border-radius: 50%;
  background: var(--obs-teal); box-shadow: 0 0 0 3px color-mix(in srgb, var(--obs-teal) 12%, transparent); }
.obs-live.offline::before { background: var(--obs-danger); box-shadow: none; }
.obs-hero { position: relative; padding: var(--obs-space-4) 0 var(--obs-space-3); }
.obs-hero > * { position: relative; z-index: 1; }
.obs-kicker { display: inline-block; font-family: var(--obs-mono); font-size: .8rem;
  letter-spacing: .1em; text-transform: uppercase; color: var(--obs-teal); }
.obs-hero h1 { font-family: var(--obs-display); font-weight: 500;
  font-size: clamp(2.5rem, 4.2vw, 4rem); line-height: 1.0; letter-spacing: -.025em;
  margin: .22em 0 .28em; color: var(--obs-ink); max-width: 22ch; }
.obs-hero p { max-width: 68ch; margin: 0; color: var(--obs-ink-2);
  font-size: clamp(1rem, 1.25vw, 1.16rem); }
.obs-hero-meta { display: flex; flex-wrap: wrap; gap: 8px; margin-top: var(--obs-space-4); }
.obs-tag { display: inline-flex; align-items: center; gap: 7px; padding: 5px 10px;
  border: 1px solid var(--obs-line); border-radius: 999px; background: var(--obs-surface-1);
  font-family: var(--obs-mono); font-size: .8rem; color: var(--obs-muted); }
.obs-tag strong { color: var(--obs-ink-2); font-weight: 500; }
.obs-caveat { margin: 20px 0 0; padding: 12px 15px; border-left: 2px solid var(--obs-amber);
  background: var(--obs-surface-1); border-radius: 0 var(--obs-radius-sm) var(--obs-radius-sm) 0;
  color: var(--obs-ink-2); font-size: .88rem; max-width: 90ch; }
.obs-caveat strong { color: var(--obs-amber); font-weight: 600; }

/* Cards, grids and type rhythm */
.obs-card { background: var(--obs-surface-1); border: 1px solid var(--obs-line);
  border-radius: var(--obs-radius); padding: 20px; min-width: 0; }
.obs-card.tight { padding: 16px; }
.obs-card[data-tone="error"] { border-left: 2px solid var(--obs-danger); }
.obs-card[data-tone="error"] .obs-kicker { color: var(--obs-danger); }
.obs-card h3, .obs-card h4 { margin: 0 0 8px; }
.obs-card h3 { font-family: var(--obs-display); font-weight: 500; font-size: 1.34rem;
  color: var(--obs-ink); letter-spacing: -.01em; }
.obs-card p { margin: 0 0 10px; color: var(--obs-ink-2); font-size: .92rem; }
.obs-card p:last-child { margin-bottom: 0; }
.obs-card .obs-kicker { margin-bottom: 8px; }
.obs-grid-2 { display: grid; grid-template-columns: minmax(0, 1.62fr) minmax(300px, 1fr);
  gap: 20px; align-items: start; }
.obs-grid-3 { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px; }
.obs-section { margin: 44px 0 0; }
.obs-section-head { display: flex; align-items: baseline; justify-content: space-between;
  gap: 16px; flex-wrap: wrap; margin-bottom: 14px; }
.obs-section-head h2 { font-family: var(--obs-display); font-weight: 500;
  font-size: clamp(1.5rem, 2.4vw, 2rem); margin: 0; letter-spacing: -.015em; }
.obs-note { color: var(--obs-muted); font-size: .78rem; line-height: 1.5; }
.obs-mono { font-family: var(--obs-mono); }
.obs-muted { color: var(--obs-muted); }
.obs-ink { color: var(--obs-ink); }
.obs-amber { color: var(--obs-amber); }
.obs-teal { color: var(--obs-teal); }
.obs-violet { color: var(--obs-violet); }
.obs-rule { height: 1px; background: var(--obs-line); border: 0; margin: 22px 0; }

/* Fact sheet, findings and entry cards */
.obs-facts { display: grid; gap: 0; }
.obs-fact { display: flex; align-items: baseline; justify-content: space-between;
  gap: 14px; padding: 11px 0; border-bottom: 1px solid var(--obs-line); }
.obs-fact:last-child { border-bottom: 0; }
.obs-fact dt { font-family: var(--obs-mono); font-size: .8rem; letter-spacing: .08em;
  text-transform: uppercase; color: var(--obs-muted); }
.obs-fact dd { margin: 0; font-size: .9rem; color: var(--obs-ink); text-align: right;
  overflow-wrap: anywhere; }
.obs-finding { position: relative; overflow: hidden; }
.obs-finding::after { content: ""; position: absolute; right: -40px; top: -50px;
  width: 150px; height: 150px; border-radius: 50%;
  background: none; }
.obs-big { font-family: var(--obs-display); font-size: clamp(2.1rem, 4vw, 3.1rem);
  line-height: 1; color: var(--obs-amber); letter-spacing: -.02em; }
.obs-big small { font-family: var(--obs-ui); font-size: .88rem; color: var(--obs-muted);
  letter-spacing: 0; }
.obs-bar { height: 7px; border-radius: 999px; background: var(--obs-surface-3);
  overflow: hidden; margin: 12px 0 8px; }
.obs-bar span { display: block; height: 100%; border-radius: inherit;
  background: linear-gradient(90deg, var(--obs-teal), var(--obs-violet)); }
.obs-split { display: flex; gap: 2px; height: 12px; border-radius: 999px; overflow: hidden;
  margin: 12px 0 10px; background: var(--obs-surface-3); }
.obs-split span { min-width: 3px; }
.obs-split .c0 { background: var(--obs-teal); }
.obs-split .c1 { background: var(--obs-violet); }
.obs-entry { display: flex; flex-direction: column; gap: 8px; min-height: 150px;
  transition: border-color 180ms ease, transform 180ms ease; }
.obs-entry:hover { border-color: var(--obs-line-strong); }
.obs-entry .obs-kicker { color: var(--obs-muted); }
.obs-entry h3 { margin: 0; }
.obs-entry p { flex: 1; }
.obs-entry-link { font-family: var(--obs-mono); font-size: .82rem; letter-spacing: .06em;
  text-transform: uppercase; color: var(--obs-teal); }
.obs-empty { border: 1px dashed var(--obs-line-strong); border-radius: var(--obs-radius);
  padding: 28px 20px; color: var(--obs-muted); text-align: center; background:
  var(--obs-surface-1); }
.obs-empty strong { color: var(--obs-ink); display: block; margin-bottom: 6px; }
.obs-badge { display: inline-flex; align-items: center; gap: 7px; padding: 4px 9px;
  border-radius: 999px; border: 1px solid var(--obs-line-strong);
  font-family: var(--obs-mono); font-size: .8rem; color: var(--obs-ink-2); }
.obs-badge .swatch, .obs-swatch { width: 9px; height: 9px; border-radius: 3px;
  display: inline-block; flex: 0 0 auto; }
.obs-badge.c0 .swatch, .obs-swatch.c0 { background: var(--obs-teal); }
.obs-badge.c1 .swatch, .obs-swatch.c1 { background: var(--obs-violet); }
.obs-detail { border-left: 2px solid var(--obs-line-strong); padding-left: 16px; }
.obs-detail h3 { margin-bottom: 4px; }
.obs-feature-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px; margin: 12px 0; }
.obs-feature { background: var(--obs-surface-2); border: 1px solid var(--obs-line);
  border-radius: 8px; padding: 9px 10px; min-width: 0; }
.obs-feature dt { font-family: var(--obs-mono); font-size: .78rem; color: var(--obs-muted);
  letter-spacing: .06em; text-transform: uppercase; }
.obs-feature dd { margin: 3px 0 0; font-size: .92rem; color: var(--obs-ink);
  font-variant-numeric: tabular-nums; overflow-wrap: anywhere; }
.obs-neighbors { width: 100%; border-collapse: collapse; font-size: .8rem; }
.obs-neighbors th { text-align: left; font-family: var(--obs-mono); font-size: .78rem;
  letter-spacing: .06em; text-transform: uppercase; color: var(--obs-muted);
  border-bottom: 1px solid var(--obs-line); padding: 6px 8px 6px 0; }
.obs-neighbors td { padding: 6px 8px 6px 0; border-bottom: 1px solid var(--obs-line);
  color: var(--obs-ink-2); }
.obs-neighbors tr:last-child td { border-bottom: 0; }
.obs-prediction { border-top: 5px solid var(--obs-teal); }
.obs-prediction.c1 { border-top-color: var(--obs-violet); }
.obs-prediction .obs-result-head { display: flex; align-items: flex-start;
  justify-content: space-between; gap: 16px; flex-wrap: wrap; }
.obs-prediction h2 { font-family: var(--obs-display); font-size: clamp(2rem, 3.4vw, 2.8rem);
  font-weight: 500; margin: 2px 0 0; letter-spacing: -.02em; }
.obs-prediction .obs-result-meta { margin-top: 8px; color: var(--obs-muted);
  font-size: .82rem; }
.obs-verdict { font-family: var(--obs-mono); font-size: .8rem; letter-spacing: .08em;
  text-transform: uppercase; color: var(--obs-ink-2); border: 1px solid var(--obs-line-strong);
  border-radius: 999px; padding: 5px 10px; white-space: normal; max-width: 100%;
  box-sizing: border-box; }
.obs-meter { margin-top: 14px; }
.obs-meter-row { display: grid; grid-template-columns: 92px minmax(0,1fr) 88px;
  gap: 10px; align-items: center; margin: 9px 0; font-size: .82rem; }
.obs-meter-row .track { height: 8px; border-radius: 999px; background: var(--obs-surface-3);
  overflow: hidden; outline: 1px solid var(--obs-line-strong); }
.obs-meter-row .track span { display: block; height: 100%; border-radius: inherit; }
.obs-meter-row .track.c0 span { background: var(--obs-teal); }
.obs-meter-row .track.c1 span { background: var(--obs-violet); }
.obs-meter-row .value { text-align: right; font-family: var(--obs-mono); color: var(--obs-ink); }
.obs-meter-row .value small { display: block; color: var(--obs-muted); font-size: .78rem;
  letter-spacing: .04em; text-transform: uppercase; }
.obs-footnote { color: var(--obs-muted); font-size: .85rem; line-height: 1.55; }
.obs-provenance { margin-top: 28px; padding-top: 18px; border-top: 1px solid var(--obs-line);
  display: flex; flex-wrap: wrap; gap: 10px 22px; align-items: center;
  justify-content: space-between; color: var(--obs-muted); font-size: .84rem; }
.obs-provenance a { color: var(--obs-ink-2); text-decoration-color: var(--obs-line-strong); }

/* Gradio chrome */
.gradio-container .main.app { padding: 0 !important; max-width: 100% !important; }
.gradio-container .main.app > .wrap, .gradio-container .main.app .contain {
  width: 100% !important; max-width: 100% !important; }
.gradio-container .tabs, .gradio-container .tab-wrapper { width: 100% !important; }
.gradio-container .tab-container { width: 100% !important; flex-wrap: nowrap !important;
  overflow-x: auto !important; }
.gradio-container .tab-container button { flex: 0 0 auto; white-space: nowrap; }
.gradio-container .block { background: transparent; border: 0; box-shadow: none;
  border-radius: 0; overflow: visible !important; }
.gradio-container .form { background: transparent; border: 0; gap: 14px; }
.gradio-container .padded { padding: 0 !important; }
.gradio-container .wrap { gap: 10px; }
.gradio-container .tabs { border: 0; background: transparent; }
.gradio-container .tab-nav { border-bottom: 1px solid var(--obs-line); gap: 2px;
  padding: 0; margin: 6px 0 26px; overflow-x: auto; scrollbar-width: thin; }
.gradio-container .tab-nav button, .gradio-container button[role="tab"] {
  font-family: var(--obs-mono); font-size: .84rem; letter-spacing: .07em;
  text-transform: uppercase; color: var(--obs-muted); background: transparent;
  border: 0; border-bottom: 2px solid transparent; border-radius: 0;
  padding: 12px 14px; min-height: 44px; height: auto; line-height: 1.5; white-space: nowrap; }
.gradio-container .tab-nav button:hover, .gradio-container button[role="tab"]:hover {
  color: var(--obs-ink); }
.gradio-container .tab-nav button.selected, .gradio-container button[role="tab"][aria-selected="true"] {
  color: var(--obs-ink); border-bottom-color: var(--obs-teal); }
.gradio-container .tabitem { padding: 0; background: transparent; border: 0; }
.gradio-container .gr-accordion {
  border: 1px solid var(--obs-line-strong) !important;
  border-radius: var(--obs-radius-sm); overflow: visible !important;
  background: var(--obs-surface-1); }
.gradio-container .gr-accordion > button.label-wrap {
  display: flex; align-items: center; justify-content: space-between; gap: 12px;
  box-sizing: border-box; width: 100%; min-height: 48px; height: auto;
  margin: 0; padding: 12px 16px !important; border: 0 !important;
  border-radius: 8px !important; text-align: left; }
.gradio-container .gr-accordion > button.label-wrap > span:first-child {
  min-width: 0; flex: 1; overflow-wrap: anywhere; line-height: 1.5; }
.gradio-container .gr-accordion > button.label-wrap > .icon {
  display: inline-flex; align-items: center; justify-content: center;
  flex: 0 0 20px; margin: 0; }
.gradio-container .gr-accordion > [data-testid="accordion-content"] {
  padding: 12px; }
.gradio-container .block-label, .gradio-container label > span, .gradio-container .label-wrap span {
  font-family: var(--obs-mono) !important; font-size: .8rem !important;
  letter-spacing: .06em; text-transform: uppercase; color: var(--obs-muted) !important; }
.gradio-container input[type="text"], .gradio-container input[type="number"],
.gradio-container input[type="email"], .gradio-container textarea,
.gradio-container .wrap-inner, .gradio-container select {
  background: var(--obs-surface-2) !important; color: var(--obs-ink) !important;
  border: 1px solid var(--obs-line-strong) !important; border-radius: 8px !important;
  font-family: var(--obs-ui); }
.gradio-container input[type="range"] { accent-color: var(--obs-teal); }
.gradio-container input[type="range"]::-webkit-slider-runnable-track {
  box-shadow: inset 0 0 0 1px var(--obs-line-strong); }
.gradio-container input[type="range"]::-moz-range-track {
  box-shadow: inset 0 0 0 1px var(--obs-line-strong); }
.gradio-container input[type="range"]::-webkit-slider-thumb {
  background: var(--obs-teal) !important; border-color: var(--obs-teal) !important; }
.gradio-container input[type="range"]::-moz-range-thumb {
  background: var(--obs-teal) !important; border-color: var(--obs-teal) !important; }
.gradio-container button { min-height: 44px; border-radius: 8px; font-family: var(--obs-ui);
  font-weight: 600; transition: background-color 160ms ease, border-color 160ms ease,
  color 160ms ease, transform 160ms ease; }
.gradio-container button.primary, .gradio-container button.lg.primary,
#predict-submit {
  background: var(--obs-teal) !important; background-color: var(--obs-teal) !important;
  background-image: none !important; color: var(--obs-on-accent) !important;
  border: 1px solid var(--obs-teal) !important; font-weight: 700; }
#predict-submit { min-height: 48px; }
.gradio-container button.primary:hover { background: var(--obs-teal-dim) !important; }
.gradio-container button.secondary { background: var(--obs-surface-2) !important;
  color: var(--obs-ink) !important; border: 1px solid var(--obs-line-strong) !important; }
.gradio-container button.secondary:hover { background: var(--obs-surface-3) !important; }
.gradio-container button:focus-visible, .gradio-container a:focus-visible,
.gradio-container input:focus-visible, .gradio-container select:focus-visible,
.gradio-container textarea:focus-visible, .obs-explorer button:focus-visible,
.obs-explorer [tabindex]:focus-visible {
  outline: 2px solid var(--obs-teal) !important; outline-offset: 2px !important; }
.gradio-container .table-wrap { border: 1px solid var(--obs-line) !important;
  border-radius: 10px !important; overflow: auto !important; max-height: 440px;
  background: var(--obs-surface-1) !important; }
.gradio-container table { font-size: .82rem !important; color: var(--obs-ink-2); }
.gradio-container thead th { background: var(--obs-surface-2) !important;
  color: var(--obs-muted) !important; font-family: var(--obs-mono) !important;
  font-size: .78rem !important; letter-spacing: .06em; text-transform: uppercase;
  position: sticky; top: 0; z-index: 1; }
.gradio-container tbody tr:nth-child(even) { background: var(--obs-surface-2); }
.gradio-container .plot-container { background: transparent; }
.gradio-container .forms, .gradio-container .panel { background: transparent; }
.gradio-container .gr-box { background: transparent; border: 0; }
.gradio-container .icon-button { background: transparent; }
#predict-form { background: var(--obs-surface-1); border: 1px solid var(--obs-line);
  border-radius: var(--obs-radius); padding: 20px; }
#predict-form .prose h3 { margin-top: 0; }
#predict-action { position: sticky; bottom: 8px; z-index: 4; background: var(--obs-bg);
  border-top: 1px solid var(--obs-line); padding: 12px 0 8px; }
#explorer-detail { min-width: 0; }
#research-overview { max-width: 100%; }
#research-overview > p { max-width: 78ch; }
/* Project-owned layout anchors; Gradio component internals are kept at the boundary. */
.obs-brandrow { display: grid !important; grid-template-columns: minmax(0, 1fr) auto auto;
  align-items: center !important; gap: var(--obs-space-4) !important; }
.obs-brandrow > :first-child { flex: 1 1 auto !important; min-width: 0 !important; }
#api-status { flex: 0 1 auto !important; min-width: 120px; }
.obs-api-status { display: flex; flex-wrap: wrap; align-items: center; gap: var(--obs-space-2); }
.obs-api-status .obs-note { max-width: 44ch; }
.obs-live.connecting::before { background: var(--obs-amber); box-shadow: none; }
#refresh-live { min-height: 44px; }
.obs-brandbar { border-bottom: 0; }
#primary-navigation { border-top: 1px solid var(--obs-line); }
#primary-navigation > .tab-wrapper .tab-container { background-image: none; }
#primary-navigation > .tab-wrapper .tab-container::after { display: none; }
#overview-hero { align-items: flex-start !important; gap: var(--obs-space-5) !important; margin-bottom: var(--obs-space-5); }
#overview-hero .obs-hero p { max-width: 38ch; }
#overview-hero .obs-nav-actions { gap: var(--obs-space-2) !important; }
.obs-nav-actions button { min-height: 44px; min-width: 0 !important; }
.obs-context { color: var(--obs-ink-2); font-size: .9rem; line-height: 1.6; }
.obs-context summary, .gradio-container details summary { cursor: pointer; min-height: 44px;
  padding: var(--obs-space-3) 0; color: var(--obs-ink-2); }
.obs-context p { margin: 0 0 var(--obs-space-3); }
.gradio-container summary:focus-visible { outline: 2px solid var(--obs-teal); outline-offset: 2px; }
.obs-context[open] { border-bottom: 1px solid var(--obs-line); }
#explorer-map-row { gap: var(--obs-space-4) !important; align-items: start; }
#explorer-inspector { min-width: 0; }
.obs-selected-track .obs-feature-grid { grid-template-columns: repeat(2,minmax(0,1fr)); }
.obs-selected-track .obs-feature dt { text-transform: none; letter-spacing: 0; overflow-wrap: anywhere; }
.obs-neighbors { display: block; overflow-x: auto; }
.obs-neighbors th, .obs-neighbors td { white-space: nowrap !important;
  overflow-wrap: normal !important; word-break: normal !important; }
.obs-table-hint { display: none; color: var(--obs-muted); font-size: .85rem; }
.gradio-container .obs-chart { padding-top: 32px !important; }
.obs-chart .modebar-container { top: -32px !important; }
#explorer-detail[data-selection="none"] .obs-selected-track { display: none; }
#explorer-detail[data-selection="pending"] .obs-selected-track { border-style: dashed; cursor: progress; }
#prediction-result { scroll-margin-top: var(--obs-space-5); }
#prediction-result[aria-busy="true"] { cursor: progress; }
#prediction-result[aria-busy="true"] .obs-card { border-style: dashed; }
#predict-form input[type="number"] { min-width: 84px; min-height: 44px; font-size: 1rem; }
#predict-form .tab-like-container {
  display: flex; align-items: stretch; min-height: 44px; height: auto;
  overflow: visible; border-radius: 8px; }
#predict-form .tab-like-container input[type="number"] {
  height: 44px; line-height: 1.4; box-sizing: border-box;
  border: 0 !important; border-radius: 8px 0 0 8px !important; }
#predict-form .tab-like-container button { margin: 0; border-radius: 0 8px 8px 0; }
#predict-form .gr-accordion .form { overflow: visible; border-radius: 0; }
#predict-form input[type="number"]::-webkit-inner-spin-button { margin-left: 8px; }
#research-overview h2 { font-family: var(--obs-display); font-size: clamp(1.6rem,2.4vw,2rem); }
.obs-research-layer { margin: var(--obs-space-5) 0; border: 1px solid var(--obs-line);
  border-radius: var(--obs-radius); padding: 0 var(--obs-space-4); }
.obs-research-layer > summary { font-family: var(--obs-display); font-size: 1.35rem; }
.obs-research-layer .obs-section { margin: var(--obs-space-4) 0; }
.obs-card, .obs-context summary, button, details summary { transition: border-color var(--obs-duration) var(--obs-ease),
  background-color var(--obs-duration) var(--obs-ease), color var(--obs-duration) var(--obs-ease); }
.gradio-container .prose h2:first-child { margin-top: var(--obs-space-4); }
@media (max-width: 1024px) {
  .obs-grid-2 { grid-template-columns: 1fr; }
  .obs-grid-3 { grid-template-columns: 1fr 1fr; }
  .gradio-container { padding: 0 18px 56px; }
}
@media (max-width: 900px) {
  #overview-hero, #overview-grid, #explorer-map-row, #predict-grid {
    flex-direction: column !important; gap: 16px !important; }
  #overview-hero > *, #overview-grid > *, #explorer-map-row > *, #predict-grid > * {
    width: 100% !important; min-width: 0 !important; }
  .obs-fact dt { white-space: nowrap; }
  .obs-fact dd { text-align: right; }
}
@media (max-width: 768px) {
  .gradio-container { padding: 0 14px 48px !important; font-size: 15px; }
  .obs-hero { padding-top: 28px; }
  #overview-hero .obs-hero { padding: 8px 0 0; }
  #overview-hero { gap: 12px !important; }
  #overview-hero > .column { gap: 8px !important; }
  #overview-hero .obs-kicker { display: none; }
  #overview-hero .obs-nav-actions button { font-size: .82rem; padding: 8px; }
  #overview-hero .obs-nav-actions { display: grid !important; grid-template-columns: 3fr 2fr; }
  #overview-hero .obs-context { margin: 0; }
  #overview-hero .obs-hero-meta { margin-top: 8px; }
  .obs-brand-name { white-space: nowrap; font-size: .9rem; letter-spacing: .02em; }
  .obs-brand-sub { font-size: .75rem; letter-spacing: .04em; }
  .obs-brand-mark { width: 28px; height: 28px; }
  .obs-brandrow { display: grid !important; grid-template-columns: 1fr auto; gap: 4px 8px !important; }
  .obs-brandrow > :first-child { grid-column: 1 / -1; }
  .obs-brandbar { padding: 12px 0 4px; border: 0; }
  #api-status { min-width: 0 !important; }
  #refresh-live { min-width: 0 !important; width: auto !important; padding: 8px 12px; }
  #primary-navigation > .tab-wrapper .tab-container { display: grid !important;
    grid-template-columns: repeat(2, minmax(0, 1fr)); overflow: visible !important; }
  #primary-navigation button[role="tab"] { white-space: normal; font-family: var(--obs-ui);
    font-size: .82rem; text-transform: none; letter-spacing: 0; padding: 4px 8px;
    line-height: 1.25; height: auto !important; width: 100%; }
  .obs-grid-3 { grid-template-columns: 1fr; }
  .obs-table-hint { display: block; }
  .obs-table .table-wrap { overflow-x: scroll !important; scrollbar-width: thin;
    scrollbar-color: var(--obs-line-strong) var(--obs-surface-1); }
  .obs-selected-track .obs-feature-grid { grid-template-columns: 1fr; }
  .obs-selected-track .obs-feature { display: flex; align-items: baseline;
    justify-content: space-between; gap: 8px; }
  .obs-selected-track .obs-feature dd { margin: 0; }
  .obs-selected-track .obs-neighbors thead { position: absolute; width: 1px;
    height: 1px; clip-path: inset(50%); overflow: hidden; }
  .obs-selected-track .obs-neighbors tbody { display: block; }
  .obs-selected-track .obs-neighbors tr { display: grid;
    grid-template-columns: 1fr 1fr; gap: 8px; padding: 12px 0;
    border-bottom: 1px solid var(--obs-line); }
  .obs-selected-track .obs-neighbors td { display: block; border: 0;
    padding: 0; white-space: normal !important; }
  .obs-selected-track .obs-neighbors td:first-child { grid-column: 1 / -1; }
  .obs-selected-track .obs-neighbors td::before { content: attr(data-label);
    display: block; font-size: .78rem; color: var(--obs-muted); }
  .obs-provenance a { display: inline-flex; align-items: center; min-height: 44px; }
  .obs-feature-grid { grid-template-columns: 1fr 1fr; }
  .obs-card { padding: 16px; }
  .obs-section { margin-top: 32px; }
  .gradio-container .tab-nav { margin-bottom: 18px; }
  .gradio-container .tab-nav button { padding: 10px 10px; font-size: .8rem; }
  .obs-meter-row { grid-template-columns: 76px minmax(0,1fr) 80px; }
}
@media (max-width: 420px) {
  .obs-feature-grid { grid-template-columns: 1fr; }
  .obs-hero-meta .obs-tag { font-size: .78rem; }
}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation-duration: .001ms !important;
    animation-iteration-count: 1 !important; transition-duration: .001ms !important;
    scroll-behavior: auto !important; }
}
"""

CSS = ":root { " + css_tokens() + "; }\n" + CSS
