# Source reconstruction figures (`source_plot.py`)

Read after `SKILL.md` when the request is a cortical source reconstruction map (dSPM, sLORETA, eLORETA on fsaverage). Spec keys: `spec.md`. The script enforces layout, template forward constraints, noise covariance validity, and caching (developer reference: `docs/rules.md`).

## Command

| Command | Use |
|---|---|
| `python source_plot.py plot <spec.json>` | Compute/load source estimates and draw cortical figures (`windows` or `timeline`). |

## Interview rounds

Read the study's own notes and preprocessing logs first (epoch bounds, reference, conditions, montage).

| Round | Decide |
|---|---|
| 1 | Figure type (`figure`: `"windows"` for discrete component windows or `"timeline"` for timecourses), maximum canvas width (`width_mm`, default 180 mm). The canvas fits its content and may be narrower. |
| 2 | Conditions (`conditions`: `{key: label}` mapping), trial selection (`query`, e.g. `"acc == 1"`), exclusions (`exclude`). All subjects pooled without groups (`group_by` ignored). |
| 3 | If `figure: "windows"`: windows (`windows`: list of `{name, tmin_ms, tmax_ms}`). If unknown, localize via `erp_plot.py windows` using `region` + `polarity` to obtain candidate FWHP windows.<br>If `figure: "timeline"`: time points (`times_ms`, default `[100, 200, ..., 800]`), window half width (`half_width_ms`, default 50 ms). |

Source computation parameters (`method`, `lambda2`, `loose`, `depth`, `noise_cov_ms`, `baseline_ms`, `threshold_pct`, `max_pct`): specify or ask only when deviating from defaults:
- `method`: default `"dSPM"` (options: `"dSPM"`, `"sLORETA"`, `"eLORETA"`).
- `lambda2`: default `1/9` (~SNR 3 for evoked responses).
- `loose`: default `0.2` (orientation constraint on cortical surface).
- `depth`: default `0.8` (depth weighting).
- `noise_cov_ms`: default `[-200, 0]` ms. Must lie within the epoch and end at or before 0 ms (pre-stimulus).
- `baseline_ms`: default `[-200, 0]` ms.
- `threshold_pct`: default `90.0` (percentile for `fmin`, below which the cortex is transparent grey).
- `max_pct`: default `99.5` (percentile for `fmax`, upper limit of hot colormap).

The cortex below `fmin` is hidden with a hard threshold, revealing the grey surface. Source runs write PNG, SVG, and
`_run.json`; they do not write `_caption.md`. Per-subject EEG rank is computed and passed to covariance and inverse
estimation. The run record includes rank, `subject_p99`, `outlier_subjects`, and the blank-render check result.

Never ask (settled by house conventions; leave out or use default):
- **Template anatomy** — fsaverage template brain, ico-5 source space, 3-layer BEM (`5120-5120-5120-bem-sol.fif`).
- **Style** — inflated lateral views per hemisphere at 16 mm wide (12–20 mm), original aspect ratio, 3 mm between hemispheres, 6 mm between columns, 3 mm between condition rows; left hemisphere on the left, labels "L" / "R" once per column pair at the top, hot colormap with grey cortex below threshold, 2 mm horizontal colour bar as wide as its brain pair, Arial house style with all text at least 7 pt.
- **Statistics** — no significance marks or p-values exist; figures are purely descriptive grand averages.
- **Journal** — ask width in mm instead (`width_mm`).

## When the script stops

Fix the cause, never work around it; tell the user when the fix changes the figure:
- **`figure must be 'windows' or 'timeline'`** — set `figure` to `"windows"` or `"timeline"`.
- **`method must be 'dSPM', 'sLORETA', or 'eLORETA'`** — set `method` to a supported minimum-norm algorithm.
- **`noise_cov_ms ... outside epoch range`** or **`ends after 0 ms`** — adjust `noise_cov_ms` to lie within the pre-stimulus epoch.
- **`subject ... channel names differ from first subject`** — ensure uniform channel sets and montage across all subject files upstream.
- **`window ... has no time points in data`** — adjust window bounds to stay inside the epoch times.

## QA after every `plot` render (open each PNG)

1. **Left brain on the left**: pairs show left hemisphere lateral on the left, right hemisphere lateral on the right, labelled "L" and "R" once per column pair at the top.
2. **Grey below threshold**: below `fmin` (90th percentile by default), the grey cortical surface shows through; hot colormap values show only above `fmin`.
3. **One colour scale and colour bar per column block**: each window or timeline time point has its own scale across conditions and its own horizontal colour bar underneath, with ticks at fmin, fmid, fmax (2 decimals) and method label.
4. **Timeline layout**: time points are windows; each block row has at most 4 columns, with a colour bar under each column.
5. **Size and proportions**: every brain image is 12–20 mm wide with its original aspect ratio within 2%; all text is at least 7 pt.
6. **No overlaps**: condition labels on the left, column headers, brain pairs, and colour bars are cleanly separated; all layout checks in `_run.json` must be empty.
6. **Outliers**: check `outlier_subjects` in `_run.json`; tell the user, never drop a subject yourself.

## Reading the map (state in Methods)

- **Estimate**: method on the fsaverage template (no individual anatomy), loose, depth, lambda2 (SNR = 1/√lambda2; 3 by default).
- **Orientation**: `pick_ori=None`: magnitude of the three orientations per vertex (non-negative); with `loose: 0` the orientation is fixed normal to the cortex and values are signed.
- **Aggregation**: inverse per subject and condition with that subject's real trial count (`nave`), then equal-weight mean over subjects; not a group statistic.
- **Trial counts**: dSPM noise normalisation scales with `nave`: conditions with different trial counts are not directly comparable in brightness (see `trials_per_subject_condition`). Matching trial counts across conditions is an analysis decision taken upstream; the plot never changes nave.
- **Colour scale**: each window/time column has its own range from percentiles across its conditions (display threshold, not significance); compare colours only within a column.
- **Noise covariance**: from pre-stimulus interval of each epoch (relative to the time-locking event; check that this interval holds no stimulus).
