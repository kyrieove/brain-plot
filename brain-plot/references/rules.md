# ERP figure rules — v1 (2026-09-25)

The only valid rule list; each rule is stated once. Type: **U** = the user's binding requirement; **M** = methods requirement; **D** = default design choice (a spec field can change it). "Code" = erp_plot.py enforces it or stops; "QA" = the agent checks the rendered figure.

**Scope.** `plot` with `kind: "combo"` (default) follows every rule. `kind: "erp"` and `kind: "topo"` follow the Science rules and those layout/style rules whose elements they draw (K1, K2). `explore` output is not a paper figure: it follows S1, S2, S8, the per-scale part of S5, T6 and E1–E3 only.

## Science

| # | Rule | Type | Enforced |
|---|---|---|---|
| S1 | Averaging only over subjects with identical channels (names, order, positions, head coordinates), digitization, units (V), time grid, baseline, filter and reference flag; no bad channels left marked; no unapplied projectors (files are read with `proj=False`); Evoked files: one `kind="average"` object per condition. EEG potentials only. The loader never re-references, resamples or interpolates. The reference flag does not prove the same reference scheme; `reference` states it. | M | Code |
| S2 | Each subject's condition average first, then subjects with equal weight. ROI = mean of its channels within each subject. No error band by default (user rule); with spec `error: "sem"` the band is between-subject SEM at each time point, omitted when n < 2, descriptive only. | U/M | Code |
| S3 | A window's source must be stated: a priori, a localizer that does not use the target contrast in the data being shown or tested, or independent data. Never choose a window from the target difference in the displayed data. `windows` gives heuristic candidates only; the user names components and fixes windows. | M | Code (window_source required) + interview |
| S4 | The gray band on the waveforms and the topomap averaging window are the same interval; both the requested window and the actual sample bounds are recorded. | M | Code |
| S5 | Topomaps share one symmetric colour scale around 0 and one set of contour levels within a figure (`explore`: within each scale, see E2); interpolation, extrapolation and one explicit head sphere are fixed and recorded: MNE's default origin, radius = 1.01 × the outermost projected electrode (MNE's own clip radius), so the coloured disc never extends beyond the drawn head. The colour limit covers the interpolated maps, not only the sensor values (both are recorded). | M | Code |
| S6 | No significance marks (v1). Statistical statements in the caption come from the user (`stats_note`), never from the figure's appearance. | U | Code (no such option) + interview |
| S7 | Scalp maps show sensor-level potentials; captions must not claim cortical sources. CSD, source estimates, time–frequency, difference waves, lateralised components: not supported in v1. | M | Code (unsupported keys stop) |
| S8 | Every requested group, condition and line is drawn: at most 7 overlaid lines, one colour each, else the script stops (also in `explore`); `plot` checks the drawn lines and maps against the expected count for its kind (combo: lines = maps; erp: no maps; topo: no lines). ROI channels are unique (repeats would re-weight the ROI). | M | Code |
| S9 | The spec records what the figure is for (`claim`, `key_comparison`) as confirmed with the user; the caption facts repeat them. | U | Code (required) + interview |

## Content and layout

| # | Rule | Type | Enforced |
|---|---|---|---|
| L1 | One figure per component (e.g. N2, P3) (`plot`, every kind). | U | Code |
| L2 | combo: one topomap per waveform line (e.g. group × condition), same subjects and condition as the line. | U | Code |
| L3 | combo, erp: waveform panels stacked vertically, one per level of the facet variable (usually condition); the overlaid variable (usually group) varies within a panel. Which variable is overlaid is a spec decision (`overlay`). | U | Code |
| L4 | combo: each panel's topomaps sit to its right, same row, in a near-square grid (4 → 2 × 2, 6 → 3 × 2), labelled in plain black text; the component window is written above them. Widths are set in mm: an 8-mm gap after the waveform column (widened by rule L7 when the legend needs it), ~19 mm per head column for the maps (at most 55 % of the remaining width), then a 4-mm spacer and a 4-mm colour bar, one for the figure. | U | Code |
| L5 | Electrode (ROI) names directly above each waveform panel. | U | Code |
| L6 | Facet names (condition or group) directly below their panel. | U | Code |
| L7 | combo, erp: legend once per figure, never on data (topo: no legend). Two or more waveform panels: (1) in the gap between the middle two panels, vertically centred, right-aligned to the panels' right edge, with the fewest columns whose height fits that gap; (2) if it would touch anything there (every text, label, tick label, component label, waveform area and topomap head is checked; e.g. a late window's label), the figure is redrawn with the waveform-map gap widened to the legend's width and the legend sits in that gap, one column, vertically centred between the middle panels. One panel: inside it, upper or lower right (the side the visible lines leave freer across the set, the y-range grows on that side if needed); the script stops if a gray band reaches into that strip. `_run.json` records where it went. (User rules, 2026-09-25.) | U | Code |
| L11 | Topomaps carry no electrode marks (no sensor dots, no ROI/mask dots), in every kind and in `explore`. (User rule, 2026-09-26.) | U | Code |
| L10 | Legend and facet labels carry names only (e.g. TD, ADHD), never n or other statistics; n goes in the caption facts. | U | Code |
| L8 | Component name on the gray band. Shared y-range within a figure; 0 µV always visible. | D | Code |
| K1 | `kind: "erp"`: waveforms by channel, not by component. `layout`: `"roi"` (mean of the chosen channels, panels stacked as in combo), `"single"` (one figure per channel; `channels: "all"` = every channel, one file each in one versioned folder), `"grid"` (one figure per facet level, a panel per channel at its grid cell, legend under the grid, no SEM band). Lines/panels follow `overlay` (L3). Gray bands only for components the user asks for after the windows are confirmed; default none. L5–L10 and T1–T3 apply; one letter per panel inside the canvas (roi/single); panels keep ≥ 13 mm between them. (User rules, 2026-09-25/26.) | U | Code |
| K2 | `kind: "topo"`: maps only; each panel is a block of maps whose rows × columns adapt to line and panel count on the fixed canvas (largest maps; among shapes within 10 % of that size the one with more rows; never an empty row); facet name rotated at the left of its block; the window title once above the first block; one 4-mm colour bar; no legend. (User rule, 2026-09-25.) | U | Code |
| L9 | Display range = the analysis range (default the whole epoch); it must include 0. Not narrowed to hide activity the author has not excluded from analysis. | U | Code + interview |

