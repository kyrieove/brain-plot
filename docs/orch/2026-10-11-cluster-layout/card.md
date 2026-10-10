# cluster-layout — one test per figure, raster left + topomap grid right (like ERP combo side); L / midline / R channel rows

## Goal
`cluster_plot.py plot` writes **one figure per test** in `spec["tests"]`. Each figure: the channel × time raster on
the left, the topomaps in a 2-column grid on the right (like `erp_plot` combo with side maps), so the maps are
~19 mm instead of 11 mm. Raster rows are ordered left hemisphere / midline / right hemisphere, each anterior →
posterior, with a thin white gap and a group name between groups, and only every other channel name as a tick label.
User feedback 2026-10-11 on the v02 render: too many electrode labels; 8 maps wrapped 5 + 3 and too small.

## Risk
medium — layout rewrite of `plot()`; no number changes (Claude re-checks Oz 702–800 ms = 7.765 µV is unchanged and
opens the render).

## Parameters
- Canvas: `width_mm` default 180; `height_mm` default computed (below). Top margin 12 mm, bottom 14 mm (x labels).
- Raster: left edge 22 mm (tick labels + group names), height `raster_h` = 100 mm, width
  `rw = W − 22 − 16 − maps_w − 14` (16 = raster colour bar + its labels, 14 = map colour bar + labels at the right edge).
  For W = 180 and the GN case: maps_w = 41 mm → rw = 87 mm.
- Raster colour bar: 2 mm wide, 3 mm right of the raster, full raster height (as now).
- Map grid: 2 columns, `n_rows = ceil(n_maps / 2)`; `map_mm = min(24, (raster_h − n_rows × 6) / n_rows)` (6 mm per row
  for the time label under each map); column gap 3 mm → `maps_w = 2 × map_mm + 3`; the grid's top aligns with the
  raster top; rows `map_mm + 6` apart. GN (8 maps): n_rows 4, map_mm 19 mm. One map colour bar right of the grid
  (2 mm wide, 3 mm gap), height = grid height. 1 map → 1 column.
- Height: `H = 12 + max(raster_h, n_rows × (map_mm + 6)) + 14` unless `height_mm` given.
- Channel order (new optional spec key `channel_order`: `"lmr"` default, `"file"` = result-file order as before):
  from `info` positions (`ep.common_sphere` is not needed; use `mne.channels.layout._find_topomap_coords(info,
  picks=np.arange(len(info.ch_names)), sphere=sphere)` like `ep.common_sphere` does) → x, y per channel;
  midline = |x| ≤ 0.1 × max|x| (Fz, Cz, Pz, Oz, Fpz, AFz, FCz, CPz, POz, Iz in 10-20); left = x < that, right = x > that;
  inside each group sort by y descending (anterior first). Groups in order Left, Midline, Right; an empty group is
  skipped. The reorder applies to rows of stat, mask and uv (columns of the (n_times, n_ch) arrays) and to tick labels;
  topomaps are unaffected.
- Group separation: one blank row between groups (fill the imshow array with NaN rows / masked rows → drawn white);
  group name (`Left`, `Midline`, `Right`, fontsize 6, rotation 90) centred on the group, 15 mm left of the raster
  (x in axes fraction from the raster width), no "Channel" y label any more.
- Tick labels: every other channel inside each group (1st, 3rd, …), fontsize 5; the other rows get a tick without a
  label. With `channel_order: "file"`: every other channel of the file order, no groups.
- Output name per figure: stem `cluster_{color}-{display}_t{NN}_topo-{bins<step>ms|clusters}` (+ `_lock-…`), `NN` =
  the test's leading number; one `_run.json` / `_caption.md` per figure (records/caption lines of that test only);
  `plot()` returns the list of output prefixes.
- Panel letters: raster `a`, map grid `b` (letter on the first map).

## Files
may change: `brain-plot/cluster_plot.py`, `brain-plot/test/test_cluster.py`, `brain-plot/references/cluster.md`, `brain-plot/references/spec.md`
read-only: `brain-plot/erp_plot.py`, `C:\Users\ASUS\Dropbox\metaphor_production\gn_manuscript\03-ERP_topomap\03_cluster_inference\01_cluster_based_permutation_0000_0800ms\`, `C:\Users\ASUS\Dropbox\metaphor_production\gn_manuscript\01-evokeds_grand_averages\`

## Steps (N = 5)
1. `check_spec`: accept `channel_order` ("lmr" | "file", else stop with the fix). Add it to `OPTIONAL`.
2. New function `channel_rows(info, ch_names, mode, sphere)` → `(order, rows)`: `order` = channel indices in display
   order; `rows` = list of `(label_or_None, channel_index_or_None, group_name)` including one `None` row between
   groups; per Parameters. Midline tolerance and sort per Parameters.
3. `plot(spec)`: loop over tests, one figure each (move the per-test body into the loop; compute `info`/`sphere`
   once, before the loop). Build the raster array with the blank rows (`np.full(..., np.nan)` then
   `np.ma.masked_invalid`, plus the significance mask in masked display; for contour display draw the contour on the
   reordered mask with blank rows = 0). Layout, colour bars, map grid, letters, tick labels, group names exactly per
   Parameters. Name, `_run.json` and `_caption.md` per figure (adapt `write_run_json` / `write_caption` to one test; no
   copy of their bodies). `ep.report_layout` → `layout_issues` per figure. Return the list of prefixes.
4. `test_cluster.py`: update the existing asserts to the per-test outputs (`_t01_` and `_t03_` figures instead of
   `_t01-t03_`; every figure `layout_issues == []`); add: (i) with the synthetic channels the row order for "lmr" is
   Left [C3], Midline [Fz, Cz, Pz, Oz], Right [C4] (check via `channel_rows`); (ii) `channel_order: "file"` renders;
   (iii) a bad `channel_order` value stops. Keep all other asserts.
5. Docs: `references/cluster.md` and `references/spec.md` — one figure per test, `channel_order`, new name pattern,
   QA item "maps ≥ 15 mm, every other channel labelled, group names readable". Then run the Check yourself in the
   foreground until `OK`, and render GN tests 01 and 03 once with the spec from card
   `docs/orch/2026-10-10-cluster-v1-v2/card.md` step 5 (written to the system temp dir); no `WARNING: layout` line
   allowed — if one appears, adjust only the Parameters numbers (raster_h, fontsize) and say so.

## Check
```
python brain-plot/test/test_cluster.py
```

## Don't
- No commits. Write only the files under "may change" (plus the GN render's own outputs in step 5, in the
  `brain_plot_…` folder next to the run folder).
- Do not change the reader, `diff_uv`, colour-limit rules or the bins; this card is layout only.
- "Run scripts in the foreground and wait; before replying, stop any background task still running."
- "Reuse existing functions; don't copy existing logic."
- "No rm, no git push, no git checkout . / restore . / reset --hard."

- scope override: research/cluster-figures/survey.md was edited by Claude during the run (channel-order corrections), not by the executor
