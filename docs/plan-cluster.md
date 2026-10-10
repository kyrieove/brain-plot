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

## Literature (answer to "what do papers use?")
`docs/research-figure-conventions.md` §1 counts t/F colour 6/8, µV 1/8, TFCE 1/8; full map + contour/mask 6/8,
significant-only 2/8. Its counts are not reliable (spot-check 2026-09-27: one paper not found, one only a preprint,
the MNE tutorial is not a raster), so they are no ground for a default. Hence both modes, asked in the interview.

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

## Figure (round 1 item 4 + defaults)
- Channel × time raster, one column per test, channels grouped left / midline / right, anterior → posterior inside
  each group; `display: "masked"` (only significant samples coloured, round 1) or `"contour"` (full map + mask
  outline). Diverging colormap, symmetric limits for t / µV, sequential from 0 for F.
- Topomap row under each column: one map per significant cluster window (onset–offset from the summary),
  significant channels marked with black dots; fixed bins (`topo_bins_ms`) as the alternative.
- Caption facts from the metadata: test, statistic, tail, forming threshold, n_permutations, cluster p, n.

## Next
Card for the executor: `docs/orch/<date>-cluster-v1/card.md` (reader, internal form, raster + topomap, interview
file `references/cluster.md`, test on a synthetic fixture + one real render of test 01).
