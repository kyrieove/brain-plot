# Spec format (erp_plot.py v1)

A JSON object. Unknown keys stop the script (an old spec with `out` stops too: delete the key). Example:
`test/fig_main.json`. Keep specs in `brain-plot/specs/`.

Outputs go to `brain-plot/` next to the data folder (rules O1–O3): `ERP_topo/ERP-topo_<component>_<channels>_<window>_<comparison>_vNN`,
`topo/topo_<component>_<window>_<comparison>_vNN`, `ERP/ERP-ROI_<channels>[_<band>-<window>]_<comparison>_vNN`, `ERP/ERP_<channel>_…` (single), `ERP/ERP-all-channels_<comparison>_vNN/` (single, all), `ERP/ERP-grid-<rows>x<cols>_<lines>_<facet level>_vNN` (grid); each as
`.png .svg`, `_caption.md`, `_run.json`. `<comparison>` is `groups-by-condition` (`overlay: "groups"`) or
`conditions-by-group`.

## Required

| Key | Meaning |
|---|---|
| `data` | Folder with one `*-epo.fif` or `*-ave.fif` per subject; sub-folders are groups. Subject ID = file name up to the first `_`, `-` or `.`. |
| `conditions` | `{file_key: label}`; file_key is the event name (epochs) or comment (evoked). Order = panel/line order. |
| `components` | combo/topo: list of `{name, channels, tmin_ms, tmax_ms}` (+ optional `window_source`); one figure each. erp: optional gray bands `{name, tmin_ms, tmax_ms}` (+ optional `window_source`) (no channels), default none. `name`: letters/digits/`_`/`-`, unique ignoring case (it becomes a file name). `channels`: non-empty, no repeats. The window must lie inside `xlim_ms`. `window_source` (optional, caption only): where the window comes from, if the author wants it in the caption. |

## Optional

