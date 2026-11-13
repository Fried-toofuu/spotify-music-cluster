# Acoustic Observatory design system

The product register is a scientific music-intelligence studio: permanently light, layered,
restrained, analytical and music-oriented. It avoids neon decoration, glass
effects and gradients that compromise reading. The scientific caveat is part of
the visual hierarchy, not a footnote hidden by styling.

## Visual direction

- Off-white page (`#F7F9FC`), white cards (`#FFFFFF`), cool secondary surfaces
  (`#F0F3F7`, `#E8EDF3`) and thin neutral separators (`#E0E6ED`). Interactive
  boundaries use `#7B8896`; shadows are reserved for light overlay depth.
- Deep teal (`#147D73`) identifies Cluster 0 and primary actions; violet
  (`#7055B9`) identifies Cluster 1. Amber (`#8A5B10`) marks findings/caveats;
  red (`#B42335`) is reserved for errors. Primary actions use white text.
- Light appearance is mandatory across Gradio, Plotly and Three.js. No theme
  selector, stored preference or separate dark palette exists. OS dark preference
  and explicit Gradio dark URLs must still render light.
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
| Page / surfaces | `#F7F9FC`, `#FFFFFF`, `#F0F3F7`, `#E8EDF3` |
| Text | `#17212B` primary, `#556270` secondary, `#596775` muted |
| Lines | `#E0E6ED`, interactive `#7B8896` |
| Accents | teal `#147D73`, violet `#7055B9`, amber `#8A5B10`, error `#B42335` |
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

- Measured text contrast on page: primary 15.45:1, secondary
  5.91:1, muted 5.5:1. Muted on the deepest light surface:
  4.93:1. White primary-action text on teal: 4.99:1. These pairs
  meet AA for normal text. Neutral control boundaries meet 3:1 on light surfaces.
  Density uses a sequential light-to-teal scale with a labeled log colorbar;
  color intensity encodes count. All density stops meet 3:1 on white (3.06?6.81:1).
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

## Permanent light implementation

[theme.py](../src/spotify_cluster/web/theme.py) owns the only color token map.
It generates CSS variables, the Gradio theme and the palette embedded in Explorer
JavaScript, which passes that palette to Three.js. Gradio's compatibility dark
slots mirror the same light values, including inherited defaults. The custom head
sets `__theme=light`, declares `color-scheme: only light` and removes Gradio's
body `dark` class when host/system preferences apply it after mounting. This is
invariant enforcement with no stored theme preference. Plotly uses explicit white
paper/plot/3D scene backgrounds; Three.js uses white with charcoal selection.

[Light theme delivery](../plans/20261113-light-theme/reports/delivery.md) records
screenshots and current verification; earlier refinement reports remain historical.
