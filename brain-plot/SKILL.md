---
name: brain-plot
description: Paper-ready ERP figures (waveforms + scalp topographies) from per-subject MNE Epochs/Evoked .fif files, in one fixed house style. First interviews the user in rounds (claim, key comparison, groups, components and windows, layout), gets explicit confirmation of a written spec, then draws with erp_plot.py and checks the render. Also draws microstate figures (templates, butterfly, GFP, segmentation ribbon; across-K template rows) from saved templates, time-frequency figures (power, ITC), and source reconstruction maps (dSPM on fsaverage). Draws only — not for ERP statistics, EEG preprocessing, or microstate clustering. Use for ERP 波形图、地形图、ERP+地形图组合图、论文 ERP 配图、微状态图、microstate figure、时频图、ITC 图、time-frequency plot、源定位图、source plot、brain plot.
---

# brain-plot

Route first, then read that module's file (next to this one, in `references/`):

| Request | Script | Read |
|---|---|---|
| ERP waveforms / topomaps / combo / overview | `erp_plot.py` | `references/erp.md` |
| Microstate figures from saved templates | `microstate_plot.py` | `references/microstate.md` |
| Time-frequency figures (power, ITC) | `tfr_plot.py` | `references/tfr.md` |
| Source maps (dSPM on fsaverage) | `source_plot.py` | `references/source.md` |

Spec keys: `references/spec.md`. Worked specs: `examples/specs/` in the repository root, one level above this skill's real folder (the installed
skill folder may be a link — resolve it first; run `examples/make_demo_data.py` there for synthetic data, or use
the synthetic data the `test/` scripts build). Statistics, preprocessing, and clustering are out of scope:
say "not supported".

## Before the first run

- Check the interpreter: `python check_env.py` (standard library only) prints Python, package versions and fonts, and
  "OK" or what to install; use the interpreter that passes (Python ≥ 3.10, mne ≥ 1.7, matplotlib ≥ 3.8, scipy). Source maps also need
  pyvista and the fsaverage template (spec `subjects_dir`, or `mne.datasets.fetch_fsaverage()` once).
- Tell the user the side effects: the scripts read every input file, write a cache (`brain_plot_<data folder name>/.cache/`, the 6 most
  recently used, each can be tens of MB — mind synced folders like Dropbox) and all figures to `brain_plot_<data folder name>/` next to
  the data folder, and move older versions of a re-drawn figure to `_history/` (never delete or overwrite). Run them
  on a trusted local copy of the data.
- The style is fixed in code. You (the agent) never restyle or edit a figure by hand or with
  ad-hoc matplotlib — change the spec. The SVG is editable so that the user can make final manual adjustments.

## Workflow (all modules)

1. **Inspect — facts are your job, not the user's.** Read the data (`inspect`) and the study's own notes and
   scripts. Never ask the user for something you can read.
2. **Interview in rounds (grilling).** Ask only what the data and notes cannot settle. Each round: every question
   whose prerequisites are settled, numbered, each with your recommended answer and one line of why. Wait for
   answers, then the next round. What to ask and what never to ask: the module file. Where something is unknown and
   only feeds the caption, leave it out of the spec — never invent a value just so the user can say "ok".
3. **Confirm.** Write the spec JSON (in `brain_plot_<data folder name>/specs/` next to the data folder; relative `data`/`templates`
   paths are taken from the spec's folder), show it as a short list, and wait for an explicit yes. Re-confirm when
   anything scientific changes (groups, exclusions, channels, windows, display range, overlay, K, conditions). Layout
   fixes need no re-confirmation.
4. **Draw.** `python <script> plot <spec.json>`. The script validates the spec and every input file and stops with a
   message on any problem — fix the cause, never work around it (the module file lists the usual stops). Outputs per
   figure: `.png .svg` (editable SVG text),
   `_caption.md` (facts for the caption; not for source maps, by user decision), `_run.json`
   (spec, subjects, versions, checks), named by content and versioned `_vNN`. Later runs use a cache that is
   invalidated when any input file changes.
5. **Check the PNG, then report.** Open each PNG and go through the module's QA list. Report every `layout_issues`
   entry and fix what the spec can fix; write the QA result into the `qa` field of each `_run.json`; list every
   `open_items` field to the user as still open. Tell the user what you checked, what is still open, and where the
   files are. Hand the caption facts over as facts to write a caption from, not as a finished caption:
   `## Whole figure`, then `## Panels` by the letters (or titles) on the figure.

Agent-level eval cases (trigger and behaviour): `evals/cases.md`.
