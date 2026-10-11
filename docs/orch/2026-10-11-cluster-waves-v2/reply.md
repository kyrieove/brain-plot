STATUS: done

Files changed:
- `brain-plot/cluster_plot.py` — in `plot_waves`: right margin `14.0 → 6.0`; 1-column ERP gap `12 → 19` mm and 2-column gap `10 → 17` mm; deleted the single shared `colorbar(...)` call; after each `draw_map` added `colorbar(fig, [map_x + map_mm + 1.5, H - y_top - 0.8 * map_mm, 1.6, 0.6 * map_mm], im, [-vt, 0.0, vt], "µV", W, H)`; dropped the now-unused `last_im`.
- `brain-plot/references/cluster.md` — waves paragraph now says "one small µV colour bar right of every topomap (shared scale across the figure)".
- `brain-plot/references/spec.md` — the `layout` row's `"waves"` text carries the same phrase.
- `docs/plan-waves-v2.md` — item 8 replaced "One µV colour bar per figure." with the new phrase.

Syntax-only check: `compile()` on `brain-plot/cluster_plot.py` passed (no bytecode written).

Could not do: nothing. The Check was not run (left to the runner) and nothing was committed.