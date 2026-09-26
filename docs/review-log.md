# brain-plot review log

## Round 1 — astra review → fixes (2026-09-25)

Review: `docs/astra-review-2026-09-25.md`. Skill folder renamed `erp-figure/` → `brain-plot/` (skill name `brain-plot`).

| astra item | Fix | Where |
|---|---|---|
| 1 time/channel contract | Every subject × condition checked against the first: channel names/order/positions, n_times/t0, sfreq, baseline, filter, reference flag, EEG-only; marked bad channels stop; non-finite values stop. No re-reference/resample/interpolate. | `erp_plot.py` `contract()`, `load()` |
| 2 cache | Key = loader version + exact file list with size and mtime_ns + conditions + query; cache stores contract, IDs, trial counts together with the arrays. Regression test proves invalidation. | `load()`; test step 5 |
| 3 silent dropping, SEM | Stop if colours < lines; assert lines = maps = expected; no SEM band for n < 2 (caption says so); group colour list has 7 unique colours; first listed group = black. | `plot()` |
| 4 spec/doc drift | Strict spec schema (required/optional keys, component keys, allowed values); unknown keys stop; `query` on `-ave.fif` stops; spec documented in `references/spec.md`; new SKILL.md matches code. | `check_spec()`, `references/spec.md`, `SKILL.md` |
| 5 IDs, exclusions | Subject ID = file name up to first `_`/`-`; exclusions are exact IDs with reasons; unknown exclusion IDs, duplicate IDs, empty groups, mixed root/sub-folder layout stop. Removed "keep groups with n ≥ 10" advice. | `select_files()` |
| 6 window heuristic | `windows` searches inside each component's range, reports "full width at half prominence" and states it is a heuristic; "orthogonal" claim removed; non-overlap rule dropped. Caption records requested window and actual sample bounds. | `windows()`, `caption()` |
| 7 rule conflicts | One versioned rule table (science / layout / style / QA), each rule once, typed U/M/D and marked Code/QA; exemplars.md no longer holds rules. Rule L7 (legend) now states the measured strip, at least the right third. | `references/rules.md`, `research/exemplars.md` |
| 8 topomap comparability | One set of contour levels per figure; extrapolation/interpolation/sphere fixed and recorded. | `TOPO`, `plot()` |
| 9 workflow contract | SKILL.md rewritten: inspect → interview rounds with recommended answers → spec confirmation (re-confirm on scientific change) → plot → QA → report; environment-neutral dependencies; `_run.json` per figure. | `SKILL.md` |
| 10 edge cases | Ticks for any display range (tested −100–400 ms); xlim and windows validated against data with half-sample tolerance; empty/out-of-range windows stop; tick-label side uses the mean ± SEM envelope of all lines. | `cross_axes()`, `plot()` |
| 11 figure size/info | Fixed canvas, no tight bbox (SVG verified 180 mm); window text above each topomap block; −200 ms tick shown; caption facts add time-locking, baseline, exclusion reasons, "white dots are not significance", stats note from the author. | `plot()`, `caption()` |
| 12 exemplars/gallery | Old 200-paper plan and protocol marked archived; exemplars list what was adopted and not; gallery JS newline bug fixed. | `docs/`, `research/` |

Not changed: origin "0" label (collides with baseline traces; exemplars E2/E3 also leave it out; rule T1).
Regression checks: `python brain-plot/test/test_erp_plot.py` → OK (synthetic: 3 conditions, single-subject group, conditions overlay, negative-up, short range, 8 error cases, cache invalidation).

## Round 2 — astra re-review → fixes (2026-09-25)

Review: `docs/astra-review-round2.md` (4 of 12 round-1 items resolved, 8 partly; 6 new items B1–B6).

