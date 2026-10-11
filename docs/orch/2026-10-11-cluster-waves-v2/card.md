# cluster-waves-v2 — rewrite layout "waves": per significant cluster one block = peak-window topomap + ERP of the two compared sides over user-chosen channels

## Goal
`layout: "waves"` of `brain-plot/cluster_plot.py` implements `docs/plan-waves-v2.md` (read it first; it is the spec). When
done: one figure per drawable test (t contrasts with a single difference wave, at least one significant cluster); each
significant cluster is one block = a µV-difference topomap at the cluster peak window plus one ERP panel with the two
compared conditions (mean over `waves_channels`, 95 % CI, cluster window shaded gray); blocks are laid out adaptively
(1–3 one column, 4–6 two columns, more than 6 split into `_part1`, `_part2` of 6 blocks). Tests that cannot be drawn (no
difference wave, i.e. the F interaction; or no significant cluster) are skipped with one terminal line and a record in
`_run.json`; the batch continues. `test/test_cluster.py` passes.

## Risk
medium — new numbers on the figure (peak window, channel means). Claude re-checks one peak time and one waveform value
with plain numpy on the GN data after acceptance.

## Parameters
- New optional spec keys (add to `OPTIONAL`, validate in `check_spec`, every message names the key and says how to fix):
  - `waves_channels`: either a list of channel names (used for every cluster) or a dict `{"<test slug>/<cluster id>": [names]}`
    (cluster id as in `cluster_summary_significant.csv`, written as digits in the key). Lists must be non-empty lists of
    non-empty strings. Only used by `layout "waves"`; ignored elsewhere.
  - `peak_window_ms`: `[lo, hi]` two numbers, `lo < hi`; overrides the computed peak window for every cluster.
  - `waves_xlim`: `"epoch"` (default, the whole evoked time axis) or `"window"` (only the tested range `times_ms[0]`..`times_ms[-1]`).
- Peak window: peak time = the sample inside the cluster window `[time_start_ms, time_end_ms]` where the sum over the
  channels of the cluster of `|t["stat"][sample, channel]|` is largest; window = peak ± 25.0 ms, clipped to the cluster window
  (mask via `ep.sample_mask(times, lo, hi)`). Topomap vector = `t["uv"][mask].mean(0)`; marked channels =
  `t["mask"][mask].mean(0) >= MARK_FRAC` (the existing constant, 0.5). Map label: `peak <peak ms:.0f> ms`; with
  `peak_window_ms` the label is `<lo:g>–<hi:g> ms`.
- Recommended channels: the 6 channels of the cluster with the largest sum over the cluster window samples of `|stat|`,
  descending (ties by channel order); fewer if the cluster has fewer channels.
- Block title: `Cluster <id>: <start:g>–<end:g> ms, p < 0.001, <n> channels` where the p part is `p = <p:.3f>` when `p >= 0.001`, else
  `p < 0.001` (a colon and commas, NO middle dot), n = number of channels of the cluster, fontsize 6, left-aligned at the
  left edge of the block, 2 mm above the block.
- Layout of k blocks in one figure: k ≤ 3 → 1 column; 4 ≤ k ≤ 6 → 2 columns filled row by row; a test with n > 6 clusters
  → figures of 6 blocks each (last one smaller; its column count follows its own k); the stem gets `_part1`, `_part2`… only
  when there is more than one part, otherwise unchanged (`cluster_waves_t<ids>`). Width `W` = `width_mm` (default 180).
  Margins left 6, right 14 (colour bar), top 8, bottom 18 mm. 1 column: map 26 mm square, ERP panel from `6 + 26 + 12` mm
  to `W − 14`, ERP height 26 mm, row pitch 26 + 14 mm. 2 columns: column width `(W − 6 − 14 − 8) / 2`, gap 8 mm, map 20 mm,
  ERP panel starts 10 mm right of the map and ends at the right edge of the column, ERP height 20 mm, row pitch 20 + 14 mm.
- ERP: side A = `LANCET[0]`, side B = `LANCET[1]` (as the current code), line width 0.9, 95 % CI bands alpha 0.15, cluster
  window `axvspan` color `0.88`, dashed vertical line at 0 and gray horizontal line at 0 as the current code. y limits
  shared by ALL blocks of the test (computed over every cluster of the test, min/max of mean ± CI, padded 5 %), inverted
  when `polarity` is `negative_up` (default). x ticks via `ep.x_ticks`; only the bottom ERP of each column carries tick
  labels and "Time (ms)"; every ERP has "µV" on y.
- Topomap ring: the channels used for the ERP get a black ring (marker `o`, facecolor none, edgecolor black, size 2.2,
  linewidth 0.5) on the map, drawn above the white dots. Positions: `mne.channels.layout._find_topomap_coords(info,
  picks=<indices of the ring channels in info.ch_names>, sphere=sphere)` (checked: returns an (n, 2) array that matches
  the axes drawn by `mne.viz.plot_topomap(..., sphere=sphere)`).
