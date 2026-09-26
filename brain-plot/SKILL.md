---
name: brain-plot
description: Paper-ready ERP figures (waveforms + scalp topographies) from per-subject MNE Epochs/Evoked .fif files, in one fixed house style. First interviews the user in rounds (claim, key comparison, groups, components and windows, layout), gets explicit confirmation of a written spec, then draws with erp_plot.py and checks the render. Also draws microstate figures (templates, butterfly, GFP, segmentation ribbon; across-K template rows) from saved templates. Draws only — not for ERP statistics, EEG preprocessing, microstate clustering, or source/time-frequency plots. Use for ERP 波形图、地形图、ERP+地形图组合图、论文 ERP 配图、微状态图、microstate figure、brain plot.
---

# brain-plot

Route first: ERP waveforms / topomaps / combo / overview → `erp_plot.py`; microstate figures from saved templates → `microstate_plot.py` (section "Microstate figures"). Statistics, preprocessing and clustering are out of scope.

Side effects (tell the user before the first run): the scripts read every input file, write a cache (`brain-plot/.cache/`, can be tens of MB — mind synced folders like Dropbox) and all figures to `brain-plot/` next to the data folder, and move older versions of a re-drawn figure to `_history/` (never delete or overwrite). They need Python with MNE ≥ 1.6, matplotlib ≥ 3.8, scipy; run them on a trusted local copy of the data.

`erp_plot.py` (next to this file) does the ERP computing and drawing; the style is fixed in code. Never restyle a
figure by hand or with ad-hoc matplotlib — change the spec instead.
Needs Python ≥ 3.10 with mne ≥ 1.6, matplotlib ≥ 3.8, scipy (tested: MNE 1.13.dev, matplotlib 3.10).
Rules: `references/rules.md` (binding). Spec fields: `references/spec.md`. Worked specs: `../examples/specs/` (run `../examples/make_demo_data.py` first for synthetic data). Relative `data`/`templates` paths in a spec file are taken from the spec's folder.

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
analysed components and windows, exclusions, reference and stimulus timing.
Never ask the user for something you can read.

## 2. Interview in rounds (grilling)

Ask only what the data and notes cannot settle. Each round: every question whose prerequisites are settled,
numbered, each with your recommended answer and one line of why. Wait for answers, then the next round.
Where something is unknown and only feeds the caption, leave it out of the spec — never invent a value just so the user can say "ok".

| Round | Decide |
|---|---|
| 1 | Figure type: `combo` (waveforms + maps, one per component), `topo` (maps only), or `erp` (waveforms by channel: ROI mean, one figure per channel incl. `all`, or a grid; channels asked here; gray bands only if the user wants them once windows are confirmed, default none — rule K1). Width (`width_mm`, e.g. 180 for double column); what the reader must see first (one sentence → `claim`; it decides the figure type, components and channels). |
| 2 | Key comparison → `key_comparison`, which decides `overlay` (the compared variable goes in the same panel) and how lines pair up in `colors`/`linestyles` (e.g. colour = task, line style = level); groups and order (first = reference, drawn black); exclusions; trial selection (all trials or e.g. correct only → `query`). |
| 3 | Components (one figure each); channels per component; windows (offer `windows` output only as candidates; don't ask where a window comes from — rule S3). The display range is the whole epoch (rule L9); don't ask about it. |

Style (polarity, colours, line styles, fonts, colour map) follows the house defaults in `references/rules.md`; don't ask about it — change it only when the user asks. Line pairing from round 2 (e.g. colour = task, line style = level) is part of the key comparison, not a style question.

`time_locked_to` and `reference` only feed the caption: read them from the preprocessing scripts and files; if they are not there, leave them out of the spec. Never ask the user for them and never fill them from memory.

Candidate windows, if the user wants help (a combo/topo spec whose components carry ROI `channels`; search ranges in `tmin_ms`/`tmax_ms`; `kind: "erp"` bands have no channels and are refused):
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
Hand the caption facts over as facts to write a caption from, not as a finished caption: `## Whole figure`, then `## Panels` by the letters on the figure.

If the script stops on flat channels (rule S10), ask whether they are the reference electrode (then add them to `flat_channels`) or broken channels to fix upstream; never add them to `flat_channels` without that answer.

## Microstate figures (branch)

For microstate figures use `microstate_plot.py` (rules MS1–MS8, spec section "Microstate spec"). Read the analysis's
docs, locked config and model files first: templates path, subjects and exclusions, window, polarity mode, minimum
segment length. Ask only: which K (or which K range for `by-K`), which conditions (and groups), which
blocks. Confirm the spec, run `python microstate_plot.py plot <spec.json>`, check the PNG (maps framed and numbered
in time order, ribbon and map labels agree; with `hatch`, hatching only where GFP is at baseline level), record `qa` in `_run.json`.

Agent-level eval cases (trigger and behaviour): `evals/cases.md`.

## Boundaries

Sensor-level ERP potentials only. Stop and say "not supported" for: difference waves, lateralised
components, CSD/source/time–frequency data, significance marks, more than 7 overlaid lines.