| astra item | Fix | Where |
|---|---|---|
| B1 input semantics | Files read with `proj=False`; unapplied projectors stop; Evoked must be `kind="average"` with unique comments; contract adds units (V), coordinate frame (head), finite positions, digitization hash. Per-file checks run before the cross-subject comparison so the message names the real cause. | `read_conditions()`, `contract()`, `load()` |
| B2 spec values | ROI channels non-empty and unique; component names unique and file-safe; `claim`, `key_comparison`, `time_locked_to`, `reference`, exclusion reasons must be non-empty strings; windows finite, ordered and inside `xlim_ms`; all components preflighted before drawing. | `check_spec()`, `plot()` |
| B3 file overwrite | Output paths append extensions (`f"{out}.{ext}"`) instead of `with_suffix()`; names with dots are refused. | `plot()` |
| B4 collisions, clipping | Each tick label is measured; its side and offset come from the mean ± SEM envelope over the label's own width; last label right-aligned; right margin 9 → 12 mm; colour-bar ticks 6 pt; rule T5 lists every font size honestly. Visual QA of both real figures passed and is recorded in `_run.json`. | `cross_axes()`, `draw()`, `rules.md` T1/T5 |
| B5 projection, saturation | One explicit head sphere from `fit_sphere_to_headshape` (fallback MNE default), recorded; if interpolated maps exceed the sensor range by > 2 %, the figure is redrawn with the interpolated maximum (N2: sensor 41.3 → 49.6 µV; P3: 21.4 → 25.7 µV). Both values recorded. | `common_sphere()`, `plot()` |
| B6 traceability, numbers | `claim` and `key_comparison` required and repeated in the caption facts; `_run.json` stores input file list (path, size, mtime), full contract incl. channel order, code MD5, rules version, versions, sphere, colour limits and a `qa` field; numerical regression of ROI mean, SEM, n = 1 and window mean via `line_stats()`. | `plot()`, `caption()`, test step 0 |
| A6 window rule wording | S3 now allows localizers on independent data; only the target difference in the displayed data is excluded. | `rules.md` S3 |
| A7 significance exception | Removed; v1 has no significance marks at all. | `rules.md` S6 |
| colour cap | Hard cap of 7 overlaid lines for any colour source. | `plot()`, `spec.md` |

Regression checks: OK (now also duplicate ROI channels, dotted component name, empty reference, window outside xlim, duplicate Evoked comments, unapplied SSP, numeric checks).

## Round 3 — astra final review → fixes (2026-09-25)

Review: `docs/astra-review-round3.md`. B1, B2, B4, A6, A7 resolved; B3, B5, B6 partly; verdict "not yet", 3 must-fix items.

| astra item | Fix | Where |
|---|---|---|
| N2 map window widened to 304–356 ms (27 samples) by the half-sample tolerance; original analysis uses 306–354 ms (25) | Sample selection uses a 1 µs float tolerance only (`sample_mask`); half-sample tolerance kept only for range checks. N2 now 306–354 ms, P3 522–622 ms. Regression asserts 25 samples 306–354 ms on a float32 grid. | `sample_mask()`, `plot()`, test 0b |
| Case collisions (`N2`/`n2`, `1`/`"1"`) overwrite files on Windows | Component names must be strings, unique ignoring case. Test added. | `check_spec()` |
| Colour limit only widened when interpolation exceeded sensors by > 2 % | Widened whenever the interpolated maximum exceeds it; final assertion that the limit covers the maps. | `plot()` |
| (can wait) 7 unordered conditions had 6 default colours | Condition palette = Okabe–Ito + black (7). | `colors_for()` |

Regression checks: OK. Real figures re-rendered; visual QA passed and recorded in `_run.json`.
Not done (astra "can wait"): rule-file hash in `_run.json`; panel-letter alignment and head-outline weight.

## After round 3 — found by the user (2026-09-25)

| Problem | Fix | Where |
|---|---|---|
| P3 Go panel: legend (lower right) sat on the gray window band; missed by my QA and by astra | Gray band now covers the data range only (not the full axes height); the band plus room for its label is an obstacle in legend placement, so the legend goes to the freer corner or into y-range extended past the data. Rule L7 and QA item 1 updated. | `draw()`, `place_legend()`, `rules.md` |
| (user) Band must stay full height as before; legend at one position across component figures | Band restored to full height. New spec key `legend` (`right` default, `upper_left`, `outside`); the corner is chosen once for the whole set (worst figure decides); a band reaching into the legend strip stops the script. User chose `right`. | `choose_corner()`, `legend_room()`, `draw()`, rules L7 |
| (user) Legend labels without n; topomap labels in black | Names only in legend and facet labels (n stays in caption facts); topomap labels plain black. | rules L10, L4 |

