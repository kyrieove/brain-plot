# ERP figure rules — v1 (2026-09-25)

The only valid rule list; each rule is stated once. Type: **U** = the user's binding requirement; **M** = methods requirement; **D** = default design choice (a spec field can change it). "Code" = erp_plot.py enforces it or stops; "QA" = the agent checks the rendered figure.

**Scope.** `plot` with `kind: "combo"` (default) follows every rule. `kind: "erp"` and `kind: "topo"` follow the Science rules and those layout/style rules whose elements they draw (K1, K2). `explore` output is not a paper figure: it follows S1, S2, S8, the per-scale part of S5, T6 and E1–E3 only.

## Science

| # | Rule | Type | Enforced |
|---|---|---|---|
| S1 | Averaging only over subjects with identical channels (names, order, positions, head coordinates), digitization, units (V), time grid, baseline, filter and reference flag; no bad channels left marked; no unapplied projectors (files are read with `proj=False`); Evoked files: one `kind="average"` object per condition. EEG potentials only. The loader never re-references, resamples or interpolates. The reference flag does not prove the same reference scheme; the optional `reference` states it for the caption. | M | Code |
| S2 | Each subject's condition average first, then subjects with equal weight. ROI = mean of its channels within each subject. No error band by default (user rule); with spec `error: "sem"` the band is between-subject SEM at each time point, omitted when n < 2, descriptive only. | U/M | Code |
| S3 | Windows are the user's: the figure draws the window given, whatever its origin. `window_source` is optional and only copied into the caption. `windows` gives heuristic candidates only; the user names components and fixes windows. (user 2026-09-26: how a window was chosen is not the figure's concern.) | U | Code |
| S4 | The gray band on the waveforms and the topomap averaging window are the same interval; both the requested window and the actual sample bounds are recorded. | M | Code |
| S5 | Topomaps share one symmetric colour scale around 0 and one set of contour levels within a figure (`explore`: within each scale, see E2); interpolation, extrapolation and one explicit head sphere are fixed and recorded: MNE's default origin, radius = 1.01 × the outermost projected electrode (MNE's own clip radius), so the coloured disc never extends beyond the drawn head. The colour limit covers the interpolated maps, not only the sensor values (both are recorded). | M | Code |
| S6 | No significance marks (v1). Statistics are not asked about; an optional `stats_note` the user writes is copied into the caption verbatim, never derived from the figure. (user 2026-09-26) | U | Code (no such option) |
| S7 | Scalp maps show sensor-level potentials; captions must not claim cortical sources. CSD, source estimates, time–frequency, difference waves, lateralised components: not supported in v1. | M | Code (unsupported keys stop) |
| S8 | Every requested group, condition and line is drawn: at most 7 overlaid lines, one colour each, else the script stops (also in `explore`); `plot` checks the drawn lines and maps against the expected count for its kind (combo: lines = maps; erp: no maps; topo: no lines). ROI channels are unique (repeats would re-weight the ROI). | M | Code |
| S9 | When given, the spec's `claim`, `key_comparison`, `time_locked_to` and `reference` (all optional, caption only, never used for drawing; user 2026-09-26) are copied into the caption facts; omitted ones leave no caption line. `_caption.md` has two parts: `## Whole figure` (facts every panel shares: claim, groups and n, exclusions, trials, time-locking, baseline, filter, reference, windows (and their source, when given), scales, statistics from the author) and `## Panels`, one entry per panel under the letter drawn on it (combo: waveforms a, c, …, maps b, d, …; erp and topo: a, b, …; grid and microstate figures have no letters and are listed by title), with that panel's lines, their n and trials per subject, channels and window source. Facts only, never a finished caption. (User request, 2026-09-26.) | U | Code |
| S10 | A channel that is constant over the whole epoch (peak-to-peak < 1e-6 µV, e.g. all zeros) in any subject × condition stops the script, naming subject, condition and channels — usually an unrecovered bad channel. A reference electrode kept at 0 µV is allowed only by listing it in `flat_channels`; the caption facts then name it. Checked on cached data too. (2026-09-26.) | M | Code |

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
| K1 | `kind: "erp"`: waveforms by channel, not by component. `layout`: `"roi"` (mean of the chosen channels, panels stacked as in combo), `"single"` (one figure per channel; `channels: "all"` = every channel, one file each in one versioned folder), `"grid"` (one figure per facet level, a panel per channel at its grid cell, legend under the grid, no SEM band). Lines/panels follow `overlay` (L3). Gray bands (named, rule L8, in every layout) only for components the user asks for after the windows are confirmed; default none. L5–L10 and T1–T3 apply; one letter per panel inside the canvas (roi/single); panels keep ≥ 13 mm between them. (User rules, 2026-09-25/26.) | U | Code |
| K2 | `kind: "topo"`: maps only; each panel is a block of maps whose rows × columns adapt to line and panel count on the fixed canvas (largest maps; among shapes within 10 % of that size the one with more rows; never an empty row); facet name rotated at the left of its block; the window title once above the first block; one 4-mm colour bar; no legend. (User rule, 2026-09-25.) | U | Code |
| L9 | Display range = the whole epoch (default; not asked in the interview, user 2026-09-26); `xlim_ms` only when the user asks for it. It must include 0 and is never narrowed to hide activity the author has not excluded from analysis. | U | Code |

