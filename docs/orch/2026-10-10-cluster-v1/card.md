# cluster-v1 — new module cluster_plot.py: draw saved ERP cluster-permutation results (raster + topomap row)

## Goal
`python brain-plot/cluster_plot.py plot <spec.json>` reads a saved MNE spatio-temporal cluster run (the GN layout
below), and writes one figure: one column per test, each column = a channel × time raster of the test statistic
(only significant samples coloured by default) with a row of µV-difference topomaps underneath (significant
channels as white dots). Outputs `.png/.svg/_run.json/_caption.md`, versioned like the other modules.
`brain-plot/test/test_cluster.py` builds a synthetic run folder and prints `OK`. The module never computes a test.
Design source: `docs/plan-cluster.md` (read it first; this card wins where they differ).

## Risk
medium — new module; the µV difference wave is the only computed number (Claude recomputes it on GN test 01 at
acceptance).

## Parameters
- Run folder files (all required; stop naming the missing file): `time_axis.csv` (columns `time_index,time_ms`),
  `channel_order.csv` (`channel_index,channel`), `run_metadata.json` (keys used: `groups` list, `conditions` list,
  `difference_definition` like `"NoGO minus GO within each participant"`), `input_manifest.csv`
  (`group,condition,participant_id,file,nave`; `file` is relative to an ancestor folder of the run folder).
- Per test folder (folder name = test slug): `observed_statistic.npy` float (n_times, n_ch),
  `significant_cluster_union_mask.npy` bool (n_times, n_ch), `test_metadata.json` (keys used: `name`, `kind`,
  `statistic` "t"|"F", `tail`, `cluster_forming_threshold`, `cluster_level_alpha`, `n_permutations`, `df1`, `df2`,
  `n_significant_clusters`), `cluster_summary_significant.csv` (columns used: `cluster_id,p_cluster,time_start_ms,
  time_end_ms,channels` with `channels` `;`-separated).
- Shapes: both arrays must equal (len(time_axis), len(channel_order)); otherwise stop.
- `kind` → subjects for the µV difference: `condition_pooled` → all manifest participants; `condition_group` → the
  one group from `run_metadata["groups"]` whose lower-case name is a `_`-separated token of the slug
  (`03_within_td_condition_effect` → `TD`); zero or several matches → stop; `interaction` (or any other kind) → no µV
  difference.
- Difference: parse `difference_definition` with regex `^\s*(\S+)\s+minus\s+(\S+)` → (A, B); both must be in
  `run_metadata["conditions"]`, else stop. diff = A − B per participant, mean over participants, in µV (evoked data × 1e6).
- Evoked sample matching: for each result time t (ms), index = argmin |evoked.times*1000 − t|; stop if any
  |difference| > 0.5 / sfreq * 1000 ms. Channels picked by name in `channel_order.csv` order; a missing channel stops.
- Manifest root: the first of `[run] + list(run.parents)` for which `root / first manifest file` exists; none → stop.
- Spec keys — required: `data` (run folder), `tests` (non-empty list of test folder names, each once).
  Optional with defaults: `labels` ({slug: column title}, default `test_metadata["name"]`), `color` "stat" | "uv"
  (default "stat"), `display` "masked" | "contour" (default "masked"), `topo` "bins" | "clusters" (default "bins"),
  `topo_bin_ms` (default 100, > 0), `width_mm` (default 180), `height_mm` (default: computed), `time_locked_to`,
  `claim` (caption only). Any other key stops (`unsupported spec keys`).
- `color: "uv"` on a test without a µV difference → stop: `test <slug> (kind interaction) has no single difference wave; use color "stat"`.
- Colour scales (one colour bar per column, right of its raster): t and µV → `RdBu_r`, symmetric ±v; F → `Reds`,
  0..v. v = max |value| over the samples drawn (masked: significant samples only; contour: all), rounded up to 1
  decimal; 0 → 1.0. Topomap row of a column: µV → `RdBu_r` ±v_topo with v_topo = max over its maps of
  max(|sensor value|, ep.interp_peak(...)) rounded up to 0.1; a test without µV → mean F (or t) per bin, `Reds` 0..v.
