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

## User-experience review (2026-09-26, external, on c5c033b) — fixes
| # | Finding (confirmed by reproduction) | Fix | Test |
|---|---|---|---|
| 1 | microstate: two conditions with one label merged silently | labels must be unique (`check`); drawn rows = requested rows | check list; plot |
| 2 | templates without `ch_names` only count-checked | warning + caption line + `templates_meta.channel_order` | microstate 1, 2 |
| 4 | three boundary definitions (ribbon half-way, spans end-of-sample, dotted lines at run start) | spans and dotted lines use `edges()`; `time_semantics` in `_run.json` | 0b; dotted lines vs `labels_ms` |
| 6 | `inspect` crashed on `<condition>/<group>/` data; evoked trials from the first file only | `discover()` covers every layout; trials from every file; `header_from`; clear error on empty folders | erp 0d |
| 7 | `sub-01_…` and `sub-02_…` both parsed as `sub` | BIDS `sub-<label>` kept | erp 0d |
| 8 | `per_group` > 2 rows pointed to `grid`, which `per_group` refuses | message: one figure per group | microstate 3 |
| 9 | identical colours → ΔE Infinity, no warning; `Infinity` in `_run.json` | colour + line style compared; same/same = 0 and warned; < 2 encodings → null; `allow_nan=False` | erp 0d, strict JSON |
| 10 | provenance: no template content digest; microstate code digest missed `erp_plot.py` | `templates_meta.md5`; `code_md5` for both scripts | microstate 1 |
| doc | SKILL explore paragraph still required a window source | removed | — |
| — | MNE 1.13 deprecates the montage name `standard_1020` (gone in 1.14) | tests and demo use `colin27_1020` when available | both suites |
- #5 (ordering formula ≠ rule text) not changed yet: checked locally first, since renumbering would change existing
  figures. Not taken (user decisions or out of scope): CVD palette, panel letters on microstate figures, submission
  export, journal questions, upstream label import, doctor/CI.
- #5 checked locally (2026-09-26): code order = "median of midpoints" order on all 9 real specs (GN K5, metaphor
  K3–K8 incl. grids). Code kept; MS4 text now states the code's formula. GN K5 v07 accepted by the user (boundaries
  1 ms earlier from #4; numbering and colours unchanged).

