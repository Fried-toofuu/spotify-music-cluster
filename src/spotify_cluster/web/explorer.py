# ruff: noqa: E501  (embedded HTML/JS)
"""Custom Gradio HTML component for the verified PCA cluster space."""

from __future__ import annotations

import gradio as gr

from .assets import constellation_url, plotly_head, register_assets

TEMPLATE = """
<div class="obs-explorer" data-compact="{{compact}}" data-constellation-url="{{constellation_url}}">
  <div class="obs-explorer-head">
    <div class="obs-explorer-title">
      <span class="obs-explorer-kicker">PCA cluster space</span>
      <strong class="obs-explorer-heading">Acoustic map</strong>
    </div>
    <div class="obs-toolbar" role="toolbar" aria-label="Cluster space controls">
      <div class="obs-seg" role="group" aria-label="Projection view">
        <button type="button" data-view="2d" aria-pressed="true">2D</button>
        <button type="button" data-view="3d" aria-pressed="false">3D</button>
        <button type="button" data-view="density" aria-pressed="false">Density</button>
        <button type="button" data-view="constellation" aria-pressed="false">Constellation</button>
      </div>
      <div class="obs-chips" role="group" aria-label="Cluster filter">
        <button type="button" data-cluster="all" aria-pressed="true">Both</button>
        <button type="button" data-cluster="0" aria-pressed="true"><span class="obs-swatch c0"></span>Cluster 0</button>
        <button type="button" data-cluster="1" aria-pressed="true"><span class="obs-swatch c1"></span>Cluster 1</button>
      </div>
      <button type="button" class="obs-reset" data-action="reset">Reset view</button>
    </div>
  </div>
  <div class="obs-plot" data-role="plot" role="img" aria-label="Interactive PCA projection of sampled training tracks"></div>
  <div class="obs-constellation" data-role="constellation" hidden>
    <div class="obs-constellation-tip" data-role="tip" hidden></div>
  </div>
  <div class="obs-explorer-foot">
    <p class="obs-caption" data-role="caption">Refresh live data to load the verified projection.</p>
    <p class="obs-status" data-role="status" role="status" aria-live="polite"></p>
  </div>
</div>
"""

