# ruff: noqa: E501  (long CSS declarations)
"""Acoustic Observatory design tokens, Gradio theme and application CSS."""

from __future__ import annotations

import gradio as gr

TOKENS = {
    "bg": "#080d0f",
    "surface_1": "#0e1719",
    "surface_2": "#132326",
    "surface_3": "#193033",
    "ink": "#eef7f4",
    "ink_2": "#c4d6d2",
    "muted": "#8ba39e",
    "line": "#22383a",
    "line_strong": "#35565a",
    "teal": "#5eead4",
    "teal_dim": "#2dd4bf",
    "violet": "#b7a4ff",
    "amber": "#f5c76a",
    "danger": "#ff9b9b",
    "success": "#6ee7b7",
    "cluster_0": "#5eead4",
    "cluster_1": "#b7a4ff",
}
CLUSTER_COLORS = {0: TOKENS["cluster_0"], 1: TOKENS["cluster_1"]}
CLUSTER_SYMBOLS = {0: "circle", 1: "diamond"}
CLUSTER_NAMES = {0: "Cluster 0", 1: "Cluster 1"}


def theme() -> gr.Theme:
    return gr.themes.Base(
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
    ).set(
        body_background_fill=TOKENS["bg"],
        body_background_fill_dark=TOKENS["bg"],
        body_text_color=TOKENS["ink"],
        body_text_color_dark=TOKENS["ink"],
        body_text_color_subdued=TOKENS["ink_2"],
        body_text_color_subdued_dark=TOKENS["ink_2"],
        background_fill_primary=TOKENS["bg"],
        background_fill_primary_dark=TOKENS["bg"],
        background_fill_secondary=TOKENS["surface_1"],
        background_fill_secondary_dark=TOKENS["surface_1"],
        block_background_fill=TOKENS["surface_1"],
        block_background_fill_dark=TOKENS["surface_1"],
        block_border_color=TOKENS["line"],
        block_border_color_dark=TOKENS["line"],
        block_border_width="1px",
        block_radius="14px",
        panel_background_fill=TOKENS["surface_1"],
        panel_background_fill_dark=TOKENS["surface_1"],
        panel_border_color=TOKENS["line"],
        panel_border_color_dark=TOKENS["line"],
        input_background_fill=TOKENS["surface_2"],
        input_background_fill_dark=TOKENS["surface_2"],
        input_border_color=TOKENS["line_strong"],
        input_border_color_dark=TOKENS["line_strong"],
        input_border_color_focus=TOKENS["teal"],
        input_border_color_focus_dark=TOKENS["teal"],
        input_placeholder_color=TOKENS["muted"],
        input_placeholder_color_dark=TOKENS["muted"],
        button_primary_background_fill=TOKENS["teal"],
        button_primary_background_fill_dark=TOKENS["teal"],
        button_primary_background_fill_hover=TOKENS["teal_dim"],
        button_primary_background_fill_hover_dark=TOKENS["teal_dim"],
        button_primary_text_color="#04110f",
        button_primary_text_color_dark="#04110f",
        button_secondary_background_fill=TOKENS["surface_2"],
        button_secondary_background_fill_dark=TOKENS["surface_2"],
        button_secondary_background_fill_hover=TOKENS["surface_3"],
        button_secondary_background_fill_hover_dark=TOKENS["surface_3"],
        button_secondary_text_color=TOKENS["ink"],
        button_secondary_text_color_dark=TOKENS["ink"],
        button_secondary_border_color=TOKENS["line_strong"],
        button_secondary_border_color_dark=TOKENS["line_strong"],
        checkbox_background_color_selected=TOKENS["teal"],
        checkbox_background_color_selected_dark=TOKENS["teal"],
        slider_color=TOKENS["teal"],
        slider_color_dark=TOKENS["teal"],
        color_accent=TOKENS["teal"],
        color_accent_soft=TOKENS["surface_3"],
        link_text_color=TOKENS["teal"],
        link_text_color_hover=TOKENS["ink"],
        link_text_color_visited=TOKENS["violet"],
        table_border_color=TOKENS["line"],
        table_even_background_fill=TOKENS["surface_1"],
        table_odd_background_fill=TOKENS["surface_2"],
        code_background_fill=TOKENS["surface_3"],
        code_background_fill_dark=TOKENS["surface_3"],
        border_color_primary=TOKENS["line"],
        border_color_primary_dark=TOKENS["line"],
        loader_color=TOKENS["teal"],
        loader_color_dark=TOKENS["teal"],
        shadow_drop="0 1px 2px rgba(0,0,0,.35)",
        shadow_drop_lg="0 18px 48px rgba(0,0,0,.35)",
        block_shadow="none",
    )