## Independent audit + fixes (2026-09-26, cloud session; user: "三处都按你的建议，确认存在的问题也都修正")
Audit method: all code read; hypotheses tested one by one; 100 ERP and 55 microstate configurations rendered on a
realistic synthetic set (64 ch incl. TP9/TP10, 7 conditions, 3 groups) and checked geometrically, flagged ones confirmed
by eye. Refuted: bads in Epochs slip through (they stop), electrodes outside the head outline with TP9/TP10 (none).
Before → after: ERP 89 clean / 11 with problems / 0 stopped → 94 clean / 0 / 6 stopped (the unreadable ones, with a
height that works); microstate 23 clean / 2 false positives / 30 stopped → 39 clean / 0 / 16 stopped (MS9 by design,
MS10 where no height fits at 180 mm).
| # | Problem | Fix | Test |
|---|---|---|---|
| QA | layout checked only by eye | `layout_issues(fig)` in both scripts: overlapping texts, text/legend on a curve, text off the canvas; printed and written to `_run.json`; texts with a white halo/box count as legible | test_layout (every figure clean), erp 8 |
| 1 | 5–7 stacked ERP panels 3–6 mm tall, y ticks piled up, "N400" on the "400" tick, no stop | panels ≥ 15 mm (stacked and grid cells) else stop naming `height_mm` (and the other `overlay`); y ticks keep 9 pt (fewer on short panels); x tick labels stay inside the panel | erp 0, 8; test_layout |
| — | y tick labels / "µV" on baseline lines (noisy data) | y labels drawn as annotations; "µV" switches side when lines pass; y-axis reaches ≥ 10 pt above the x-axis; last resort white box (SVG text stays editable) | erp 0 (10 pt), test_layout (no box needed) |
| 2 | polarity-insensitive templates: sign-flipped map = new identity colour | identity by |r| when `polarity: insensitive`; maps shown with the family's sign (by-K) or the data's sign (states); `shown_sign`; caption line | microstate 0e, 3; test_layout |
| 3 | different figures (group/condition subsets, other grid channels) shared one name → archived as versions | `_grp-`, `_cond-`, `_query-<hash>` only for subsets; grid names list channels; LOADER_VERSION 4 records all groups/conditions (one re-read per dataset) | erp 4d; replay: 3 figures → 3 names |
| 4 | erp grid: band name under the channel name | channel name raised (pad 11), top margin 14 mm with bands | test_layout |
| 5 | one-condition microstate figure always stopped at the default 110 mm | default height table by layout (1 row 62/80, 2 rows 110/140, both panels 70/90, grid 100), measured over K 2–10 | microstate 3, test_layout |
| — | MS10 message printed min–max although valid heights have holes (map column switches 1–3 columns): the suggested middle could fail | message lists every range ("60–63 or 73–78") | microstate 3 |
| — | small maps: range labels wider than the map column overlapped | ranges left to the caption when they do not fit (`ranges_under_maps`) | test_layout |
| 6 | 2 × 2 map blocks: label on the nose below; cache grew without bound; doc drift | map rows ≥ 3 mm apart; `.cache` keeps the 6 most recently used; SKILL/docstrings MS1–MS10, BIDS IDs | erp 5, test_layout |
| env | no quick way to see if the interpreter can run the scripts | `check_env.py` (standard library only): versions, fonts, OK / what to install | manual (MNE hidden → PROBLEMS, exit 1) |
Mutation check: undoing any one of 7 fixes makes a suite fail. Suites: test_erp_plot, test_microstate, test_layout, all
OK on matplotlib 3.10.9 and 3.11.2 (Linux, DejaVu Sans).
- Local run (Windows, Arial): test_layout failed — the K = 8 range-omission case used short names ("NoGo 133–199",
  12.7 mm in Arial, 15.0 in DejaVu), which fit under the maps in Arial. Test now uses long names (17.5 / 21.3 mm) so the
  omission holds in any font; the figure itself was clean in both.

## 2026-09-27 — rules split (user: rules.md too long; new modules paused)
- `brain-plot/references/rules.md` (20.7 KB, 45 rules, mostly enforced by code) moved to `docs/rules.md` as the
  developer reference; rule text and IDs unchanged, the QA section now points to the module files.
- New agent-facing module files: `references/erp.md` (commands, explore, interview rounds, never-ask list, stops,
  QA 1–7) and `references/microstate.md` (read-first list, what to ask, grid/hatch/per_group limits, stops, QA).
- `SKILL.md` cut to a router + the common workflow (8.4 → 4.2 KB). Agent load per figure: ~37 KB → ~18 KB (ERP) /
  ~15 KB (microstate).
- Paths updated in the script docstrings, `_run.json` `rules` field (`docs/rules.md v1`), README (en + zh-CN),
  HANDOFF, research/exemplars.md. `spec.md` unchanged. Three suites OK in the cloud (matplotlib 3.10, DejaVu Sans).
- To check: one fresh-session interview run with the split skill (Antigravity prompt in the chat).
- Local check (Antigravity, 2026-09-27): e49a76e fast-forwarded, three suites OK on Windows; dry-run interviews for
  eval cases 9 and 10 graded pass. Two caveats: nothing was drawn, so the PNG / `qa` items of case 9 were not
  exercised; the demo data has no analysis config, yet the dry run filled `polarity: "insensitive"` as if read from
  one. Fix: `microstate.md` now says to ask for `polarity` / `min_segment_ms` / `window_ms` when no file states them.
- User merged `daf4662` into local `main` and pushed (via Antigravity). New modules stay paused; optional next step:
  a full draw + QA run with the split skill on real data (GN or metaphor).
