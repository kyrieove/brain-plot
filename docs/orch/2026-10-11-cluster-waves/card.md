# cluster-waves — new layout "waves": per cluster a µV topomap + the two condition waveforms with 95% CI

## Goal
New value `layout: "waves"` for `brain-plot/cluster_plot.py`, modelled on the MNE example "spatio-temporal
permutation F-test on full sensor data" (user's reference figure, 2026-10-11): ONE figure per test; ONE row per
significant cluster of that test; each row = a topomap at the left and a waveform panel at the right.
- Topomap: µV difference (A − B from run_metadata `difference_definition`, e.g. NoGO − GO) averaged over the cluster's
  time window, every channel drawn, the cluster's channels marked white. This is exactly what
  `maps_of(t, times, ch_names, "clusters", bins, True)` already returns per cluster (vector, marked, label) — reuse it.
- Waveform panel: the grand average of condition A and of condition B over that test's own subjects (01 = all,
  03 = TD only, …: the same participants `diff_uv` uses), averaged over the cluster's channels, on the evoked files'
  full time axis (includes the baseline), each line with a 95% confidence band; the cluster window shaded light gray.
Only tests with a single difference wave (`t["has_diff"]`, i.e. kinds `condition_pooled` / `condition_group`) can be
drawn; F interaction tests stop. A test with no significant cluster stops with a clear message.

## Risk
medium — new numbers (cluster-channel waveforms and CIs). Claude re-checks one waveform value and one CI half-width
with plain numpy, and the Oz 702–800 ms = 7.765 µV check must stay unchanged.

## Parameters
- `layout`: `"side"` | `"columns"` | `"waves"`. `waves` needs every test to have a difference wave; otherwise stop:
  `layout "waves" draws condition waveforms; test <slug> (kind <kind>) has no single difference wave`. A test with an
  empty `clusters` list stops: `layout "waves": test <slug> has no significant cluster; drop it from tests`.
- `color`, `display`, `topo`, `topo_bin_ms`, `channel_order` are ignored by `waves` (no raster); do not stop on them.
- New optional key `polarity`: `"negative_up"` (default, the house ERP style of erp_plot) | `"positive_up"`; anything
  else stops (same message style as erp_plot line ~235). Add `"polarity"` to `OPTIONAL`.
- 95% CI per condition and time point across subjects: `m ± scipy.stats.t.ppf(0.975, n - 1) * sd / sqrt(n)`,
  `sd` with `ddof=1`, on each subject's cluster-channel mean. (scipy is installed.)
- Colours: condition A = `ep.LANCET[0]`, condition B = `ep.LANCET[1]`; lines 0.9 pt solid; band same colour,
  `alpha=0.15`, `lw=0` (as erp_plot `fill_between`). Legend once, in the first row's waveform panel, upper left,
  fontsize 5, no frame, labels = condition names from `difference_definition` (A, B).
- Cluster window: `ax.axvspan(start, end, color="0.88", lw=0, zorder=0)`; dashed vertical line at 0 ms
  (`color="0.5", lw=0.4, ls="--"`), horizontal line at 0 µV (`color="0.5", lw=0.4`).
- Geometry (mm): `width_mm` default 180; left margin 6, right margin 14 (map colour bar), top 8, bottom 12; per row
  map 26 × 26 at x = 6, waveform panel from x = 6 + 26 + 12 to W − right margin, height 26; row pitch 26 + 12.
  `H = top + n_rows * 38 - 12 + bottom` unless `height_mm` is given.
- Row title above each waveform panel (fontsize 6, left-aligned): `Cluster <id> · p = <p:g> · <n> channels ·
  <start:g>–<end:g> ms`. Panel letters a, b, c … on the maps (`ep.letter(im.axes, row)`), as in `plot_columns`.
- Axes: shared y-limits across all rows of the figure (symmetric padding 5 % of the data range incl. bands); y label
  `µV` on every waveform panel; x label `Time (ms)` only on the last row; x ticks via
  `ep.x_ticks(ax, fig, t0, t1, zero=True)` on the evoked time range. `negative_up` → `ax.invert_yaxis()`.
- Map colour scale: shared across the figure via `topo_limits(maps, True, info, sphere)`; one colour bar at the right
  edge spanning all map rows, `colorbar(...)` with title `µV`, ticks `[-v, 0, v]`.