## Test on a second dataset (metaphor production, 60 subjects, 2026-09-25)

| Found | Fix | Where |
|---|---|---|
| Groups stored in trial metadata (WM), not folders | Spec `group_by`: groups from a between-subject metadata column (must be constant per file). | `groups_from_metadata()` |
| 2 × 3 conditions in one panel unreadable with 6 colours | Spec `linestyles`: colour = task, line style = SND. | `line_styles()`, rule T3 |
| Legend touched the x-axis tick labels | The x-axis ± one text line is an obstacle; extension re-measured until the legend fits. | `legend_room()`, `draw()` |
| (user) No error band by default | Spec `error` (`none` default, `sem`). | rule S2 |
| (user) Topomap colour extended beyond the head outline: sphere fitted to electrodes raised the origin 4.4 cm | MNE default origin, radius grown until every electrode projects inside the outline. | `common_sphere()`, rule S5 |
| (user) Waveforms took too much width, heads too small with many lines | Map block ~24 mm per head column (max 55 %); 6 lines → 3 × 2 heads. | `canvas()`, rule L4 |
| Reference in my draft spec was wrong (average) | Corrected from the preprocessing script to linked mastoids; lesson: never fill `reference` from memory. | spec |
| (user) Legend should not crowd the first panel | Default `legend: "side"`: own column right of the waveforms, vertically centred on the stacked panels; inside-panel modes kept as options. | `canvas()`, `draw()`, rule L7 |
| Narrower waveforms made "800" and "1000 ms" collide | "ms" moved to the end of the x-axis; tick labels centred; step doubles only if labels still collide. Map column 24 → 19 mm per head (heads are height-limited). | `cross_axes()`, `canvas()`, rules T1/L4 |
| (user) Legend belongs to the waveform column: right side, vertically in the middle, not beyond the panels' right edge | `side` now places the legend in the gap between the middle two waveform panels, right-aligned to their edge; fewest columns that fit the gap; single panel falls back to `right`. Extra legend column removed. | `draw()`, rule L7 |
| (user) Waveforms and maps too close | 8-mm gap column between waveforms and maps. | `canvas()`, rule L4 |
| (user) Negative y half had no tick (N400: range −1.9…5.3, step 2) | `nice_ticks()`: every side of 0 that the axis extends to by > 15 % gets a tick (finer step first, else extend to the next tick); regression case added. | `nice_ticks()`, `data_ylim()`, rule T1 |
| (user) A late window's label collides with the right-aligned legend; then use the centre of the four panels | Legend spot chosen by collision check against every text, label, tick label, waveform area and head: gap right-aligned first, else the centre where the four middle panels meet; fewest columns first, spots before extra columns. LPC now uses the centre. | `draw()`, rule L7 |
| (user) Not the centre of the four panels: widen the waveform-map gap for the legend instead | Fallback (2) now redraws with the waveform-map gap widened to the legend's width; legend in that gap, one column, centred between the middle panels. Centre spot removed. | `draw()`, `plot()`, rule L7 |

## Round 4 — astra consistency/redundancy review → fixes (2026-09-25)

Review: `docs/astra-review-round4.md`. User chose to delete the unrequested legend modes.