- 2026-09-29: the two one-off agent test plans (`agent-test-PLAN.md`, `agent-test-interview-PLAN.md`) moved from the
  repo root to `docs/archive/` with an "archived, outdated paths" note; nothing referenced them.

## 2026-09-29 — full draw + QA run with the split skill (cloud, synthetic demo data)
- Cloud container: `pip install -r requirements.txt "matplotlib<3.11"`, `MPLBACKEND=Agg`; three suites OK before and after.
  Followed `SKILL.md` + `references/microstate.md` on `examples/specs/microstate_k4.json` (K = 4, standard / target,
  butterfly + ribbon): PNG opened, QA 1–6 walked through, `layout_issues` and `open_items` empty.
- Found: the Standard panel's "GFP" label (right-aligned at the last sample, 4.6 mm box, ends at 800 ms) sat on the
  dotted boundary line at 769 ms (S2 ends 768, S3 starts 770), 31 ms from the end, cutting the "G"; `layout_issues` and
  the placement (MS7c) only looked at channel traces. Fix (5ad8668): `gfp_label_spot(…, bounds)` treats dotted boundary
  lines inside the label box as obstacles.
- Code review of 5ad8668 (`/code-review`, 6 findings), follow-up fixes:
  | # | Finding | Action |
  |---|---|---|
  | 1 | a line counted as one channel sample, drowned by dozens of trace hits on real data | placement key is `(lines, trace samples)`: line-free first; a spot free of both is still preferred (test 0f: dense traces vs a line) |
  | 2 | 1 mm gap only on the right of the label | gap on both sides (`GFP_LABEL_GAP_MM`); test 0f and `gfp_label_clear` check 1 mm on the drawn figure |
  | 3 | test did not cover the `plot_states` call (dropping `bounds` left all suites OK) | test 2b: window 0–512 ms, `min_segment_ms` 10, the 498 ms boundary sits in the label box; the label must move left of it. Mutations: no `bounds` from `plot_states`, line counted as one sample, gap on one side — each fails a test |
  | 4 | `layout_issues` ignores 2-point lines (vertical dotted lines) | not taken: adding a new check for every text × vertical line would flag gray band edges and zero lines in ERP figures too, and the user has not asked for more self-checks; the placement fix and the drawn-figure test cover this case |
  | 5 | MS7b wording (threshold scales with the number of columns; span excludes one sample) and the boundary position in this log (767, "33 ms") | rules.md MS7b reworded; numbers here corrected |
  | 6 | per-sample Python loop over `bounds` | one `np.searchsorted` per call |
  A figure whose "GFP" label never met a boundary line is unchanged; a re-render of GN K5 may move the label if it did.
  When no spot is free of both lines and traces (short windows), the label keeps off the lines and traces may cross it
  (white outline).
- Doc drift fixed: MS7b did not say that short ribbon segments carry no label (code did); MS7c text now names the
  boundary lines.
- Seen, not a defect (unchanged): map blocks fill column-wise (S1, S2 left column; S3, S4 right), so a 2 × 2 block reads
  S1 S3 / S2 S4 row-wise; the user accepted the K5 layout on 2026-09-26.

## 2026-09-29 (later) — "GFP" text label dropped (user decision)
- User: "GFP 这个不要了" → chosen scope: butterfly panels no longer carry a "GFP" text label. Supersedes MS7c and the
  two commits above (5ad8668, ebe00cd): `gfp_label_spot`, `GFP_LABEL_MM`, `GFP_LABEL_GAP_MM`, the annotation and the
  `patheffects` import are deleted; tests 0f, 2b and `gfp_label_clear` are removed. In the table above, rows 1, 2, 3 and 6
  describe code that no longer exists; rows 4 (not taken) and 5 (MS7b wording, corrected numbers) stand.