- Raster: `ax.imshow(values.T, aspect="auto", origin="upper", extent=[t0 - dt/2, t1 + dt/2, n_ch - 0.5, -0.5],
  interpolation="nearest", cmap=..., vmin, vmax, rasterized=True)`; rows in `channel_order.csv` order (row 0 at top),
  every channel name as a y tick label at fontsize 4.5; masked → `np.ma.masked_where(~mask.T, values.T)` with
  `cmap.set_bad("white")` (copy the cmap first: `plt.get_cmap(name).copy()`); contour → full values plus
  `ax.contour(times, np.arange(n_ch), mask.T.astype(float), levels=[0.5], colors="black", linewidths=0.4)`.
  Raster height = max(60 mm, 1.0 mm × n_ch). x ticks via `ep.x_ticks(ax, fig, lo, hi, zero=True)`, "Time (ms)" label,
  "Channel" y label on the first column only, column title = label (fontsize 7), panel letter `ep.letter(ax, i)`.
- Topomaps, `topo: "bins"`: bins [t0, t0+step), … covering the result time range (last bin may be shorter); map value
  = mean over the bin's samples; marked channels = significant at any sample in the bin. `topo: "clusters"`: one map
  per row of `cluster_summary_significant.csv` (time_start..time_end inclusive), marked = that row's channels; a test
  with no significant cluster gets the text "no significant cluster" instead of maps. Under each map its time range
  `"<a>–<b> ms"` (fontsize 5). Draw with `mne.viz.plot_topomap(vec, info, axes=tax, show=False, cmap=..., vlim=(lo, hi),
  contours=np.linspace(lo, hi, ep.TOPO["contours"] + 1), sensors=False, extrapolate=ep.TOPO["extrapolate"],
  image_interp=ep.TOPO["image_interp"], sphere=sphere, mask=marked, mask_params=dict(marker="o",
  markerfacecolor="white", markeredgecolor="black", markeredgewidth=0.3, markersize=2.5))`, `sphere =
  ep.common_sphere(info)`; info = first evoked's info picked to `channel_order` (for a run whose tests have no µV at
  all, info still comes from the first manifest file).
- Map layout per column: column width cw; maps per row n_row = max(1, floor((cw + 2) / (11 + 2))) (≥ 11 mm map, 2 mm
  gap); as many rows as needed; one colour bar right of the map block, label "µV" (or the statistic).
- Canvas: `width_mm` default 180; left 14 mm, right 14 mm, column gap 16 mm (room for the per-column colour bar);
  height = top 12 + raster + 14 (x labels) + map rows × (map + 7) + 4, unless `height_mm` is given.
- Output: folder `ep.out_root(spec) / "cluster"`; stem `cluster_{color}-{display}_{tests}_topo-{bins<step>ms|clusters}`
  + (`_lock-<time_locked_to>` via `ep.safe` if given), `tests` = the leading number of each slug joined by `-` with a
  `t` prefix (`t01-t03`); path from `ep.versioned(folder, stem)`; save `.png` (dpi 600) and `.svg`; `ep.report_layout`
  before saving; `ep.archive(out)` after every file is written.
- `_run.json`: spec, per test {slug, metadata dict, n_subjects for µV (or null), color_limits}, layout_issues,
  code_md5, versions (mne, matplotlib, numpy), size_mm, qa "PENDING: …" — same pattern as `tfr_plot.write_run_json`.
