# ruff: noqa: E501  (embedded HTML/JS)
"""Custom Gradio HTML component for the verified PCA cluster space."""

from __future__ import annotations

import json

import gradio as gr

from .assets import constellation_url, plotly_head, register_assets
from .theme import TOKENS

TEMPLATE = """
<div class="obs-explorer" data-compact="{{compact}}" data-constellation-url="{{constellation_url}}">
  <div class="obs-explorer-head">
    <div class="obs-explorer-title">
      <span class="obs-explorer-kicker">PCA cluster space</span>
      <strong class="obs-explorer-heading">Acoustic map</strong>
    </div>
    <div class="obs-toolbar" role="toolbar" aria-label="Cluster space controls">
      <div class="obs-seg" role="group" aria-label="Projection view">
        <button type="button" data-view="2d" aria-pressed="true">PCA 2D</button>
        <button type="button" data-view="3d" aria-pressed="false">PCA 3D</button>
        <button type="button" data-view="density" aria-pressed="false">Density</button>
        <button type="button" data-view="constellation" aria-pressed="false">Constellation</button>
      </div>
      <div class="obs-chips" role="group" aria-label="Cluster filter">
        <button type="button" data-cluster="all" aria-pressed="true">Both</button>
        <button type="button" data-cluster="0" aria-pressed="false"><span class="obs-swatch c0"></span>Cluster 0</button>
        <button type="button" data-cluster="1" aria-pressed="false"><span class="obs-swatch c1"></span>Cluster 1</button>
      </div>
      <button type="button" class="obs-reset" data-action="reset">Reset view</button>
    </div>
  </div>
  <button type="button" class="obs-touch-toggle obs-reset" data-action="touch" hidden>Enable rotation</button>
  <div class="obs-plot" data-role="plot" role="img" aria-label="Interactive PCA projection of sampled training tracks"></div>
  <div class="obs-constellation" data-role="constellation" hidden>
    <div class="obs-constellation-tip" data-role="tip" hidden></div>
  </div>
  <div class="obs-explorer-foot">
    <p class="obs-caption" data-role="caption">Refresh live data to load the verified projection.</p>
    <p class="obs-status" data-role="status" role="status" aria-live="polite"></p>
    <form class="obs-sample-picker" data-role="sample-picker" hidden>
      <label>Sample number <input type="number" min="0" step="1" required aria-label="Sample number (zero-based)"></label>
      <button type="submit" class="obs-reset">Inspect sample</button>
    </form>
  </div>
</div>
"""

