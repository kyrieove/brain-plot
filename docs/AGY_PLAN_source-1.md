# AGY PLAN source-1: the `source` module (cortical dSPM maps) + a region-based localizer

You implement; Claude reviews the diff and the figures afterwards. Repo `C:\dev\brain-plot` (git branch `source`,
already checked out — do not switch branches, do not commit, do not use git at all).
Python: `C:\Users\ASUS\miniconda3\envs\mnedev\python.exe` (MNE 1.13 dev, pyvista 0.48, pyvistaqt, nibabel).
fsaverage: `C:\Users\ASUS\mne_data\MNE-fsaverage-data` (subjects_dir; `fsaverage\bem\fsaverage-5120-5120-5120-bem-sol.fif`,
`fsaverage\bem\fsaverage-ico-5-src.fif`, inflated surfaces, aparc labels). Real data (READ-ONLY):
`D:\1-python_datasets\metaphor production\derivatives\preprocessed_epochs_verb\` (`sub*-epo.fif`, 60 subjects,
−1…2 s, 500 Hz, 63 EEG channels, montage present, linked-mastoid reference, no baseline applied, metadata has `acc`).

## Boundaries
- Allowed files (create/change only these): `brain-plot/source_plot.py` (new), `brain-plot/test/test_source.py` (new),
  `brain-plot/references/source.md` (new), `brain-plot/references/spec.md` (new section at the end, before Microstate
  is fine), `brain-plot/SKILL.md` (router row + the description's "not for … source" wording), `docs/rules.md`
  (new section "Source figures", rules SRC1…), `brain-plot/erp_plot.py` (function `windows` and `check_spec` only),
  `brain-plot/references/erp.md` (the windows lines only), `brain-plot/test/test_erp_plot.py` (windows tests only).
  Outputs of the real run: only under `D:\1-python_datasets\metaphor production\derivatives\brain_plot_preprocessed_epochs_verb\`
  (`source\`, `specs\source_*.json`, `.cache\source\`). Never delete, move or overwrite anything else.
- **Reuse existing functions; do not copy existing logic**: from `erp_plot` (`ep`) use `die`, `read_spec`,
  `select_files`, `unit_files`, `uid`, `query_epochs`, `out_root`, `safe`, `name_part`, `versioned`, `archive`,
  `report_layout`, `letter`; follow `tfr_plot.py` for the structure (check_spec with REQUIRED/OPTIONAL, cache under
  `out_root/.cache/<module>/<param hash>/`, `_run.json`, `plot()` + `__main__`). No `_caption.md` for source (user).
- Run every script in the foreground and wait for it; before you reply, make sure no background task is still running.
- `n_jobs` ≤ 2 everywhere.
- Progress: after each step append one line to `C:\dev\brain-plot\AGY_PROGRESS_source.md`,
  format `[██░░░░] 2/6 <what> · HH:MM`; first line `[░░░░░░] 0/6 start · HH:MM`.

## What the module computes (`source_plot.py`)
Per subject (one epochs file = one subject; all subjects pooled, no groups — ignore `group_by` if given):
1. Read epochs, `ep.query_epochs` (spec `query`, e.g. `"acc == 1"`), `set_eeg_reference("average", projection=True)`,
   `apply_baseline((-0.2, 0))` (spec `baseline_ms`, default `[-200, 0]`).
2. Noise covariance from the same epochs, `tmin/tmax` = spec `noise_cov_ms` (default `[-200, 0]`),
   `method="shrunk"`. Stop (ep.die) if the window is outside the epoch or ends after 0 ms.
3. One evoked per condition key (`conditions` like the ERP specs), cropped to `[-200, 1000]` ms and decimated to
   100 Hz (data are low-passed at 45 Hz).
4. Cache per subject: `npz` with the evoked data (cond × ch × t), nave per condition, the noise cov matrix and the
   channel names (small; this is what makes the run resumable — a subject whose npz exists is not re-read).
Forward: computed once from the first subject's info (`trans="fsaverage"`, the src and bem-sol files above,
`eeg=True, meg=False, mindist=5`), cached as `-fwd.fif` in the cache folder; stop if a subject's channel names differ.
Inverse per subject: `make_inverse_operator(info, fwd, cov, loose=0.2, depth=0.8)`,
`apply_inverse(evoked, inv, lambda2=1/9, method="dSPM", pick_ori=None)` → magnitude (the stc already is the norm).
Spec keys `method` (`"dSPM"` default, `"sLORETA"`, `"eLORETA"`), `lambda2`, `loose`, `depth` override these.
Grand average = equal-weight mean over subjects of the per-subject stc data, accumulated in a running sum (never hold
all subjects in memory). Cache the grand average (cond × vertices × t, float32) keyed by the parameter hash + the
sorted subject list. Subjects: all readable files minus `exclude` (dict id → reason, like the ERP specs); optional
`subjects` list restricts the pool.

## Figures (`python source_plot.py plot <spec.json>`)
Rendering: `mne.viz.Brain("fsaverage", hemi, "inflated", subjects_dir=..., background="white",
cortex="low_contrast", offscreen=True, size=...)`, lateral view per hemisphere, `add_data(values, fmin, fmid, fmax,
thresh=fmin, colormap="hot", colorbar=False, smoothing_steps="nearest" or 10)`; update the data on one Brain per
hemisphere and `screenshot()` each map; trim white margins; place the images with `imshow` on a matplotlib figure of
fixed width (`width_mm`, default 180 mm), height from the grid. All text by matplotlib (Arial house style, as in
`tfr_plot`), none in 3D; no electrode marks; brains of a pair: left hemisphere on the left, labels "L" / "R" once
per column pair at the top.
Colour limits (one set per colour-bar group, computed over all maps of that group, both hemispheres):
`fmin` = percentile `threshold_pct` (default 90), `fmax` = percentile `max_pct` (default 99.5), `fmid` = mean of both.
Below `fmin` the grey cortex shows (like the reference figure). Colour bar: horizontal, under its block, ticks at fmin,
fmid, fmax with 2 decimals, label "dSPM" (or the method name).
- `figure: "windows"` (main figure; reference: Tian et al., Neurobiology of Language, Fig. 2B): rows = conditions (in
  `conditions` order; row label = condition label, left), column blocks = `windows` (list of `{name, tmin_ms,
  tmax_ms}`), each block = L + R lateral; block title "<name> (<tmin>–<tmax> ms)" above; value = mean over the window;
  **one colour bar per block**, under it.
- `figure: "timeline"` (reference: same author, Fig. 2 of the metaphor study): rows = conditions, columns = time
  points `times_ms` (default 100, 200, …, 800), value = mean over ± `half_width_ms` (default 50); each column = L + R
  pair with the time above; when there are more than 4 time points, split into blocks of 4 stacked vertically;
  **one colour bar for the whole figure**, under the last block.
Outputs in `out_root(spec)/"source"`: stem `source-<figure>_<method>[_<window names>]{ep.name_part(spec)}`, PNG + SVG
via `ep.versioned` / `ep.archive` like `tfr_plot`; `_run.json` with: subjects used, excluded (+ reasons), trials per
subject × condition, all parameters (method, lambda2, loose, depth, noise_cov_ms, baseline_ms, src/bem file names),
colour limits per block, `layout_issues` from `ep.report_layout` (must be empty), `hemisphere_check` (below).
Self-check `hemisphere_check`: not needed on real data; it is the test below.

## Localizer: `erp_plot.py windows` without fixed channels
Today every component needs `channels`. Add: a component may instead give `region` (list of channel names — a rough
area from the literature) and `polarity` (`"positive"` / `"negative"`) with its search range `tmin_ms`–`tmax_ms`.
Then, on the same collapsed average `windows` already uses (all subjects, all conditions, equal weight): find the
channel × time with the most extreme value of that polarity inside region × range; print peak channel, latency,
amplitude; the window = full width at half prominence of that channel's waveform around the peak (same `peak_widths`
logic as today — reuse it, do not copy); ROI = region channels whose value at the peak latency is ≥ 80 % of the peak
(same sign). Also print the GFP (std over all channels) peak latency inside the range as a cross-check, and a
`WARNING` line if it is more than 50 ms from the channel peak. Finally print one JSON line
`WINDOWS_JSON [{"name":…, "tmin_ms":…, "tmax_ms":…, "peak_ms":…, "peak_channel":…, "roi":[…]}, …]` so the result
can be pasted into a source spec. Components with `channels` keep today's behaviour; a component with neither
`channels` nor `region`+`polarity` still stops (update the existing test at `test_erp_plot.py` ~line 291 accordingly,
and add one test for the region path on the synthetic data the test file already builds). `check_spec` must accept
components without `channels` for this command.

## Steps (N = 6)
1. Read `brain-plot/tfr_plot.py`, `brain-plot/references/tfr.md`, the TFR section of `references/spec.md`, and the
   helpers listed above in `erp_plot.py`. Write nothing yet.
2. Localizer change in `erp_plot.py` + tests; run `python brain-plot/test/test_erp_plot.py` → `OK`.
3. `source_plot.py`.
4. `test/test_source.py` (fast, no real data; target < 3 min): synthetic evoked on a `standard_1020` montage
   (~32 EEG channels) with a source simulated in `superiortemporal-lh` (aparc) using a coarse fsaverage source space
   (`setup_source_space("fsaverage", "oct4", add_dist=False)`); the module functions must accept the src/forward so the
   test does not need ico-5. Assertions: (a) **hemisphere check** — in the rendered L/R images of that map, the count
   of coloured (non-grey, non-white) pixels is larger on the left brain than on the right; (b) noise_cov_ms ending
   after 0 ms stops with a message; (c) a spec with an unknown key stops; (d) a `windows` and a `timeline` figure are
   written with empty `layout_issues`. Then run all suites, each must print `OK`:
   `test_erp_plot.py`, `test_layout.py`, `test_microstate.py`, `test_tfr.py`, `test_source.py`.
5. Docs: `references/source.md` (same shape as `references/tfr.md`: command, interview rounds, never ask, stops, QA
   list incl. "left brain on the left", "grey below threshold", "one colour bar per window block / one per timeline"),
   spec section, SKILL.md router row `| Source maps (dSPM on fsaverage) | source_plot.py | references/source.md |`,
   `docs/rules.md` SRC1–SRC6 (method + template forward; noise cov / baseline window; averaging; thresholded hot
   colour map and colour-bar groups; layouts; cache).
6. Real data, timeline figure only (windows are decided later): write
   `…\brain_plot_preprocessed_epochs_verb\specs\source_timeline.json` with `data` = the verb epochs folder,
   `conditions` = `{"Hmet": "Metaphor (high)", "Hlit": "Literal (high)", "Hrep": "Repetition (high)", "Lmet":
   "Metaphor (low)", "Llit": "Literal (low)", "Lrep": "Repetition (low)"}`, `query: "acc == 1"`,
   `exclude: {"sub27": "acc is 3 on every trial in epoch_10800_60_final.xlsx (no acc == 1 trials)"}`,
   `time_locked_to: "verb onset"`, `figure: "timeline"`. Run `python brain-plot/source_plot.py plot <spec>`
   (all 59 subjects; this also builds the per-subject cache). Report the wall time and the `_run.json` path.

## Reply (≤ 10 lines)
Status; files changed; test output lines; the real-run PNG path and wall time; anything you could not do or changed
from this plan (and why).
