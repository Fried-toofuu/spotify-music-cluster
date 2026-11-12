# Acoustic Observatory visual critique

## Review basis

This is an independent read-only critique of the baseline UI for the accepted
refinement direction: charcoal surfaces, restrained teal/violet cluster
identity, serif display type, sans body copy, and mono technical labels. I
reviewed `docs/DESIGN.md`, `plans/20261112-ui-refinement/plan.md`, the twelve
baseline tab screenshots at 1440, 768, and 375 widths, and
`reports/baseline.json`. The baseline came from the main checkout identified in
the plan (`7fb39ef9e0221e84951c8e7d607c5c7469165f70`).

The visual language is already coherent: the charcoal/teal/violet system reads
as a scientific instrument, cluster identity is carried by labels and marker
shape as well as color, and the serif/sans/mono contrast is distinctive without
being decorative. The highest-value work is information architecture and
responsive prioritization, not a palette or component restyle.

## Baseline rubric

Scores use a 0–3 scale: 0 = absent or broken, 1 = present but high-friction,
2 = usable with material friction, 3 = clear and strong for the stated scope.

| Check | Score | Evidence from baseline | Acceptance check for the refinement |
|---|---:|---|---|
| **1. Acoustic map in the first viewport** | **1/3** | `baseline.json` reports the map at y=818px (1440), y=825px (768), and y=1200px (375). The 1440 and 768 captures show only the map header entering a 900/1024px viewport; the 375 overview reaches the map only after the long hero, caveat, and intro cards. The product’s primary content is therefore below the fold on every tested width. | At 1440×900, show a recognizable map plot (not only its card header) beside a compact introduction. At 375×812, show the map or a purposeful map preview immediately after a short orientation block. Keep the caveat visible but cap its measure/height so it does not displace the instrument. |
| **2. Compact mobile header and discoverable tab entry** | **1/3** | At 375px, the brand, status chips, refresh button, API status card, and tab row consume roughly the first 390px before page content. The tab row exposes clipped labels (for example `PREDICT…` on Overview and a clipped left edge on Research); there is no strong affordance that more tabs are horizontally scrollable. The active underline is clear, but entry is slow and easy to miss. | Reserve one compact header block, keep the status/refresh affordance concise, and make all four destinations reachable without clipped labels. If tabs scroll, preserve a visible partial next-tab cue and keyboard focus; otherwise use a compact 2×2 mobile tab grid. Verify active, focus, and selected states at 375px and landscape 768px. |
| **3. Explorer filters and sample inspector agreement** | **1/3** | The map has the right controls (2D/3D/Density plus Both/Cluster 0/Cluster 1), but their compact pill groups lack plain-language grouping or a clear “what will change” cue. The inspector is an empty card until a plot point is clicked; the baseline does not tell a touch user how to select a point, and the useful descriptor/nearest-neighbour content sits far below the map on mobile. The profile comparison is readable but visually detached from the selected sample. | Give filters explicit group labels and persistent pressed/disabled states; preserve the camera when changing cluster filters. Show a useful inspector empty state with a one-step “tap a point” instruction, then confirm the selected point, cluster, permitted descriptors, and nearest neighbours in the same visual context. On mobile, keep the inspector adjacent to the map before aggregate comparison. |
| **4. Prediction result first, distance detail on demand** | **1/3** | Empty prediction screens expose a large unused distance region, the “Submit a feature vector to see distances” placeholder, and an empty table header even before a request. At 375px this creates a long blank gap between the result card and exact distances; at 1440px the right column has the same dead space. The primary outcome and supporting evidence have equal visual weight despite no evidence existing yet. | Keep the result/status card as the primary outcome. Hide the distance chart/table and explanatory note behind a clearly labeled, closed “Distance breakdown” disclosure until a real prediction returns; after success, show a compact two-row summary and let the user expand exact chart/table details. Confirm no empty chart frame, no blank gap, and preserved scroll-to-result after submit. |
| **5. Research as three progressive layers** | **1/3** | Research is a complete evidence dump in the baseline: data, representation, dominant finding, historical-vs-deployment table, two comparisons, limits, charts, and archived evidence all render expanded. The 375 capture is 5,892px tall; the exact archived table is clipped/truncated on mobile, while the figures and caveats compete with the main finding. There is no first-pass summary versus method versus archival detail. | Make layer 1 a short answer/key finding, layer 2 the method plus limitations, and layer 3 the exact figures/archived evidence. Keep layer 1 open and layers 2–3 progressively disclosed with stable headings and counts/status labels. At 375px, tables must remain readable in a bounded scroller and the main caveat must precede, not follow, the evidence. |

## Five concrete checks to apply during implementation review

1. **Measure the first viewport, not only total-page polish.** Capture 1440×900,
   768×1024, and 375×812 with the same ready state. Record the first visible
   plot pixels, the first meaningful heading, and whether the primary next
   action is visible. The map should be legible in the first viewport without
   making the intro unreadable.
2. **Test mobile entry with one thumb and a keyboard.** At 375px, reach every
   tab from the top, then tab through the navigation. No label may be clipped,
   no control may be below a 44px hit target, and the active tab must remain
   obvious after horizontal scroll or grid reflow. Check landscape 768px for
   accidental two-line header growth.
3. **Run an Explorer selection script.** Starting from a fresh tab: identify
   the map, toggle one cluster, switch view, select a point, and reset. At each
   step confirm pressed state, map/camera continuity, and inspector agreement.
   The inspector must state what is selected and expose the permitted raw
   descriptors and nearest-neighbour context; do not rely on hover alone.
4. **Run prediction in both empty and success states.** Before submit, there
   should be no empty distance chart or table scaffold competing with the form.
   After submit, the assigned cluster and concise distances should appear first;
   exact chart/table evidence should be explicitly expandable. Verify loading,
   error, stale-output clearing, reduced motion, and keyboard focus behavior.
5. **Audit Research at three disclosure depths.** Confirm that a visitor can
   understand the finding from layer 1 alone, reproduce the meaning from layer
   2, and reach every archived value/figure in layer 3 without losing context.
   Test mobile table scrolling, long headings, visible “NOT VERIFIED” status,
   and screen-reader order. No historical metric may visually read as a
   deployment score.

## Cross-cutting guardrails

- Keep the existing tokens and cluster symbols; do not use color as the only
  assignment cue.
- Preserve visible 2px focus outlines, semantic button/summary controls, and
  `prefers-reduced-motion` behavior while adding disclosure or filter states.
- Keep body copy at a readable measure and avoid introducing sub-12px text to
  recover space on mobile.
- Maintain bounded table/plot overflow inside the component; the page itself
  must not acquire horizontal scroll.
- The strongest visual hierarchy should be: map/finding → user action → exact
  evidence. Decorative depth or animation should not compete with those three.

## Unresolved questions

- For the compact 375px navigation, should the implementation prefer a visible
  two-row tab grid or a horizontally scrollable one-row strip with a next-item
  cue? Either can satisfy the direction, but the choice should be consistent
  across all four tabs.
- Should the Explorer inspector remain an empty state until selection, or show a
  representative schema preview before selection? The latter may better teach
  the interaction but must not be mistaken for real sampled-track data.
