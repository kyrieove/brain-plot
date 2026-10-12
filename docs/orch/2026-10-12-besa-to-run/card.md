# besa-to-run — convert a BESA Statistics result + .avr files into the run folder cluster_plot.py reads

## Goal
New file `brain-plot/besa_to_run.py`. One command turns a BESA Statistics paired-t cluster project (the
`*_Results.dat` file, the exported `cluster_summary.csv`, the per-subject `.avr` files and `channels.elp`) into a NEW run
folder that `cluster_plot.py` reads without any change to `cluster_plot.py`:
`python brain-plot/besa_to_run.py convert --results R --summary S --avr-dir A --elp E --cond-a NoGO --cond-b GO --out O`
writes `O/` with `time_axis.csv`, `channel_order.csv`, `run_metadata.json`, `input_manifest.csv`,
`evoked/<cond>/<id>_<cond>-ave.fif` (one per .avr) and one test folder `O/01_cond_all/` with
`observed_statistic.npy`, `significant_cluster_union_mask.npy`, `test_metadata.json`, `cluster_summary_significant.csv`.
The script never computes a statistic: it copies BESA's t map, cluster ids and p-values. It only converts units and shapes,
and stops (`ep.die`) when BESA's own files disagree with each other.
Done when the Check ends with `OK`.

## Risk
medium — a new module, no change to existing code. (Claude recomputes the t map from the .avr files after acceptance.)

## Parameters
- Real data root (read-only) `BESA = C:/Users/ASUS/Dropbox/metaphor_production/gn_manuscript/10-ERP_stats/02_v2_cluster_three-groups/besa_check`:
  - `--results` `BESA/besa_data_folder/StatGroup_All/StatFiles/IntermediateFiles/Stat_gn_T01_NoGO-GO_Results.dat`
  - `--summary` `BESA/besa_out/T01/T01_cluster_summary.csv`
  - `--avr-dir` `BESA/avr/paired_all` (holds `GO/` and `NoGO/`, 130 files each, names `<id>_<cond>.avr`, e.g. `0008_GO.avr`)
  - `--group-dir` `BESA/avr` (optional; holds `<cond>/<group>/<id>_<cond>.avr` with groups ADHD, LD, TD: 35, 64, 31 files)
  - `--elp` `BESA/avr/channels.elp` (lines `EEG <name> <theta> <phi>`)
  - `--cond-a NoGO --cond-b GO` (t = A − B; BESA project: condition 1 NoGO, condition 2 GO)
- Real result shape: `TValues` 64 channels × 501 samples; 7 clusters (BESA numbers 1..7); time axis 0..1000 ms step 2 ms (501 samples, from `Start time`/`End time` in the summary); N = 130 pairs; df = 129.
- BESA cluster numbers 1..7 are `ClusterIDs` values 0..6 (`-1` = no cluster). Significant = p < `--alpha` (default 0.05): real clusters 1, 2, 3 (p = 0, 0, 0.0014). Cluster p-values are copied as BESA wrote them (0 stays 0).
- Real clusters (BESA number: channels, start–end ms): 1: 47 ch, 264–1000; 2: 64 ch, 32–1000; 3: 26 ch, 60–294; 4: 1 ch (Iz), 60–96; 5: 2 ch, 52–72; 6: 1 ch (TP9), 660–674; 7: 1 ch (PO3), 26–28.
- Cluster-forming threshold written to `test_metadata.json`: `scipy.stats.t.ppf(1 - cluster_alpha / 2, N - 1)` with `cluster_alpha` = the summary's `Cluster Alpha` (0.05) → 1.97852 for N = 130. BESA's "Cluster Alpha" only forms clusters; the significance level is `--alpha`.
- Units: .avr values are µV, rows = channels, columns = time samples (corrected after the first run: the real BESA .avr stores one row per channel). fif data = µV × 1e-6. sfreq = 1000 / `DI` (500 Hz), tmin = `TSB` / 1000.
- Electrode positions from `channels.elp` (theta, phi in degrees): if theta < 0 then theta = −theta and phi = phi + 180; unit vector `x = sin(theta)·cos(phi)`, `y = sin(theta)·sin(phi)`, `z = cos(theta)` (x right, y front, z up); times 0.095 m; MNE `head` frame.
- `test_metadata.json`: `name` = f"{cond_a} − {cond_b}, all participants (N = {N})", `slug` "01_cond_all" (`--slug`), `kind` "condition_pooled", `statistic` "t", `tail` "two-sided" when the summary has both a `Right-tail` and a `Left-tail` threshold line, else die, `cluster_forming_alpha`, `cluster_forming_threshold`, `cluster_level_alpha` (= `--alpha`), `n_permutations` (summary `Number of Permutations`), `df1` N−1, `df2` null, `n_clusters`, `n_significant_clusters`, `minimum_cluster_p`, `source` "BESA Statistics 2.1, converted by besa_to_run.py".

