# ERP figures (`erp_plot.py`)

Read after `SKILL.md` when the request is an ERP figure (waveforms, topomaps, combo, overview). Spec keys:
`spec.md`. The script enforces layout, style, naming and the data contract itself (developer reference:
`docs/rules.md` in the repository; rule IDs in its messages point there) — you don't need those details to draw.

## Commands

| Command | Use |
|---|---|
| `python erp_plot.py inspect <data_dir>` | Facts about the data: subjects, groups, conditions, channels, epoch, baseline. Run first. |
| `python erp_plot.py explore <explore.json>` | Optional overview before windows are known (below). |
| `python erp_plot.py windows <spec.json>` | Optional candidate windows (below). |
| `python erp_plot.py plot <spec.json>` | The figure(s). |

## Explore (optional, before windows are known)

If the user doesn't yet know the components or windows, draw overview figures first — no interview needed: 3 × 3
waveforms (F3 Fz F4 / C3 Cz C4 / P3 Pz P4, one figure per group) plus a condition × component topomap table,
optionally with difference maps (keys: `spec.md`, section Explore). These are candidates for choosing windows, not
paper figures: no `_run.json`, no QA record; just look at the PNGs before showing them. Windows read off them are
still candidates for the user to fix in round 3.

## Interview rounds

Also read the study's own notes if they exist (analysis plan, results, preprocessing log) to learn the analysed
components and windows, exclusions, reference and stimulus timing.

| Round | Decide |
|---|---|
| 1 | Figure type: `combo` (waveforms + maps, one figure per component), `topo` (maps only), or `erp` (waveforms by channel: `layout` `roi` mean, `single` one figure per channel incl. `channels: "all"`, or `grid`; channels asked here). For `combo`, the maps go beside each waveform panel (default `map_placement: "side"`); when the user wants the maps inside the waveforms, in one multi-panel figure, use `"inset"` with a `grid` for the design (e.g. a 2 × 3 design as 2 rows of 3; not asked by default). Width (`width_mm`, e.g. 180 for double column). What the reader must see first (one sentence → `claim`; always ask — it decides the figure type, components and channels). |
| 2 | Key comparison → `key_comparison` (always ask), which decides `overlay` (the compared variable goes in the same panel) and how lines pair up in `colors`/`linestyles` (e.g. colour = task, line style = level); groups and order (first = reference, drawn black); exclusions; trial selection (all trials or e.g. correct only → `query`, epochs only). |
| 3 | Components (one figure each); channels per component (ROI); windows. `kind: "erp"`: gray component bands only if the user wants them once windows are confirmed — default none. |

Never ask (settled by the user; leave out or use the default):
- **Where a window comes from** — the figure draws the window given; `window_source` is optional, caption only.
- **Display range** — the whole epoch; `xlim_ms` only when the user asks for it (it must include 0).
- **Statistics or the figure's role** — no significance marks exist; if the user volunteers a statistical statement,
  copy it verbatim into `stats_note`, never derive one.
- **`time_locked_to`, `reference`** — caption only: read them from the preprocessing scripts and files; if they are
  not there, leave them out. Never ask, never fill from memory.
- **Style** — polarity (positive up), colours (Lancet palette in order, any line count; ordered
  levels viridis), line styles, fonts, colour map (RdBu_r), SEM band (none): house defaults; change only when the
  user asks (`polarity`, `colors`, `linestyles`, `cmap`, `error: "sem"`). Line pairing from round 2 is part of the
  key comparison, not a style question.
- **Journal** — ask the width instead.

Caption-only fields (`claim`, `key_comparison`, `time_locked_to`, `reference`, `window_source`, `stats_note`,
exclusion reasons) are optional: unknown → leave the key out, never "to be confirmed". Never put n in labels or
titles; n goes into the caption facts automatically.

Candidate windows, only if the user wants help: `windows` needs a `combo`/`topo` spec whose components carry ROI
`channels`, with search ranges in `tmin_ms`/`tmax_ms`. A `kind: "erp"` spec is refused — tell the user so, don't
guess an ROI. Its output is heuristic candidates; the user names components and fixes windows.

## When the script stops

Fix the cause, never work around it; tell the user when the fix changes the figure.
- **Stacked panels shorter than 15 mm** — take the `height_mm` the message names, or the other `overlay` it
  proposes.
- **Flat channel** (constant over the epoch) — ask whether it is the reference electrode (then add it to
  `flat_channels`) or a broken channel to fix upstream; never add it without that answer.
- **Data contract** (channels, time grid, baseline, filter, reference flag, bad channels, projectors differ between
  subjects) — report it; the loader never re-references, resamples or interpolates.
- **Unsupported request** — difference waves, lateralised components (N2pc, LRP), CSD/source/time–frequency data,
  significance marks, more than 7 overlaid lines: say "not supported", don't approximate.

## QA after every `plot` render (open each PNG)

1. Nothing overlaps: legend vs lines, SEM shading, gray band and its label; tick labels vs lines; titles vs letters.
   The script checks texts, legends and lines itself (`layout_issues` in `_run.json`, also printed): report every
   entry, fix what the spec can fix, and still look for what it cannot see (SEM shading, bands).
2. Gray band, topomap window text and caption window agree (inset: no band and no window text; the caption states it).
3. combo/topo: no dots or other electrode marks on the maps.
4. `open_items` in `_run.json` is empty, or every listed field is reported to the user as open.
5. `colour_distinctness`: report a normal-vision value below 10 with the two colours (colour-blind values are
   recorded, not reported). The palette stays the user's choice.
6. Readability (report, don't change the figure on your own): `xlim_ms` hides part of the baseline; or one map
   dominates the shared colour scale so the others look near-white — correct, but readers may read it as no activity.
7. `map_placement: "inset"`: `inset_audit` in `_run.json` has no clashes (the script has already stopped on any: maps
   over a curve, an axis or a text, rule L13); look anyway. One legend under the grid, panel letters in
   reading order, and the same y-range and map size in every panel. If the script stops because nothing fits, follow
   its message (fewer panels per row, larger canvas, fewer lines) — never fall back to overlapping maps.
8. `_run.json`: `lines`/`maps` fit the kind (combo: both = expected; erp: maps 0; topo: lines 0); `size_mm` equals
   the spec canvas; `legend` says where the legend went; then replace its `qa` field with the result ("passed" or the
   open problems).
