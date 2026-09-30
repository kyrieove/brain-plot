# AGY PLAN source-1c: rank-deficient subjects + a cache bug (from the independent check)

Same boundaries and allowed files as `C:\dev\brain-plot\docs\AGY_PLAN_source-1.md`.
Progress: append to `C:\dev\brain-plot\AGY_PROGRESS_source.md`, first line `[░░░] 0/3 rank fix start · HH:MM`.

Finding (codex, `C:\dev\brain-plot\research\source\verify.md`; Claude confirmed): sub33's epochs have rank 54 of 63
(`mne.compute_rank(epochs, tol=1e-6, tol_kind="relative")`; sub1, sub10: 63) — channels were interpolated / components
removed upstream. The module passes no rank, so the noise covariance's near-zero directions are whitened as if they
were real channels: sub33's `Llit` dSPM is 20× the median and dominates the grand average. Other subjects may be
rank-deficient too.

## Steps (N = 3)
1. In `source_plot.py`, per subject after the average-reference projection: `rank = mne.compute_rank(ep_sub,
   tol=1e-6, tol_kind="relative")`; pass it to `mne.compute_covariance(..., rank=rank)` and to
   `make_inverse_operator(..., rank=rank)`; store the rank in the per-subject cache (older cache files without it must
   be recomputed — include a cache version in the parameter hash) and report `rank` per subject in `_run.json`.
   Also fix the cache bug codex found: `json.dumps` at ~line 359 fails on NumPy `int64` counts (convert to `int`).
2. Test in `test_source.py`: a synthetic subject whose data are made rank-deficient (e.g. one channel replaced by the
   mean of two neighbours) must not get a dSPM maximum more than 3× that of the same data at full rank. All five
   suites `OK`.
3. Re-run the real timeline spec (`…\specs\source_timeline.json`). Report `outlier_subjects`, the ranks that are
   < 62 (subject → rank), and the new PNG path.

## Reply (≤ 8 lines)
