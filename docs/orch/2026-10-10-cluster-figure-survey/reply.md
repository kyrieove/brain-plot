STATUS: done

Files changed
- `research/cluster-figures/survey.md` (new): header, one 15-row table (15 columns), `## Summary`, `## Dropped`.
- `research/cluster-figures/figures/` (new, 15 images): `01_ma2026_fig3.png`, `02_pirescoelho2026_fig5.jpg`, `03_lucero2026_fig3.png`, `04_wang2026_fig4.png`, `05_schlossmacher2026_fig3.png`, `06_zheng2026_fig3.jpg`, `07_monahhova2026_fig3.png`, `08_flosch2026_fig3.jpg`, `09_leoncabrera2026_fig3.png`, `10_ma2026_fig3.jpg`, `11_ahmadighomroudi2026_fig4.jpg`, `12_costa2026_fig2.png`, `13_contemori2026_fig3.jpg`, `14_mne2026_fig3.png`, `15_fieldtrip2026_fig4.png`.

Notes on the work
- Steps 1–3 done as written: Europe PMC/PMC full text searched, each candidate caption + the methods sentence naming the test read, all 13 empirical DOIs resolved on Crossref (title + first author matched) plus 2 tutorials (URLs loaded, access date 2026-10-10 recorded), every image downloaded from the publisher/PMC/tutorial page and opened; all are ≥300 px on the short side. 13 empirical (all 2025–2026, open access) + 2 tutorials; ≤1 figure per paper.
- Syntax-only check: no compiled-language file was changed (scratch scripts lived in the temp dir). `survey.md` was verified as valid UTF-8 with the exact required first line, 15 data rows, and all 15 referenced `figures/…` paths present (no missing, no orphans). This was not the Check.

Could not do / left open
- Did not run the Check (`python research/cluster-figures/check_survey.py`) — per your instruction it is left to the runner.
- Row 15 (FieldTrip) `Colour value` is `n/a`: the tutorial page/colourbars do not legibly state whether the topomaps encode t or µV, so I did not guess.
- Fields the sources never state are `n/a` (e.g. tails for most rows; permutation counts for the TFCE and tutorial rows). One row (Gómez-Andrés 2026, iScience) and three decoding/TFR papers were dropped and listed under `## Dropped`.
- No commits; subject data untouched. Obsolete intermediate downloads were moved out to the system temp dir (no `rm`).

Figure folder: `C:\dev\brain-plot\research\cluster-figures\figures\`