## Style

| # | Rule | Type | Enforced |
|---|---|---|---|
| T1 | Cross axes: x-axis at 0 µV, y-axis at 0 ms. Each x tick label is measured and placed on the side where the visible lines (the SEM band only when `error: "sem"`) over the label's width leave it closest to the axis without touching; "ms" sits at the right end of the x-axis; the tick step doubles until neighbouring labels keep a 3-pt gap; "µV" at the top of the y-axis; every side of 0 that the y-axis extends to by more than 15 % of its range carries at least one tick (finer step first, else the axis extends to the next tick). Origin is not labelled (the y-axis marks 0 ms). | D | Code |
| T2 | Polarity positive up unless the spec says `negative_up`. | D | Code |
| T3 | Colours of the overlaid variable: groups → first listed group black, then Okabe–Ito (7 lines max); 2 conditions → teal #1b7f79 / red #e0533d; ≥ 3 unordered → Okabe–Ito; ordered levels → viridis steps. `colors` overrides. Two crossed factors in one panel: colour = one factor, line style = the other (`colors` + `linestyles`, e.g. solid = high, dashed = low). | D | Code |
| T4 | Topomap colour map RdBu_r (0 = white). | D | Code |
| T5 | Arial/Helvetica at final size: titles 7 pt, facet names 7.5 pt bold, component labels 6.5 pt, ticks/legend/colour bar/map labels 6 pt, panel letters 8 pt bold; line width 0.9 pt, SEM alpha 0.15; fixed canvas `width_mm` (default 180) × `height_mm`, no tight cropping; output PNG (600 dpi) and SVG with editable text, no PDF (user rule, 2026-09-26: SVG is for adjusting by hand); `explore` also writes PNG + SVG. | U/D | Code |
| T6 | The canvas is fixed (spec `width_mm` × `height_mm`, default 180 × 120 mm) and never derived from the content: panels, heads and gaps are fitted inside it; fonts keep their point sizes. (User rule, 2026-09-25.) | U | Code |

## Explore (overview before windows are chosen)

| # | Rule | Type | Enforced |
|---|---|---|---|
| E1 | Waveforms: one figure per group on the fixed canvas, default 3 × 3 channels F3 Fz F4 / C3 Cz C4 / P3 Pz P4 (`channels` changes it), all conditions overlaid, one shared y-range, no window bands; legend centred under the grid, one row (two rows if more than 4 conditions), read row-wise. (User rule, 2026-09-25.) | U | Code |
| E2 | Topomap table: rows = conditions (+ difference rows if asked), columns = components; windows must lie inside the data. Default one global scale for the condition maps and one for the difference rows; `topo_scale: "component"` = one scale per column (and block), each with a horizontal µV bar under it inside the canvas. Every scale covers its interpolated maps. (User rule, 2026-09-25.) | U | Code |
| E3 | Explore figures are candidates for choosing windows, not paper figures: no `_run.json`, no QA record; a window read off them still needs its source stated in the `plot` spec (S3). | M | Interview |

## Output files

| # | Rule | Type | Enforced |
|---|---|---|---|
| O1 | Every output goes to `brain-plot/` next to the data folder: `ERP/`, `topo/`, `ERP_topo/` (and `localizer/`, `specs/`, `data_log.md` when used); the spec has no output path. (User rule, 2026-09-26.) | U | Code |
| O2 | Nothing is overwritten: a new render of the same figure gets the next version `_vNN`; every file of the previous versions (figure, caption, run) moves to that folder's `_history/`. (User rule, 2026-09-26.) | U | Code |
| O3 | File names say what the figure is: kind, component, channels and/or window, comparison (`groups-by-condition` or `conditions-by-group`) or group, version; e.g. `ERP-topo_N400_Pz-CPz_350-500ms_conditions-by-group_v01`. (User rule, 2026-09-26.) | U | Code |

## QA after every `plot` render (agent looks at the PNG)

1. Nothing overlaps: legend vs lines, SEM shading, gray band and its label; tick labels vs lines; titles vs letters.
2. Gray band, topomap window text and caption window agree.
3. combo/topo: no dots or other electrode marks on the maps (rule L11).
4. `open_items` in `_run.json` is empty, or every listed field (marked "to be confirmed" / "not recorded") is reported to the user as open; `stats_note` matches what the user said.
5. `_run.json`: `lines`/`maps` fit the kind (combo: both = expected; erp: maps 0; topo: lines 0); `size_mm` equals the spec canvas; `legend` says where the legend went; then replace its `qa` field with the result ("passed" or the open problems).