- One legend under the figure (the two sides), one µV colour bar on the right spanning all blocks, scale from
  `topo_limits` over all blocks of the test (the existing function), figure height computed from the blocks.
- Skips: print one line per skipped test `skipped <slug>: <reason>` (reasons: `no single difference wave (kind <kind>)`
  and `no significant cluster`) and store the list as `waves_skipped` (list of `{test, reason}`) in every written
  `_run.json`. If every selected test is skipped → `ep.die` with `layout "waves": no test left to draw; skipped: <slugs and reasons>`.
- Missing channels: if any cluster of a drawable test has no channel list in `waves_channels` (key absent, or the spec has
  no `waves_channels` at all), stop BEFORE any figure is written with
  `layout "waves" needs waves_channels for <slug>/<id> (recommended: <6 names comma separated>)` listing every uncovered
  cluster (one line each). A listed channel that is not one of the channels of the run stops with
  `waves_channels: unknown channel(s) <names> for <slug>/<id>`.
- Caption lines (`write_caption(..., waves=True)`): replace the two waves lines by
  `- **Topomaps**: µV difference over the peak window of each cluster (peak time of the summed |t| over the channels of the cluster ± 25 ms, clipped to the cluster window)` and
  `- **Channel marker**: white dots: channels significant in at least half of the samples of the map window; black rings: the channels the waveforms average`.
  At the end of every waves caption append (as now, after write_caption) one line `Waveforms: mean over the user-chosen channels (<per cluster list>); bands = 95% CI across subjects (t, df = n − 1); gray = cluster window` and one line `The cluster is inferred as a whole (Sassenhagen & Draschkow 2019); channels, windows and waveforms are descriptive, not a second test`.
- Run record per test (`record` in `plot_waves`): add `clusters` entries with `cluster_id`, `channels`, `time_start_ms`,
  `time_end_ms`, `peak_ms` (or null with `peak_window_ms`), `window_ms` `[lo, hi]`, `waves_channels`.

## Files
may change: `docs/plan-waves-v2.md`, `brain-plot/cluster_plot.py`, `brain-plot/test/test_cluster.py`, `brain-plot/references/cluster.md`, `brain-plot/references/spec.md` / read-only: `brain-plot/erp_plot.py`, `docs/plan-waves-v2.md`, `docs/cluster-waves-candidates/`

## Steps (N = 9)
1. `cluster_plot.py` → `OPTIONAL` and `check_spec`: add `waves_channels`, `peak_window_ms`, `waves_xlim` with the validation in Parameters. Keep every other check. In the `layout` error text keep the three layout names.
2. `cluster_plot.py` → new functions next to `maps_of` (reuse `ep.sample_mask`, `MARK_FRAC`): `cluster_peak(t, c, times, ch_names)` returns `(peak_ms, lo, hi)` per Parameters; `recommend_channels(t, c, times, ch_names, k=6)` returns the list per Parameters; `peak_map(t, c, times, ch_names, window=None)` returns `(vector, marked bool array, label, (lo, hi), peak_ms_or_None)` using `peak_window_ms` when `window` is given.
3. `cluster_plot.py` → `cluster_waves(run, test, run_dir, chans)`: new 4th argument `chans` = `{cluster_id: [channel names]}`; use `chans[cid]` instead of `c["channels"]` for the channel means (index per event file as now, including the existing missing-channel check, extended to the names in `chans`). Everything else (pairs, CI t-based, `ref * 1000.0`, return shape) unchanged.
4. `cluster_plot.py` → `draw_map(...)`: new optional keyword `ring=None` (an array of `(x, y)` rows from `_find_topomap_coords`); when given, draw them on the topomap axes with the ring style from Parameters. Existing callers unchanged.
5. `cluster_plot.py` → `plot()`: in the `layout == "waves"` branch replace the two `ep.die` loops by: resolve `waves_channels` per drawable cluster; build the list of drawable tests; print the skip lines; die per Parameters when nothing is left or channels are missing or unknown. Only drawable tests continue to `diff_uv` and `plot_waves` (pass the skipped list through, e.g. as an argument).
6. `cluster_plot.py` → rewrite `plot_waves(...)` per Parameters (layout, parts, blocks, title, ring, legend, colour bar, shared y, `waves_xlim`, stems, record). Extract the arithmetic "n blocks → parts and columns" into a small pure function `waves_parts(n)` returning `[(k, ncols), ...]`. Compute `maps` via `peak_map`; `topo_limits(all maps of the test, True, info, sphere)` once per test so all parts share one scale; call `cluster_waves` once per test. Keep `ep.report_layout`, png at dpi 600 + svg, `write_run_json`, `ep.archive`; extend `write_run_json` with an optional keyword `extra=None` (a dict merged into the record; do not change other callers) and pass `{"waves_skipped": [...]}`.
7. `cluster_plot.py` → `write_caption(... waves=True)`: replace the two waves lines per Parameters; the appended lines are written in `plot_waves` after `write_caption` (as the current code does).
8. `test/test_cluster.py` → update the waves tests: (n) pass `waves_channels` = a dict keyed `"<slug>/<id>"` for every cluster of every drawable test, value = the first two channels of that cluster; assert figures exist per drawable test, T02 (interaction) is skipped (not an error) and the record has `waves_skipped` naming it, `layout_issues == []`; (o) call `cluster_waves(read_w, tw, run, {c0["cluster_id"]: <those channels>})` and compare mean_a with numpy over those channels; replace (p): `waves` with only T02 stops with `no test left to draw`; add: a spec without `waves_channels` stops with `needs waves_channels` and the message contains `recommended:`; `cluster_peak` returns a peak inside the cluster window and a window of at most 50 ms, `recommend_channels` returns at most 6 names all inside the cluster; `waves_parts(1)==[(1,1)]`, `waves_parts(3)==[(3,1)]`, `waves_parts(4)==[(4,2)]`, `waves_parts(6)==[(6,2)]`, `waves_parts(7)==[(6,2),(1,1)]`, `waves_parts(13)==[(6,2),(6,2),(1,1)]`.
9. Docs: `references/cluster.md` → rewrite the `layout: "waves"` description and the two waves error entries to match Parameters (mention `waves_channels`, the interview recommends a list and the user confirms, `peak_window_ms`, `waves_xlim`, skip behaviour, naming `_partN`); `references/spec.md` → table rows for the three new keys and a corrected `polarity` / layout line. Keep the existing writing style of those files.