CSS = """
.obs-explorer { background: var(--obs-surface-1, __OBS_SURFACE_1__);
  container-type: inline-size;
  border: 1px solid var(--obs-line, __OBS_LINE__); border-radius: 14px; overflow: hidden;
  color: var(--obs-ink, __OBS_INK__); }
.obs-explorer-head { display: flex; align-items: flex-start; justify-content: space-between;
  gap: 14px; flex-wrap: wrap; padding: 16px 18px 14px;
  border-bottom: 1px solid var(--obs-line, __OBS_LINE__); }
.obs-explorer-title { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.obs-explorer-kicker { font-family: var(--obs-mono, monospace); font-size: .8rem;
  letter-spacing: .16em; text-transform: uppercase; color: var(--obs-muted, __OBS_MUTED__); }
.obs-explorer-heading { font-family: var(--obs-display, Georgia, serif); font-size: 1.28rem;
  font-weight: 500; letter-spacing: -.01em; color: var(--obs-ink, __OBS_INK__); }
.obs-toolbar { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1.3fr);
  align-items: start; gap: 10px; width: 100%; min-width: 0; }
.obs-toolbar > .obs-reset { grid-column: 1 / -1; justify-self: start; }
.obs-explorer:not(.is-compact) .obs-seg {
  grid-auto-flow: row; grid-template-columns: repeat(2, minmax(0, 1fr)); }
.obs-seg, .obs-chips { display: grid; grid-auto-flow: column; grid-auto-columns: 1fr;
  align-items: stretch; gap: 4px; padding: 4px; max-width: 100%; min-width: 0; width: 100%;
  background: var(--obs-surface-2, __OBS_SURFACE_2__); border: 1px solid var(--obs-line, __OBS_LINE__);
  border-radius: 12px; }
.obs-seg button, .obs-chips button { appearance: none; border: 0; background: transparent;
  white-space: nowrap;
  color: var(--obs-muted, __OBS_MUTED__); font-family: var(--obs-mono, monospace);
  font-size: .82rem; letter-spacing: .04em; border-radius: 8px; padding: 8px 11px;
  margin: 0; box-sizing: border-box; line-height: 1.4; justify-content: center;
  min-height: 44px; cursor: pointer; display: inline-flex; align-items: center; gap: 6px;
  transition: background-color 160ms ease, color 160ms ease; }
.obs-seg button:hover, .obs-chips button:hover { color: var(--obs-ink, __OBS_INK__); }
.obs-seg button[aria-pressed="true"], .obs-chips button[aria-pressed="true"] {
  background: var(--obs-surface-3, __OBS_SURFACE_3__); color: var(--obs-ink, __OBS_INK__); }
.obs-seg button:disabled, .obs-chips button:disabled { color: var(--obs-muted, __OBS_MUTED__); background: transparent; text-decoration: line-through; cursor: not-allowed; opacity: 1; }
.obs-chips button:focus-visible, .obs-seg button:focus-visible, .obs-reset:focus-visible {
  outline: 2px solid var(--obs-teal, __OBS_TEAL__); outline-offset: 2px; }
.obs-swatch { width: 8px; height: 8px; border-radius: 2px; display: inline-block; }
.obs-swatch.c0 { background: var(--obs-teal, __OBS_TEAL__); }
.obs-swatch.c1 { background: var(--obs-violet, __OBS_VIOLET__); }
.obs-reset { appearance: none; border: 1px solid var(--obs-line-strong, __OBS_LINE_STRONG__);
  background: transparent; color: var(--obs-ink-2, __OBS_INK_2__);
  font-family: var(--obs-mono, monospace); font-size: .82rem; border-radius: 8px;
  padding: 8px 11px; min-height: 44px; cursor: pointer; }
.obs-reset:hover { background: var(--obs-surface-2, __OBS_SURFACE_2__); color: var(--obs-ink, __OBS_INK__); }
.obs-reset[hidden] { display: none; }
.obs-sample-picker { display: flex; align-items: end; flex-wrap: wrap; gap: 8px; width: 100%; }
.obs-sample-picker[hidden] { display: none; }
.obs-sample-picker label { font-size: .85rem; color: var(--obs-ink-2, __OBS_INK_2__); }
.obs-sample-picker input { display: block; width: 120px; min-height: 44px;
  background: var(--obs-surface-2, __OBS_SURFACE_2__); color: var(--obs-ink, __OBS_INK__);
  border: 1px solid var(--obs-line-strong, __OBS_LINE_STRONG__); border-radius: 8px; padding: 8px; }
.obs-sample-picker input:focus-visible { outline: 2px solid var(--obs-teal, __OBS_TEAL__); }
.obs-touch-toggle { margin: 8px 14px; }
.obs-explorer.is-touch-locked .obs-plot,
.obs-explorer.is-touch-locked .obs-constellation { pointer-events: none; touch-action: pan-y; }
.obs-plot { width: 100%; height: clamp(340px, 54vh, 560px); min-height: 280px; }
.obs-constellation { position: relative; width: 100%; height: clamp(340px, 54vh, 560px);
  min-height: 280px; }
.obs-constellation[hidden], .obs-constellation-tip[hidden] { display: none; }
.obs-constellation-canvas { display: block; width: 100%; height: 100%;
  touch-action: none; cursor: grab; }
.obs-constellation-tip { position: absolute; z-index: 2; pointer-events: none;
  max-width: 220px; padding: 7px 9px; border-radius: 8px; border: 1px solid var(--obs-line-strong, __OBS_LINE_STRONG__);
  background: var(--obs-surface-3, __OBS_SURFACE_3__); color: var(--obs-ink, __OBS_INK__);
  font-family: var(--obs-mono, monospace); font-size: .8rem; line-height: 1.5;
  box-shadow: 0 6px 18px rgba(23,33,43,.10); }
.obs-explorer.is-constellation .obs-plot { display: none; }
.obs-explorer.is-compact [data-view="constellation"] { display: none; }
.obs-explorer.is-compact .obs-plot { height: clamp(280px, 40vh, 400px); }
.obs-explorer.is-compact .obs-constellation { height: clamp(280px, 40vh, 400px); }
.obs-explorer.is-compact .obs-explorer-head { padding: 13px 15px 12px; }
.obs-explorer.is-compact .obs-explorer-heading { font-size: 1.1rem; }
.obs-explorer.is-compact .modebar-container { display: none; }
.obs-explorer:not(.is-compact) .obs-plot { margin-top: 32px; }
.obs-explorer:not(.is-compact) .obs-plot .modebar-container { top: -32px !important; }
.obs-explorer-foot { display: flex; align-items: flex-start; justify-content: space-between;
  gap: 10px 18px; flex-wrap: wrap; padding: 11px 18px 13px;
  border-top: 1px solid var(--obs-line, __OBS_LINE__); }
@media (pointer: coarse) {
  .obs-plot, .obs-plot .main-svg, .obs-plot .draglayer, .obs-plot .nsewdrag {
    touch-action: pan-y !important;
  }
  .obs-explorer.is-touch-enabled .obs-plot,
  .obs-explorer.is-touch-enabled .obs-plot .main-svg,
  .obs-explorer.is-touch-enabled .obs-plot .draglayer,
  .obs-explorer.is-touch-enabled .obs-plot .nsewdrag {
    touch-action: none !important;
  }
}
.obs-caption, .obs-status { margin: 0; font-size: .85rem; line-height: 1.5; }
.obs-caption { color: var(--obs-muted, __OBS_MUTED__); max-width: 76ch; }
.obs-status { color: var(--obs-ink-2, __OBS_INK_2__); font-family: var(--obs-mono, monospace);
  font-size: .82rem; }
.obs-empty { display: flex; align-items: center; justify-content: center; height: 100%;
  min-height: 240px; padding: 24px; text-align: center; color: var(--obs-muted, __OBS_MUTED__);
  font-size: .86rem; }
@container (max-width: 600px) {
  .obs-toolbar { grid-template-columns: minmax(0, 1fr); }
}
@media (max-width: 640px) {
  .obs-explorer-head { padding: 13px 14px; }
  .obs-toolbar { width: 100%; }
  .obs-toolbar { grid-template-columns: minmax(0, 1fr); }
  .obs-seg, .obs-chips { flex: 1 1 auto; }
  .obs-chips button, .obs-seg button { padding: 7px 8px; font-size: .78rem; }
  .obs-reset { width: auto; }
  .obs-toolbar { gap: 8px; }
  .obs-seg { width: 100%; grid-auto-flow: row; grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .obs-explorer.is-compact .obs-seg { grid-template-columns: repeat(3, minmax(0, 1fr)); }
  .obs-chips { border-radius: 12px; }
  .obs-explorer.is-compact .obs-chips { display: none; }
  .obs-plot { height: 340px; }
  .obs-explorer-foot { padding: 10px 14px 12px; }
}
@media (prefers-reduced-motion: reduce) {
  .obs-explorer *, .obs-explorer *::before, .obs-explorer *::after {
    transition-duration: .001ms !important; animation-duration: .001ms !important; }
}
"""

