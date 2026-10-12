STATUS: done

Files changed:
- `brain-plot/erp_plot.py` — step 1: added `SIDE_MAP_SHARE, SIDE_HEAD_MAX_MM = 0.45, 40.0` next to `MIN_WAVE_MM`; step 2: in `canvas()` replaced the fixed-19 mm head with the panel-height/width-derived `head` (docstring phrase updated); step 3: in `draw()` replaced the map `subgridspec` with the head/block/pad computation (`area` centred on the panel, `hspace=MAP_GAP_MM/head`) and changed the window text to use `pos = area.get_position(fig)`.
- `brain-plot/test/test_erp_plot.py` — step 4: inserted section 4b2 (300 × 150 mm box, one panel, 3 maps; head ≥ 30 mm, row gap ≤ 6 mm, block centre within 3 mm) after the end of 4b.
- `brain-plot/references/spec.md` — step 4: `map_placement` `"side"` row now states the head size follows the panel height (≤ 40 mm, column ≤ 45 % of the width) and the block is centred on its panel.

Could not do: nothing. Syntax-only check run: `python -m py_compile brain-plot/erp_plot.py brain-plot/test/test_erp_plot.py` → OK. The Check was not run (left to the runner); no commits, no other files touched.