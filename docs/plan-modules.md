# Plan: modules beyond ERP / microstate (interview with the user, started 2026-09-27)

## Principle (user, 2026-09-27)
Figures draw the data they are given. Descriptive data (ERP, topomaps, microstates, PSD, time-frequency) carry no
statistics, so their figures show none. Statistical results (cluster permutation / TFCE, decoding statistics) are
results, so their figures draw them — the significant samples, clusters and channels exactly as the result file gives
them. The skill never computes a test or decides significance itself.

## Round 1 (decided)
1. One skill `brain-plot`; `SKILL.md` routes and holds the common workflow; one module file + one script per module.
2. Draw only. PSD / TFR: prefer saved MNE objects (Spectrum, -tfr.h5); computing from epochs is allowed with every
   parameter in the spec and `_run.json`. Cluster permutation and MVPA: draw saved results only.
3. Statistical marks: see the principle — drawn when the input is a statistical result, never on descriptive figures.
4. "Raster plot" = the cluster-permutation result figure (user's example): channel × time matrix, only significant
   samples coloured (µV difference), channels grouped left / midline / right, one column per comparison; plus a row of
   topomaps over time bins with the significant channels marked. Raster and cluster permutation are one module.
5. First extract the shared code (loading, input contract, output/versioning, layout self-check, style, colour
   checks) into `core.py`; ERP and microstate use it; then split the skill text (lean SKILL.md, one file per module,
   rules.md → developer docs).
6. Modules are independent; order does not matter (planned: PSD, time-frequency, statistical results, MVPA).
