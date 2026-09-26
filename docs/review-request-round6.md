# Review request, round 6 (2026-09-26)

Full review of the brain-plot skill in `C:\dev\brain-plot` (public repo https://github.com/kyrieove/brain-plot).
Read-only: do not edit files, do not commit. Write the findings to `docs/astra-review-round6.md`.

## Read first
1. `HANDOFF.md`, `docs/review-log.md` (every change since round 5, with reasons), `docs/astra-review-round5.md`
2. `docs/plan-2026-09-26.md` (ERP branch; note the revision: no localizer) and `docs/plan-microstate.md`
3. `brain-plot/SKILL.md`, `brain-plot/references/rules.md` (U = binding user rules), `brain-plot/references/spec.md`
4. Code: `brain-plot/erp_plot.py`, `brain-plot/microstate_plot.py`; tests: `brain-plot/test/test_erp_plot.py`,
   `brain-plot/test/test_microstate.py`

Python: `C:\Users\ASUS\miniconda3\envs\mnedev\python.exe`. Both test files must print `OK`; you may run them
(they write only to temp folders).

## What to check
1. Round-5 findings: is each one fixed? Give a failing input if not.
2. New since round 5: output layout and versioning (rules O1–O3, `versioned()`, `_history/`), `kind: "erp"` by
   channel (K1: roi / single / all / grid, optional bands), the `<condition>/<group>/<subject>-ave.fif` loader layout,
   and the whole microstate branch (MS1–MS10: segmentation and minimum-run merge, low-GFP hatch, numbering, identity
   colours, the `layout()` geometry, grid rule, panel-shape check).
3. Contract gaps: every rule in rules.md is enforced as its "Enforced" column says; spec.md matches the code's keys and
   defaults; SKILL.md's workflow matches what the scripts do.
4. Scientific correctness: averaging weights, segmentation vs the reference method
   (`C:\Users\ASUS\Dropbox\metaphor_production\gn_manuscript\05-microstate_GA\code\gen_fig_per_k_independent.py`,
   `signed_microstate.py`), what the caption facts claim.
5. Tests: which rules have no check that would fail on wrong code.

## Part B: skill-level audit with yao-meta-skill
Use the `yao-meta-skill` skill (in `~/.codex/skills/yao-meta-skill`) in **audit mode on the existing skill
`brain-plot/`**: findings and proposed fixes only, no edits, no generated packages. Cover what it checks that Part A
does not: the frontmatter `description` as a trigger (should fire for ERP waveform / topomap / microstate figure
requests, not for ERP statistics or preprocessing), routing between `erp_plot.py` and `microstate_plot.py`, missing
trigger/output evals, the interface between SKILL.md, rules.md and spec.md, and install/trust concerns (the skill runs
local scripts on user data and writes next to the data folder). Report these as a separate section of the same file.

## Output format
Numbered findings, P1 (wrong result or silent data problem) / P2 (rule or layout violation, misleading output) /
P3 (cleanup). Each: file:line, a concrete failing input, a minimal fix. End with a one-line verdict.
Reply in Chinese.
