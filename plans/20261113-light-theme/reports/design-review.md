# Permanent Light Scientific Editorial theme review

Review date: 2026-11-13. This is a read-only design and contrast review of the
current light-theme implementation in `theme.py`, `explorer.py`, `figures.py`
and `scripts/constellation/entry.js`. The review does not change layout,
interaction, or scientific behavior.

## Evidence and method

The source review covered the token map, Gradio theme slots, `color-scheme`
enforcement, hover/selected/disabled/focus/busy rules, Plotly figure defaults,
heatmap colors, 2D/3D marker opacity, and the Three.js background/selection
colors. Ratios below use WCAG 2 relative luminance, rounded to two decimals.
Normal text uses the 4.5:1 AA threshold; large text uses 3:1; UI components and
informational graphics use 3:1.

The local browser evidence reports all 27 light-preference checks as PASS in
`light-browser.json`, and the existing points-mode walk reports all 26 checks as
PASS in `points-browser.json`. I inspected the local ignored captures for the
desktop overview, Explorer 2D/3D/constellation/density, prediction, error and
research states. Repeated `net::ERR_ABORTED` data requests in those JSON reports
have no recorded browser errors and do not appear to be palette failures.

## Palette results

| Foreground | On `bg` `#F7F9FC` | On `surface_1` `#FFFFFF` | On `surface_2` `#F0F3F7` | On `surface_3` `#E8EDF3` | Assessment |
|---|---:|---:|---:|---:|---|
| `ink` `#17212B` | 15.45 | 16.29 | 14.64 | 13.84 | Passes normal text everywhere |
| `ink_2` `#556270` | 5.91 | 6.24 | 5.60 | 5.30 | Passes normal text everywhere |
| `muted` `#596775` | 5.50 | 5.80 | 5.21 | 4.93 | Passes normal text everywhere |
| `teal` `#147D73` | 4.73 | 4.99 | 4.48 | 4.24 | Use as normal text on `bg`/`surface_1`; graphical use passes 3:1 |
| `violet` `#7055B9` | 5.40 | 5.69 | 5.11 | 4.84 | Passes normal text and graphical use |
| `amber` `#8A5B10` | 5.55 | 5.86 | 5.26 | 4.98 | Passes normal text and graphical use |
| `danger` `#B42335` | 6.16 | 6.50 | 5.84 | 5.52 | Passes normal text and graphical use |
| `success` `#147D59` | 4.85 | 5.11 | 4.59 | 4.34 | Passes normal text on `bg`/`surface_1`; graphical use passes 3:1 |
| `line_strong` `#7B8896` | 3.43 | 3.62 | 3.25 | 3.07 | Passes non-text/UI boundary contrast |
| `line` `#E0E6ED` | 1.19 | 1.26 | 1.13 | 1.07 | Decorative divider only; not an affordance |

White `on_accent` text is 4.99:1 on teal, 5.69:1 on violet, 5.86:1 on
amber, 6.50:1 on danger and 5.11:1 on success. The current primary button
text and contribution-bar inside labels therefore have a safe pairing. The
`teal_dim` hover token `#10665E` is 6.81:1 with white.

The current `color-scheme: only light`, light meta tag, `__theme=light` URL
selection, and mirrored Gradio dark compatibility slots are consistent with a
permanent light route. No dark media query or alternate application palette was
found in the reviewed sources.

## Explicit state and graph review

Passes observed in source and loaded captures:

- Ready/offline/connecting status has a written label in addition to the teal,
  danger or amber dot (`theme.py:165-171,410`); it does not rely on color alone.
- Pressed Explorer controls use `ink` on `surface_3` (`explorer.py:78-80`),
  and focus outlines use solid teal. The outline is at least 4.24:1 even on
  `surface_3`, above the 3:1 non-text threshold.
- Empty states, Plotly hover labels and table text use the dark ink/secondary
  tokens. Primary and secondary buttons have safe text/background pairings.
- Cluster 0/1 retain labels plus circle/diamond marks. The Plotly point colors
  and Three.js scene use the new palette, with an ink-colored Three.js selection
  marker (`entry.js:71-95`) rather than the former white-on-light marker.