## Style

| # | Rule | Type | Enforced |
|---|---|---|---|
| T1 | Cross axes: x-axis at 0 µV, y-axis at 0 ms. Each x tick label is measured and placed on the side where the visible lines (the SEM band only when `error: "sem"`) over the label's width leave it closest to the axis without touching; "ms" sits at the right end of the x-axis; the tick step doubles until neighbouring labels keep a 3-pt gap; "µV" at the top of the y-axis; every side of 0 that the y-axis extends to by more than 15 % of its range carries at least one tick (finer step first, else the axis extends to the next tick). Origin is not labelled (the y-axis marks 0 ms). | D | Code |
| T2 | Polarity positive up unless the spec says `negative_up`. | D | Code |
| T3 | Colours of the overlaid variable: groups → first listed group black, then Okabe–Ito (7 lines max); 2 conditions → teal #1b7f79 / red #e0533d; ≥ 3 unordered → Okabe–Ito; ordered levels → viridis steps. `colors` overrides. Two crossed factors in one panel: colour = one factor, line style = the other (`colors` + `linestyles`, e.g. solid = high, dashed = low). | D | Code |
| T4 | Topomap colour map RdBu_r (0 = white). | D | Code |
| T5 | Arial/Helvetica at final size: titles 7 pt, facet names 7.5 pt bold, component labels 6.5 pt, ticks/legend/colour bar/map labels 6 pt, panel letters 8 pt bold; line width 0.9 pt, SEM alpha 0.15; fixed canvas `width_mm` (default 180) × `height_mm`, no tight cropping; output PNG (600 dpi) and SVG with editable text, no PDF (user rule, 2026-09-26: SVG is for adjusting by hand); `explore` also writes PNG + SVG. | U/D | Code |
| T6 | The canvas is fixed (spec `width_mm` × `height_mm`, default 180 × 120 mm) and never derived from the content: panels, heads and gaps are fitted inside it; fonts keep their point sizes. (User rule, 2026-09-25.) | U | Code |
| T7 | Categorical encodings (line colour + line style; states; identity families) are checked for the smallest CIE76 ΔE between any two in normal vision and simulated deuteranopia/protanopia (Machado 2009); all three recorded in `_run.json` (`colour_distinctness`); the same colour with the same line style counts as ΔE 0, the same colour with a different line style is not compared, fewer than two encodings record null; only normal vision warns below 10 (user 2026-09-26: colour-blind values are recorded, not warned). The palette stays the user's choice; the agent reports warnings. | D | Code + QA |

## Explore (overview before windows are chosen)

| # | Rule | Type | Enforced |
|---|---|---|---|
| E1 | Waveforms: one figure per group on the fixed canvas, default 3 × 3 channels F3 Fz F4 / C3 Cz C4 / P3 Pz P4 (`channels` changes it), all conditions overlaid, one shared y-range, no window bands; legend centred under the grid, one row (two rows if more than 4 conditions), read row-wise. (User rule, 2026-09-25.) | U | Code |
| E2 | Topomap table: rows = conditions (+ difference rows if asked), columns = components; windows must lie inside the data. Default one global scale for the condition maps and one for the difference rows; `topo_scale: "component"` = one scale per column (and block), each with a horizontal µV bar under it inside the canvas. Every scale covers its interpolated maps. (User rule, 2026-09-25.) | U | Code |
| E3 | Explore figures are candidates for choosing windows, not paper figures: no `_run.json`, no QA record. | M | Code |

## Output files