- Replaced by: rule MS7c now says there is no label; the microstate caption facts state "thin lines = every channel of the
  grand average, thick line = GFP" whenever a butterfly panel is drawn (the figure itself no longer says it); test 1 asserts
  that no axes text contains "GFP" and that the caption line exists (mutation: the previous code fails it). The GFP-only
  panel keeps its "GFP" title and "GFP (µV)" axis label (they name a panel, not a trace).
- Suites OK (matplotlib 3.10.9, DejaVu Sans); demo K4 re-rendered (v05): `layout_issues` and `open_items` empty.
- Not redone: `docs/images/example-microstate-butterfly.png` (README; real metaphor data, drawn with the old code) still
  shows "GFP" labels — re-render it locally with the current code before the README is next updated.

## 2026-09-29 (later) — ERP combo: maps inside the waveforms (`map_placement: "inset"`, rules L12, L13)
User reference: a published figure with the topomaps placed inside the waveform panels, near the component, each map
group with its own colour bar. Built and shown to the user in four rounds; what the user said each time is why the
final rules read as they do.
| User feedback | Change |
|---|---|
| "一个 combo 一张图，上下叠放不好看，ERP 太宽" (then, after a per-panel-figure version) "单个图不行，必须多张图组合到一起才美观，单张、两张都太长或太宽；试试 2 × 3、2 × 2" | one figure with the panels in a grid (`grid`, rows × columns of condition keys, like microstate MS9; automatic 1 × n up to 3, 2 × 2 for 4, two rows up to 8), one legend under the grid, letters in reading order, one y-range / map size / colour scale for all panels; default height gives 1.45 : 1 panels, taller when the maps need it |
| "colorbar 是跟随地形图的，你仔细看示例图" | the colour bar belongs to each map block (right of the maps, per panel), not a column at the figure's edge |
| "1 2 都有重叠现象 … 不是我提出一次改一次，应该写入规则，一次画好，要有自检功能" | the gray window band (full height) is now a hard obstacle in the search, not a soft cost; rule L13 lists what a map block must clear (band, curves incl. SEM, both axis lines, every text, each other, the panel edge); `inset_audit` measures every part against all of them on the drawn panel and the script stops on a clash; parts checked and clashes go to `_run.json`; when no shape or size fits it stops naming the fixes |
| "colorbar 要更窄一些，变为原来的一半" | 1.8 → 0.9 mm (L13); test asserts 0.9 mm |
- Search: a raster of free places per panel (curve envelope + clearance, x tick columns where a label sits past lines on
  both sides, axes and labels, band); block shapes tried in order of map size (one row, then stacked), first one that
  fits every panel with the y-range grown at most 2.2 × the data range wins; nearest to the window's middle, on the side
  the component points to.
- Found on the way, fixed: the facet name sat at 6 % of the panel height below it and left the canvas when a panel was
  tall (now capped at 2.5 mm; panels < 42 mm unchanged); `draw()` and `canvas()` are unchanged for the side layout.
- Tests (`test_layout.py`, realistic 64-channel data): 2 × 2, 2 × 3, panels = 3 groups, negative up + SEM, one panel,
  3 lines per panel — each must pass `layout_issues`, the script's audit and `inset_clear()`, a separate re-measurement
  in the test (maps/bar/window text inside a panel and off band, curves, SEM bands, axes, texts, each other), 0.9-mm bars,
  caption letters in grid order; stops: grid with a wrong key set, grid without inset, 3 lines on an 89-mm canvas, long
  line names in narrow panels. Mutations: band not an obstacle → the script's audit stops the figure; band not an
  obstacle and audit blind → the test's own check fails; bar 1.8 mm → test fails.
- Known limit: panels of ~46 mm (2 × 3 at 180 mm) hold one or two lines' maps; three lines make the default height 173 mm
  — use 3 rows × 2 columns instead. Not asked, not done: side layout untouched; README figures not redrawn.
