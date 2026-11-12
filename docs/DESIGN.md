# Acoustic Observatory design system

The product register is a scientific music-intelligence studio: dark, layered,
restrained, analytical and music-oriented. It avoids neon decoration, glass
effects and gradients that compromise reading. The scientific caveat is part of
the visual hierarchy, not a footnote hidden by styling.

## Visual direction

- Deep charcoal page (`#080d0f`) with layered surface tints (`#0e1719`,
  `#132326`, `#193033`) and hairline boundaries (`#22383a`, `#35565a`).
- Muted teal (`#5eead4`) is the primary accent and the fixed color for
  Cluster 0; violet (`#b7a4ff`) is the fixed color for Cluster 1. Amber
  (`#f5c76a`) marks the dominant finding and caveat accents. Red is reserved
  for errors.
- Display type is a system serif stack (Iowan/Palatino/Georgia) for the hero and
  section headings; body is Inter/Segoe UI/system sans; labels and data use a
  mono stack. This contrast axis gives the observatory an editorial/scientific
  feel without downloading fonts.
- One radius system: 14px cards, 8–10px controls; pills for status and cluster
  badges.
- Depth uses hairlines and tint elevation, not heavy shadows. The map supplies the visual signature; the hero stays quiet.
- Cluster identity never depends on color alone: every view also uses cluster
  labels and counts; the 2D Plotly markers use circle/diamond symbols; the
  density view is explicitly labeled aggregate.

## Tokens

| Group | Values |
|---|---|
| Page / surfaces | `#080d0f`, `#0e1719`, `#132326`, `#193033` |
| Text | `#eef7f4` primary, `#c4d6d2` secondary, `#8ba39e` muted |
| Lines | `#22383a`, strong `#35565a` |
| Accents | teal `#5eead4`, violet `#b7a4ff`, amber `#f5c76a`, error `#ff9b9b` |
| Type | hero `clamp(2.5rem, 4.2vw, 4rem)`, section `clamp(1.5rem, 2.4vw, 2rem)`, body 16px/1.6, small 0.8–0.9rem |
| Spacing | 4, 8, 12, 16, 20, 24, 32, 44, 64 |
| Motion | 160–240ms ease; Plotly transitions disabled; reduced-motion media query removes transitions/animations |

## Layout and hierarchy

- Maximum content width 1280px; page gutters 24px desktop / 14px mobile.
- Overview pairs a compact editorial introduction and primary Explore action with
  the genuine interactive map. Scientific Context is expandable; fact sheet,
  dominant finding and full-population balance follow below.
- Explorer pairs the map with a mode-aware guide or selected sample inspector.
  Population profile comparisons and exact raw-unit tables follow the instrument.
- Predict keeps the assigned cluster and concise distance meters prominent.
  Distance Breakdown preserves the chart and exact values on demand.
- Research leads with Research Findings, then Model Comparison, then expandable
  Methodology and Reproducibility. Supporting figures and exact archived evidence
  remain available without duplicating the historical table.


## Responsive behavior

Verified at 1440×900, 768×1024 and 375×812:

- Gradio inner `.main.app` padding is removed so the app uses the viewport.
- Overview, Explorer and Predict rows stack at ≤900px; the hero and map fill the
  width.
- All four tabs remain visible in a two-column grid on small screens; long labels
  wrap within their own button. Desktop uses a single row.
- Plot heights are `clamp(340px, 54vh, 560px)`, with a 340px mobile fallback;
  the Overview preview is shorter.
- One status and a compact refresh utility accompany the brand at ≤768px; the brand name stays on one line.
- Wide tables scroll inside their own bounded containers; the page itself does
  not overflow horizontally.

## States

Defined and exercised: loading skeleton text, API ready, backend offline,
optional visualization unavailable, aggregate-only mode, empty prediction,
invalid input, prediction error with stale output cleared, no selection,
WebGL/constellation failure with density fallback, and reduced-motion mode.

## Accessibility

- Text/token contrast ratios (WCAG): primary 17.9:1, secondary 12.9:1, muted
  7.3:1 on the page; muted on surface 6.8:1; muted on surface-3 5.2:1; primary
  button text 13.0:1. All tested text pairs pass AA for normal text.
- Native buttons, selects, sliders and disclosure elements; custom Explorer
  buttons expose `aria-pressed`, `role="toolbar"`, `role="status"` live regions
  and visible 2px teal focus outlines.
- Pointer users pick real marks; the zero-based sample-number form provides the
  same inspector and fitted-space neighbors by keyboard without hover. Exact
  population tables remain available. A sample index is never a Spotify ID.
- `prefers-reduced-motion: reduce` removes transitions/animations; the
  constellation has no auto-rotation and no damping loop.
- Custom map controls and sample input have 44px minimum targets. On coarse
  pointers, 3D starts in page-scrolling mode; Enable rotation opts into canvas
  gestures and Resume page scrolling releases them. The mobile submit stays sticky.
- Legends reserve space above narrow plots so touch hit areas do not overlap marks.


## Verification and performance evidence

[Web verification](WEB.md#verification) owns the repeatable checks. UI changes
require actual loaded screenshots at desktop, tablet and mobile widths, an
interaction walk including error recovery, keyboard focus and reduced motion,
and regression checks for 2D/3D, camera/filter continuity and constellation fallback.
Stateful timings and review findings belong in
[refinement evidence](../plans/20261112-ui-refinement/reports/delivery.md), not in
permanent performance guarantees. No decorative animation or new frontend
runtime dependency is required by this design.