- `_caption.md` facts, one `-` line each: per column: label, statistic and tail, cluster-forming threshold,
  n_permutations, cluster-level alpha, significant clusters with p and time range; µV maps: difference definition and
  N; display mode in words ("only samples in significant clusters are coloured" / "full map, significant samples
  outlined"); bins or cluster windows; channel marker meaning ("white dots: channels in a significant cluster within
  the map's time range"); `claim` if given.

## Files
may change: `brain-plot/cluster_plot.py`, `brain-plot/test/test_cluster.py`, `brain-plot/references/cluster.md`, `brain-plot/references/spec.md`, `brain-plot/SKILL.md`
read-only: `brain-plot/erp_plot.py`, `brain-plot/tfr_plot.py`, `docs/plan-cluster.md`, `C:\Users\ASUS\Dropbox\metaphor_production\gn_manuscript\`

## Steps (N = 6)
1. `brain-plot/cluster_plot.py` — module docstring like `tfr_plot.py` (usage line `python cluster_plot.py plot <spec.json>`),
   `import erp_plot as ep`, `matplotlib.use("Agg")`. `REQUIRED = {"data", "tests"}`, `OPTIONAL` = the optional keys in
   Parameters. `check_spec(spec)` validates every key and value listed in Parameters with `ep.die` messages that say
   the fix.
2. Reader `read_run(spec)` → dict: `times_ms` (np array), `ch_names`, `meta` (run_metadata), `tests` = list of dicts
   {slug, label, meta (test_metadata), stat, mask, clusters (list of dicts from the summary CSV, channels as list),
   group (or None), has_diff (bool)}. Use `csv` + `json` + `np.load` only. Every shape / file / column check from
   Parameters. Test folders are `Path(spec["data"]) / slug`; a missing folder stops listing the available folders.
3. `diff_uv(run, test, run_dir)` → (n_times, n_ch) µV mean difference and n_subjects, plus `info`. Reads the
   manifest, picks participants per Parameters (`kind`), pairs A and B files by `participant_id` (a participant
   without both → stop), `mne.read_evokeds(path, verbose="error")[0]`, picks/reorders channels, samples times per
   Parameters. Load each file once per call; no cache (ponytail: ~200 small evoked files; add a cache only if a real
   render takes > 60 s). Also a helper `first_info(run, run_dir)` for the topomap info when no test has a diff.
4. `plot(spec)` — layout, raster, contour/mask, colour bars, topomap rows, caption and run files exactly as in
   Parameters; `plt.rcParams.update(ep.STYLE)` first; returns the output path prefix; `__main__` like `tfr_plot.py`
   (`sys.stdout.reconfigure(encoding="utf-8")`, `plot(ep.read_spec(sys.argv[2]))`).
5. `brain-plot/test/test_cluster.py` — same skeleton as `test/test_tfr.py` (`run_tests()`, prints `OK`, `assert_stops`
   pattern for expected `SystemExit` messages). Synthetic run folder in a temp dir:
   - channels `["Fz", "Cz", "Pz", "Oz", "C3", "C4"]`, `standard_1020` montage, sfreq 500, evoked times −0.2…1.0 s;
     groups `TD`, `MD` × 3 participants; conditions `GO`, `NoGO`; NoGO = GO + 2 µV (2e-6 V) at Cz and Pz from 300 to
     500 ms, plus small seeded noise (`np.random.default_rng(0)`, 0.05 µV); files under `<tmp>/ev/<cond>/<group>/<id>_<cond>-ave.fif`
     (`mne.EvokedArray(..., comment=cond).save(..., overwrite=True)`), manifest paths relative to `<tmp>`;
     run folder `<tmp>/stats/run1/` (so the manifest root is two parents up).
   - `time_axis.csv` 2…800 ms step 2 (400 rows); tests `01_condition_main_effect_all` (kind condition_pooled, t,
     mask = Cz/Pz × 300–500 ms, stat 5 there and 0.5 elsewhere), `02_condition_by_group_interaction` (interaction, F,
     no significant samples, empty summary CSV with header only), `03_within_td_condition_effect` (condition_group, t,
     same mask as 01).
   - Asserts: (a) `cluster_plot.diff_uv` for test 01 gives 2.0 ± 0.1 µV at Cz, 400 ms and |value| < 0.2 at Oz;
     n_subjects 6 for 01 and 3 for 03; (b) default spec with tests [01, 03] writes png/svg/_run.json/_caption.md,
     `layout_issues == []`; (c) `display: "contour"` and `topo: "clusters"` each render; (d) tests [02] with default
     colour renders (F topomaps); (e) stops: `color: "uv"` with test 02 ("no single difference wave"), unknown spec
     key ("unsupported spec keys"), unknown test folder, a mask of the wrong shape.
6. Docs: `brain-plot/references/cluster.md` (≤ 60 lines, same structure as `references/tfr.md`: Command, Interview
   rounds — round 1: which tests (columns) and labels; round 2: `color`, `display`, `topo`/`topo_bin_ms`, width; Never
   ask: style, colormaps, marker; When the script stops — one line per stop message; QA list — no overlaps, every
   channel label legible, colour bar per column with the statistic named, white dots on maps, `layout_issues` empty).
   `references/spec.md`: a `## Cluster spec (python cluster_plot.py plot <spec.json>)` section with the key table and
   the output name pattern. `SKILL.md`: one routing row `| Saved cluster-permutation results (raster + topomaps) |
   cluster_plot.py | references/cluster.md |` and add "cluster-permutation result figure、cluster 图" to the description's
   trigger list; keep "Draws only".

## Check
```
python brain-plot/test/test_cluster.py
```

## Don't
- No commits. Write only the files under "may change". Never write into `gn_manuscript` (read-only; the real render is
  done by Claude after acceptance).
- Do not compute any statistic, threshold or p-value; the module only draws what the files contain (plus the µV mean
  difference).
- Do not edit `erp_plot.py` or other modules; call their helpers (`ep.die`, `ep.out_root`, `ep.versioned`, `ep.archive`,
  `ep.report_layout`, `ep.x_ticks`, `ep.letter`, `ep.common_sphere`, `ep.interp_peak`, `ep.TOPO`, `ep.STYLE`, `ep.MM`,
  `ep.safe`, `ep.read_spec`).
- "Run scripts in the foreground and wait; before replying, stop any background task still running."
- "Reuse existing functions; don't copy existing logic."
- "No rm, no git push, no git checkout . / restore . / reset --hard."

## Fix 1
The Check fails: `cluster_plot.py` `picked_info` calls `Info.pick_channels`, which does not exist (mne 1.13).
1. `brain-plot/cluster_plot.py` → `picked_info`: replace the copy + `pick_channels` lines with
   `return mne.pick_info(info, [info.ch_names.index(c) for c in ch_names])` (keeps `channel_order.csv` order).
2. Then run the Check `python brain-plot/test/test_cluster.py` yourself, in the foreground, and fix every further
   failure in `cluster_plot.py` / `test_cluster.py` (only those two files) until it prints `OK`. Do not weaken an
   assert from the card's Step 5 to make it pass; if an assert itself contradicts the card, stop and report it.
3. Reply with each failure you hit and the fix you made (file:line, one line each).

## Fix 2
The Check now fails on the output name (`cluster_stat-masked_t01-03_topo-bins100ms_v01`; the card says `t01-t03`).
1. `brain-plot/cluster_plot.py:416` → `stem = f"cluster_{color}-{display}_{'-'.join('t' + n for n in nums)}_topo-{topo_part}"`.
2. `brain-plot/test/test_cluster.py:117` → the expected part is `"_t01-t03_"` (underscore before, as in the stem), not `"-t01-t03_"`.
3. Read the rest of `test_cluster.py` after line 117 and of `plot()` once more against the card's Parameters and
   Step 5 (asserts c–e); fix any other mismatch you can see in those two files and list it in the reply.

## Acceptance
- verdict: accepted after cluster-v1-v2 (Check green only after Fix 2; review FAIL -> fixed in v2)
- files: brain-plot/SKILL.md, brain-plot/cluster_plot.py, brain-plot/references/cluster.md, brain-plot/references/spec.md, brain-plot/test/test_cluster.py
- check: `python brain-plot/test/test_cluster.py` → exit 0 (run by run-card)
- tokens:
  - round 1: exec deepseek-v4.1-flash: fresh 69k, cached 5049k, out 81k  (codex-cluster-v1.jsonl)
  - Fix 1: exec deepseek-v4.1-flash: fresh 14k, cached 218k, out 4k  (codex-cluster-v1.jsonl)
  - Fix 2: exec deepseek-v4.1-flash: fresh 21k, cached 556k, out 9k  (codex-cluster-v1.jsonl)
- review findings: 2 real / 0 false positive / 3 missed (medium, gpt-6-luna review after Fix 2: B file read with A indices; index columns unchecked). Missed, found by Claude on the GN render: overlapping channel labels (card sizing error, Claude), topomap bins sharing a boundary sample, oversized markers -> all fixed in cluster-v1-v2
  - review gpt-6-luna: fresh 56k, cached 222k, out 4k  (codex-review-cluster-v1.jsonl)
- notes: wb ran no Check itself in any round (runner prompt says the runner runs it), so each fix round found only the next failure.