- Round 5 (user: "第二个不行，只有两个的时候不能竖着排列，另外两个看着还不错"; then "放不下就自适应调整子图之间的间距"): the
  2 × 3 figure had stacked its two maps in a column to fit beside the gray band. Now the maps of a panel stand in one row
  (up to 4 lines; two are never stacked), and when the block does not fit the layout adapts: colour bar right at the
  default spacing → the same with tighter spacing between panels (9/13 → 6.5/12 mm, margin 12 → 8 mm) → colour bar under the
  maps (horizontal) at each spacing → stop. `_run.json` `inset_layout` records the choice. Findings on the way: the
  script's own audit stopped a first version of the bar-under-maps layout ("the unit overlaps the colour bar", the "µV" text
  box against the tick label's box) — moved 1.2 mm, then it passed. Three lines per panel do not fit the 2 × 3 panels
  (the script says so; use 3 rows × 2 columns). Tests: 2 × 2 (bar right), 2 × 3 (bar under), 3 panels in a row (tighter
  spacing), 3 × 2 with 3 lines, one panel; maps of a panel in one row (independent check); mutations: two maps allowed to
  stack, no tighter spacing tier — both fail a test.

## 2026-09-29 (end of day) — inset layout on real data (metaphor N400), merged to main
- Local agent (Antigravity) ran it in a git worktree of the branch (its `C:\dev\brain-plot` had uncommitted work of the
  user, which it correctly refused to touch; worktree `C:\dev\brain-plot-inset` at `4811d80`, removed afterwards).
  Suites OK on Windows. Figure A (2 × 3, groups as lines): drawn, bar under the maps, side 7.0 mm, audit 30 / 0 clashes,
  14 s. Figure B (panels = groups, six lines): stopped as rule L13 requires, because six maps do not fit one row with
  18-mm labels ("Repetition (high)"; panels 74–79 mm; height alone cannot help, width would need ≈ 212 mm).
- Found while preparing the prompt: an assertion of test_layout held only with DejaVu (where the switch to the tighter
  spacing happens depends on text widths); now scans widths, verified in DejaVu and in Liberation Sans (Arial metrics);
  HANDOFF says how to mimic the Windows font in the cloud.
- User looked at figure A and found problems (to be listed on the next session). No scheduled reminder (offered a daily
  routine; user: "不用发给我，你知道就行", then "只需要这一次就够了"): the next session opens with one reminder, said once
  (HANDOFF, first "Next" bullet, deleted after it is said).
  Candidate change for B (not done): wrap long map labels onto two lines.

## 2026-09-30 — inset layout revised on the metaphor N400 figure (user review of figure A)
- User's points on v01: colour bar belongs on the right, not under the maps; no window text ("350–500 ms") in this
  layout; maps too small against the waveforms; line colours not an SCI palette. Reference: the user's Go/NoGo figure
  (maps inside the waveform panels, no gray band, one bar beside the maps).
- Done (v02–v17, each shown to the user): one vertical colour bar for the whole figure at its right edge (scale is
  shared anyway), ~11 mm from the panels; window text removed (caption keeps it); gray band removed and the component
  name moved into the title (user: "干脆就不要mask了"), so the band no longer blocks the maps; maps placed at the lower
  right; planner now tries each map size from the largest down and grows the y-range per size (before, it grew the
  y-range only at the largest size and fell to 7 mm); constants: map ≤ 27 % of panel width, growth ≤ 2 × data range,
  square panels (aspect 1.0), map labels 5 pt. Tried and rejected on the way: maps over the gray band (user: overlap is
  the old mistake), parula map colours (user: map colours were fine), growth 2.4 / aspect 1.05 (maps too big, ERP
  squashed), growth 1.4–1.6 (maps back at 7 mm).
- ERP line colours: Lancet (ggsci) in order for any line count, groups and conditions alike (was: first group black +
  Okabe–Ito, two conditions teal/red). Rule T3 rewritten.