- Output: `cluster/cluster_waves_t<NN>[_lock-<event>]_vNN.png/.svg` + `_run.json` (via `write_run_json`, pass
  `layout="waves"`; per test record: metadata, n_subjects, `topo` colour limits, `y_limits`, and per cluster
  `{cluster_id, channels, time_start_ms, time_end_ms}`) + `_caption.md` (via `write_caption(out, spec, run, [t])`,
  plus one line: "Waveforms: mean over each cluster's channels; bands = 95% CI across subjects (t, df = n − 1);
  gray = cluster window").
- Layout self-check: `issues = ep.report_layout(fig, out.name)` as the other layouts; none allowed in the test.

## Files
- may change: `brain-plot/cluster_plot.py`, `brain-plot/test/test_cluster.py`, `brain-plot/references/cluster.md`,
  `brain-plot/references/spec.md`

## Steps (N = 5)
1. Refactor without behaviour change: move the participant pairing at the top of `diff_uv` (difference_definition
   parse, manifest selection by kind/group, `by_id`, missing-file stop) into `pairs_of(run, test, run_dir)` returning
   `(a, b, [(file_a, file_b), …] sorted by participant id, root)`; `diff_uv` calls it. Same messages, same numbers.
2. Add `cluster_waves(run, test, run_dir)`: for every pair read both evokeds (`mne.read_evokeds(..., verbose="error")[0]`),
   check both have every run channel (reuse the existing message style), and collect per subject, per cluster, the mean
   over the cluster's channels of A and of B in µV (`ev.data[idx].mean(0) * 1e6`) on the evoked's own time axis.
   Stop if subjects' time axes differ (`np.allclose` on `ev.times`). Return `times_ms` (evoked, ms) and, per
   cluster id, `(mean_a, ci_a, mean_b, ci_b)` as numpy arrays plus `n` subjects. CI per Parameters.
3. Add `plot_waves(spec, run, tests, info, sphere)`: one figure per test per Parameters (reuse `maps_of`,
   `topo_limits`, `draw_map`, `colorbar`, `ep.letter`, `ep.x_ticks`, `ep.versioned`, `ep.out_root`,
   `ep.report_layout`, `write_run_json`, `write_caption`, `ep.archive`, the stem/lock logic of `plot_columns`).
   Wire it: `check_spec` accepts `"waves"` and `polarity`; in `plot()` the `waves` checks (difference wave, ≥ 1
   cluster) run before any evoked is read; `plot()` returns `plot_waves(...)` (a list of outs) for `waves`.
   `side` and `columns` outputs must not change.
4. Test `brain-plot/test/test_cluster.py`: (n) `layout: "waves"` on the synthetic run with the tests that have a
   difference wave and ≥ 1 cluster writes one figure per test, `layout_issues == []`, `_run.json` `layout == "waves"`;
   (o) the first cluster's `mean_a` from `cluster_waves` equals a plain-numpy recomputation (read the evokeds directly,
   mean over the cluster channels and subjects) to 1e-9; (p) an F test under `waves` stops with the message above.
   Keep every existing case.
5. Docs: `references/cluster.md` (interview round 2: the `waves` option and when to offer it — "show the two
   compared conditions per cluster"; output name) and `references/spec.md` (`layout` row gets `"waves"`; new
   `polarity` row for cluster specs). Then render GN once with spec
   `{"data": "C:/Users/ASUS/Dropbox/metaphor_production/gn_manuscript/03-ERP_topomap/03_cluster_inference/01_cluster_based_permutation_0000_0800ms",
   "tests": ["01_condition_main_effect_all", "03_within_td_condition_effect"], "layout": "waves"}` written to the
   system temp dir: no `WARNING: layout` line allowed — if one appears, adjust only the geometry numbers and say so.

## Fix 1
Check failed: `waves layout issues in cluster_waves_t01_v01: ["a data line runs under text 'NoGO'", 'a data line runs
under the legend']` — the in-axes legend sits on the synthetic waveforms. Move the legend OUT of the axes, as erp_plot
does ("one legend under the grid"): remove the per-axes legend; after all rows are drawn add ONE `fig.legend` with the
two line handles of the first row, `ncol=2`, `frameon=False`, `fontsize=5`, `loc="upper center"`, anchored under the
last row's waveform panel: `bbox_to_anchor=(x_center_of_wave_panel / W, (bottom_m - 8.0) / H)` in figure fractions
(bottom origin), where the panel's horizontal centre is `(wave_x + wave_w / 2)`. Raise the bottom margin 12 → 18 mm
(in the `H` formula too) so the legend sits below the "Time (ms)" label. Change nothing else. Run the Check in the
foreground until it passes, then re-render GN with the step-5 spec; no `WARNING: layout` line allowed.

## Check
```
python brain-plot/test/test_cluster.py
```

## Don't
- No commits. Write only the files under "may change" (plus the GN render's own outputs in step 5).
- Do not change the reader, the bins, the colour-limit rules, `channel_rows`, `plot_side` or `plot_columns`.
- "Run scripts in the foreground and wait; before replying, stop any background task still running."
- "Reuse existing functions; don't copy existing logic."
- "No rm, no git push, no git checkout . / restore . / reset --hard."

## Acceptance (draft)
- verdict: TODO (accepted / review pending / rejected)
- files: brain-plot/cluster_plot.py, brain-plot/references/cluster.md, brain-plot/references/spec.md, brain-plot/test/test_cluster.py
- check: `python brain-plot/test/test_cluster.py` → exit 0 (run by run-card)
- tokens:
  - round 1: exec deepseek-v4.1-flash: fresh 62k, cached 5965k, out 39k  (codex-cluster-waves.jsonl)
  - Fix 1: exec deepseek-v4.1-flash: fresh 23k, cached 489k, out 5k  (codex-cluster-waves.jsonl)
- review findings: TODO N real / M false positive / K missed (medium, no review)

## Acceptance
- verdict: accepted after Fix 1 (legend moved under the figure). Claude checks: GN test 01 cluster 8 NoGO at 336 ms
  = 10.9631 µV, 95% CI half-width 0.7904 µV — module equals an independent numpy/scipy recomputation (95 subjects,
  29 channels); Oz 702–800 ms = 7.765 µV unchanged; GN renders cluster_waves_t01_v02 / t03_v02 visually QA'd.
- review: skipped by the runner (round 1 check failed; Fix 1 rounds have no review); numbers verified by Claude.
- note: GN test 01 cluster 5 (63 ch × 52–800 ms) is a flat line — average reference: the mean over ~all channels is ~0.
