# Browser presentation review

Chrome/Playwright, dark preference, 1440×900, 768×1024 and 375×812. All four tabs
were navigated at each size. Twelve tab screenshots plus three invalid-input
screenshots are stored in [screenshots](screenshots/). Screenshots were opened
and inspected, including desktop overview, tablet methodology and phone prediction,
explorer and error states. The browser also submits the explicitly synthetic
example, clears an input to exercise validation, changes Mean/Median, switches
to Tempo and selects Cluster 1. No private verification features enter screenshots.

## Problems discovered and fixes

- Replaced the overflowing nine-column example grid with a native labelled example
  button. Retained every F9 value and the API submission behavior.
- Removed duplicate page padding, bounded tab panel intrinsic sizing, used native
  wrapped tab navigation, stacked phone selectors and expanded the last metric card.
- Shortened chart/accordion titles and retained correct axis units. All magnitude
  bar charts now include zero. Prediction and explorer identities wrap on mobile.
- Disabled unnecessary dataframe action buttons after the render checker found
  undersized targets. Kept native horizontal scrolling for wide statistical tables.
- Awaited completed event states and the selected chart labels before screenshots
  so loading transitions are not mistaken for the final presentation.

The frontend skill's `render-check.mjs` reports zero errors at all three widths.
Its three warnings refer solely to the native `.sr-only` Loading announcement:
this text is intentionally clipped for screen readers, not visibly truncated
content. It remains in place for accessibility. No page horizontal overflow or
browser runtime errors were observed in the tested tab workflows.

## Rubric

| Item | Score / 2 | Observed evidence |
|---|---:|---|
| Brief fidelity | 2 | Calm, restrained, analytical; green/blue acoustic bars and dark cards |
| Hierarchy | 2 | Project heading, tab heading, then the primary action or distribution |
| Spacing | 2 | Grouped controls and consistent gaps between chart/text regions |
| Alignment | 1 | Card/grid edges align; native table numbers remain left aligned |
| Typography | 2 | Local system sans, distinct headings, readable wrapped explanations |
| Color discipline | 2 | Accent for action/selection and two explicitly labelled clusters |
| Depth and shape | 2 | Hairlines, flat surface tints, consistent modest radii |
| States and feedback | 2 | Native loading/selection, tested success and visible invalid-input feedback |
| Responsiveness | 1 | No page overflow; wide aggregate tables still require local horizontal scrolling |
| Decorative restraint | 2 | No cover artwork, random scatter, invented personas or ornamental animation |
| Content | 2 | Actual API populations/profiles, clear caveats and archived evidence distinction |
| Craft | 1 | Native Gradio slider number controls and table typography limit customization |

Total: **21/24**, no item below 1. The weakest areas were alignment, responsiveness
and native control details. Improvements focused on stacking selectors, correctly
bounded panels, compact titles and removing unnecessary action buttons, retaining
native Gradio behavior as requested. This review does not establish full WCAG
conformance, cross-browser compatibility or user testing. Only installed Chrome
was exercised; native tables and the nine-field form remain vertically long on phones.

## Follow-up: chart engine correction (2026-11-12)

The smoke then exposed that Gradio 6.31's native `BarPlot` does not apply data
updates: after selecting a cluster, changing Mean/Median or changing the feature,
the title and axis changed but the first bars stayed. A minimal reproduction
outside the application confirmed the defect. Charts are now Matplotlib figures
delivered through `gr.Plot`; the same browser workflow was repeated and now shows
the selected cluster, the selected statistic and the selected feature with correct
bars, tick labels and values. The 375px chart was also enlarged from an unreadable
wide image to a compact 4.6×2.9 figure capped at 620px on desktop.

Revised rubric after the follow-up: **22/24** — responsiveness rises to 2 because
charts are legible on phones without page overflow (wide tables still scroll
locally); alignment and craft remain 1. Charts are static PNGs, so tooltips and
zoom are unavailable; the adjacent tables carry the exact values.
