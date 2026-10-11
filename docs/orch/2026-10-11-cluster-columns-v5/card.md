# cluster-columns-v5 — cluster outline on the raster, stricter channel dots, cluster notes (from the BESA/MNE survey)

## Goal
Three changes to the columns layout, taken from `research/cluster-figures/survey-mne.md` / `survey-besa.md`:
(1) the masked raster gets a thin black outline around the significant region (as MNE's tutorial figure does), so cluster
edges are visible next to pale cells; (2) a topomap time-bin marks a channel with a white dot only when the channel is
significant in at least half of the bin's samples (today: in any sample, so large clusters mark nearly every channel and
the dots carry no information); (3) under each test column's raster, up to 5 lines list its significant clusters:
`Cluster <id>: <start>–<end> ms, p = <p>` (or `p < 0.001`), so the figure carries the cluster time window and p value.
The user approved doing all three on 2026-10-11 and will compare before/after on GN tests 01 + 03.

## Risk
medium — changes what the figure shows (marked channels, outline, new text); no statistics or data change.

## Parameters
- `MARK_FRAC = 0.5` (module constant in `brain-plot/cluster_plot.py`): a channel is marked in a `topo: "bins"` map when `mask[bin_samples, channel].mean() >= 0.5`.
- Outline: black, `linewidths=0.4`, level 0.5 of the boolean significance mask (the same call `draw_raster` already uses for `display: "full"`).
- Cluster notes: font size 5, left-aligned at each column's raster left edge, 2.4 mm per line, at most 5 lines per column (6th+ collapse into the line `+ N more (see caption)`), a test with no cluster gets the single line `no significant cluster`.
- p text: `p = {p:.3f}` when p >= 0.001, else `p < 0.001`.
- Unchanged: `topo: "clusters"` marking (the cluster's own channels), the `side` layout's look (it shares `maps_of`, so its dots follow the new fraction rule; its raster outline is NOT added there), the waves layout, all file names.

## Files
may change: `brain-plot/cluster_plot.py`, `brain-plot/test/test_cluster.py`, `brain-plot/references/cluster.md` / read-only: `C:/Users/ASUS/Dropbox/metaphor_production/`, `research/`

## Steps (N = 6)
1. `brain-plot/cluster_plot.py`, just above `def maps_of`: add `MARK_FRAC = 0.5  # a bin marks a channel when it is significant in at least this fraction of the bin's samples`. In `maps_of`, the `"bins"` branch: replace `t["mask"][m].any(0)` with `t["mask"][m].mean(0) >= MARK_FRAC`; update the docstring ("marked channels: significant in at least half of the bin's samples, or the cluster's channels").
2. `brain-plot/cluster_plot.py`, `draw_raster`: after the `if display == "masked": ... else: ...` block, draw the outline for BOTH displays and delete the contour line inside the `else` branch: `if sig.any() and not sig.all(): ax.contour(times, np.arange(n_rows), sig.astype(float), levels=[0.5], colors="black", linewidths=0.4)` (the guard avoids matplotlib's "no contour levels" warning when the block is empty or full). Update the docstring (both displays outline the significant region).
3. `brain-plot/cluster_plot.py`: add `def cluster_notes(t, cap=5)` returning the list of lines described in Parameters (`f"Cluster {c['cluster_id']}: {c['time_start_ms']:g}–{c['time_end_ms']:g} ms, {ptxt}"`, ptxt per Parameters; `no significant cluster` when `t["clusters"]` is empty; more than `cap` clusters → first `cap` lines then `+ {n - cap} more (see caption)`; at most `cap + 1` lines).
4. `brain-plot/cluster_plot.py`, `plot_columns`: `notes = [cluster_notes(t) for t in tests]`, `ann_h = 2.4 * max(len(x) for x in notes) + 1.0`. In `H = ... top_m + raster_block + 10.0 + 6.0 + n * (map_mm + 11.0) + 4.0` and in `topo_top = top_m + raster_block + 10.0 + 6.0` add `+ ann_h` (both, so the maps move down and the figure grows by the same amount; when the spec gives `height_mm`, only `topo_top` shifts). After the raster loop, for each test column `c` and line `j`: `fig.text((left_m + c * (cw + 8.0)) / W, (H - (top_m + raster_block + 10.0 + 2.4 * j)) / H, line, ha="left", va="top", fontsize=5)`. The x-axis label "Time (ms)" lives in the first ~9 mm below the raster, hence the 10.0 offset; after rendering confirm via the `layout_issues` list in `_run.json` that nothing overlaps (the Check does this on the synthetic run).
5. `brain-plot/cluster_plot.py`, `write_caption`: (a) masked display text becomes `"only samples in significant clusters are coloured and outlined"`; (b) the non-waves Channel-marker line: when `topo_mode == "bins"` it reads `"white dots: channels significant in at least half of the samples of the map's time bin"`, otherwise keep the current text. `brain-plot/references/cluster.md` line 75 (rule 5 "White dots"): same wording for bins, and add rule text under the `columns` rules that each column lists its clusters (id, window, p) under the raster (max 5 lines) and the masked raster is outlined.
6. `brain-plot/test/test_cluster.py`: add one block before the final summary print of `run_tests`, using the existing synthetic run: (a) a direct call `cluster_plot.maps_of({"stat": s, "uv": None, "mask": m, "clusters": []}, times, ["A", "B"], "bins", cluster_plot.bins_of_times(times, 5.0), False)` with `times = np.arange(5.0)`, `m` (5 samples × 2 channels) True for channel A in 3 samples and channel B in 1 sample, `s = np.zeros((5, 2))`, and assert the returned `marked == [True, False]`; (b) `cluster_notes` on a dict with 7 clusters has 6 lines, the 6th is `+ 2 more (see caption)`, and a dict with `clusters: [dict(cluster_id=1, p_cluster=0.0004, time_start_ms=100, time_end_ms=200, channels=[])]` gives `["Cluster 1: 100–200 ms, p < 0.001"]`; (c) existing assertions that rely on the old any-sample marking, if any, are updated and named in your reply.

## Check
```
python brain-plot/test/test_cluster.py
```

## Don't
- No commits. Change only what the steps name; do not touch `plot_side`, `plot_waves`, spec keys or `check_spec`.
- Run scripts in the foreground and wait; before replying, stop any background task still running.
- Reuse existing functions; don't copy existing logic.
- No rm, no git push, no git checkout . / restore . / reset --hard.
- Do not render or write anything under `C:/Users/ASUS/Dropbox/` (Claude renders the GN figure after acceptance).

## Acceptance
- verdict: accepted (medium). Claude read the full cluster_plot.py diff: matches Steps 1–5; test block present, Check exit 0. Note: draw_raster is shared, so the `side` layout's masked raster also gets the outline (card said it would not).
- files: brain-plot/cluster_plot.py, brain-plot/references/cluster.md, brain-plot/test/test_cluster.py
- check: `python brain-plot/test/test_cluster.py` → exit 0 (run by run-card)
- tokens:
  - round 1: exec deepseek-v4.1-flash: fresh 36k, cached 1705k, out 13k  (codex-cluster-columns-v5.jsonl) · review gpt-6-luna: fresh 51k, cached 206k, out 2k  (codex-review-cluster-columns-v5.jsonl)
- review findings: TODO N real / M false positive / K missed (medium, gpt-6-luna)
