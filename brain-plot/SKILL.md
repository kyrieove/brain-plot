---
name: brain-plot
description: Paper-ready ERP figures (waveforms + scalp topographies) from per-subject MNE files, in one fixed house style. First interviews the user in rounds (claim, key comparison, groups, components and windows, layout), gets explicit confirmation of a written spec, then draws with erp_plot.py and checks the render. Use for ERP 波形图、地形图、ERP+地形图组合图、论文 ERP 配图、brain plot.
---

# brain-plot

`erp_plot.py` (next to this file) does all computing and drawing; the style is fixed in code. Never restyle a
figure by hand or with ad-hoc matplotlib — change the spec instead.
Needs Python ≥ 3.10 with mne ≥ 1.6, matplotlib ≥ 3.8, scipy (tested: MNE 1.13.dev, matplotlib 3.10).
Rules: `references/rules.md` (binding). Spec fields: `references/spec.md`. Worked spec: `test/fig_main.json`.

## 0. Explore (optional, before windows are known)

If the user doesn't yet know the components or windows, first draw overview figures — no interview needed:
```
python erp_plot.py explore <explore.json>
```
3 × 3 waveforms (F3 Fz F4 / C3 Cz C4 / P3 Pz P4) plus a condition × component topomap table, optionally with
difference maps. Keys: `references/spec.md`, section Explore. Windows read off these figures are still
candidates; their source must be stated in round 3 (rule S3). Explore writes no `_run.json` and needs no QA
record (rules E1–E3); just look at the PNGs before showing them.

## 1. Inspect — facts are your job, not the user's

```
python erp_plot.py inspect <data_dir>
```
Also read the study's own notes if they exist (analysis plan, results, preprocessing log) to learn the
hypotheses, analysed components and windows, exclusions, reference, stimulus timing and statistical results.
Never ask the user for something you can read.

## 2. Interview in rounds (grilling)

Ask only what the data and notes cannot settle. Each round: every question whose prerequisites are settled,
numbered, each with your recommended answer and one line of why. Wait for answers, then the next round.
Where the science is unknown, recommend "to be confirmed" — never invent a value just so the user can say "ok".

| Round | Decide |
|---|---|
| 1 | Figure type: `combo` (waveforms + maps, one per component), `topo` (maps only), or `erp` (waveforms by channel: ROI mean, one figure per channel incl. `all`, or a grid; channels asked here; gray bands only if the user wants them once windows are confirmed, default none — rule K1). Role of the figure (main / one of several / supplement); journal and width; what the reader must see first (one sentence → `claim`). |
| 2 | Key comparison → `key_comparison` and `overlay` (the compared variable goes in the same panel); groups and order (first = reference, drawn black); exclusions with reasons; trial selection (all trials or e.g. correct only → `query`; must match the trials the statistics used); what the statistics say (→ `stats_note`) and whether the intended message fits them. |
| 3 | Components (one figure each); channels per component; windows **and their source** (rule S3; offer `windows` output only as candidates); display range (rule L9). |
| 4 | Anything still open: polarity, colours, time-locking wording, reference wording. |

If the intended message and the statistics disagree (e.g. "show group differences" but no effect survived
correction), say so plainly and offer an honest message before drawing.

Candidate windows, if the user wants help (search ranges in `tmin_ms`/`tmax_ms`):
```
python erp_plot.py windows <spec.json>
```

## 3. Confirm

Write the spec JSON, show it as a short list, and wait for an explicit yes. Re-confirm when anything
scientific changes (groups, exclusions, channels, windows, display range, overlay). Layout fixes within the
rules need no re-confirmation.

## 4. Draw

```
python erp_plot.py plot <spec.json>
```
The script validates the spec and every input file and stops with a message on any problem — fix the cause,
never work around it. Outputs go to `brain-plot/` next to the data folder, one sub-folder per kind, named and
versioned by rules O1–O3 (old versions move to `_history/`). Outputs per component: `.png .svg` (fixed physical size; SVG text stays editable), `_caption.md` (facts for
the caption), `_run.json` (spec, subject IDs, versions, sample bounds, line/map counts). The first run reads
every file; later runs use a cache that is invalidated when any input file changes.

## 5. Check the PNG, then report

Open each PNG and go through the QA list at the end of `references/rules.md` (items scoped by `kind`). Fix via the spec or report the
problem; do not edit images. Write the QA result into the `qa` field of each `_run.json`, and list every `open_items` field to the user as still open. Tell the user what you checked, what is still open, and where the files are.
Hand the caption facts over as facts to write a caption from, not as a finished caption.

## Boundaries

Sensor-level ERP potentials only. Stop and say "not supported" for: difference waves, lateralised
components, CSD/source/time–frequency data, significance marks, more than 7 overlaid lines.