| # | Rule | Type | Enforced |
|---|---|---|---|
| O1 | Every output goes to `brain-plot/` next to the data folder: `ERP/`, `topo/`, `ERP_topo/`, `microstate/` (plus `specs/` for the user's specs and `.cache/`); the spec has no output path. (User rule, 2026-09-26.) | U | Code |
| O2 | Nothing is overwritten: a new render of the same figure gets the next version `_vNN`; only after every file of it (figure, caption, run) is written do the previous versions move to that folder's `_history/`, so a failed render leaves them in place. (User rule, 2026-09-26.) | U | Code |
| O3 | File names say what the figure is: kind, component, channels and/or window, comparison (`groups-by-condition` or `conditions-by-group`) or group, version; e.g. `ERP-topo_N400_Pz-CPz_350-500ms_conditions-by-group_v01`. (User rule, 2026-09-26.) | U | Code |

## Microstate figures (`microstate_plot.py`, plan `docs/plan-microstate.md`)

Rules S1 (input contract), S9 (caption structure), S10 (flat channels), T5 (PNG + SVG), T6 (fixed canvas) and O1–O3 apply; the ERP layout rules do not.

| # | Rule | Type | Enforced |
|---|---|---|---|
| MS1 | Draw only: templates are read from the analysis (npz `centers` K × channels, aligned by `ch_names` if stored; without them the columns are assumed to follow the data's channel order, which prints a warning and is stated in the caption facts), never re-fitted; the template file's content digest is recorded; `templates_source` names the analysis. | U | Code |
| MS2 | Each row is the subject-equal grand average of one condition (or condition × group). Every sample gets the template with the highest spatial correlation after average reference and unit norm — signed unless the analysis ignored polarity (`polarity`) — and runs shorter than `min_segment_ms` (default 30) take the better-fitting neighbour; neighbouring runs meet half-way between samples in every drawn element (ribbon, GFP fill, hatch, boundary lines) and in the longest-run times under the maps and in the caption (`labels_ms` in `_run.json` keeps sample centres; `time_semantics` says so); condition labels must be unique and every requested condition (× group) is exactly one row; the method and its parameters must match the analysis and are recorded. | M | Code + interview |
| MS3 | Opt-in (`hatch: true`, default off; user 2026-09-26): samples whose GFP is below the 95th percentile of the same average's pre-stimulus GFP keep their state colour and number but are hatched; no text note on the figure. With `hatch` and no pre-stimulus samples the script stops; without `hatch` nothing needs a baseline. | U | Code |
| MS4 | States are numbered by the median midpoint of their longest runs across rows (reference rule); states that never occur come last. | D | Code |
| MS5 | Colours: the reference 10-colour palette by display number; across-K figures colour by template identity (signed r ≥ `identity_threshold`, default 0.9, with the family's first template). | U | Code |
| MS6 | Layout from `blocks`: framed template maps at the left in 1–3 columns, whichever gives the largest maps (≤ 22 mm) while the time panels keep half the canvas width (state label above in its colour), time panels on the right (`butterfly`: all channels thin gray + GFP; `gfp`: GFP filled with state colours), one row per condition (× group with `per_group`), `ribbon` under the butterfly (it needs `butterfly`); fixed canvas `width_mm` × `height_mm` (default 180 × 110). Across-K: one row per K, no time ranges. | U | Code |
| MS7 | (a) Under each map its longest run per row (`—` if absent), while there are ≤ 4 rows; (b) ribbon segments read `S1`, `S2`, … like the maps, in white on dark/saturated states and black on light ones (relative luminance > 0.3); (c) the GFP trace is labelled "GFP", just above the curve at the latest point where no channel trace crosses the label (fewest crossings plus a white outline if none is clear); (d) panel titles carry the condition name only, never N (n goes in the caption facts). Maps carry no electrode marks. (User rules, 2026-09-26.) | U | Code |
| MS8 | Outputs in `brain-plot/microstate/`, named by content: `topo-butterfly-ribbon_K5_GO-NoGO_vNN`, `…-GFP-…`, `…_by-group`, `topo-by-K_K3-9_vNN`; each with `_caption.md` and `_run.json` (labels in ms, low-GFP fraction, spans, identity families). | U | Code |
| MS9 | Arrangement of the time panels: 1–2 rows are stacked with the maps in a left column; more rows need `grid` (rows × columns of condition keys, each once, e.g. a 2 × 3 design as 2 rows of 3) with at least two columns — the script stops otherwise. A grid with more than one column puts the template maps in one row above it (8 mm above the first panel titles), takes one time panel per condition — `butterfly` or `gfp`, not both — and labels y once per grid row; all three together only when the panels are stacked. (User rule, 2026-09-26: never stack six conditions.)  With `per_group`, more than 2 rows (conditions × groups) are not supported: draw one figure per group. | U | Code |
| MS10 | Every time panel (butterfly and GFP alike) keeps width : height between 1.8 and 3.5; otherwise the script stops and names the `height_mm` range that works. Default canvas 180 × 110 mm (stacked) or 180 × 100 mm (grid). (User rule, 2026-09-26.) | U | Code |

## QA after every `plot` render (agent looks at the PNG)

1. Nothing overlaps: legend vs lines, SEM shading, gray band and its label; tick labels vs lines; titles vs letters.
2. Gray band, topomap window text and caption window agree.
3. combo/topo: no dots or other electrode marks on the maps (rule L11).
4. `open_items` in `_run.json` is empty, or every listed field (marked "to be confirmed" / "not recorded") is reported to the user as open.
5. Colour warnings (T7): report a normal-vision `colour_distinctness` below 10 to the user with the two colours (deutan/protan values are not reported).
6. Readability (report to the user, don't change the figure on your own): the display range (`xlim_ms`) hides part of the baseline interval; or one map dominates the shared scale (rule S5) so the others look near-white — correct, but readers may read it as no activity.
7. `_run.json`: `lines`/`maps` fit the kind (combo: both = expected; erp: maps 0; topo: lines 0); `size_mm` equals the spec canvas; `legend` says where the legend went; then replace its `qa` field with the result ("passed" or the open problems).
