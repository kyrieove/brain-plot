# Time-frequency figures (`tfr_plot.py`)

Read after `SKILL.md` when the request is a time-frequency figure (power, ITC). Spec keys: `spec.md`. The script enforces layout, style, edge-zone constraints, and caching (developer reference: `docs/rules.md`).

## Command

| Command | Use |
|---|---|
| `python tfr_plot.py plot <spec.json>` | Compute/load TFR grand averages and draw figure(s). |

## Interview rounds

Read the study's own notes and preprocessing logs first (epoch bounds, reference, conditions).

| Round | Decide |
|---|---|
| 1 | ROI channels (`channels`: e.g. `["Fz", "Cz"]`), measure (`measure`: `"power"` or `"itc"`), canvas width (`width_mm`, default 180 mm). |
| 2 | Condition arrangement (`grid`: rows of condition keys, e.g. `[["Hmet","Hlit","Hrep"],["Lmet","Llit","Lrep"]]`; default: up to 3 per row); groups (`groups` and `group_by`, one figure per group); trial selection (`query`, e.g. `"acc == 1"`). |
| 3 | Windows (`windows`: list of `{name, fmin, fmax, tmin_ms, tmax_ms}`; optional, default none) for dashed ROI boxes and topomap rows underneath the panel grid. |

TF computation parameters (`freqs`, `n_cycles`, `decim`, `baseline_ms`, `baseline_mode`, `xlim_ms`): ask or specify only when deviating from standard defaults:
- `freqs`: default `{"fmin": 3, "fmax": 40, "n": 30}` log-spaced.
- `n_cycles`: default `"freqs/2"` (wavelet duration ~ 0.5 s across frequencies).
- `decim`: default down to ~100 Hz.
- `baseline_ms`: default `[-500, -200]` (power only).
- `baseline_mode`: default `"logratio"` (dB = 10 × log10(power / baseline); power only).
- `xlim_ms`: default `[-500, 1500]`.

Never ask (settled by house conventions; leave out or use default):
- **Style** — log-frequency axis with standard band-edge ticks (4, 8, 13, 30 Hz), outward box ticks, dotted vertical line at 0 ms, panel aspect ratio (~1.4 : 1), condition names bold 7.5 pt, panel letters `a`, `b`, ..., shared colour scale (`RdBu_r` symmetric ±v for power, `Reds` 0..v for ITC), right-edge colorbar.
- **Statistics** — no significance marks or p-values exist; figures are purely descriptive grand averages.
- **Journal** — ask width in mm instead (`width_mm`).

## When the script stops

Fix the cause, never work around it; tell the user when the fix changes the figure:
- **`measure must be 'power' or 'itc'`** — set `measure` to `"power"` or `"itc"`.
- **`channels ... not in data channels`** — select channels that exist in the preprocessed epoch files (check online reference electrodes).
- **`... reaches into the edge zone`** — `xlim_ms` or `baseline_ms` is within half the longest wavelet (`(n_cycles/fmin)/2` seconds) of the epoch start or end. Widen the epoch length upstream, or adjust `xlim_ms`, `baseline_ms`, `fmin`, or `n_cycles`.
- **`window ... outside freqs or xlim_ms`** — adjust window `fmin`/`fmax` to stay within `freqs` and `tmin_ms`/`tmax_ms` to stay within `xlim_ms`.
- **`grid key ... not found in conditions`** — fix typo in `grid` to match keys in `conditions`.
- **`group ... has no valid readable subject files`** — check data directory and subject files.

## QA after every `plot` render (open each PNG)

1. **No overlaps**: panel titles, panel letters, condition labels below panels, and window topomap rows must be cleanly separated with no collisions.
2. **Axes and ticks**: frequency ticks at 4, 8, 13, 30 Hz; x-ticks clean with 0 ms marked; "Frequency (Hz)" on left column, "Time (ms)" on bottom row.
3. **Colour bar**: shared vertical colour bar at right edge; dB for power, ITC for itc; symmetric for power.
4. **Topomaps**: topomap row for each window; no sensor dots (rule L11); condition titles below each map; shared row colour bar.
5. **Run record**: `layout_issues` in `_run.json` must be empty.
