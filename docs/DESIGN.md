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
- Depth uses hairlines and tint elevation, not heavy shadows. A subtle radial
  tint is confined to the hero.
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
| Type | hero `clamp(2.7rem, 5.6vw, 4.9rem)`, section `clamp(1.5rem, 2.4vw, 2rem)`, body 16px/1.6, small 0.72–0.9rem |
| Spacing | 4, 8, 12, 16, 20, 24, 32, 44, 64 |
| Motion | 160–240ms ease; Plotly transitions disabled; reduced-motion media query removes transitions/animations |

## Layout and hierarchy

- Maximum content width 1280px; page gutters 24px desktop / 14px mobile.
- Overview: hero → interactive cluster space (primary) → supporting fact sheet,
  dominant finding and population → entry points → model identity.
- Explorer: spatial map and toolbar first, then sample inspector and profile
  comparison, then exact aggregate tables.
- Predict: grouped descriptors (core acoustic character; rhythm/energy/dynamics)
  and a prominent result card with a distance chart and exact table.
- Research: question → data → dominant finding → historical vs deployment →
  controlled comparisons → figures → archived evidence → limits.

## Responsive behavior

Verified at 1440×900, 768×1024 and 375×812:

- Gradio inner `.main.app` padding is removed so the app uses the viewport.
- Overview, Explorer and Predict rows stack at ≤900px; the hero and map fill the
  width.
- The tab bar scrolls horizontally on small screens rather than wrapping into
  several rows.
- Plot heights are `clamp(340px, 54vh, 560px)`, with a 340px mobile fallback;
  the Overview preview is shorter.
- The brand bar stacks at ≤768px; the brand name stays on one line.
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
- The Plotly canvas is pointer-based; exact numeric tables and the aggregate
  density view are the keyboard-accessible equivalents. Plotly's modebar buttons
  are keyboard focusable.
- `prefers-reduced-motion: reduce` removes transitions/animations; the
  constellation has no auto-rotation and no damping loop.
- Touch targets are ≥34px in the dense map toolbar and ≥44px for primary
  controls; the submit action is sticky on mobile.

## Performance budgets (measured on this checkout)

- First contentful paint ~100 ms; Overview map ready ~2.0 s; Explorer plot
  ~1.2 s after tab selection; 3D switch ~1.3 s.
- API points ~7.6 ms local (574 KB JSON / 207 KB gzip); Plotly JS asset
  ~1.4 MB gzip.
- JS heap ~39 MB after load, ~99 MB after the 6,000-point Explorer, ~115 MB
  after 18 view switches. No runaway growth observed.

These are measurements on ordinary local development hardware, not universal
guarantees. Public traffic needs proxy-level rate limiting and TLS.