CSS = """
:root { color-scheme: dark; --obs-display: "Iowan Old Style", "Palatino Linotype",
  "Book Antiqua", Palatino, Georgia, serif;
  --obs-ui: "Inter", "Segoe UI Variable", "Segoe UI", system-ui, -apple-system, sans-serif;
  --obs-mono: "JetBrains Mono", "Cascadia Code", "SFMono-Regular", Consolas, monospace; }
html, body { background: #080d0f !important; }
body { margin: 0; }
/* The app shell owns width and rhythm so every view shares one grid. */
.gradio-container {
  --obs-bg: #080d0f; --obs-surface-1: #0e1719; --obs-surface-2: #132326;
  --obs-surface-3: #193033; --obs-ink: #eef7f4; --obs-ink-2: #c4d6d2;
  --obs-muted: #8ba39e; --obs-line: #22383a; --obs-line-strong: #35565a;
  --obs-teal: #5eead4; --obs-violet: #b7a4ff; --obs-amber: #f5c76a;
  --obs-danger: #ff9b9b; --obs-radius: 14px; --obs-radius-sm: 9px;
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
  letter-spacing: .16em; text-transform: uppercase; color: var(--obs-ink); }
.obs-brand-sub { font-family: var(--obs-mono); font-size: .68rem; color: var(--obs-muted);
  letter-spacing: .12em; text-transform: uppercase; }
.obs-brand-right { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.obs-live { display: inline-flex; align-items: center; gap: 8px; padding: 6px 11px;
  border: 1px solid var(--obs-line-strong); border-radius: 999px;
  font-family: var(--obs-mono); font-size: .7rem; letter-spacing: .06em;
  color: var(--obs-ink-2); background: var(--obs-surface-1); }
.obs-live::before { content: ""; width: 7px; height: 7px; border-radius: 50%;
  background: var(--obs-teal); box-shadow: 0 0 0 3px rgba(94,234,212,.12); }
.obs-live.offline::before { background: var(--obs-danger); box-shadow: none; }
.obs-hero { position: relative; padding: clamp(28px, 4.5vw, 58px) 0 28px; }
.obs-hero::before { content: ""; position: absolute; inset: 0 -24px auto; height: 420px;
  pointer-events: none; background:
    radial-gradient(720px 260px at 18% 0%, rgba(94,234,212,.08), transparent 70%),
    radial-gradient(620px 240px at 82% 10%, rgba(183,164,255,.07), transparent 72%);
  opacity: .9; z-index: 0; }
.obs-hero > * { position: relative; z-index: 1; }
.obs-kicker { display: inline-block; font-family: var(--obs-mono); font-size: .7rem;
  letter-spacing: .2em; text-transform: uppercase; color: var(--obs-teal); }
.obs-hero h1 { font-family: var(--obs-display); font-weight: 500;
  font-size: clamp(2.7rem, 5.6vw, 4.9rem); line-height: 1.0; letter-spacing: -.025em;
  margin: .22em 0 .28em; color: var(--obs-ink); max-width: 22ch; }
.obs-hero p { max-width: 68ch; margin: 0; color: var(--obs-ink-2);
  font-size: clamp(1rem, 1.25vw, 1.16rem); }
.obs-hero-meta { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 22px; }
.obs-tag { display: inline-flex; align-items: center; gap: 7px; padding: 5px 10px;
  border: 1px solid var(--obs-line); border-radius: 999px; background: var(--obs-surface-1);
  font-family: var(--obs-mono); font-size: .69rem; color: var(--obs-muted); }
.obs-tag strong { color: var(--obs-ink-2); font-weight: 500; }
.obs-caveat { margin: 20px 0 0; padding: 12px 15px; border-left: 2px solid var(--obs-amber);
  background: var(--obs-surface-1); border-radius: 0 var(--obs-radius-sm) var(--obs-radius-sm) 0;
  color: var(--obs-ink-2); font-size: .88rem; max-width: 90ch; }
.obs-caveat strong { color: var(--obs-amber); font-weight: 600; }

/* Cards, grids and type rhythm */
.obs-card { background: var(--obs-surface-1); border: 1px solid var(--obs-line);
  border-radius: var(--obs-radius); padding: 20px; min-width: 0; }
.obs-card.tight { padding: 16px; }
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
.obs-fact dt { font-family: var(--obs-mono); font-size: .7rem; letter-spacing: .08em;
  text-transform: uppercase; color: var(--obs-muted); }
.obs-fact dd { margin: 0; font-size: .9rem; color: var(--obs-ink); text-align: right;
  overflow-wrap: anywhere; }
.obs-finding { position: relative; overflow: hidden; }
.obs-finding::after { content: ""; position: absolute; right: -40px; top: -50px;
  width: 150px; height: 150px; border-radius: 50%;
  background: radial-gradient(circle, rgba(245,199,106,.14), transparent 68%); }
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
.obs-entry-link { font-family: var(--obs-mono); font-size: .72rem; letter-spacing: .06em;
  text-transform: uppercase; color: var(--obs-teal); }
.obs-empty { border: 1px dashed var(--obs-line-strong); border-radius: var(--obs-radius);
  padding: 28px 20px; color: var(--obs-muted); text-align: center; background:
  var(--obs-surface-1); }
.obs-empty strong { color: var(--obs-ink); display: block; margin-bottom: 6px; }
.obs-badge { display: inline-flex; align-items: center; gap: 7px; padding: 4px 9px;
  border-radius: 999px; border: 1px solid var(--obs-line-strong);
  font-family: var(--obs-mono); font-size: .68rem; color: var(--obs-ink-2); }
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
.obs-feature dt { font-family: var(--obs-mono); font-size: .64rem; color: var(--obs-muted);
  letter-spacing: .06em; text-transform: uppercase; }
.obs-feature dd { margin: 3px 0 0; font-size: .92rem; color: var(--obs-ink);
  font-variant-numeric: tabular-nums; overflow-wrap: anywhere; }
.obs-neighbors { width: 100%; border-collapse: collapse; font-size: .8rem; }
.obs-neighbors th { text-align: left; font-family: var(--obs-mono); font-size: .64rem;
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
.obs-verdict { font-family: var(--obs-mono); font-size: .68rem; letter-spacing: .08em;
  text-transform: uppercase; color: var(--obs-ink-2); border: 1px solid var(--obs-line-strong);
  border-radius: 999px; padding: 5px 10px; white-space: nowrap; }
.obs-meter { margin-top: 14px; }
.obs-meter-row { display: grid; grid-template-columns: 92px minmax(0,1fr) 88px;
  gap: 10px; align-items: center; margin: 9px 0; font-size: .82rem; }
.obs-meter-row .track { height: 8px; border-radius: 999px; background: var(--obs-surface-3);
  overflow: hidden; }
.obs-meter-row .track span { display: block; height: 100%; border-radius: inherit; }
.obs-meter-row .track.c0 span { background: var(--obs-teal); }
.obs-meter-row .track.c1 span { background: var(--obs-violet); }
.obs-meter-row .value { text-align: right; font-family: var(--obs-mono); color: var(--obs-ink); }
.obs-meter-row .value small { display: block; color: var(--obs-muted); font-size: .64rem;
  letter-spacing: .04em; text-transform: uppercase; }
.obs-footnote { color: var(--obs-muted); font-size: .76rem; line-height: 1.55; }
.obs-provenance { margin-top: 28px; padding-top: 18px; border-top: 1px solid var(--obs-line);
  display: flex; flex-wrap: wrap; gap: 10px 22px; align-items: center;
  justify-content: space-between; color: var(--obs-muted); font-size: .74rem; }
.obs-provenance a { color: var(--obs-ink-2); text-decoration-color: var(--obs-line-strong); }

/* Gradio chrome */
.gradio-container .main.app { padding: 0 !important; max-width: 100% !important; }
.gradio-container .main.app > .wrap, .gradio-container .main.app .contain {
  width: 100% !important; max-width: 100% !important; }
.gradio-container .tabs, .gradio-container .tab-wrapper { width: 100% !important; }
.gradio-container .tab-container { width: 100% !important; flex-wrap: nowrap !important;
  overflow-x: auto !important; }
.gradio-container .tab-container button { flex: 0 0 auto; white-space: nowrap; }
.gradio-container .block { background: transparent; border: 0; box-shadow: none; }
.gradio-container .form { background: transparent; border: 0; gap: 14px; }
.gradio-container .padded { padding: 0 !important; }
.gradio-container .wrap { gap: 10px; }
.gradio-container .tabs { border: 0; background: transparent; }
.gradio-container .tab-nav { border-bottom: 1px solid var(--obs-line); gap: 2px;
  padding: 0; margin: 6px 0 26px; overflow-x: auto; scrollbar-width: thin; }
.gradio-container .tab-nav button, .gradio-container button[role="tab"] {
  font-family: var(--obs-mono); font-size: .74rem; letter-spacing: .07em;
  text-transform: uppercase; color: var(--obs-muted); background: transparent;
  border: 0; border-bottom: 2px solid transparent; border-radius: 0;
  padding: 12px 14px; min-height: 44px; white-space: nowrap; }
.gradio-container .tab-nav button:hover, .gradio-container button[role="tab"]:hover {
  color: var(--obs-ink); }
.gradio-container .tab-nav button.selected, .gradio-container button[role="tab"][aria-selected="true"] {
  color: var(--obs-ink); border-bottom-color: var(--obs-teal); }
.gradio-container .tabitem { padding: 0; background: transparent; border: 0; }
.gradio-container .label-wrap { border-radius: 9px; }
.gradio-container .block-label, .gradio-container label > span, .gradio-container .label-wrap span {
  font-family: var(--obs-mono) !important; font-size: .68rem !important;
  letter-spacing: .06em; text-transform: uppercase; color: var(--obs-muted) !important; }
.gradio-container input[type="text"], .gradio-container input[type="number"],
.gradio-container input[type="email"], .gradio-container textarea,
.gradio-container .wrap-inner, .gradio-container select {
  background: var(--obs-surface-2) !important; color: var(--obs-ink) !important;
  border: 1px solid var(--obs-line-strong) !important; border-radius: 8px !important;
  font-family: var(--obs-ui); }
.gradio-container input[type="range"] { accent-color: var(--obs-teal); }
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
  background-image: none !important; color: #04110f !important;
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
  font-size: .64rem !important; letter-spacing: .06em; text-transform: uppercase;
  position: sticky; top: 0; z-index: 1; }
.gradio-container tbody tr:nth-child(even) { background: rgba(255,255,255,.02); }
.gradio-container .plot-container { background: transparent; }
.gradio-container .forms, .gradio-container .panel { background: transparent; }
.gradio-container .gr-box { background: transparent; border: 0; }
.gradio-container .icon-button { background: transparent; }
#predict-form { background: var(--obs-surface-1); border: 1px solid var(--obs-line);
  border-radius: var(--obs-radius); padding: 20px; }
#predict-form .prose h3 { margin-top: 0; }
#predict-action { position: sticky; bottom: 8px; z-index: 4; background: var(--obs-bg);
  border-top: 1px solid var(--obs-line); padding: 12px 0 8px; }
#explorer-detail { min-height: 132px; }
#research-overview { max-width: 100%; }
#research-overview > p { max-width: 78ch; }
@media (max-width: 1024px) {
  .obs-grid-2 { grid-template-columns: 1fr; }
  .obs-grid-3 { grid-template-columns: 1fr 1fr; }
  .gradio-container { padding: 0 18px 56px; }
}
@media (max-width: 900px) {
  #overview-grid, #explorer-panels, #predict-grid {
    flex-direction: column !important; gap: 16px !important; }
  #overview-grid > *, #explorer-panels > *, #predict-grid > * {
    width: 100% !important; min-width: 0 !important; }
  .obs-fact dt { white-space: nowrap; }
  .obs-fact dd { text-align: right; }
}
@media (max-width: 768px) {
  .gradio-container { padding: 0 14px 48px !important; font-size: 15px; }
  .obs-hero { padding-top: 28px; }
  .obs-brandrow { flex-direction: column !important; align-items: stretch !important;
    gap: 10px !important; }
  .obs-brandrow > * { width: 100% !important; min-width: 0 !important; }
  .obs-brandrow button { width: 100% !important; }
  .obs-brandbar { padding: 14px 0; flex-direction: column; align-items: flex-start;
    gap: 10px; }
  .obs-brand { width: 100%; }
  .obs-brand > div { min-width: 0; }
  .obs-brand-name { white-space: nowrap; font-size: .92rem; letter-spacing: .1em; }
  .obs-brand-right { width: 100%; }
  .obs-live, .obs-tag { font-size: .64rem; }
  .gradio-container .tab-nav { flex-wrap: nowrap !important; overflow-x: auto !important; }
  .gradio-container .tab-nav button { flex: 0 0 auto; }
  .obs-grid-3 { grid-template-columns: 1fr; }
  .obs-feature-grid { grid-template-columns: 1fr 1fr; }
  .obs-card { padding: 16px; }
  .obs-section { margin-top: 32px; }
  .gradio-container .tab-nav { margin-bottom: 18px; }
  .gradio-container .tab-nav button { padding: 10px 10px; font-size: .68rem; }
  .obs-meter-row { grid-template-columns: 76px minmax(0,1fr) 80px; }
}
@media (max-width: 420px) {
  .obs-feature-grid { grid-template-columns: 1fr; }
  .obs-hero-meta .obs-tag { font-size: .64rem; }
}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation-duration: .001ms !important;
    animation-iteration-count: 1 !important; transition-duration: .001ms !important;
    scroll-behavior: auto !important; }
}
"""