- test_layout: inset expectations updated (colour bar 'none' inside panels, one shared 2-mm bar, parts = maps only,
  3 lines in 2 × 3 panels now fit instead of stopping, the 'tighter spacing must be hit' check dropped). Suites:
  test_erp_plot OK, test_layout OK, test_microstate OK (mnedev, Arial).

## 2026-09-30 (later) — second axis style `axes: "box"` (left + bottom axes)
- User asked for a classic left/bottom axis style next to the cross axes (reference: the Go/NoGo figure). Planned by
  Claude (PLAN in the session scratchpad), implemented by agy (Gemini 3.8 Flash High, ~20 min): `box_axes()` (outward
  ticks, labels outside, `Time (ms)` / `Amplitude (µV)`, thin 0-µV line, dotted 0-ms line), room for outside labels in
  `canvas()` and `inset_geometry()`, inset planner without the cross-axis label bands, spec key + validation, tests.
  Explore overview stays cross. Default is cross; cross output unchanged.
- Claude's review of agy's renders found two defects, fixed by Claude: (1) no `0` tick on the y-axis (`nice_ticks`
  leaves 0 out because cross axes label the origin) — box mode now adds it; (2) side combo: the legend between the
  panels sat on the `800`/`1000` tick labels — `obstacles_of` now uses the tight box (tick labels, titles) of panels
  that carry an x title, so the clash is seen and the legend moves to the widened gap (+10 mm in box mode, `1000`
  pokes into it). Suites OK (erp_plot, layout, microstate). Renders: inset v19, side combo v09 (specs `*_box.json`).
- Then (user: every ERP figure needs the box style): `wave_grid` (kind `erp` layout `grid`, explore overview) got it too —
  wider left margin and gaps, axis titles on the outer panels only; `axes` accepted in explore specs. New test cases
  (erp grid 3 × 3 box, explore box); suites OK. Real data: `specs/erp_grid_3x3_box.json` → ERP grid v01 (HWM, LWM).

## 2026-09-30 (end) — cleanup of today's orphans (ponytail review)
- Removed what the inset revision left dead: the in-panel colour-bar variants (5 constants, right/below branches,
  one-value loops), the window-text height, the gray-band obstacle parameter, the constant `prefer_top` branch and
  unused window arguments; `lay` is now the map shape, `tw` the widest label. `box_axes` no longer re-sets spine
  visibility (STYLE does it); cross and box share `x_ticks()`. `_run.json` `inset_layout.colour_bar` = `"figure right"`.
- Check: six synthetic renders (side / inset / grid × cross / box) pixel-identical before and after; suites OK.
  erp_plot.py −49 lines net.

## 2026-10-01 — `source` module (branch `source`, not merged)
- User (2026-09-30 night): Claude leads (plan + review), agy / codex implement; all 59 subjects (sub27 excluded);
  layout after Tian (Neurobiology of Language, Fig. 2B) and her metaphor study (Fig. 2); no caption file; one colour
  bar per window block (`figure: "windows"`) / one per figure (`figure: "timeline"`); noise cov and baseline
  −200…0 ms (user choice 3b); hard display threshold P90–P99.5, `hot` map.
- Method: fsaverage template forward (ico-5, 5120 BEM), average-reference projection, shrunk noise cov, dSPM
  λ² = 1/9, loose 0.2, depth 0.8, magnitude; per-subject stc averaged with equal weight (running sum); caches:
  per-subject evoked + cov (npz, small) and the grand average (≈ 60 MB). 59 subjects ≈ 4 min.
- Independent check (codex, `research/source/verify.md`): three dSPM numbers recomputed with plain MNE agree with the
  module to < 0.00001 %. It also found sub33's `Llit` 20× the median → cause: rank-deficient epochs (sub21 58,
  sub33 54, sub35 59, sub42 58 of 63) whitened at full rank. Fix: `mne.compute_rank` per subject passed to the
  covariance and the inverse (test added). Review also caught: blank brains after the first map (fixed, plus a
  `render_check` stop), a soft alpha ramp instead of the hard threshold, windows on the desktop (offscreen now).