| astra item | Fix |
|---|---|
| 1 redraw loop could save an unchecked figure | One loop updates colour limit and gap together, stops when nothing changes, and refuses to save unless the colour limit covers the maps and the legend is placed. |
| 2 optional legend modes bypassed checks | `upper_left` and `outside` deleted with the `legend` spec key; placement is automatic: between panels → widened gap; single panel → inside right (stops if a band blocks it). |
| 3 sphere loop useless, colour 1 % past outline | Radius computed once = 1.01 × outermost projected electrode (MNE's clip rule); verified clip scale = 1.0. |
| 4 "8 mm" gap was 12.3 mm | All columns in mm with `wspace=0`; gap measured 8.0 mm; colour bar 4 mm + 4-mm spacer. |
| 5 T1 exceptions | "µV" always at the display top; tick labels must keep 3 pt unless only one tick remains. |
| 6 caption said "confirmed" next to "to be confirmed" | "Claim:" only; `open_items` in `_run.json` and an "OPEN" line in caption facts list fields marked to be confirmed / not recorded; QA item 4 checks them. |
| 7 stale text | exemplars.md lists only design sources; rules T1/L4/L7/S5 reworded to match code. |
| 8 input contract wording | spec.md: subject ID up to `_`/`-`/`.`; component names unique ignoring case; `group_by` groups alphabetical unless `groups` given (code now sorts). |
| 9 dead code | Removed `need_components`, unused `idx`/`col`/`info`, the `n` element of lines, `legend_width_mm` (one legend measurement), `choose_corner` (→ `single_panel_corner`). |
| 10 tests | Fixture uses the default legend; asserts `legend` placement and `open_items`; single-panel path and its failure; removed modes rejected. |

Regression checks: OK. Six figures redrawn; legend: N400/P200/N300/N2/P3 between panels, LPC widened gap (27.4 mm).

## Agent reproducibility tests (2026-09-25)

| Test | Result |
|---|---|
| Codex, given the confirmed spec | Pixel-identical PNG (0 of 11.0 M pixels differ); identical run record. First attempt stopped correctly on a sandbox error (`~/.mne` unreadable); rerun with `_MNE_FAKE_HOME_DIR`. |
| Codex, full interview from raw data, Claude answering as the user | 4 rounds + confirmation. Same data-determining fields (groups, overlay, conditions and order, Pz/CPz, 350–500 ms, −200…1000 ms, polarity, width, line styles) → same numbers (window samples, colour limit, IDs, legend, gap, 12 lines = 12 maps). Differences only in wording (labels, claim, stats note, source texts) and colour assignment (metaphor blue vs vermillion). Codex recommended metaphor-only lines and Fz/Cz/Pz; the user's answers corrected both. |
| SKILL gap found | The interview never asked about trial selection. Added to round 2 in SKILL.md. |
| Antigravity (Gemini 3.8 Flash High), given the confirmed spec — run after the user approved in chat | Pixel-identical PNG (0 differing pixels); identical run record; spec differs only in `out`; QA 5/5 passed with open items listed; inputs unchanged; 169 s, 199 k tokens. |

## Single-type and exploratory figures (2026-09-25, previews for the user to choose)

| Change | Where |
|---|---|
| `kind`: `combo` (default), `erp` (waveforms only), `topo` (maps only; preview layouts `topo_layout: rows | grid`) — restores the user's original requirement | `draw()`, `draw_topo()`, `plot()` |
| `explore` command: core channels (Fz, Cz, Pz, Oz), other channels in pages (`electrode_grouping: regions | blocks`), topography table conditions × components with optional within-subject difference rows (`differences`), `topo_scale: component | global`; no window bands | `explore()` and helpers |
| (user) Fixed canvas: size only from `width_mm` × `height_mm` (default 180 × 120), content fitted inside | `canvas_size()`, rule T6 |
| (user) Core channels as 2 × 2, not a column; pages must be 4, 6, 8 or 9 channels (full 2×2, 2×3, 2×4, 3×3); global colour scale looked best | Core grid near-square; `page_sizes()` (fewest pages, most 9s) + `bisect_pages()` (recursive split along the wider scalp axis) give compact full pages (here 9, 8, 6, 9, 9, 9, 9); `electrode_grouping` option removed; `topo_scale` default `global`. | `electrode_pages()`, `explore()` |

## Explore v3 (2026-09-25, user feedback)
- Waveforms: one 3 × 3 figure at F3 Fz F4 / C3 Cz C4 / P3 Pz P4 (spec key `channels`, rows of names). Core page and
  4/6/8/9 paging removed (`page_sizes`, `bisect_pages`, `electrode_pages`, `scalp_xy`, `core_channels` deleted).
- Legend: no separate right-hand column; centred under the grid, one row (two rows if more than 4 conditions),
  read row-wise.
- Topomap table unchanged (user: looks good).

## Single-type figures chosen (2026-09-25)
- `kind: "erp"`: default 180 × 120 mm (89 mm variant dropped). `kind: "topo"`: block layout only; `topo_layout` key
  and the one-row "grid" variant removed. Tried centring maps + labels as one compact unit; user rejected it (too cramped), reverted to
  the spread layout. Documented in spec.md.
- Topo-only shape adapts (`topo_block`): rows × columns per panel chosen for the largest maps on the fixed canvas,
  preferring more rows within 10 % (fills the canvas), never an empty row. E.g. 180 × 120 mm: 3 lines × 2 panels
  → 1 × 3, 6 × 2 → 2 × 3, 7 × 2 → 2 × 4, 4 × 1 → 2 × 2. Regression-tested.
- Topo-only colour bar: widths were ratios (bar ≈ 8 mm); now real mm, 4 mm per rule L4 (user: halve it).
- Topo-only window title once above the first block (per-block titles collided with map names at 4 panels).

## astra round 5 (2026-09-25) — fixed 2026-09-26
Review of explore, `kind`, `topo_block`: `docs/astra-review-round5.md`, 10 findings (2 × P1, 7 × P2, 1 × P3).

| # | Fix | Where |
|---|---|---|
| 1 | explore preflight: `xlim_ms` and every component window inside the data (finite, non-empty sample mask) | `explore()`, `check_explore()` |
| 2 | explore stops on > 7 conditions or fewer colours than conditions (zip no longer drops lines) | `explore()` |
| 3 | `kind: "topo"` skips waveform-legend sizing and the single-panel corner check | `plot()` |
| 4 | topomap table: each scale (global / per column, main / difference) widened to its interpolated maps, one redraw | `topo_table()` |
| 5 | scale floor 1e-6 µV: identical conditions give an all-zero difference map without crashing | `topo_table()` |
| 6 | waveform letter at a fixed 15 pt above the axes (was 1.12 × panel height → off-canvas with one panel); panels keep ≥ 13 mm between them (was hspace 0.55 → facet/title overlap at 7 panels); figures with ≤ 3 panels unchanged | `letter()`, `canvas()` |
| 7 | per-column bars placed in mm (1.5 mm below the maps, 1.2 mm high), 6 mm bottom reserve, `µV` on the last tick | `topo_table()` |
| 8 | caption facts by kind: erp has no topography line, topo has no lines/gray band/polarity | `caption()` |
| 9 | rules.md: scope paragraph; L1–L7 scoped by kind; new K1 (erp), K2 (topo), E1–E3 (explore); QA scoped; SKILL.md: explore has no `_run.json` | docs |
| 10 | removed `head = 17.0`, unused `meta`; draw_topo docstring and spec.md `kind` describe the adaptive block | code, spec.md |

Tests: new checks 4b, 8, 9 in `test_erp_plot.py` (captions by kind, one-panel letter inside canvas, 7 panels without
text overlap, explore preflight, zero difference maps in both scale modes inside a 180-mm-high canvas); the three layout
checks were confirmed to fail on the old code. Re-rendered N400 main, supplementary, both previews and explore v2.

## User rules (2026-09-26)
- L11: topomaps carry no electrode marks (the ROI mask dots are gone in combo and topo; explore never had them).
  MNE takes the contour width from `mask_params["markeredgewidth"]` even without a mask, so `markeredgewidth=0.3`
  stays to keep the 0.15-pt contours. Caption facts and QA item 3 updated; regression check: no markers on any axes.
- T5: figures are written as PNG (600 dpi) + SVG (editable text), no PDF — `plot` and `explore`. Old PDFs in the
  metaphor output folders are stale (not deleted).

## kind "erp" by channel; localizer dropped (2026-09-26)
- User: the skill only draws. The planned `localize` (collapsed localizer, bootstrap, component table, data_log) is
  dropped — windows and channels come from the analysis. `windows` and `explore` stay. Codex's unfinished localizer is
  kept in branch `codex/step3-localize-erp` and `git stash`, not merged.
- `kind: "erp"` rebuilt (rule K1): `channels` + `layout` = `roi` (mean), `single` (one figure per channel, `"all"` →
  one versioned folder), `grid` (one figure per facet level, reuses `wave_grid`). Components are optional gray bands
  `{name, tmin_ms, tmax_ms, window_source}`; default none. `draw()` and `legend_room()` take any number of bands;
  `_run.json` written by `write_run()` (records channels and band sample bounds). Tests 4b, 4c, 8.
- Note: the erp grid and the explore overview share the name `ERP-grid-3x3_conditions_<group>`, so they version
  together (a paper grid after an explore overview becomes v02).

## Microstate branch (2026-09-26, plan `docs/plan-microstate.md`)
- `microstate_plot.py`: `figure: "states"` (blocks topo / butterfly / gfp / ribbon) and `"by-K"`; rules MS1–MS8.
  Reproduces the v10 K = 5 reference (boundaries per condition, e.g. S1 GO 80–252 ms, NoGO 74–246 ms; reference
  median 77–251). Improvements over the reference: per-condition ranges, `S#` on the ribbon, GFP labelled, low-GFP
  hatch. By-K numbering pools the two conditions, so a few identity colours differ from the reference strip.
- Loader: `<condition>/<group>/<subject>*-ave.fif` layout (`split_layout`, `uid`), used by both branches.
- `test/test_microstate.py`: planted windows recovered to the sample, 12-ms blip merged, polarity, name alignment,
  versioning, errors. Mutations (no merge, polarity ignored) fail the tests.
- Metaphor GN specs: `gn_manuscript/01-evokeds_grand_averages/brain-plot/specs/microstate_*.json`.
- 2026-09-26, user: template maps looked too small next to the butterfly plot. The map column now takes 1–3 columns,
  whichever gives the largest maps (≤ 22 mm) while the time panels keep half the canvas (K = 5: 10 → 22 mm, two
  columns). User: "还不错".

- 2026-09-26, user on the 6-condition metaphor test: the figure was 180 × 230 mm (my suggestion, panels ~130 × 27 mm,
  5 : 1) and stacked six conditions, which the user never asked for. Fixed: `grid` (MS9, rows × columns of conditions;
  more than 2 rows without it stops), template row above multi-column grids, panel shape check 1.8–3.5 : 1 (MS10)
  that stops with the working `height_mm` range. The grid default height is 100 mm, not the 130 mm I proposed: 130 gives
  1.3 : 1 panels for a 2 × 3 grid (valid range 84–110 mm at 180 mm width).

- 2026-09-26, user on the 2 × 3 grid: titles show the condition only (N removed; the user had said so for ERP, rule L10,
  and it applies here too: MS7d); 8 mm between the template row and the panels; a multi-column grid takes either the
  butterfly or the GFP panel, not both (user: "三者再放一起就有点挤"). GFP-panel hatch now fills under the curve only
  (the full-height hatch cut the y axis into dashes).

## Round 6 fixes (2026-09-26, `docs/astra-review-round6.md`, 15 findings, all fixed)
| # | Fix | Test |
|---|---|---|
| 1 | split layout stops on two files with one subject ID in a condition folder | microstate test 4 |
| 2 | one window check (`window_mask`) for states and by-K | by-K 0–1000 ms on 800-ms data stops |
| 3 | templates must be finite and non-flat | zero templates stop |
| 4 | MS10 checks every time panel; height range must fit all | 254 × 143 slide now stops, 120 passes |
| 5 | ERP grid bands carry the component name (L8) | two "N4" labels on a 1 × 2 grid |
| 6 | `ribbon` requires `butterfly` | check() refuses gfp + ribbon |
| 7 | runs meet half-way between samples in ribbon, GFP fill and hatch (`edges`, `under`) | edge values asserted |
| 8 | `versioned()` no longer moves; `archive(out)` after every file is written | invalid colour after the version was chosen leaves v01 (fails on the old code) |
| 9 | > 2 conditions need a grid with ≥ 2 columns | check() refuses a 3 × 1 grid |
| 10 | O1 no longer lists localizer/data_log | — |
| 11 | description says "draws only" and names the excluded neighbours | evals/cases.md 3–5, 8 |
| 12 | SKILL.md routes to the two scripts in its first lines | evals 1, 2 |
| 13 | agent-level eval cases `brain-plot/evals/cases.md` (8 trigger, 4 behaviour; manual, holdout marked) | — |
| 14 | SKILL.md states the side effects (cache, output folder, `_history/`, dependencies) | — |
| 15 | `windows` refuses components without ROI channels with a clear message | erp test |
The GN slide spec (254 × 143 mm, butterfly + GFP) now fails MS10; its height was set to 110 mm (valid 79–114 at 254 mm width).

## Absorbed from cogsci-visualization / nature-figure (2026-09-26)
- Compared by agy (both skills vs rules.md); 5 of its 12 suggestions were already in place (SVG text, Agg + close,
  interpolation-covering colour limit, mm layout, render-time checks).
- T7 (from the cogsci-visualization colour-blind checklist): ΔE between categorical colours under normal vision and
  simulated deuteranopia/protanopia, recorded and warned. Finding: in the reference microstate palette S4 cyan
  `#0099B4` and S5 purple `#925E9F` are ΔE 7.5 for deuteranopes (red/green S2/S3 stay 18.5); palette unchanged,
  user's choice.
- MS7b (from nature-figure `is_dark()`): ribbon labels black on light states (green, apricot, mustard), white otherwise.
- Not taken yet: panel-structured caption skeleton, flat-channel guard, reviewer-risk QA list (offered to the user).

## Palette decision (2026-09-26)
- User: colour blindness is not a concern; keep the Lancet palette (MS5). Checked 9 established 10-colour palettes
  (ggsci Lancet/NPG/AAAS, Paul Tol muted, Tableau 10 / colorblind, seaborn deep/colorblind, tab10): under normal
  vision Lancet has the largest smallest ΔE (28.3; tab10 27.7, Tableau 10 25.9, Tol muted 22.8, NPG 20.9).
- T7 changed: normal, deutan and protan values are all still recorded in `_run.json`; only normal vision warns below 10.
  Test: the cyan/purple pair (deutan 7.5) prints no warning; two near-identical reds do.

## Offered items 3–5 (2026-09-26, user: "继续做 3、4、5")
| # | Change | Test |
|---|---|---|
| 3 | `_caption.md` in two parts (rule S9): `## Whole figure` (shared facts; filter/baseline/reference stated once, identical in every panel by S1) and `## Panels` under the letters drawn (combo a/c… waveforms, b/d… maps; erp and topo a, b, …; grid and microstate by title, no letters), each with its lines' n and trials per subject, channels, window source | ERP tests 1, 4b, 4c; microstate test 1 |
| 4 | Rule S10: a channel constant over the epoch (ptp < 1e-6 µV) in any subject × condition stops the script with subject, condition and channels; spec `flat_channels` allows a reference electrode kept at 0 µV (named in the caption); checked on cached data too; for plot, explore and microstate | ERP test 4a (mutation: disabled check fails the test) |
| 5 | QA item 6 "reviewer risks" (a–i): circular window source, claim vs statistics, trial imbalance > 1.5 ×, n < 10 or 2 × n imbalance, high-pass > 0.1 Hz with late components, baseline hidden, one map dominating the shared scale, source language, microstate > 50 % hatched / K choice unstated. Reported to the user, never fixed silently. QA items renumbered 1–7 (were 1, 2, 3, 4, 6, 5). | — (agent QA) |

## First local run of S9/S10/QA 6 (2026-09-26, metaphor N400 v02, GN K5 v04)
- Both suites OK on Windows; no flat-channel stop on either data set.
- Microstate NoGO: the "GFP" label (anchored at the last sample) sat on a channel trace. Now placed by
  `gfp_label_spot()` at the latest sample where no trace crosses its box (MS7c); test measures the drawn label against
  every trace (fails with the old placement).
- Captions: the window source was repeated in every panel entry → stated once under Whole figure; filter printed as
  0.10000000149 (float32) → 6 significant digits.
- Reviewer risks reported to the user (not changed): N400 window chosen post hoc from the grand average (a); claim says
  the SND effect "differs in direction" while no simple contrast survived FDR (b); K5 `templates_source` does not say
  how K was chosen (i). Also noted by the local agent: Repetition maps with red extremes at the left temporal edge
  (FT9/T7), possibly a noisy channel.
- User on the reviewer risks: "这些都不是画图该考虑的问题，是写文章考虑的问题". QA item 6 reduced to the two
  figure-reading checks (baseline hidden by the display range, one map dominating the shared scale); window source,
  claim vs statistics, trial and sample balance, filter, source language and K choice are not the figure's concern
  (S3/S9 still record what the user states).

## Optional caption fields (2026-09-26, local session, commit 29b50c7)
- `claim`, `key_comparison`, `time_locked_to`, `reference` are optional in the ERP spec (they only feed the caption);
  omitted → no caption line. CLAUDE.md: user-facing text in Chinese. Rules S1/S9 wording synced in the cloud session.
- Interview (user, after a neutral review): `claim` and `key_comparison` are design inputs and are always asked (claim →
  figure type, components, channels; key comparison → `overlay` and colour/line-style pairing); they stay optional in
  the spec. `time_locked_to` and `reference` only feed the caption: read from scripts/files, else left out, never
  asked. Display range = whole epoch, not asked (L9).

## Caption-only and analysis-policing requirements removed (2026-09-26, local session, commits eb42f85, f058705)
- User question: "统计结果对画图有任何影响吗？为什么一定要问" → audit of every interview question and every script stop
  for things that do not change the drawing. Removed or made optional (user: "全改"):
  `window_source` (optional, caption only); exclusion reasons (`exclude` may be a plain ID list); `templates_source`
  (optional); interview no longer asks statistics (`stats_note` stays optional, written by the user), the figure's
  role, the journal (asks width instead) or a window's source; Inspect no longer reads hypotheses/statistical results;
  S3/E3 no longer police how a window was chosen; QA 4 no longer checks `stats_note`; unknown caption facts are left
  out of the spec instead of "to be confirmed".
- Microstate hatching (MS3) is opt-in (`hatch: true`, default off); without it no pre-stimulus baseline is needed
  (the script used to stop). User looked at K5 v06 without hatching: "可以，不用加斜线".
- Kept (they change what is drawn): `claim`/`key_comparison` questions, trial selection (`query`), data-contract stops
  (S1, S10, bad channels, units, projectors, positions), layout stops, spec-syntax stops, the spec confirmation step.
- Metaphor `n400_spec.json` (outside the repo): `time_locked_to` and `claim` deleted. Re-renders: N400 v04 (pixel-
  identical to v03, `open_items` empty) and GN K5 v06 (only change: NoGO hatch at 0–16 ms gone); both QA passed.
- CLAUDE.md: every new figure is sent into the chat (SendUserFile, render), not left in a folder.
- Cloud branch `claude/bold-gates-u9nx46` fast-forwarded to main (f058705) by the local agent.

## Style is not asked (2026-09-26, local session)
- User: polarity and colours are house style, "不用问 设置默认的就行 除非用户要求改". Interview round 4 removed; style
  follows the defaults in rules.md unless the user asks. Line pairing (colour = task, line style = level) stays part
  of the key comparison.

## Sharing: README, demo data, portability (2026-09-26, cloud session)
- README.md (English) + README.zh-CN.md; example figures in `docs/images/` from synthetic data
  (`examples/make_demo_data.py`, specs in `examples/specs/`); `requirements.txt`. Stale `test/fig_main.json` (had the
  removed `out` key) deleted; SKILL.md and spec.md point to `examples/specs/`.
- Relative `data`/`templates` in a spec file are resolved from the spec's folder (`read_spec`); absolute paths unchanged.
- Portability: tests failed on matplotlib 3.11 (closed pyplot figures lose their Agg canvas; test helper `renderer()`
  re-attaches one) and on systems without Arial (grid "ms" label ~0.3 mm past the right edge; grid right margin 4 → 6 mm).
  Both suites now pass on matplotlib 3.10 and 3.11 with DejaVu Sans.
- Microstate map labels printed "-0" for a run starting at the first sample; now integers.
- Seen, not changed: with `hatch: true` the ribbon's S# labels are hard to read over the hatching.