| Key | Default | Meaning |
|---|---|---|
| `kind` | `"combo"` | `"combo"`: waveforms + topomaps. `"erp"`: waveforms by channel (rule K1; needs `channels`, optional `layout`). `"topo"`: topomaps only, each panel a block of maps whose shape adapts to line and panel count (rule K2; e.g. 6 lines × 2 panels → 2 × 3, × 4 panels → 1 × 6), one shared colour scale. |
| `channels` | — | erp only: list of names (`roi`, `single`), `"all"` (`single`), or rows of names (`grid`, e.g. `[["F3","Fz","F4"],["C3","Cz","C4"],["P3","Pz","P4"]]`). |
| `layout` | `"roi"` | erp only: `"roi"` (mean of the channels), `"single"` (one figure per channel), `"grid"` (one figure per facet level, a panel per channel). |
| `groups` | all sub-folders (or `group_by` values), alphabetical | Which groups, in order; the first is drawn black when groups are overlaid. |
| `group_by` | none | Metadata column holding a between-subject group (e.g. `"WM"`), for a flat folder of epochs files; must be constant within each file. Groups are its values. |
| `exclude` | none | List of subject IDs, or `{subject_id: reason}` (reason optional, caption only); every ID must exist. |
| `query` | none | Pandas-style metadata query, epochs only (stops on `-ave.fif`). |
| `overlay` | `"groups"` | `"groups"`: one panel per condition, groups overlaid. `"conditions"`: one panel per group, conditions overlaid. |
| `ordered` | false | Conditions are ordered levels (viridis colours). |
| `linestyles` | all solid | One of `-`, `--`, `:`, `-.` per line, for a second factor in the same panel (rule T3). |
| `colors` | rule T3 | List of colours, one per overlaid line, in order (at most 7 lines). |
| `xlim_ms` | whole epoch | Display range; must include 0 and lie inside the data. |
| `polarity` | `"positive_up"` | or `"negative_up"`. |
| `claim` | none | Caption only: what the figure is meant to show (one sentence). Omitted → no caption line. |
| `key_comparison` | none | Caption only: the comparison the layout serves (e.g. "groups within each condition"). |
| `time_locked_to` | none | Caption only: event at 0 ms, as it should read in the caption. |
| `reference` | none | Caption only: reference scheme (files often don't store it). |
| `width_mm` / `height_mm` | 180 / 120 | Fixed final canvas (rule T6); content is fitted inside. |
| `cmap` | `"RdBu_r"` | Topomap colour map (a diverging map). |
| `error` | `"none"` | `"sem"` adds a between-subject ± SEM band. |
| `stats_note` | none | The author's statistical statement, copied into the caption facts. |
| `flat_channels` | none | Channels allowed to be constant over the epoch (rule S10), e.g. `["FCz"]` for a reference electrode kept at 0 µV; any other flat channel stops the script. Also in explore and microstate specs. |

## Not supported in v1 (stop, don't approximate)

Difference waves, lateralised components (N2pc, LRP), CSD or source data, time–frequency, significance marks, response-locked data with no 0 in range, more than 7 overlaid lines.

## Microstate spec (`python microstate_plot.py plot <spec.json>`)

Required: `data` (any loader layout, including `<condition>/<group>/<subject>*-ave.fif`), `conditions`, `templates`
(path; `{k}` is replaced, e.g. `…/centers_k{k:02d}.npz`), `k` (integer for `figure: "states"`, list for `"by-K"`).

| Key | Default | Meaning |
|---|---|---|
| `figure` | `"states"` | `"states"`: one K, templates + time panels; `"by-K"`: template rows for several K. |
| `blocks` | `["topo", "butterfly", "ribbon"]` | Any of `topo`, `butterfly`, `gfp`, `ribbon`, with `butterfly` and/or `gfp`; order sets the file name. |
| `window_ms` | `[0, 800]` | Segmented and drawn range (as in the analysis). |
| `min_segment_ms` | 30 | Shorter runs merge into the better-fitting neighbour. |
| `polarity` | `"sensitive"` | `"insensitive"` if the analysis ignored map polarity. |
| `per_group` | false | One row per condition × group instead of per condition (at most 2 rows without a grid). |
| `grid` | none | Rows × columns of condition keys, e.g. `[["Hmet","Hlit","Hrep"],["Lmet","Llit","Lrep"]]`; required for more than 2 conditions (rule MS9). |
| `hatch` | false | true: hatch samples whose GFP is below the pre-stimulus 95th percentile (rule MS3); needs pre-stimulus samples. |
| `templates_source` | none | Caption only: which analysis made the templates. |
| `identity_threshold` | 0.9 | by-K: signed r at which two templates count as the same map. |
| `groups`, `exclude`, `flat_channels`, `width_mm`/`height_mm` (180 × 110), `cmap`, `reference`, `time_locked_to` | | As above; the last two only feed the caption facts. |

## Explore spec (`python erp_plot.py explore <spec.json>`)

Overview figures for choosing components and windows — not paper figures, no window bands, no interview needed.
Required: `data`, `conditions`. Also accepted from above: `groups`, `group_by`, `exclude`, `query`, `colors`,
`linestyles`, `ordered`, `xlim_ms`, `polarity`, `width_mm`/`height_mm`, `cmap`, `flat_channels`.

| Key | Default | Meaning |
|---|---|---|
| `channels` | `[["F3","Fz","F4"],["C3","Cz","C4"],["P3","Pz","P4"]]` | Waveform grid, rows front to back, each row left to right; every name must exist. |
| `components` | none | `[{name, tmin_ms, tmax_ms}]`; topomap table columns (tentative windows). No components → no table. |
| `differences` | none | `[[A, B], …]` condition keys; adds A − B difference-map rows (within subject, then averaged; own colour scale). |
| `topo_scale` | `"global"` | One colour scale for all condition maps; `"component"` = one per column (horizontal µV bar under it). |

Outputs per group: `ERP/ERP-grid-<rows>x<cols>_conditions_<group>_vNN` (all conditions overlaid per channel, shared
y-range, legend centred under the grid) and `topo/topo-table_<components>_<group>_vNN` (rows = conditions +
differences, columns = components), `.png/.svg`.
