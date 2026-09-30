# PLAN source-3: size and text balance; per-column colour scales in the timeline

Same boundaries and allowed files as `C:\dev\brain-plot\docs\AGY_PLAN_source-1.md` (python, data, output folder,
"reuse, don't copy", foreground only). Progress: append to `C:\dev\brain-plot\AGY_PROGRESS_source.md`, first line
`[░░░░] 0/4 plan 3 start · HH:MM`.

User verdict on `source-windows_dSPM_P200-N400_lock-verbonset_v01.png` and `source-timeline_dSPM_lock-verbonset_v05.png`:
"the figure is too big, the text too small, the proportions are off — a major problem". Cause: `plot()` stretches the
brains to fill `width_mm` (default 180): brains are ~23 mm (windows) / ~17 mm (timeline) wide next to 7-pt labels
and 6-pt L/R and ticks. User also wants the timeline with **one colour scale per time column** (with one global scale
most maps are grey).

## Steps (N = 4)
1. Sizes (both figures): each hemisphere image **16 mm wide** (`BRAIN_MM = 16.0`, height from the image's aspect
   ratio — never stretch or squash), gap between L and R **3 mm**, between blocks **6 mm**, between rows **3 mm** (user,
with a reference figure: brains need clear space between them, ≈ 20 % of a brain's width). Canvas width =
   content width (label column + blocks + right margin 4 mm); `width_mm` in the spec is a maximum: if the content is
   wider, shrink the brains to fit (never below 12 mm → otherwise `ep.die` naming the fix: fewer windows/times per
   block row). Height = content height (`height_mm` removed from the spec keys unless it is needed elsewhere).
   Text: condition labels 8 pt, block titles 8 pt bold ("P200 (152–272 ms)", "100 ms"), "L"/"R" 7 pt, colour-bar tick
   labels 7 pt, colour-bar title ("dSPM") 7 pt; colour bar 2 mm tall, as wide as its block's two brains.
2. Timeline = the windows layout: build one window per time point (`±half_width_ms`, name "<t> ms") and draw it with
   the same code path as `figure: "windows"` — one colour scale and one colour bar **per column (block)**; at most 4
   blocks per block row (the 8 default times → 2 block rows, colour bars under each block). Delete the separate
   timeline layout code that this replaces (no duplicated layout logic).
3. Self-check (added to the layout issues in `_run.json`, test in `test_source.py`): every brain image drawn 12–20 mm
   wide with its original aspect ratio (±2 %); all text ≥ 7 pt. `references/source.md` QA and `docs/rules.md` (SRC
   rules) updated with these sizes. All five suites `OK`.
4. Re-render `S\source_windows.json` and `S\source_timeline.json`
   (`S` = `D:\1-python_datasets\metaphor production\derivatives\brain_plot_preprocessed_epochs_verb\specs\`); remove
   `height_mm`/`width_mm` from those specs if they set them. Open both PNGs and confirm every cell shows a brain.

## Reply (≤ 8 lines)
Canvas sizes (mm) of both figures; PNG paths; suites; lines of layout code removed.
