# AGY PLAN source-2b: localizer sign rule, final windows figure, clean-up

Same boundaries and allowed files as `C:\dev\brain-plot\docs\AGY_PLAN_source-1.md`.
Progress: append to `C:\dev\brain-plot\AGY_PROGRESS_source.md`, first line `[░░░░] 0/4 plan 2b start · HH:MM`.
`S` = `D:\1-python_datasets\metaphor production\derivatives\brain_plot_preprocessed_epochs_verb\specs\`.

Review finding: the localizer reported "LPC (positive)" with a peak of −0.88 µV at F4 and an empty ROI — the whole
500–900 ms range is negative, so there is no positivity; the rule agreed with the user is "in the literature but not
in the waveform → leave it out and tell the user".

## Steps (N = 4)
1. `erp_plot.windows`, region path: a positive component whose peak value is ≤ 0 µV (negative: ≥ 0 µV) is not found:
   print `  no <polarity> peak inside <tmin>–<tmax> ms (most <polarity> value <v> µV has the wrong sign)` and leave it
   out of WINDOWS_JSON. Test in `test_erp_plot.py`. Re-run the localizer on `S\source_localizer.json` and overwrite
   `S\source_localizer_output.txt` (it is your own output from plan 2).
2. `S\source_windows.json`: windows = the new WINDOWS_JSON entries (name, tmin_ms, tmax_ms; expect P200 and N400
   only). Render it (`source_plot.py plot`). Keep the earlier 3-window figure where it is (different file name).
3. Clean-up of your own code (no behaviour change): delete dead code, unused imports/variables, leftover
   try/except fallbacks, duplicated logic that an `erp_plot` helper already does; `references/source.md` and
   `docs/rules.md` must describe what the code does now (rank per subject, render_check, outlier_subjects, no caption,
   hard threshold). All five suites `OK`.
4. Re-render both real specs (`source_timeline.json`, `source_windows.json`) after the clean-up and confirm by
   opening both PNGs that every cell shows a brain.

## Reply (≤ 8 lines)
Localizer lines for each component; PNG paths; suites; lines removed in the clean-up (rough count).
