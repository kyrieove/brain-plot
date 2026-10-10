# Plan: cluster-permutation result figure (round 2, 2026-10-10)

Round 1 (`docs/plan-modules.md`) stands: draw saved results only, never compute a test or decide significance.

## Round 2 decisions (user, 2026-10-10)
1. **Colour value: both, chosen in the spec** — `color: "stat"` (t / F from the result file) or `color: "uv"`
   (grand-average difference in µV, computed from the per-subject files the result lists; descriptive, not a test).
2. **Input: no fixed format.** The module reads what the analysis saved and converts it to one internal form
   (below). One reader per known layout; an unknown layout stops with what is missing.
3. **First data: GN MNE cluster results** (`gn_manuscript\03-ERP_topomap\03_cluster_inference\
   01_cluster_based_permutation_0000_0800ms\`, six tests).
4. **v1 scope: raster + topomap row only.** Cluster-channel waveforms, MVPA masks etc. wait for the user.

## Literature
`research/cluster-figures/survey.md` (15 verified figures, 2026-10-10) supersedes the counts of
`docs/research-figure-conventions.md`. User decision 2026-10-10: **follow the mainstream of that survey**:
- raster colour = the statistic (t / F): all 6 rasters in the survey use t or F, none µV. µV goes on the topomaps.
  `color: "uv"` for the raster stays available as an option (round-2 item 1), not the default.
- significance = only significant samples coloured, the rest blank (5 of 6 rasters; contour 1).
- channel order = the montage order of the result file (4 of 5 rasters that show one; region 1; none L/mid/R).
  This replaces the round-1 left / midline / right grouping.
- topomaps = µV difference in fixed time bins (6 of 13 figures with maps; cluster window 4, component window 3);
  cluster-window maps stay as the alternative.
- significant channels on topomaps = white dots (3; black 2, red 1, star 1).

## Internal form (what every reader returns)
`stat (n_times, n_ch)`, `mask (n_times, n_ch) bool`, `times_ms (n_times,)`, `ch_names`, `stat_name` ("t"/"F"),
`test_name`, `clusters` (id, p, time range, channels, direction) and, for `color: "uv"`, the subject file list
with the difference definition (e.g. "NoGO minus GO").

## GN MNE cluster reader (layout found 2026-10-10)
- Run folder: `time_axis.csv` (time_ms, 400 rows, 2–800 ms), `channel_order.csv` (64), `run_metadata.json`
  (difference definition, groups, n), `input_manifest.csv` (group, condition, participant_id, file relative to
  `gn_manuscript\`, nave; 190 rows = 95 × GO/NoGO).
- Per test folder: `observed_statistic.npy` (400 × 64 float32), `significant_cluster_union_mask.npy` (400 × 64
  bool), `test_metadata.json` (statistic, tail, threshold, n_permutations), `cluster_summary_significant.csv`.
- µV difference for a test: mean over the subjects the test used (`kind`: pooled / one group; the interaction
  test has F and no single difference → `color: "uv"` stops for it unless the user names one).

## Figure (defaults from the survey; each is a spec key the interview can change)
- Channel × time raster, one column per test, channels in result-file order; `color: "stat"` (default) or `"uv"`;
  `display: "masked"` (default: non-significant samples blank) or `"contour"` (full map + mask outline).
  Diverging colormap with symmetric limits for t / µV, sequential from 0 for F; colour bar per column.
- Topomap row under each column: µV difference averaged in fixed bins (`topo_bins_ms`, default step chosen in the
  interview), channels significant anywhere in the bin marked with white dots; `topo: "clusters"` = one map per
  significant cluster window instead. A test with no single difference (the F interaction) gets F topomaps.
- Caption facts from the metadata: test, statistic, tail, forming threshold, n_permutations, cluster p, n.

## Next
Card for the executor: `docs/orch/<date>-cluster-v1/card.md` (reader, internal form, raster + topomap, interview
file `references/cluster.md`, test on a synthetic fixture + one real render of test 01).