- Localizer (`erp_plot.py windows`, components with `region` + `polarity`; regions from `research/source/
  survey-metaphor-erp.md`, Li et al. 2022 sites for N400): collapsed average of all subjects and conditions; peak =
  real local extremum of that polarity (not on the search-range edge), window = FWHP on the whole waveform.
  Results: P200 152–272 ms (F4, 182 ms, +0.50 µV — weak), N400 402–528 ms (Cz, 428 ms, −5.38 µV).
- Mistakes corrected by the user: (1) N1/N400 were taken over from old specs without a user decision or literature
  — components now come from literature + waveform. (2) A "peak must be > 0 µV" rule was added and reverted: polarity
  is the direction of the deflection, not the absolute sign. (3) LPC → checked as SN (`specs/sn_check.txt`): a
  centro-parietal negativity from ≈ 400 ms to the epoch end (2000 ms), not separated from the N400, not frontal →
  not the literature's SN; no late window drawn until the user decides.
- agy's 5-h quota ran out mid-task; codex (`--add-dir` data outputs, `~/.mne`, `~/mne_data`) finished plan 2c.
- Plan 3 (user: "figure too big, text too small, proportions off — a major problem"; reference figure with wide
  gaps): brains no longer stretched to 180 mm — 16 mm per hemisphere, canvas = content width (`width_mm` is a
  maximum, brains shrink to ≥ 12 mm), gaps L–R 3 mm / blocks 6 mm / rows 3 mm, text 8 pt (labels, titles) and 7 pt
  (L/R, ticks); timeline drawn through the windows code path with one colour scale per time column (user: one global
  scale left most maps grey); size self-check in `layout_issues`. Done by codex (agy quota out). −101 lines net.
  Figures: windows v02 (105 × 113 mm), timeline v06 (180 × 216 mm). Late window: dropped (user: "不用管了").
  Merged into `main` 2026-10-01 (user).

## 2026-10-01 — source fixes (astra findings 1, 3, 6, 8, 9)
- Real post-decimation sfreq, no crop, out-of-range windows stop, forward keyed by geometry + src/BEM identity (no sibling reuse), hard-threshold LUT, unique window names (source + TFR). Card, review and acceptance: `docs/orch/2026-10-01-source-fixes/card.md`.
- 2026-10-01 — cache fingerprints + figure identity (astra findings 2, 16): TFR/source caches keyed on input file stamps; TFR/source/explore names carry subset, window ranges, custom channels. `docs/orch/2026-10-01-cache-fingerprint/card.md`.
- 2026-10-01 — TFR fixes (astra 4, 5, 7, 10, 11): shared S1 contract check for ERP/TFR/source (also on cache hits), no skipping unreadable files, real-wavelet edge zone, logratio only, grid/ROI/window checks. `docs/orch/2026-10-01-tfr-fixes/card.md`.
- 2026-10-01 — display fixes (astra 12, 14, 15 + TFR parts of 16, 17): prominence-based localizer ROI, ITC trial floor and bias in caption, topomap limits cover interpolation (ITC linear), TFR window ranges in names. Codex quota out: reviewed by Claude. `docs/orch/2026-10-01-display-fixes/card.md`.
- 2026-10-01 — provenance + docs (astra 13, 17, 18, 19, small parts of 20): source run method facts and provenance, microstate nave, inset caption without gray band, mne >= 1.7 + pyvista in check_env, fsaverage not hard-coded, rule scope/exceptions, shared cache-dir pruning. All 20 astra findings handled. `docs/orch/2026-10-01-provenance-docs/card.md`.
- 2026-10-01 — zcode review (A1 eval case 8 vs description + TFR/source trigger cases, A3 examples path through the install link) and OCR low finding (assert -> ep.die). A2 (session evals not run) open. `docs/orch/2026-10-01-zcode-fixes/card.md`.