## Check
`python brain-plot/test/test_cluster.py`

## Don't
- No commits, no other files, no refactors beyond the steps.
- Run scripts in the foreground and wait; before replying, stop any background task still running.
- Reuse existing functions; don't copy existing logic.
- No rm, no git push, no git checkout . / restore . / reset --hard.
- Do not change the `side` or `columns` layouts or `erp_plot.py`.
- Do not average all cluster channels anywhere in waves; the only source of ERP channels is `waves_channels`.

## Acceptance
- verdict: accepted
- files: brain-plot/cluster_plot.py, brain-plot/references/cluster.md, brain-plot/references/spec.md, brain-plot/test/test_cluster.py
- check: `python brain-plot/test/test_cluster.py` → exit 0 (run by run-card)
- tokens:
  - round 1: exec deepseek-v4.1-flash: fresh 86k, cached 8616k, out 56k  (codex-cluster-waves-v2.jsonl) · review gpt-6-luna: fresh 63k, cached 319k, out 4k  (codex-review-cluster-waves-v2.jsonl)
- review findings: 0 real / 1 false positive (P1 on the runner's own reply.md) / 1 missed (user layout decision: 3 clusters 2 + 1, fixed in Fix 1; P3 deferred: cluster_waves needs chans for every cluster of the test) (medium, gpt-6-luna)
- claude fix: none; Fix 1 by wb. Recheck exit 0. Independent recompute on GN test 01: peak 516/148/514 ms and NoGO mean over C3,FC3,CP3,FC5,F5,F3 at 334 ms = -10.8672 uV (numpy = code)

## Fix 1
User decision 2026-10-11 (after seeing the 3-block single-column render): a single column makes the ERP too long, so three blocks must NOT be stacked; three clusters are drawn 2 + 1. New layout rule replacing the one in Parameters: 1 block → 1 column (as now); 2 to 6 blocks → 2 columns filled row by row (a last odd block stays in the left column, the right cell is left empty); more than 6 blocks → figures of 6 blocks, 2 columns each, the last part follows the same rule for its own count.
1. `cluster_plot.py` → `waves_parts(n)`: return `[(k, 1 if k == 1 else 2), ...]` with parts of at most 6 blocks. Expected: `waves_parts(1)==[(1,1)]`, `(2)==[(2,2)]`, `(3)==[(3,2)]`, `(4)==[(4,2)]`, `(6)==[(6,2)]`, `(7)==[(6,2),(1,1)]`, `(13)==[(6,2),(6,2),(1,1)]`.
2. `cluster_plot.py` → `plot_waves`: make sure a 2-column part with an odd block count draws the last block in the left cell only, the colour bar still spans the full block area, and the figure height uses `ceil(k / 2)` rows. No other layout change.
3. `test/test_cluster.py` → update the `waves_parts` asserts to the list above.
4. Docs: `references/cluster.md`, `references/spec.md` and `docs/plan-waves-v2.md` item 7 → replace "1–3 one column, 4–6 two columns" by "1 block one column, 2–6 blocks two columns (three clusters = 2 + 1), more than 6 split into parts of 6". (`docs/plan-waves-v2.md` may change for this step only.)
Check: same as the card.