## Files
may change: `brain-plot/besa_to_run.py` (new), `brain-plot/test/test_besa.py` (new), `brain-plot/references/cluster.md`
read-only: `brain-plot/cluster_plot.py`, `brain-plot/erp_plot.py`, `brain-plot/test/test_cluster.py`, `C:/Users/ASUS/Dropbox/metaphor_production/`, `docs/cluster-before-after/`, `docs/cluster-layout-compare.html`, `docs/cluster-layout-compare-real.html`, `docs/tfce-mne-vs-standard.html`, `AGENTS.md`, `AGENTS.md.bak-doctor-2026-10-09`

## Steps (N = 6)
1. `brain-plot/besa_to_run.py`, header and imports (follow `cluster_plot.py`'s style: module docstring, `import erp_plot as ep` for `ep.die`). Imports: argparse, csv, json, re, sys, `Path`, mne, numpy as np, `from scipy import stats`. Put `sys.path.insert(0, str(Path(__file__).resolve().parent))` before `import erp_plot as ep` only if `cluster_plot.py` does the same (check its top lines); otherwise rely on the script directory already being on `sys.path`.

2. `read_results(path)` → dict(t, ids, cluster_p, cluster_value). `Results.dat` is XML-like text; read it with this regex (tested on the real file; do not use an XML parser):
   ```python
   def block(txt, tag):
       m = re.search(rf"<{tag}>\s*<(Matrix|Array)([^>]*)>(.*?)</\1>", txt, re.S)
       if not m:
           ep.die(f"{tag} not found in the BESA results file")
       dims = re.search(r'DimsSizes="([\d;]+)"', m.group(2))
       vals = np.array([float(v) for v in m.group(3).replace("\n", ";").split(";") if v.strip()])
       return vals.reshape([int(d) for d in dims.group(1).split(";")]) if dims else vals
   ```
   Use `TValues` → `t` (n_ch, n_t), `ClusterIDs` → `ids` (int, same shape), `ClusterProbabilities` → `cluster_p`, `ClusterValues` → `cluster_value`. Die when `t.shape != ids.shape` or when `len(cluster_p) != ids.max() + 1`.

3. `read_summary(path)` → dict(settings, rows, channels). The file is `;`-separated text. First line `sep=;`. Settings lines look like `Neighbor Distance = 4.6` → `settings["Neighbor Distance"] = "4.6"` (split at the first ` = `). The cluster table starts at the line whose first field is `Cluster ID`; its header fields are `Cluster ID;p-value;Cluster value;Mean for <A>;Mean for <B>;Start Time;End Time;maximum t-value;latency at maximum;channel at maximum`. Rows follow until the first blank line; one row per cluster, first field `Cluster k` → `number` k (int), then the other fields as floats (channel at maximum stays text). After the blank line come lines `Cluster k;ch1;ch2;...` → `channels[k] = [names]` in BESA's order. Return the means as `mean_a`, `mean_b` by reading the header (`Mean for <cond>` for `--cond-a` / `--cond-b`; die when a name is not in the header). Die when the cluster numbers of the table are not exactly 1..K, or the table and the channel lines disagree on the numbers.

4. `read_avr(path)` → (data in µV shape (n_t, n_ch), channel names, tsb_ms, di_ms) and `read_elp(path)` → ordered dict name → (theta, phi). `.avr`: line 1 `Npts= 501   TSB= 0.000 DI= 2.000000 SB= 1.000 SC= 200.0 Nchan= 64` (parse with `re.search(r"Npts=\s*(\d+)\s+TSB=\s*([\d.\-]+)\s+DI=\s*([\d.\-]+)")` and `Nchan=\s*(\d+)`); line 2 the channel names separated by spaces; then `Npts` lines of `Nchan` floats each (`np.loadtxt(path, skiprows=2)`; die when the shape differs from (Npts, Nchan)).
   `convert(args)`:
   a. Read results, summary, elp. `names = list(elp)`; `n_ch, n_t = t.shape`; die when `len(names) != n_ch`. Time axis `times = np.linspace(float(settings["Start time"]), float(settings["End time"]), n_t)`.
   b. Find avr files: for each cond in (`cond_a`, `cond_b`): `sorted((avr_dir / cond).glob(f"*_{cond}.avr"))`; participant id = file name before the first `_`. Die when the two id lists differ or are empty. N = number of ids. Groups: with `--group-dir`, map every id to the folder name under `<group-dir>/<cond_a>/<group>/` holding `<id>_<cond_a>.avr` (die unless every id is found exactly once); without it, group "all". `groups` = distinct groups in sorted order.
   c. Die when `args.out` exists (message: the output folder must not exist; never clear it). `Path.mkdir(parents=True)`.
   d. For every file: `read_avr`; die when its channel names differ from `names`, `Npts != n_t`, `TSB != times[0]` or `DI != times[1] - times[0]` (tolerance 1e-6). Build the montage once: `mne.channels.make_dig_montage(ch_pos={name: xyz}, coord_frame="head")` with the positions from the Parameters rule; `info = mne.create_info(names, 1000.0 / DI, "eeg")`; `info.set_montage(montage)`; `ev = mne.EvokedArray(data.T * 1e-6, info, tmin=TSB / 1000.0, nave=1, comment=cond)`; `ev.save(out / "evoked" / cond / f"{id}_{cond}-ave.fif")` (create the folder). The .avr files carry no nave; the manifest `nave` column stays empty.
   e. Write `time_axis.csv` (`time_index,time_ms`), `channel_order.csv` (`channel_index,channel`), `input_manifest.csv` (`group,condition,participant_id,file,nave`; `file` = `evoked/<cond>/<id>_<cond>-ave.fif` with forward slashes, relative to `out`; rows for both conditions, `nave` empty), `run_metadata.json` with keys `analysis` ("BESA Statistics 2.1 cluster-based permutation test (converted by besa_to_run.py)"), `time_window_ms` [start, end], `n_time_samples`, `sampling_frequency_hz`, `n_channels`, `groups`, `conditions` = `sorted([cond_a, cond_b])`, `sample_sizes` ({group: count}), `difference_definition` f"{cond_a} minus {cond_b} within each participant", `cluster_forming_alpha`, `cluster_level_alpha`, `n_permutations`, `neighbor_distance_cm`, `all_participants_used` true, `exclusions` [].
   f. Test folder `out / args.slug`: `observed_statistic.npy` = `t.T.astype(np.float32)` (shape (n_t, n_ch)); the BESA numbers of the significant clusters are those with `p < args.alpha`; `significant_cluster_union_mask.npy` = `np.isin(ids, [k - 1 for k in sig]).T` (bool, (n_t, n_ch)); `cluster_summary_significant.csv` with columns `cluster_id,p_cluster,time_start_ms,time_end_ms,n_channels,channels,cluster_mass,peak_stat,peak_time_ms,peak_channel,direction` — one row per significant cluster, `cluster_id` = the BESA number k, `channels` joined with `;` in BESA's order, `cluster_mass` = Cluster value, `peak_*` = BESA's maximum t-value / latency at maximum / channel at maximum, `direction` = f"{cond_a} > {cond_b}" for a positive cluster value else f"{cond_a} < {cond_b}"; a header-only file when none is significant. `test_metadata.json` per Parameters.
   g. `verify(...)` (call it at the end of `convert`; die with the first mismatch): for every BESA cluster k (all, not only significant), `m = ids == k - 1` as (n_ch, n_t): (i) the set of channel names where `m.any(1)` equals `set(channels[k])`; (ii) `times[m.any(0)].min()` equals Start Time and `.max()` equals End Time of the table row; (iii) `np.sign(t[m])` is one sign everywhere and equals the sign of Cluster value; (iv) `np.abs(t[m]).min() >= threshold - 1e-3` (threshold from Parameters); (v) the mean over the cluster samples of the subjects' `cond_a` avr data (shape (N, n_t, n_ch), kept in memory from step d) minus the same for `cond_b` equals `mean_a - mean_b` of the table row within 1e-3 µV (tests the .avr orientation and the mask orientation). Print one line `OK: <K> clusters, <S> significant, N = <N>, out = <out>` on success.
   CLI: `main()` with argparse subcommand `convert` and the arguments named in the Goal plus `--group-dir`, `--slug` (default "01_cond_all"), `--alpha` (float, default 0.05); `if __name__ == "__main__": main()`.

5. `brain-plot/test/test_besa.py` (module docstring like `test_cluster.py`; prints `OK` at the end; `sys.path.insert(0, str(Path(__file__).resolve().parents[1]))`). Two parts:
   (a) synthetic: in `tempfile.TemporaryDirectory()` build a mini BESA project: channels Fz, Cz, Pz, Oz (elp lines `EEG Fz 45.000 90.000`, `EEG Cz 0.000 0.000`, `EEG Pz 45.000 -90.000`, `EEG Oz 90.000 -90.000`); 6 time samples 0..10 ms (TSB 0, DI 2); 3 participants (ids `0001..0003`) × conditions NoGO, GO as `avr/paired_all/<cond>/<id>_<cond>.avr` (header `Npts= 6   TSB= 0.000 DI= 2.000000 SB= 1.000 SC= 200.0 Nchan= 4`, a line of channel names, 6 rows of 4 numbers; NoGO = GO + 2.0 µV on Cz and Pz at samples 2..4, plus small different noise per subject so the paired t is finite) and `avr/<cond>/<group>/…` copies for the groups A (ids 0001, 0002) and B (0003) under `avr/` as `--group-dir`; a `Results.dat` text written with the same XML tags the real one has (`<StatResults><WS_SetParams><TValues><Matrix DataType="float" DimsSizes="4;6" NumDims="2">…</Matrix></TValues>…`, `<ClusterIDs>` int matrix, `<ClusterProbabilities><Array … ValidSize="2">`, `<ClusterValues>`; rows joined with `;`, as the real file) built from `scipy.stats.ttest_rel` t values of the synthetic avr data, cluster 0-based id 0 = samples 2..4 on Cz and Pz (rest −1) and id 1 = one sample on Fz; and a `cluster_summary.csv` in the real layout (`sep=;`, settings lines including `Start time = 0`, `End time = 10`, `Cluster Alpha = 0.05`, `Number of Permutations = 100`, `Right-tail cluster threshold value = 1`, `Left-tail cluster threshold value = -1`, the table, blank line, channel lines). Use cluster p-values 0.01 and 0.5 and make the cluster-forming threshold consistent (`t.ppf(0.975, 2)` = 4.30: set the synthetic effect large and noise tiny so |t| inside cluster 1 exceeds 4.30; cluster 2's single sample must also exceed it).
   Run `besa_to_run.convert` (call its function directly with an argparse-like namespace, or `main([...])` if `main` takes an argv list — make `main(argv=None)`), then assert: output folder holds the 4 top-level files and `01_cond_all/` files; `observed_statistic.npy` shape (6, 4); the mask is True exactly at samples 2..4 × (Cz, Pz); `cluster_summary_significant.csv` has one row (cluster_id 1, channels `Cz;Pz`... in the summary's order); manifest has 12 rows with groups A/B; a fif reads back with `mne.read_evokeds` and its data equals the avr values × 1e-6; a second call with the same `--out` stops (catch `SystemExit` from `ep.die`; check how `ep.die` ends the program in `erp_plot.py` line 59 and catch what it raises).
   (b) real data: if `BESA` (Parameters) exists, `convert` into `tempfile.TemporaryDirectory()` with the Parameters arguments, then assert: `significant_cluster_union_mask.npy` shape (501, 64) and `observed_statistic.npy` shape (501, 64); `cluster_summary_significant.csv` has exactly 3 rows with cluster_id 1, 2, 3 and `n_channels` 47, 64, 26; the manifest has 260 rows; `test_metadata.json` `n_permutations` 5000 and `cluster_forming_threshold` ≈ 1.97852 (abs tol 1e-4). Then run `cluster_plot.read_run({"data": str(run), "tests": ["01_cond_all"]})` (import `cluster_plot`) and assert it returns one test with 3 clusters. Print `skipped real-data part: <path> not found` when the folder is absent. Print `OK` last.

6. `brain-plot/references/cluster.md`: add one short section `## BESA Statistics input` right before `## Interview rounds` (about 8 lines, English): `besa_to_run.py convert` turns a BESA paired-t cluster project into a run folder; list its arguments in one line; say what it copies (t map, cluster ids, p-values, as written by BESA; p = 0 stays 0 and means p < 1/permutations), what it computes (nothing but the forming threshold from the Cluster Alpha and N), what it needs (the `*_Results.dat` of the project's `IntermediateFiles`, the exported "Summary of Cluster Statistics" csv, the .avr files and `channels.elp`), and that the evoked `.fif` files are rebuilt from the .avr files (nave empty). Then the user draws with the normal cluster spec (`data` = the new run folder).

## Check
`C:/Users/ASUS/miniconda3/envs/mne/python.exe brain-plot/test/test_besa.py`

## Don't
- No commits.
- No rm, no git push, no git checkout . / restore . / reset --hard.
- Only the three files in `## Files`. Leave every other uncommitted file alone, in particular `AGENTS.md`, `AGENTS.md.bak-doctor-2026-10-09`, `docs/cluster-before-after/`, `docs/cluster-layout-compare*.html`, `docs/tfce-mne-vs-standard.html`. Never write inside the Dropbox data folder (the real-data test writes to a temp directory).
- No change to `cluster_plot.py`; no new dependency beyond mne, numpy, scipy.
- Do not weaken a `verify` assertion to make the real-data run pass: if a real-data assertion fails, stop and report which one and its numbers.
- Run scripts in the foreground and wait; before replying, stop any background task still running.
- Reuse existing functions; don't copy existing logic. (`ep.die` is the one this card names.)
- No rm, no git push, no git checkout . / restore . / reset --hard.

## Acceptance
- verdict: accepted (wb executor, medium; codex luna review FAIL with 2 P1, handled below)
- files: `brain-plot/besa_to_run.py`, `brain-plot/test/test_besa.py`, `brain-plot/references/cluster.md`, spec files `docs/besa-candidates/`
- Check: `test_besa.py` OK (synthetic + real data: 7 clusters, 3 significant, N = 130)
- review findings: 1 real / 1 false positive / 2 K missed (luna, medium). Real: [P1] Results.dat p/value vs summary table never compared (fixed by Claude: check added to `verify`). False positive: [P1] .avr orientation (the card said rows = time, wrong; the real file has one row per channel; `verify` check (v) on the real data and Claude's scipy recompute confirm the code). Reviewer P2 on spec files and reply.md: kept (user-requested figures; reply.md is allowed by the runner convention).
- K missed (found by Claude on the first Check runs): test_besa.py mask indexing `[:, m]` should be `[:, m.T]` (also in `verify`), the card's .avr orientation was wrong.
- claude fix: transposed the mask in `verify`/test, .avr read as (channels, samples), p/cluster-value consistency check, removed unused `import sys`.
- independent recompute: t map from raw .avr via `scipy.stats.ttest_rel` vs BESA TValues: max |diff| 5.2e-5; vs the MNE run `erp_cluster_run/01_cond_all`: 8.9e-5; union masks agree on 99.78 % of samples (22501 vs 22483).
- runner note: outcome was `readonly_violated` because `05_v5_tanova_three-groups/` (another analysis, edited by the user at 13:19) changed under the Dropbox read-only path; wb's stream never names it.
- deferred: P3 caption prints `p=0` for BESA's p = 0 (cluster_plot.py line 413, not changed here).