CSS = """
.obs-explorer { background: var(--obs-surface-1, #0e1719);
  border: 1px solid var(--obs-line, #22383a); border-radius: 14px; overflow: hidden;
  color: var(--obs-ink, #eef7f4); }
.obs-explorer-head { display: flex; align-items: flex-start; justify-content: space-between;
  gap: 14px; flex-wrap: wrap; padding: 16px 18px 14px;
  border-bottom: 1px solid var(--obs-line, #22383a); }
.obs-explorer-title { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.obs-explorer-kicker { font-family: var(--obs-mono, monospace); font-size: .66rem;
  letter-spacing: .16em; text-transform: uppercase; color: var(--obs-muted, #8ba39e); }
.obs-explorer-heading { font-family: var(--obs-display, Georgia, serif); font-size: 1.28rem;
  font-weight: 500; letter-spacing: -.01em; color: var(--obs-ink, #eef7f4); }
.obs-toolbar { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.obs-seg, .obs-chips { display: flex; align-items: center; gap: 2px; padding: 3px;
  background: var(--obs-surface-2, #132326); border: 1px solid var(--obs-line, #22383a);
  border-radius: 999px; }
.obs-seg button, .obs-chips button { appearance: none; border: 0; background: transparent;
  white-space: nowrap;
  color: var(--obs-muted, #8ba39e); font-family: var(--obs-mono, monospace);
  font-size: .68rem; letter-spacing: .04em; border-radius: 999px; padding: 8px 11px;
  min-height: 34px; cursor: pointer; display: inline-flex; align-items: center; gap: 6px;
  transition: background-color 160ms ease, color 160ms ease; }
.obs-seg button:hover, .obs-chips button:hover { color: var(--obs-ink, #eef7f4); }
.obs-seg button[aria-pressed="true"], .obs-chips button[aria-pressed="true"] {
  background: var(--obs-surface-3, #193033); color: var(--obs-ink, #eef7f4); }
.obs-seg button:disabled, .obs-chips button:disabled { opacity: .38; cursor: not-allowed; }
.obs-chips button:focus-visible, .obs-seg button:focus-visible, .obs-reset:focus-visible {
  outline: 2px solid var(--obs-teal, #5eead4); outline-offset: 2px; }
.obs-swatch { width: 8px; height: 8px; border-radius: 2px; display: inline-block; }
.obs-swatch.c0 { background: var(--obs-teal, #5eead4); }
.obs-swatch.c1 { background: var(--obs-violet, #b7a4ff); }
.obs-reset { appearance: none; border: 1px solid var(--obs-line-strong, #35565a);
  background: transparent; color: var(--obs-ink-2, #c4d6d2);
  font-family: var(--obs-mono, monospace); font-size: .68rem; border-radius: 8px;
  padding: 8px 11px; min-height: 34px; cursor: pointer; }
.obs-reset:hover { background: var(--obs-surface-2, #132326); color: var(--obs-ink, #eef7f4); }
.obs-reset[hidden] { display: none; }
.obs-plot { width: 100%; height: clamp(340px, 54vh, 560px); min-height: 280px; }
.obs-constellation { position: relative; width: 100%; height: clamp(340px, 54vh, 560px);
  min-height: 280px; }
.obs-constellation[hidden], .obs-constellation-tip[hidden] { display: none; }
.obs-constellation-canvas { display: block; width: 100%; height: 100%;
  touch-action: none; cursor: grab; }
.obs-constellation-tip { position: absolute; z-index: 2; pointer-events: none;
  max-width: 220px; padding: 7px 9px; border-radius: 8px; border: 1px solid var(--obs-line-strong, #35565a);
  background: var(--obs-surface-3, #193033); color: var(--obs-ink, #eef7f4);
  font-family: var(--obs-mono, monospace); font-size: .66rem; line-height: 1.5;
  box-shadow: 0 6px 18px rgba(0,0,0,.35); }
.obs-explorer.is-constellation .obs-plot { display: none; }
.obs-explorer.is-compact [data-view="constellation"] { display: none; }
.obs-explorer.is-compact .obs-plot { height: clamp(280px, 40vh, 400px); }
.obs-explorer.is-compact .obs-constellation { height: clamp(280px, 40vh, 400px); }
.obs-explorer.is-compact .obs-explorer-head { padding: 13px 15px 12px; }
.obs-explorer.is-compact .obs-explorer-heading { font-size: 1.1rem; }
.obs-explorer-foot { display: flex; align-items: flex-start; justify-content: space-between;
  gap: 10px 18px; flex-wrap: wrap; padding: 11px 18px 13px;
  border-top: 1px solid var(--obs-line, #22383a); }
.obs-caption, .obs-status { margin: 0; font-size: .72rem; line-height: 1.5; }
.obs-caption { color: var(--obs-muted, #8ba39e); max-width: 76ch; }
.obs-status { color: var(--obs-ink-2, #c4d6d2); font-family: var(--obs-mono, monospace);
  font-size: .68rem; }
.obs-empty { display: flex; align-items: center; justify-content: center; height: 100%;
  min-height: 240px; padding: 24px; text-align: center; color: var(--obs-muted, #8ba39e);
  font-size: .86rem; }
@media (max-width: 640px) {
  .obs-explorer-head { padding: 13px 14px; }
  .obs-toolbar { width: 100%; }
  .obs-seg, .obs-chips { flex: 1 1 auto; justify-content: center; }
  .obs-chips button, .obs-seg button { padding: 7px 8px; font-size: .62rem; }
  .obs-reset { width: 100%; }
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
  const constellationHost = root.querySelector('[data-role="constellation"]');
  const tip = root.querySelector('[data-role="tip"]');
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  let constellation = null;
  let constellationLoading = null;
  const compact = (root.dataset.compact || '').toLowerCase() === 'true';
  const constellationUrl = root.dataset.constellationUrl || '';
  if (compact) root.classList.add('is-compact');
  if (resetButton) resetButton.hidden = compact;
  const COLORS = {0: '#5eead4', 1: '#b7a4ff'};
  const INK = '#eef7f4';
  const MUTED = '#8ba39e';
  const LINE = '#22383a';
  const SURFACE = '#0e1719';
  const nf = new Intl.NumberFormat();
  const WEBGL = (() => {
    try {
      const probe = document.createElement('canvas');
      return Boolean(probe.getContext('webgl2') || probe.getContext('webgl'));
    } catch (error) {
      return false;
    }
  })();
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
        : state.clusters.has(Number(key));
      setPressed(button, pressed);
      button.disabled = state.view === 'density' || !available();
    });
    if (resetButton && !compact) resetButton.hidden = !available();
    if (caption) caption.textContent = captionText();
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
    const has = index !== null && points && points.x[index] !== undefined;
    if (state.view === '3d') {
      return {
        type: 'scatter3d', mode: 'markers', name: 'Selected sample', showlegend: false,
        hoverinfo: 'skip',
        x: has ? [points.x[index]] : [], y: has ? [points.y[index]] : [],
        z: has ? [points.z[index]] : [],
        marker: {size: 8, color: '#ffffff',
          line: {color: has ? COLORS[points.cluster[index]] : '#ffffff', width: 3}}
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
      autosize: true, paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
      font: {family: 'Inter, Segoe UI, sans-serif', color: MUTED, size: 11},
      margin: {l: 46, r: 18, t: 18, b: 44},
      hoverlabel: {bgcolor: SURFACE, bordercolor: LINE, font: {color: INK}},
      showlegend: true,
      legend: {orientation: 'h', y: 1.06, x: 0, font: {color: MUTED, size: 11},
        bgcolor: 'rgba(0,0,0,0)'},
      transition: {duration: 0}
    };
  }
  function layout3d() {
    const base = baseLayout();
    base.margin = {l: 0, r: 0, t: 0, b: 0};
    base.scene = {
      xaxis: {title: {text: pcaLabel(0)}, gridcolor: LINE, zerolinecolor: LINE, color: MUTED},
      yaxis: {title: {text: pcaLabel(1)}, gridcolor: LINE, zerolinecolor: LINE, color: MUTED},
      zaxis: {title: {text: pcaLabel(2)}, gridcolor: LINE, zerolinecolor: LINE, color: MUTED},
      camera: {eye: {x: 1.15, y: 1.15, z: 0.95}},
      aspectmode: 'data',
      dragmode: 'orbit'
    };
    return base;
  }
  function layout2d() {
    const base = baseLayout();
    base.xaxis = {title: {text: pcaLabel(0)}, gridcolor: LINE, zerolinecolor: LINE, color: MUTED};
    base.yaxis = {title: {text: pcaLabel(1)}, gridcolor: LINE, zerolinecolor: LINE, color: MUTED};
    base.dragmode = 'pan';
    return base;
  }
  const CONFIG = {responsive: true, displaylogo: false, scrollZoom: true,
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
      colorbar: {title: {text: 'Tracks (log)', font: {color: MUTED, size: 9}},
        thickness: 9, len: 0.55, tickfont: {color: MUTED, size: 8},
        outlinewidth: 0},
      colorscale: [[0, '#0b1416'], [0.25, '#123033'], [0.6, '#1f6f6b'], [1, '#5eead4']],
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
      if (compact) {
        if (status) status.textContent = 'Open the Cluster Explorer tab to inspect samples.';
        return;
      }
      const point = event.points && event.points[0];
      if (!point || !point.customdata) return;
      const index = point.customdata[0];
      const row = state.payload.points.raw_features[index];
      state.selected = index;
      if (status) {
        status.textContent = 'Selected sample #' + index + ' · Cluster '
          + state.payload.points.cluster[index] + ' · instrumentalness '
          + Number(value(row, 'instrumentalness')).toFixed(3);
      }
      trigger('select', {index: index});
      render();
    });
  }
  function hideTip() {
    if (tip) tip.hidden = true;
  }
  function disposeConstellation() {
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
    constellationLoading = import(constellationUrl)
      .then((module) => {
        constellation = module.createConstellation({
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
            trigger('select', {index: index});
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
        root.__acousticConstellation = constellation;
        rendered = true;
        return constellation;
      })
      .catch(() => {
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
        window.setTimeout(render, 50);
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
      state.view = button.dataset.view;
      state.selected = null;
      if (status) status.textContent = '';
      render();
    });
  });
  clusterButtons.forEach((button) => {
    button.addEventListener('click', () => {
      if (button.disabled) return;
      const key = button.dataset.cluster;
      if (key === 'all') {
        state.clusters = new Set([0, 1]);
      } else {
        const cluster = Number(key);
        if (state.clusters.has(cluster)) state.clusters.delete(cluster);
        else state.clusters.add(cluster);
        if (!state.clusters.size) state.clusters.add(cluster);
      }
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
      state.selected = null;
      if (status) status.textContent = '';
      hideTip();
      if (state.view === 'constellation' && constellation) {
        constellation.resetCamera();
        return;
      }
      if (window.Plotly && state.payload) {
        if (state.view === '3d') {
          Plotly.relayout(plot, {'scene.camera': {eye: {x: 1.45, y: 1.35, z: 1.25}}});
        } else if (state.view === '2d') {
          Plotly.relayout(plot, {xaxis: {autorange: true}, yaxis: {autorange: true}});
        }
      }
      render();
    });
  }
  function setPayload(value) {
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
