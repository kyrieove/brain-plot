# Spec format (erp_plot.py v1)

A JSON object. Unknown keys stop the script. Example: `test/fig_main.json`.

## Required

| Key | Meaning |
|---|---|
| `data` | Folder with one `*-epo.fif` or `*-ave.fif` per subject; sub-folders are groups. Subject ID = file name up to the first `_`, `-` or `.`. |
| `conditions` | `{file_key: label}`; file_key is the event name (epochs) or comment (evoked). Order = panel/line order. |
| `components` | List of `{name, channels, tmin_ms, tmax_ms, window_source}`; one figure each. `name`: letters/digits/`_`/`-`, unique ignoring case (it becomes a file name). `channels`: non-empty, no repeats. The window must lie inside `xlim_ms`. `window_source` says exactly where the window comes from (rule S3). |
| `claim` | What the figure is meant to show, as confirmed with the user (one sentence). |
| `key_comparison` | The comparison the layout serves (e.g. "groups within each condition"). |
| `time_locked_to` | Event at 0 ms, as it should read in the caption (non-empty). |
| `reference` | Reference scheme for the caption (non-empty; files often don't store it). |
| `out` | Output prefix; files are `<out>_<component>.png/.svg`, `<out>_<component>_caption.md`, `<out>_<component>_run.json`. |

## Optional

| Key | Default | Meaning |
|---|---|---|
| `kind` | `"combo"` | `"combo"`: waveforms + topomaps. `"erp"`: waveforms only (default canvas 180 × 120 mm). `"topo"`: topomaps only, each panel a block of maps whose shape adapts to line and panel count (rule K2; e.g. 6 lines × 2 panels → 2 × 3, × 4 panels → 1 × 6), one shared colour scale. |
| `groups` | all sub-folders (or `group_by` values), alphabetical | Which groups, in order; the first is drawn black when groups are overlaid. |
| `group_by` | none | Metadata column holding a between-subject group (e.g. `"WM"`), for a flat folder of epochs files; must be constant within each file. Groups are its values. |
| `exclude` | none | `{subject_id: reason}`; every ID must exist, every reason non-empty. |
| `query` | none | Pandas-style metadata query, epochs only (stops on `-ave.fif`). |
| `overlay` | `"groups"` | `"groups"`: one panel per condition, groups overlaid. `"conditions"`: one panel per group, conditions overlaid. |
| `ordered` | false | Conditions are ordered levels (viridis colours). |
| `linestyles` | all solid | One of `-`, `--`, `:`, `-.` per line, for a second factor in the same panel (rule T3). |
| `colors` | rule T3 | List of colours, one per overlaid line, in order (at most 7 lines). |
| `xlim_ms` | whole epoch | Display range; must include 0 and lie inside the data. |
| `polarity` | `"positive_up"` | or `"negative_up"`. |
| `width_mm` / `height_mm` | 180 / 120 | Fixed final canvas (rule T6); content is fitted inside. |
| `cmap` | `"RdBu_r"` | Topomap colour map (a diverging map). |
| `error` | `"none"` | `"sem"` adds a between-subject ± SEM band. |
| `stats_note` | none | The author's statistical statement, copied into the caption facts. |

## Not supported in v1 (stop, don't approximate)

Difference waves, lateralised components (N2pc, LRP), CSD or source data, time–frequency, significance marks, response-locked data with no 0 in range, more than 7 overlaid lines.

## Explore spec (`python erp_plot.py explore <spec.json>`)

Overview figures for choosing components and windows — not paper figures, no window bands, no interview needed.
Required: `data`, `conditions`, `out`. Also accepted from above: `groups`, `group_by`, `exclude`, `query`, `colors`,
`linestyles`, `ordered`, `xlim_ms`, `polarity`, `width_mm`/`height_mm`, `cmap`.

| Key | Default | Meaning |
|---|---|---|
| `channels` | `[["F3","Fz","F4"],["C3","Cz","C4"],["P3","Pz","P4"]]` | Waveform grid, rows front to back, each row left to right; every name must exist. |
| `components` | none | `[{name, tmin_ms, tmax_ms}]`; topomap table columns (tentative windows). No components → no table. |
| `differences` | none | `[[A, B], …]` condition keys; adds A − B difference-map rows (within subject, then averaged; own colour scale). |
| `topo_scale` | `"global"` | One colour scale for all condition maps; `"component"` = one per column (horizontal µV bar under it). |

Outputs per group: `<out>_<group>_waves` (all conditions overlaid per channel, shared y-range, legend centred
under the grid) and `<out>_<group>_topo` (rows = conditions + differences, columns = components), `.png/.svg`.