- `figures.py` now renders on a white plot surface, uses `on_accent` for inside
  bar labels, and keeps the dark ink for outside labels and hover text.

The following concerns remain before calling the conversion fully verified:

1. **Busy-state opacity removes text contrast.** `theme.py:437` fades the
   pending selected card to `.5`; dark ink composited at that opacity on white
   is only 3.22:1, while secondary and muted text are 2.18:1 and 2.12:1.
   `theme.py:439` fades the prediction result to `.65`; its ink remains 5.10:1,
   but secondary and muted text fall to 2.89:1 and 2.79:1. Apply the fade to a
   visual region or add a loading overlay while keeping readable text at full
   opacity.

2. **Density scale is too pale at the low end for an informational graphic.**
   On the white Plotly surface, `density_low` `#C9E4DF` is 1.34:1 and
   `density_mid` `#79B8AD` is 2.26:1; only `density_high` `#3D9589` (3.58:1)
   and teal (4.99:1) meet the 3:1 graphical target. The screenshot makes the
   low-count cells visibly faint. Darken the lower stops (approximately
   `#5D9F96` gives 3.06:1 on white) or add a non-color boundary/texture while
   retaining the existing numeric hover details.

3. **Unfilled slider and meter rails are visually very faint.** `surface_3`
   against the white form is only about 1.18:1, and the reviewed prediction
   capture shows pale rails with the teal fill and thumb carrying most of the
   value cue. Set the rail to a neutral meeting 3:1 (the existing
   `line_strong` is 3.62:1 on white) or otherwise preserve a clearly visible
   track. This is a graphical/UI contrast issue, not a change to slider values.

4. **Disabled density filters are washed out.** `explorer.py:273-280` disables
   the cluster chips in density mode and `explorer.py:81` supplies muted text,
   but no explicit opacity reset. The loaded density capture shows the chips
   very faint, consistent with Gradio's disabled opacity. Preserve the
   strike-through/disabled semantics but keep the label and swatch perceivable
   with explicit disabled styling.

5. **Error styling does not use the danger token.** The prediction error capture
   presents “COULD NOT COMPLETE” in the teal kicker style, while `danger` is
   currently used only for the offline status dot. Keep the written error text
   and live-region semantics, but use a danger kicker or border for error cards;
   `#B42335` is 6.16:1 on the page and 6.50:1 on white, so this can improve
   scanning without a contrast trade-off or color-only meaning.

6. **Point-cloud opacity is close to the graphical threshold.** Explorer 2D
   uses `.72` and 3D `.82` (`explorer.py:324-343`). On white, teal composites
   to 3.02:1/3.61:1 and violet to 3.20:1/3.89:1. They pass on the current
   explicit white plot surface, and the captures are readable, but antialiasing
   or a different surface would drop below 3:1. Keep the plot surface fixed or
   raise opacity toward `.95` (teal 4.52:1; violet 5.11:1).

The very light `line` token is acceptable for non-semantic separators and chart
gridlines because labels and marks carry the information, but it should not be
the sole boundary for an interactive control. `line_strong` is suitable for
inputs, accordions, focus-adjacent boundaries and other affordances.

## Documentation and verification limits

`docs/DESIGN.md:3-34` still describes the old charcoal palette and
`docs/DESIGN.md:78-80` records old contrast ratios. `docs/WEB.md:137-143` does
the same. These are stale design authority after the permanent light change and
must be updated before the project claims the docs describe the shipped theme.

The available captures cover loaded desktop/tablet/mobile views and the main
visualization modes, but they are local ignored files rather than durable report
artifacts. I did not receive separate visual captures for pending/busy, loading,
backend-offline, or keyboard-focus states; those findings above are source and
computed-ratio checks. The browser JSON evidence was not rerun as part of this
read-only review.

Status: DONE_WITH_CONCERNS
Summary: The proposed light palette is strong for normal text, controls, focus,
buttons and the loaded scientific views, with permanent light enforcement in
place. Busy opacity, low-end density colors, disabled filter rendering, faint
slider rails and missing danger styling should be addressed or explicitly
accepted before final sign-off.
Concerns/Blockers: See the six numbered concerns and stale design documentation
above; no scientific or functional regression was inferred from the captures.
