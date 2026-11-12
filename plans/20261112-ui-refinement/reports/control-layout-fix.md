# Control clipping and alignment repair

## Cause and correction

The prediction slider number inputs were 44px tall inside Gradio's 24px
`tab-like-container` with hidden overflow. Their values were visibly clipped.
The compact wrapper now accommodates the complete 44px field (46px with its
border), including its reset control.

Transparent Gradio component wrappers no longer impose rounded clipping.
Accordion surfaces own a consistent 9px outer / 8px inner radius, 16px label
inset and 48px title target, including Distance Breakdown, provenance, form
groups, research evidence and Detailed Aggregate Statistics. Inner tables retain
their bounded scroll containers.

PCA and cluster controls use equal grid tracks with zero inherited button margins,
44px targets and nested 12px/8px radii. The full phone projection control uses
two columns; the compact preview uses three.

## Evidence

- [Before](control-layout-before.json): seven clipped fields at each viewport,
  unequal PCA widths and inherited button-margin mismatches.
- [After](control-layout-after.json): zero failures at 1440x900, 768x1024, 375x812.
- Real API prediction after editing a formerly clipped field; Distance Breakdown
  and Detailed Aggregate Statistics open correctly; no page-level overflow.
- Inspected actual screenshots under ignored `points/controls-after/`.
- Focused existing web suite: 55 passed. Scoped Ruff and diff whitespace pass.

The user-requested app remains running on port 7860 with the updated CSS and the
existing backend on 8000. No model, API contract, artifact or deployment changed.
