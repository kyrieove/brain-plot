# Spec format (erp_plot.py v1)

A JSON object. Unknown keys stop the script (an old spec with `out` stops too: delete the key). Examples:
`examples/specs/` (synthetic data: `python examples/make_demo_data.py`). Relative `data` and `templates` paths are taken from the spec file's folder. Keep specs in `brain_plot_<data folder name>/specs/`.

Outputs go to `brain_plot_<data folder name>/` next to the data folder (rules O1–O3): `ERP_topo/ERP-topo_<component>_<channels>_<window>_<comparison>_vNN`,
`topo/topo_<component>_<window>_<comparison>_vNN`, `ERP/ERP-ROI_<channels>[_<band>-<window>]_<comparison>_vNN`, `ERP/ERP_<channel>_…` (single), `ERP/ERP-all-channels_<comparison>_vNN/` (single, all), `ERP/ERP-grid-<rows>x<cols>_<channels>_<lines>_<facet level>_vNN` (grid); a figure of only some groups or conditions, or with a `query`, adds `_grp-…`, `_cond-…` or `_query-<hash>` before `_vNN` (rule O3); each as
`.png .svg`, `_caption.md`, `_run.json`. `<comparison>` is `groups-by-condition` (`overlay: "groups"`) or
`conditions-by-group`.

## Required

| Key | Meaning |
|---|---|
| `data` | Folder with one `*-epo.fif` or `*-ave.fif` per subject; sub-folders are groups. Subject ID = file name up to the first `_`, `-` or `.`; BIDS names keep their label (`sub-01_task-x-ave.fif` → `sub-01`). |
| `conditions` | `{file_key: label}`; file_key is the event name (epochs) or comment (evoked). Order = panel/line order. |
| `components` | combo/topo: list of `{name, channels, tmin_ms, tmax_ms}` (+ optional `window_source`); one figure each. erp: optional gray bands `{name, tmin_ms, tmax_ms}` (+ optional `window_source`) (no channels), default none. `name`: letters/digits/`_`/`-`, unique ignoring case (it becomes a file name). `channels`: non-empty, no repeats. The window must lie inside `xlim_ms`. `window_source` (optional, caption only): where the window comes from, if the author wants it in the caption. |

## Optional

