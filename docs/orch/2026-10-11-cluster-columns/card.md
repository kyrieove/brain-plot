# cluster-columns — second layout: tests as columns, raster split Left / Midline / Right, topomap rows below

## Goal
New spec key `layout`: `"side"` (default, today's one-figure-per-test layout, unchanged output) or `"columns"`
(user's reference figure, 2026-10-11): ONE figure for all tests; top block = one column per test, each column three
stacked raster sub-panels (Left, Midline, Right hemisphere groups from `channel_rows`), one shared raster colour bar at
the right; bottom block = one row of topomaps per test, all time bins side by side across the full width, test label at
the row's left, one shared map colour bar at the right. `side` renders stay byte-for-byte equivalent in layout.

## Risk
medium — new layout path in `plot()`; no number changes (Claude re-checks Oz 702–800 ms = 7.765 µV and opens both
renders).

## Parameters
- `layout`: `"side"` | `"columns"`; anything else stops. `columns` needs `channel_order: "lmr"` (stop otherwise:
  `layout "columns" splits the raster by hemisphere; set channel_order to "lmr"`), 1–3 tests (stop above 3), and all
  tests with the same `statistic` when `color: "stat"` (stop: `layout "columns" shares one colour scale; tests mix t and F`).
- Canvas: `width_mm` default 180. Margins: left 24 mm (group names + channel labels), right 14 mm (colour bars),
  top 12 mm.
- Raster columns: gap 8 mm between columns; column width `cw = (W − 24 − 14 − (n − 1) × 8) / n`. Sub-panel height =
  1.2 mm × number of rows in that group (every other channel labelled, fontsize 5, as `side`), 2.5 mm gap between
  sub-panels; x tick labels only on the Right (bottom) sub-panel, "Time (ms)" under it; ticks on all three.
  Channel tick labels on every column (the reference repeats them). Group names `Left` / `Midline` / `Right`
  (fontsize 6, rotation 90) only left of the first column, 19 mm left of it. Column title = test label (fontsize 7)
  above the Left sub-panel. Panel letter per column (`a`, `b`, …) on its Left sub-panel.
- Raster colour scale: ONE scale for all columns: v = max over tests of the per-test v rule (today's rule); RdBu_r ±v
  or Reds 0..v; one colour bar right of the last column (2 mm wide, 3 mm gap) spanning the whole raster block.
- Topomap block: starts 16 mm below the raster block's x label. One row per test (top to bottom in `tests` order);
  maps of a row side by side; `map_mm = min(20, (W − 24 − 14 − (n_maps − 1) × 2) / n_maps)` with n_maps = the largest
  map count of any row; 2 mm gaps; time label under every map (fontsize 5); row label = test label, fontsize 6,
  right-aligned 2 mm left of the first map, vertically centred; row pitch `map_mm + 7`. Panel letters continue
  (`c`, `d`, … on each row's first map). ONE shared map colour scale over all rows (µV if every test has a µV
  difference, else the statistic, per today's per-test rule taken over all rows) and one colour bar at the right
  spanning the map block. A test with no maps: its row shows "no significant cluster" (fontsize 5).
- Height: `H = 12 + raster_block + 10 (x labels) + 16 + n_tests × (map_mm + 7) + 4` unless `height_mm` is given.
  GN (2 tests, 64 channels, 8 bins): raster block ≈ 0.0012 m… i.e. 1.2 × (28 + 8 + 28 rows) + 2 × 2.5 ≈ 82 mm,
  maps 16.7 mm → H ≈ 172 mm.
- Output: one figure; stem `cluster_{color}-{display}_columns_t{NN}-t{NN}…_topo-{bins<step>ms|clusters}` (+ `_lock-…`);
  `_run.json` holds every test's record (same record dict as today) and `layout: "columns"`; `_caption.md` = the
  per-test caption lines of every test, in order (reuse `write_caption`'s per-test body — make it take a list of tests,
  `side` passes one). `plot()` still returns a list of output prefixes (one element).

## Files
may change: `brain-plot/cluster_plot.py`, `brain-plot/test/test_cluster.py`, `brain-plot/references/cluster.md`, `brain-plot/references/spec.md`
read-only: `brain-plot/erp_plot.py`, `C:\Users\ASUS\Dropbox\metaphor_production\gn_manuscript\03-ERP_topomap\03_cluster_inference\01_cluster_based_permutation_0000_0800ms\`, `C:\Users\ASUS\Dropbox\metaphor_production\gn_manuscript\01-evokeds_grand_averages\`

## Steps (N = 5)
1. `check_spec`: `layout` and its stops (Parameters); add to `OPTIONAL`. The mixed-statistic check needs the test
   metadata: do it in `plot()` right after `read_run`.
2. Refactor `plot()` (cluster_plot.py:315–494) into helpers used by BOTH layouts, no duplicated block:
   `raster_limits(t, color, display)` → (v, vmin, vmax, cmap name) (today's lines ~388–395);
   `raster_array(t, rows, values)` → (masked array, sig) (today ~397–403) — for `columns` call it with the rows of
   one group (slice of `rows`, without separator rows);
   `draw_raster(ax, arr, sig, display, extent_rows, cmap, vmin, vmax)` → im (imshow + optional contour);
   `colorbar(fig, rect_mm, im, ticks, title, W, H)` (today's two colour-bar blocks);
   `topo_limits(maps_list, has_uv, info, sphere)` → (vt, lo, hi, cmap, sensor, interp) over one or several tests' maps;
   `draw_map(fig, rect_mm, vec, marked, lab, cmap, lo, hi, info, sphere, W, H)` → im.
   Then `plot_side(...)` = today's per-test loop using the helpers (same output), `plot_columns(...)` = the new
   layout; `plot(spec)` prepares data once (run, µV, info, sphere, rows, maps per test) and dispatches.
3. `plot_columns` per Parameters. Group rows: split `rows` at separator rows into the three groups (keep the group
   name from the rows); each sub-panel's extent uses its own row count.
4. `test_cluster.py`: (j) `layout: "columns"` with tests [01, 03] writes one figure whose name has `_columns_t01-t03_`,
   `layout_issues == []`, and its `_run.json` holds both tests; (k) `layout: "columns"` with tests [01, 02] (t and F,
   colour stat) stops ("mix t and F"); (l) `layout: "columns"` with `channel_order: "file"` stops; (m) the default
   (side) outputs and every earlier assert unchanged.
5. Docs: `references/cluster.md` (round 2 now asks `layout`; QA items for columns: three sub-panels per column, one
   colour bar each block, map labels readable) and `references/spec.md` (key + name pattern). Run the Check yourself
   in the foreground until `OK`. Then render GN once with `layout: "columns"` and tests 01 + 03 (spec from card
   `docs/orch/2026-10-10-cluster-v1-v2/card.md` step 5 plus `"layout": "columns"`, written to the system temp dir);
   no `WARNING: layout` line allowed — if one appears, adjust only the Parameters numbers and say so.

## Check
```
python brain-plot/test/test_cluster.py
```

## Don't
- No commits. Write only the files under "may change" (plus the GN render's own outputs in step 5, in the
  `brain_plot_…` folder next to the run folder).
- Do not change the reader, `diff_uv`, `channel_rows`, the bins or the colour-limit rules; `side` output must keep its
  layout and name.
- "Run scripts in the foreground and wait; before replying, stop any background task still running."
- "Reuse existing functions; don't copy existing logic."
- "No rm, no git push, no git checkout . / restore . / reset --hard."