JS = r"""
(() => {
  const root = element.querySelector('.obs-explorer');
  if (!root) return;
  const plot = root.querySelector('[data-role="plot"]');
  const caption = root.querySelector('[data-role="caption"]');
  const status = root.querySelector('[data-role="status"]');
  const viewButtons = Array.from(root.querySelectorAll('[data-view]'));
  const clusterButtons = Array.from(root.querySelectorAll('[data-cluster]'));
  const resetButton = root.querySelector('[data-action="reset"]');
  const touchButton = root.querySelector('[data-action="touch"]');
  const samplePicker = root.querySelector('[data-role="sample-picker"]');
  const sampleInput = samplePicker.querySelector('input');
  const coarsePointer = matchMedia('(pointer: coarse)').matches;
  let touchEnabled = false;
  const constellationHost = root.querySelector('[data-role="constellation"]');
  const tip = root.querySelector('[data-role="tip"]');
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  let constellation = null;
  let constellationLoading = null;
  const compact = (root.dataset.compact || '').toLowerCase() === 'true';
  const constellationUrl = root.dataset.constellationUrl || '';
  if (compact) root.classList.add('is-compact');
  if (resetButton) resetButton.hidden = compact;
  const PALETTE = __OBS_PALETTE__;
  const COLORS = {0: PALETTE.cluster_0, 1: PALETTE.cluster_1};
  const INK = PALETTE.ink;
  const MUTED = PALETTE.muted;
  const LINE = PALETTE.line;
  const SURFACE = PALETTE.surface_1;
  const nf = new Intl.NumberFormat();
  const WEBGL = (() => {
    try {
      const probe = document.createElement('canvas');
      return Boolean(probe.getContext('webgl2') || probe.getContext('webgl'));
    } catch (error) {
      return false;
    }
  })();
  let sceneGeneration = 0;
  let resetRevision = 0;
  let disposed = false;
  let renderTimer = null;
  let camera3d = null;
  const state = {view: '2d', clusters: new Set([0, 1]), selected: null, payload: null};
  let rendered = false;
  let attempts = 0;

  function available() {
    return Boolean(state.payload && state.payload.points && state.payload.points.x);
  }
  function features() {
    return (state.payload && state.payload.features) || [];
  }
  function column(name) {
    return features().indexOf(name);
  }
  function value(row, name) {
    const index = column(name);
    return index >= 0 ? row[index] : null;
  }
  function pcaLabel(axis) {
    const ratios = (state.payload && state.payload.pca && state.payload.pca.explained_variance_ratio) || [];
    return 'PC' + (axis + 1) + ' · ' + ((ratios[axis] || 0) * 100).toFixed(1) + '%';
  }
  function setPressed(button, pressed) {
    button.setAttribute('aria-pressed', pressed ? 'true' : 'false');
  }
  function captionText() {
    if (!state.payload) return 'Refresh live data to load the verified projection.';
    if (state.view === 'constellation') {
      return 'Immersive 3D constellation · PCA coordinates. Drag to orbit, scroll to zoom, click a sample to inspect.';
    }
    if (state.view === '2d' && !WEBGL) {
      return 'SVG 2D projection (WebGL unavailable). Stratified sample; plotted proportions are not population proportions.';
    }
    if (!available() || state.view === 'density') {
      const occupancy = state.payload.occupancy || {};
      return 'Aggregate density over the training population. Cells with fewer than '
        + (occupancy.min_cell_count || 0) + ' tracks are omitted; no individual tracks are displayed.';
    }
    const sample = state.payload.sample || {};
    const counts = sample.cluster_counts || [];
    return 'Stratified visualization sample: ' + nf.format(sample.size || 0)
      + ' tracks (' + nf.format(counts[0] || 0) + ' / ' + nf.format(counts[1] || 0)
      + '). Plotted proportions are not population proportions; PCA is visualization only.';
  }
  function updateControls() {
    samplePicker.hidden = compact || !available() || state.view === 'density';
    if (available()) sampleInput.max = state.payload.points.x.length - 1;
    const touchScene = coarsePointer && ['3d', 'constellation'].includes(state.view);
    touchButton.hidden = !touchScene;
    touchButton.textContent = touchEnabled ? 'Resume page scrolling' : 'Enable rotation';
    touchButton.setAttribute('aria-pressed', String(touchEnabled));
    root.classList.toggle('is-touch-locked', touchScene && !touchEnabled);
    root.classList.toggle('is-touch-enabled', touchScene && touchEnabled);
    viewButtons.forEach((button) => {
      const view = button.dataset.view;
      button.disabled = view === 'constellation'
        ? (!WEBGL || compact || !available())
        : (view === '3d'
            ? (!WEBGL || !available())
            : (view === '2d' ? !available() : false));
      setPressed(button, state.view === view);
    });
    clusterButtons.forEach((button) => {
      const key = button.dataset.cluster;
      const pressed = key === 'all'
        ? state.clusters.size === 2
        : state.clusters.size === 1 && state.clusters.has(Number(key));
      setPressed(button, pressed);
      button.disabled = state.view === 'density' || !available();
    });
    if (resetButton && !compact) resetButton.hidden = !available();
    if (caption) caption.textContent = captionText();
  }
  const inspector = compact ? null : document.getElementById('explorer-detail');
  function syncInspector() {
    if (!inspector) return;
    const card = inspector.querySelector('.obs-selected-track, .obs-selection-error');
    if (card) card.hidden = state.selected === null || Number(card.dataset.sample) !== state.selected;
    const guide = inspector.querySelector('.obs-guide');
    if (guide) guide.hidden = state.selected !== null;
    inspector.setAttribute('aria-busy', state.selected !== null && (!card || card.hidden) ? 'true' : 'false');
  }
  const inspectorObserver = inspector ? new MutationObserver(syncInspector) : null;
  if (inspectorObserver) inspectorObserver.observe(inspector, {childList: true, subtree: true});
  function notifySelection(index) {
    state.selected = index;
    syncInspector();
    if (!compact) trigger('select', {index, view: state.view});
  }
  function indicesFor(cluster) {
    const labels = state.payload.points.cluster;
    const result = [];
    for (let index = 0; index < labels.length; index += 1) {
      if (labels[index] === cluster) result.push(index);
    }
    return result;
  }
  function customData(index) {
    const row = state.payload.points.raw_features[index];
    return [index, state.payload.points.cluster[index],
      value(row, 'instrumentalness'), value(row, 'energy'), value(row, 'valence'),
      value(row, 'tempo'), value(row, 'loudness')];
  }
  const HOVER = '<b>Sample #%{customdata[0]}</b><br>Cluster %{customdata[1]}'
    + '<br>Instrumentalness %{customdata[2]:.3f}<br>Energy %{customdata[3]:.3f}'
    + '<br>Valence %{customdata[4]:.3f}<br>Tempo %{customdata[5]:.1f} BPM'
    + '<br>Loudness %{customdata[6]:.1f} dB<extra></extra>';
  function traceFor(cluster) {
    const points = state.payload.points;
    const indices = indicesFor(cluster);
    const name = 'Cluster ' + cluster + ' · '
      + nf.format((state.payload.sample.cluster_counts || [])[cluster] || indices.length)
      + ' sampled';
    if (state.view === '3d') {
      return {
        type: 'scatter3d', mode: 'markers', name: name, legendgroup: 'c' + cluster,
        x: indices.map((index) => points.x[index]),
        y: indices.map((index) => points.y[index]),
        z: indices.map((index) => points.z[index]),
        customdata: indices.map(customData),
        marker: {size: 2.6, color: COLORS[cluster], opacity: 0.82, line: {width: 0}},
        hovertemplate: HOVER
      };
    }
    return {
      type: WEBGL ? 'scattergl' : 'scatter', mode: 'markers', name: name,
      legendgroup: 'c' + cluster,
      x: indices.map((index) => points.x[index]),
      y: indices.map((index) => points.y[index]),
      customdata: indices.map(customData),
      marker: {size: 6, color: COLORS[cluster],
        symbol: cluster === 0 ? 'circle' : 'diamond', opacity: 0.72, line: {width: 0}},
      hovertemplate: HOVER
    };
  }
  function selectionTrace() {
    const points = state.payload.points;
    const index = state.selected;
    const has = index !== null && points && points.x[index] !== undefined
      && state.clusters.has(points.cluster[index]);
    if (state.view === '3d') {
      return {
        type: 'scatter3d', mode: 'markers', name: 'Selected sample', showlegend: false,
        hoverinfo: 'skip',
        x: has ? [points.x[index]] : [], y: has ? [points.y[index]] : [],
        z: has ? [points.z[index]] : [],
        marker: {size: 8, color: PALETTE.ink,
          line: {color: has ? COLORS[points.cluster[index]] : PALETTE.ink, width: 3}}
      };
    }
    return {
      type: WEBGL ? 'scattergl' : 'scatter', mode: 'markers', name: 'Selected sample',
      showlegend: false,
      hoverinfo: 'skip',
      x: has ? [points.x[index]] : [], y: has ? [points.y[index]] : [],
      marker: {size: 16, color: 'rgba(0,0,0,0)',
        line: {color: has ? COLORS[points.cluster[index]] : 'rgba(0,0,0,0)', width: 3}}
    };
  }
  function baseLayout() {
    return {
      autosize: true, paper_bgcolor: SURFACE, plot_bgcolor: SURFACE,
      uirevision: state.view + ':' + resetRevision,
      font: {family: 'Inter, Segoe UI, sans-serif', color: MUTED, size: 12},
      margin: {l: 46, r: 18, t: plot.clientWidth < 500 ? 76 : 36, b: 44},
      hoverlabel: {bgcolor: SURFACE, bordercolor: LINE, font: {color: INK}},
      showlegend: true,
      legend: {orientation: 'h', y: 1.04, yanchor: 'bottom', x: 0, font: {color: MUTED, size: 12},
        bgcolor: 'rgba(0,0,0,0)'},
      transition: {duration: 0}
    };
  }
  function rememberCamera() {
    // Plotly wheel zoom updates the rendered camera before its layout/event state.
    // Snapshot that camera before changing traces; uirevision retains other UI state.
    const scene = plot._fullLayout && plot._fullLayout.scene && plot._fullLayout.scene._scene;
    if (state.view === '3d' && scene && typeof scene.getCamera === 'function') {
      camera3d = scene.getCamera();
    }
  }
  function layout3d() {
    const base = baseLayout();
    base.margin = {l: 12, r: 12, t: 32, b: 24};
    base.scene = {
      bgcolor: SURFACE,
      xaxis: {title: {text: pcaLabel(0)}, gridcolor: LINE, zerolinecolor: LINE, color: MUTED, backgroundcolor: SURFACE},
      yaxis: {title: {text: pcaLabel(1)}, gridcolor: LINE, zerolinecolor: LINE, color: MUTED, backgroundcolor: SURFACE},
      zaxis: {title: {text: pcaLabel(2)}, gridcolor: LINE, zerolinecolor: LINE, color: MUTED, backgroundcolor: SURFACE},
      camera: camera3d || {eye: {x: 1.15, y: 1.15, z: 0.95}},
      aspectmode: 'data',
      dragmode: 'orbit'
    };
    return base;
  }
  function layout2d() {
    const base = baseLayout();
    base.xaxis = {title: {text: pcaLabel(0)}, gridcolor: LINE, zerolinecolor: LINE, color: MUTED};
    base.yaxis = {title: {text: pcaLabel(1)}, gridcolor: LINE, zerolinecolor: LINE, color: MUTED};
    base.dragmode = coarsePointer ? false : 'pan';
    return base;
  }
  const CONFIG = {responsive: true, displaylogo: false, scrollZoom: !coarsePointer,
    doubleClick: 'reset', modeBarButtonsToRemove: ['lasso2d', 'select2d', 'autoScale2d']};

  function showEmpty(message) {
    if (window.Plotly) Plotly.purge(plot);
    plot.innerHTML = '<div class="obs-empty">' + message + '</div>';
  }
  function renderDensity() {
    const occupancy = state.payload.occupancy;
    if (!occupancy || !occupancy.cells || !occupancy.cells.length) {
      showEmpty('Aggregate visualization data is unavailable for this model.');
      return;
    }
    const bins = occupancy.bins;
    const xmin = occupancy.x_range[0];
    const xmax = occupancy.x_range[1];
    const ymin = occupancy.y_range[0];
    const ymax = occupancy.y_range[1];
    const z = Array.from({length: bins}, () => Array(bins).fill(null));
    const cells = Array.from({length: bins}, () => Array(bins).fill(null));
    let maxCount = occupancy.min_cell_count || 1;
    occupancy.cells.forEach((cell) => {
      const xIndex = Math.min(bins - 1, Math.max(0,
        Math.round(((cell.x - xmin) / (xmax - xmin || 1)) * (bins - 1))));
      const yIndex = Math.min(bins - 1, Math.max(0,
        Math.round(((cell.y - ymin) / (ymax - ymin || 1)) * (bins - 1))));
      z[yIndex][xIndex] = Math.log10(Math.max(1, cell.count));
      maxCount = Math.max(maxCount, cell.count);
      cells[yIndex][xIndex] = [cell.count, cell.cluster1_share, cell.mean_instrumentalness];
    });
    const xs = Array.from({length: bins}, (_, i) => xmin + (xmax - xmin) * (i / (bins - 1)));
    const ys = Array.from({length: bins}, (_, i) => ymin + (ymax - ymin) * (i / (bins - 1)));
    const trace = {
      type: 'heatmap', z: z, x: xs, y: ys, customdata: cells, hoverongaps: false,
      zmin: Math.log10(Math.max(1, occupancy.min_cell_count)),
      zmax: Math.log10(maxCount),
      showscale: true,
      colorbar: {title: {text: 'Tracks (log)', font: {color: MUTED, size: 12}},
        thickness: 9, len: 0.55, tickfont: {color: MUTED, size: 12},
        outlinewidth: 0},
      colorscale: [[0, PALETTE.density_low], [0.25, PALETTE.density_mid],
        [0.6, PALETTE.density_high], [1, PALETTE.teal_dim]],
      hovertemplate: 'Cell track count: %{customdata[0]}<br>Cluster 1 share: '
        + '%{customdata[1]:.1%}<br>Mean instrumentalness: %{customdata[2]:.3f}<extra></extra>'
    };
    const layout = baseLayout();
    layout.showlegend = false;
    layout.title = {text: 'Training-population density · log color scale',
      x: 0, xanchor: 'left', font: {size: 12, color: INK}};
    layout.xaxis = {title: {text: pcaLabel(0)}, gridcolor: LINE, zerolinecolor: LINE, color: MUTED};
    layout.yaxis = {title: {text: pcaLabel(1)}, gridcolor: LINE, zerolinecolor: LINE, color: MUTED};
    layout.margin = {l: 46, r: 70, t: 36, b: 44};
    Plotly.react(plot, [trace], layout, CONFIG);
  }
  function attachClick() {
    if (typeof plot.removeAllListeners === 'function') {
      plot.removeAllListeners('plotly_click');
    }
    plot.on('plotly_click', (event) => {
      if (state.view === 'density' || !available()) return;
      if (compact) {
        if (status) status.textContent = 'Open the Cluster Explorer tab to inspect samples.';
        return;
      }
      const point = event.points && event.points[0];
      if (!point || !point.customdata) return;
      const index = point.customdata[0];
      const row = state.payload.points.raw_features[index];
      rememberCamera();
      state.selected = index;
      if (status) {
        status.textContent = 'Selected sample #' + index + ' · Cluster '
          + state.payload.points.cluster[index] + ' · instrumentalness '
          + Number(value(row, 'instrumentalness')).toFixed(3);
      }
      notifySelection(index);
      render();
    });
  }
  function hideTip() {
    if (tip) tip.hidden = true;
  }
  function disposeConstellation() {
    sceneGeneration += 1;
    if (constellation) {
      try {
        constellation.dispose();
      } catch (error) {
        // Teardown can race a pending frame; the scene is discarded either way.
      }
      constellation = null;
    }
    constellationLoading = null;
    if (root) root.__acousticConstellation = null;
    if (constellationHost) constellationHost.hidden = true;
    root.classList.remove('is-constellation');
    if (plot) plot.hidden = false;
    hideTip();
  }
  function showTip(index, x, y) {
    if (!tip || !constellationHost) return;
    if (index === null || index === undefined) {
      tip.hidden = true;
      return;
    }
    const row = state.payload.points.raw_features[index];
    tip.textContent = 'Sample #' + index + ' · Cluster '
      + state.payload.points.cluster[index]
      + ' · instr ' + Number(value(row, 'instrumentalness')).toFixed(3)
      + ' · energy ' + Number(value(row, 'energy')).toFixed(3);
    const rect = constellationHost.getBoundingClientRect();
    const left = Math.min(Math.max(8, x - rect.left + 12),
      Math.max(8, rect.width - 230));
    const top = Math.min(Math.max(8, y - rect.top + 12),
      Math.max(8, rect.height - 64));
    tip.style.left = left + 'px';
    tip.style.top = top + 'px';
    tip.hidden = false;
  }
  function renderConstellation() {
    if (!available()) {
      disposeConstellation();
      showEmpty('The immersive view requires the sampled points.');
      return;
    }
    plot.hidden = true;
    if (constellationHost) constellationHost.hidden = false;
    root.classList.add('is-constellation');
    updateControls();
    if (constellation) {
      constellation.resize();
      return;
    }
    if (!constellationUrl) {
      disposeConstellation();
      state.view = 'density';
      if (status) status.textContent = 'Immersive bundle unavailable; showing aggregate density.';
      render();
      return;
    }
    if (constellationLoading) return constellationLoading;
    const generation = sceneGeneration;
    constellationLoading = import(constellationUrl)
      .then((module) => {
        if (disposed || generation !== sceneGeneration || state.view !== 'constellation') return null;
        constellation = module.createConstellation({
          palette: PALETTE,
          container: constellationHost,
          points: state.payload.points,
          reduceMotion: reduceMotion,
          onSelect: (index) => {
            if (compact) return;
            state.selected = index;
            const row = state.payload.points.raw_features[index];
            if (status) status.textContent = 'Selected sample #' + index + ' · Cluster '
              + state.payload.points.cluster[index] + ' · instrumentalness '
              + Number(value(row, 'instrumentalness')).toFixed(3);
            notifySelection(index);
          },
          onHover: (index, x, y) => showTip(index, x, y),
          onReady: () => {
            if (caption) caption.textContent = 'Constellation · '
              + nf.format(state.payload.sample.size || 0) + ' sampled tracks · PCA 3D ('
              + pcaLabel(0) + ' / ' + pcaLabel(1) + ' / ' + pcaLabel(2)
              + '). Drag to orbit, scroll to zoom, click to inspect.';
          },
        });
        constellation.setVisibleClusters(Array.from(state.clusters));
        if (state.selected !== null) constellation.select(state.selected);
        root.__acousticConstellation = constellation;
        rendered = true;
        return constellation;
      })
      .catch(() => {
        if (disposed || generation !== sceneGeneration) return null;
        constellationLoading = null;
        disposeConstellation();
        state.view = 'density';
        if (status) status.textContent = 'Immersive scene unavailable in this browser; showing aggregate density.';
        render();
        return null;
      });
    return constellationLoading;
  }
  function render() {
    if (disposed) return;
    updateControls();
    if (state.view === '3d' && !WEBGL) {
      state.view = '2d';
      if (status) status.textContent = 'WebGL unavailable; using SVG 2D.';
    }
    if (state.view === 'constellation') {
      if (!WEBGL) {
        state.view = 'density';
        if (status) status.textContent = 'WebGL unavailable; showing aggregate density.';
      } else {
        renderConstellation();
        return;
      }
    }
    disposeConstellation();
    if (!window.Plotly) {
      attempts += 1;
      if (attempts < 120) {
        renderTimer = window.setTimeout(render, 50);
      } else {
        showEmpty('The visualization library could not be loaded.');
      }
      return;
    }
    if (!state.payload) {
      showEmpty('Refresh live data to load the verified projection.');
      return;
    }
    if (!available() || state.view === 'density') {
      renderDensity();
      return;
    }
    const traces = [0, 1].filter((cluster) => state.clusters.has(cluster)).map(traceFor);
    traces.push(selectionTrace());
    const layout = state.view === '3d' ? layout3d() : layout2d();
    Plotly.react(plot, traces, layout, CONFIG).then(() => {
      rendered = true;
      attachClick();
    });
  }
  viewButtons.forEach((button) => {
    button.addEventListener('click', () => {
      if (button.disabled) return;
      if (state.view === button.dataset.view) return;
      touchEnabled = false;
      state.view = button.dataset.view;
      camera3d = null;
      notifySelection(null);
      if (status) status.textContent = '';
      render();
    });
  });
  touchButton.addEventListener('click', () => {
    touchEnabled = !touchEnabled;
    updateControls();
  });
  samplePicker.addEventListener('submit', (event) => {
    event.preventDefault();
    const index = Number(sampleInput.value);
    if (!available() || !Number.isInteger(index) || index < 0 || index >= state.payload.points.x.length) return;
    if (!state.clusters.has(state.payload.points.cluster[index])) {
      status.textContent = 'That sample is hidden by the cluster filter. Choose Both to inspect it.';
      return;
    }
    rememberCamera();
    notifySelection(index);
    status.textContent = 'Selected sample #' + index + ' · Cluster ' + state.payload.points.cluster[index];
    if (constellation) constellation.select(index);
    else render();
  });
  clusterButtons.forEach((button) => {
    button.addEventListener('click', () => {
      if (button.disabled) return;
      rememberCamera();
      const key = button.dataset.cluster;
      if (key === 'all') {
        state.clusters = new Set([0, 1]);
      } else {
        state.clusters = new Set([Number(key)]);
      }
      if (state.selected !== null && !state.clusters.has(state.payload.points.cluster[state.selected])) {
        notifySelection(null);
        if (constellation) constellation.clearSelection();
      }
      hideTip();
      if (state.view === 'constellation' && constellation) {
        constellation.setVisibleClusters(Array.from(state.clusters));
        updateControls();
        if (status) status.textContent = '';
        return;
      }
      render();
    });
  });
  if (resetButton) {
    resetButton.addEventListener('click', () => {
      notifySelection(null);
      resetRevision += 1;
      camera3d = null;
      if (status) status.textContent = '';
      hideTip();
      if (state.view === 'constellation' && constellation) {
        constellation.clearSelection();
        constellation.resetCamera();
        return;
      }
      if (window.Plotly && state.payload) {
        if (state.view === '3d') {
          Plotly.relayout(plot, {'scene.camera': {eye: {x: 1.45, y: 1.35, z: 1.25}}});
        } else if (state.view === '2d') {
          Plotly.relayout(plot, {'xaxis.autorange': true, 'yaxis.autorange': true});
        }
      }
      render();
    });
  }
  const refreshButton = document.getElementById('refresh-live');
  function clearForRefresh() {
    rememberCamera();
    state.selected = null;
    syncInspector();
    if (constellation) constellation.clearSelection();
    if (status) status.textContent = '';
    hideTip();
    render();
  }
  if (refreshButton) refreshButton.addEventListener('click', clearForRefresh);
  function setPayload(value) {
    if (state.payload && value && JSON.stringify(state.payload) === JSON.stringify(value)) return;
    disposeConstellation();
    state.payload = value && typeof value === 'object' ? value : null;
    state.selected = null;
    if (!state.payload || !state.payload.points) state.view = 'density';
    else if (state.view === 'density') state.view = '2d';
    if (status) status.textContent = '';
    render();
  }
  setPayload(props.value);
  watch('value', () => setPayload(props.value));
  const observer = new ResizeObserver(() => {
    if (state.view === 'constellation' && constellation) {
      constellation.resize();
      return;
    }
    if (!window.Plotly || !state.payload) return;
    if (!rendered && plot.clientWidth > 240) {
      render();
    } else if (rendered && !plot.hidden && plot.clientWidth > 240) {
      Plotly.Plots.resize(plot);
    }
  });
  observer.observe(plot);
  const lifecycle = new MutationObserver(() => {
    if (root.isConnected) return;
    disposed = true;
    clearTimeout(renderTimer);
    observer.disconnect();
    lifecycle.disconnect();
    if (inspectorObserver) inspectorObserver.disconnect();
    if (refreshButton) refreshButton.removeEventListener('click', clearForRefresh);
    disposeConstellation();
    if (window.Plotly) Plotly.purge(plot);
  });
  lifecycle.observe(document.body, {childList: true, subtree: true});
})();
"""


def create_explorer(elem_id: str, *, compact: bool = False) -> gr.HTML:
    register_assets()
    return gr.HTML(
        value=None,
        html_template=TEMPLATE,
        css_template=CSS,
        js_on_load=JS,
        head=plotly_head(),
        compact=compact,
        constellation_url=constellation_url(),
        elem_id=elem_id,
        elem_classes=["obs-explorer-host"],
        container=False,
        padding=False,
    )


# Resolve standalone HTML/CSS and JavaScript from the authoritative light tokens.
for _key, _value in TOKENS.items():
    CSS = CSS.replace("__OBS_" + _key.upper() + "__", _value)
JS = JS.replace("__OBS_PALETTE__", json.dumps(TOKENS))
