# combo-side-adaptive — side-layout topomaps sized from the canvas, block centred on its waveform panel

## Goal
In `kind: "combo"`, `map_placement: "side"`, the topomap head size follows the waveform panel height and the canvas
width instead of a fixed ~19 mm per head column, and the map block is vertically centred on its panel. Reported
case (2026-10-12): 300 × 150 mm, one panel, `axes: "box"`, six conditions → 19-mm heads at the top and bottom of a
127-mm column with ~45 mm empty between the rows. After the change that case gives ~39-mm heads, rows 3 mm apart,
block centred on the waveform. Multi-panel figures at the default 180 × 120 mm keep (almost) the same head size.

## Risk
medium — figure geometry only; no computed numbers change.

## Parameters
- `SIDE_MAP_SHARE = 0.45` — the map column is at most this share of `usable` (was `0.55 * usable` with 19 mm/column).
- `SIDE_HEAD_MAX_MM = 40.0` — largest head side in the side layout.
- Gap between map rows = `MAP_GAP_MM` (3.0, existing constant) exactly.
- Subgrid `wspace = 0.02` between map columns (unchanged).
- Test case: 300 × 150 mm, `axes: "box"`, one panel, 3 lines (2 × 2 grid, 3 maps): every head ≥ 30 mm wide, vertical
  gap between the two map rows ≤ 6 mm, map block centre within 3 mm of the waveform axes centre.

## Files
may change: `brain-plot/erp_plot.py`, `brain-plot/test/test_erp_plot.py`, `brain-plot/references/spec.md`
read-only: `brain-plot/test/fixtures/`, `examples/`

## Steps (N = 4)
1. `brain-plot/erp_plot.py`, next to `MIN_WAVE_MM` (line ~1140): add the two constants
   ```python
   SIDE_MAP_SHARE, SIDE_HEAD_MAX_MM = 0.45, 40.0  # rule L4: side map column ≤ 45 % of the usable width; head ≤ 40 mm
   ```
2. `brain-plot/erp_plot.py` → `canvas()` (line ~1157): replace the line
   `topo_mm = min(19 * topo_grid(n_lines)[1], 0.55 * usable) if maps else tiny`
   with a head size derived from the panel height (reuse `wave_panel_mm`, do not re-derive the panel height):
   ```python
   nrow_t, ncol_t = topo_grid(n_lines)
   cols = ncol_t + 0.02 * (ncol_t - 1)  # columns + the subgrid's wspace 0.02 in draw()
   head = min((wave_panel_mm(H, n, is_box) - (nrow_t - 1) * MAP_GAP_MM) / nrow_t,  # rows fill the panel height
              SIDE_HEAD_MAX_MM, SIDE_MAP_SHARE * usable / cols)
   topo_mm = head * cols if maps else tiny
   ```
   Keep this before the `GridSpec(...)` call (it already is). Update the docstring phrase
   "(~19 mm per head column, at most 55 % of what is left)" to
   "(head side from the panel height, at most 40 mm and 45 % of what is left)". Nothing else in `canvas()` changes.
3. `brain-plot/erp_plot.py` → `draw()`, the block after `# rule L4: topomaps to the right` (lines ~1608–1629):
   - Replace the `sub = gs[r_i, 2].subgridspec(...)` statement with:
     ```python
     W, H = canvas_size(spec)
     cell = gs[r_i, 2].get_position(fig)
     cell_w, cell_h = cell.width * W, cell.height * H
     head = min(cell_w / (ncol_t + 0.02 * (ncol_t - 1)), (cell_h - (nrow_t - 1) * MAP_GAP_MM) / nrow_t)
     block = nrow_t * head + (nrow_t - 1) * MAP_GAP_MM
     pad = (cell_h - block) / 2
     area = gs[r_i, 2].subgridspec(3, 1, height_ratios=[pad, block, pad], hspace=0)[1] if pad > 0.5 else gs[r_i, 2]
     sub = area.subgridspec(nrow_t, ncol_t, wspace=0.02, hspace=MAP_GAP_MM / head if nrow_t > 1 else 0)
     ```
     (In the subgrid the cell height is `head` exactly: `block = nrow·head + (nrow−1)·hspace·head`.)
   - The window text: replace `pos = gs[r_i, 2].get_position(fig)` with `pos = area.get_position(fig)` so
     "<name>  <tmin>–<tmax> ms" sits just above the map block, not above the full panel column.
   - Do not touch `map_hspace` (still used by `draw_topo` at line ~1702), the colour bar, the legend code or the
     `inset` layout.
