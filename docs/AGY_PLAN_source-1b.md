# AGY PLAN source-1b: review fixes for PLAN source-1

Same boundaries and allowed files as `C:\dev\brain-plot\docs\AGY_PLAN_source-1.md`. Keep the signature of
`source_plot.load_and_compute` unchanged (another agent calls it right now). Reuse existing functions; do not copy logic.
Progress: append to `C:\dev\brain-plot\AGY_PROGRESS_source.md`, first line `[░░░░░] 0/5 fixes start · HH:MM`.

## Fixes (N = 5)
1. **Localizer (`erp_plot.windows`, region path)**
   a. The extreme must be a real local peak: if it lies on the first or last sample of the search range (the wave
      is still rising/falling there), print `  no peak inside <tmin>–<tmax> ms (extreme at the range edge)` for that
      component and leave it out of `WINDOWS_JSON`. Same if `find_peaks` on the chosen channel finds no peak of that
      polarity at that sample.
   b. Compute the FWHP with `peak_widths` on the chosen channel's **whole** waveform (all samples of `ms`, peak index
      mapped to the full axis), not on the cropped search range, so the window is not clipped by the search range.
   c. Tests in `test_erp_plot.py`: one case where the extreme sits on the range edge → the component is reported as
      "no peak" and absent from WINDOWS_JSON; one case where the FWHP extends beyond the search range and is not
      clipped.
2. **Rendering (`BrainRenderer`)**: `offscreen=True` and `show=False` (no windows on the desktop); before each
   `add_data`, remove the previous data layer (`remove_data()` or the MNE 1.13 equivalent) so layers never stack;
   hard threshold like the reference figure: `add_data(..., thresh=fmin, transparent=False)` so everything below
   fmin shows the grey cortex and everything at/above fmin is coloured from dark red upward.
3. **No `_caption.md`** for source figures (user): remove the writer and any leftover code; update
   `references/source.md` / `spec.md` / `rules.md` if they mention it.
4. **Outlier record in `_run.json`**: while accumulating, keep per subject × condition the 99th percentile over
   vertices of that subject's stc averaged over each shown window/time bin... simpler: of the stc averaged over the
   whole 0…1000 ms. Store it as `subject_p99` (subject → condition → value) and list in `outlier_subjects` every
   subject × condition whose value is > 3 × the median of that condition. `references/source.md` QA list: "check
   `outlier_subjects`; tell the user, never drop a subject yourself". Cache these numbers with the grand average.
5. Run all five suites (each `OK`), then re-run the real timeline spec
   `D:\1-python_datasets\metaphor production\derivatives\brain_plot_preprocessed_epochs_verb\specs\source_timeline.json`
   (the per-subject cache is reused; the grand-average cache may be rebuilt because of step 4).

## Reply (≤ 10 lines)
Tests; new PNG path; `outlier_subjects` content; anything not done.