| Key | Default | Meaning |
|---|---|---|
| `kind` | `"combo"` | `"combo"`: waveforms + topomaps. `"erp"`: waveforms by channel (rule K1; needs `channels`, optional `layout`). `"topo"`: topomaps only, each panel a block of maps whose shape adapts to line and panel count (rule K2; e.g. 6 lines × 2 panels → 2 × 3, × 4 panels → 1 × 6), one shared colour scale. |
| `channels` | — | erp only: list of names (`roi`, `single`), `"all"` (`single`), or rows of names (`grid`, e.g. `[["F3","Fz","F4"],["C3","Cz","C4"],["P3","Pz","P4"]]`). |
| `layout` | `"roi"` | erp only: `"roi"` (mean of the channels), `"single"` (one figure per channel), `"grid"` (one figure per facet level, a panel per channel). |
| `map_placement` | `"side"` | kind `combo` only. `"side"`: stacked waveform panels, maps in a column right of each. `"inset"` (rule L12): the panels in a grid in one figure, each with its maps (in one row) at its lower right; no gray band, no window text, one colour bar at the figure's right edge; nothing overlaps (rule L13, self-checked); when the maps do not fit, the spacing between the panels tightens, else the script stops. Output `ERP-topo-inset_…`. |
| `grid` | none | `map_placement: "inset"` only: rows × columns of the panel keys (condition keys, or group names with `overlay: "conditions"`), each once, rows of equal length, e.g. `[["c1","c2","c3"],["c4","c5","c6"]]`. Default: up to 3 panels in a row, 4 as 2 × 2, up to 8 in two rows. |
| `groups` | all sub-folders (or `group_by` values), alphabetical | Which groups, in order (colours follow this order). |
| `group_by` | none | Metadata column holding a between-subject group (e.g. `"WM"`), for a flat folder of epochs files; must be constant within each file. Groups are its values. |
| `exclude` | none | List of subject IDs, or `{subject_id: reason}` (reason optional, caption only); every ID must exist. |
| `query` | none | Pandas-style metadata query, epochs only (stops on `-ave.fif`). |
| `overlay` | `"groups"` | `"groups"`: one panel per condition, groups overlaid. `"conditions"`: one panel per group, conditions overlaid. |
| `ordered` | false | Conditions are ordered levels (viridis colours). |
| `linestyles` | all solid | One of `-`, `--`, `:`, `-.` per line, for a second factor in the same panel (rule T3). |
| `colors` | rule T3 | List of colours, one per overlaid line, in order (at most 7 lines). |
| `xlim_ms` | whole epoch | Display range; must include 0 and lie inside the data. |
| `polarity` | `"negative_up"` | or `"positive_up"` (every waveform panel, both axis styles; names get `_pos-up`, rule O3). |
| `axes` | `"cross"` | `"cross"`: spines through origin (0 µV, 0 ms), labels next to lines (rule T1). `"box"`: left + bottom axes with outside ticks, "Time (ms)" / "Amplitude (µV)" titles, thin 0-µV and dotted 0-ms lines; every ERP waveform figure (combo side/inset, erp roi/single/grid, explore) supports it. In a grid of channel panels the axis titles sit on the outer panels only. Also an explore key. |
| `claim` | none | Caption only: what the figure is meant to show (one sentence). Omitted → no caption line. |
| `key_comparison` | none | Caption only: the comparison the layout serves (e.g. "groups within each condition"). |
| `time_locked_to` | none | Event at 0 ms, as it should read in the caption; also appended to every output name as `_lock-<event>` (rule O3), so datasets locked to different events never share a name. ERP, explore and TFR specs. |
| `reference` | none | Caption only: reference scheme (files often don't store it). |
| `width_mm` / `height_mm` | 180 / 120 | Fixed final canvas (rule T6); content is fitted inside. Stacked waveform panels (and erp grid cells) need ≥ 15 mm each; the script stops and names the `height_mm` that works (rule L3). |
| `cmap` | `"RdBu_r"` | Topomap colour map (a diverging map). |
| `error` | `"none"` | `"sem"` adds a between-subject ± SEM band. |
| `stats_note` | none | The author's statistical statement, copied into the caption facts. |
| `flat_channels` | none | Channels allowed to be constant over the epoch (rule S10), e.g. `["FCz"]` for a reference electrode kept at 0 µV; any other flat channel stops the script. Also in explore and microstate specs. |

## Not supported in v1 (stop, don't approximate)

Difference waves, lateralised components (N2pc, LRP), CSD or source data, significance marks, response-locked data with no 0 in range, more than 7 overlaid lines. (Time–frequency is supported via `tfr_plot.py`, see below.)

## Time–frequency spec (`python tfr_plot.py plot <spec.json>`)

Required: `data` (folder of `*-epo.fif` files), `conditions` (`{key: label}`), `channels` (ROI list, e.g. `["Fz", "Cz"]`), `measure` (`"power"` or `"itc"`).

| Key | Default | Meaning |
|---|---|---|
| `measure` | — | `"power"` (total Morlet power relative to baseline, displayed in dB) or `"itc"` (inter-trial phase coherence, 0–1). |
| `channels` | — | List of channel names to average over for the ROI panels. |
| `grid` | up to 3 per row | Rows × columns of condition keys, e.g. `[["Hmet","Hlit","Hrep"],["Lmet","Llit","Lrep"]]`. |
| `groups` | all discovered | List of groups to draw (one figure per group). |
| `group_by` | none | Metadata column holding between-subject group (e.g. `"WM"`). |
| `exclude` | none | List of subject IDs to exclude. |
| `query` | none | Pandas-style query applied to epochs metadata (e.g. `"acc == 1"`). |
| `freqs` | `{"fmin": 3, "fmax": 40, "n": 30}` | Log-spaced frequencies dict or list of frequencies. |
| `n_cycles` | `"freqs/2"` | Number of cycles per wavelet, or `"freqs/2"` (~0.5 s wavelets). |
| `decim` | to ~100 Hz | Decimation factor for time points. |
| `baseline_ms` | `[-500, -200]` | Baseline interval in ms (measure `"power"` only). |
| `baseline_mode` | `"logratio"` | Only `"logratio"` (dB); other values stop. Measure `"power"` only. |
| `xlim_ms` | `[-500, 1500]` | Time range to display in ms. Must not reach into edge zone. |
| `windows` | none | List of `{name, fmin, fmax, tmin_ms, tmax_ms}`. Adds dashed rectangle in panels and a topomap row per window. |
| `cmap` | `"RdBu_r"` (power) / `"Reds"` (itc) | Colormap for TF panels and topomaps. |
| `width_mm` | 180 | Figure width in mm. |
| `height_mm` | auto | Figure height in mm (~1.4 : 1 per panel plus 26 mm per topomap row). |

Outputs go to `TFR/` under the output root: `TFR-<measure>_<channels>_<group>[_<windows>]_vNN.png/.svg`, `_run.json`, `_caption.md`.


## Source reconstruction spec (`python source_plot.py plot <spec.json>`)

Required: `data` (folder of `*-epo.fif` files), `conditions` (`{key: label}`).

| Key | Default | Meaning |
|---|---|---|
| `figure` | `"windows"` | `"windows"`: discrete component windows; `"timeline"`: timecourses across time points. |
| `windows` | none | Required for `figure: "windows"`. List of `{name, tmin_ms, tmax_ms}`. |
| `times_ms` | `[100, 200, 300, 400, 500, 600, 700, 800]` | Time points in ms (`figure: "timeline"` only). |
| `half_width_ms` | 50 | Time window half-width in ms around each time point (`figure: "timeline"` only). |
| `method` | `"dSPM"` | Minimum-norm inverse method (`"dSPM"`, `"sLORETA"`, or `"eLORETA"`). |
| `lambda2` | `1/9` (~0.111) | Regularization parameter. |
| `loose` | 0.2 | Orientation constraint on cortical surface (0: fixed, 1: free). |
| `depth` | 0.8 | Depth weighting exponent. |
| `noise_cov_ms` | `[-200, 0]` | Pre-stimulus noise covariance window in ms. Must not end after 0 ms. |
| `baseline_ms` | `[-200, 0]` | Baseline interval in ms applied to epochs. |
| `threshold_pct` | 90.0 | Percentile for `fmin`, below which the cortex is transparent grey. |
| `max_pct` | 99.5 | Percentile for `fmax`, upper limit of hot colormap. |
| `subjects` | all found | Optional subset of subject IDs to include. |
| `exclude` | none | List of subject IDs to exclude or `{id: reason}` dict. |
| `query` | none | Pandas-style query applied to epochs metadata (e.g. `"acc == 1"`). |
| `width_mm` | 180 | Maximum figure width in mm; the canvas fits the content and may be narrower. |
| `time_locked_to` | none | Caption fact and file name part. |

Outputs go to `source/` under the output root: `source-<figure>_<method>[_<windows>]_vNN.png/.svg`, `_run.json`.


## Microstate spec (`python microstate_plot.py plot <spec.json>`)

Required: `data` (any loader layout, including `<condition>/<group>/<subject>*-ave.fif`), `conditions`, `templates`
(path; `{k}` is replaced, e.g. `…/centers_k{k:02d}.npz`), `k` (integer for `figure: "states"`, list for `"by-K"`).

| Key | Default | Meaning |
|---|---|---|
| `figure` | `"states"` | `"states"`: one K, templates + time panels; `"by-K"`: template rows for several K. |
| `blocks` | `["topo", "butterfly", "ribbon"]` | Any of `topo`, `butterfly`, `gfp`, `ribbon`, with `butterfly` and/or `gfp`; order sets the file name. |
| `window_ms` | `[0, 800]` | Segmented and drawn range (as in the analysis). |
| `min_segment_ms` | 30 | Shorter runs merge into the better-fitting neighbour. |
| `polarity` | `"sensitive"` | `"insensitive"` if the analysis ignored map polarity (pycrostates' default): identity across K uses \|r\|, and maps are shown with a consistent sign (rule MS5). |
| `per_group` | false | One row per condition × group instead of per condition (at most 2 rows without a grid). |
| `grid` | none | Rows × columns of condition keys, e.g. `[["Hmet","Hlit","Hrep"],["Lmet","Llit","Lrep"]]`; required for more than 2 conditions (rule MS9). |
| `hatch` | false | true: hatch samples whose GFP is below the pre-stimulus 95th percentile (rule MS3); needs pre-stimulus samples. |
| `templates_source` | none | Caption only: which analysis made the templates. |
| `identity_threshold` | 0.9 | by-K: signed r at which two templates count as the same map. |
| `groups`, `exclude`, `flat_channels`, `width_mm`/`height_mm` (180 × default by layout, rule MS10: 1 row 62 with maps / 80 without; 2 rows 110 / 140, with both panel types 70 / 90; grid 100), `cmap`, `reference`, `time_locked_to` | | As above; the last two only feed the caption facts. |

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