4. `brain-plot/test/test_erp_plot.py`: right after the block that ends with
   `assert any(t == "a" for t, _ in texts_of(SAVED[-1]))` (end of section 4b, line ~257), insert:
   ```python
       # 4b2. side combo (rule L4): map size follows the panel height, block centred on its panel (user, 2026-10-12:
       #      a 300 × 150 mm single panel left 19-mm heads at the top and bottom of a 127-mm column)
       ep.plot(spec(root, groups=["G1"], overlay="conditions", axes="box", width_mm=300, height_mm=150))
       fig = SAVED[-1]
       R, mm = ep.renderer(fig), 25.4 / fig.dpi
       heads = [a.get_window_extent(R) for a in fig.axes if a.images]
       wave = next(a for a in fig.axes if a.lines and not a.images).get_window_extent(R)
       assert len(heads) == 3 and min(b.width for b in heads) * mm >= 30, [round(b.width * mm, 1) for b in heads]
       top = max(b.y0 for b in heads)
       gap = top - max(b.y1 for b in heads if b.y0 < top - 1)
       assert gap * mm <= 6, gap * mm
       mid = (max(b.y1 for b in heads) + min(b.y0 for b in heads)) / 2
       assert abs(mid - (wave.y0 + wave.y1) / 2) * mm <= 3, (mid, wave)
       inside_canvas(fig)
   ```
   Then `brain-plot/references/spec.md`, the `map_placement` row: change
   `"side"`: stacked waveform panels, maps in a column right of each.` to
   `"side"`: stacked waveform panels, maps in a column right of each; the head size follows the panel height (at most 40 mm, map column at most 45 % of the width) and the block is centred on its panel.`

## Check
`MPLBACKEND=Agg python brain-plot/test/test_erp_plot.py`
(prints `OK` at the end; the new section 4b2 fails on the old code: heads ~19 mm.)

## Don't
- No commits, no other files, no refactors beyond the steps; reuse `wave_panel_mm`, `topo_grid`, `canvas_size`, `MAP_GAP_MM`.
- Do not change the inset layout, `draw_topo`, `map_hspace`, the colour bar or legend placement.
- "Run scripts in the foreground and wait; before replying, stop any background task still running."
- "Reuse existing functions; don't copy existing logic."
- "No rm, no git push, no git checkout . / restore . / reset --hard."

## Acceptance
- verdict: accepted (rendered 300x150 / 180x90 / 180x150 two groups / 180x100 on synthetic six-condition data: heads 39 mm at 300x150, blocks centred, layout_issues empty)
- files: brain-plot/erp_plot.py, brain-plot/references/spec.md, brain-plot/test/test_erp_plot.py
- check: `MPLBACKEND=Agg python brain-plot/test/test_erp_plot.py` → exit 0 (run by run-card)
- tokens:
  - round 1: exec deepseek-v4.1-flash: fresh 23k, cached 954k, out 8k  (codex-combo-side-adaptive.jsonl) · review gpt-6-luna: fresh 46k, cached 260k, out 2k  (codex-review-combo-side-adaptive.jsonl)
- review findings: 0 real / 1 false positive (reply.md flagged as out of scope; it is the runner's own reply file) / 0 missed (medium, gpt-6-luna)
- claude fix: none needed; review_fail is the reply.md false positive
