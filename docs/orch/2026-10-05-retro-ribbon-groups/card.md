# retro-ribbon-groups — say the ribbon is a back-fit; name the group × condition limit where agents look

## Goal
A microstate `states` figure's `_caption.md` and `_run.json` both say the ribbon / state colours are this script's
back-fit of the templates to the drawn grand average (with `min_segment_ms`), not the analysis's own labels.
`references/microstate.md` "Read first" states that groups are between-subject, and the two load errors name that
cause and the remedy. `python brain-plot/test/test_microstate.py` and `python brain-plot/test/test_erp_plot.py`
both print `OK`.

## Risk
medium

## Parameters
- new `_run.json` key: `segmentation`, only for `figure: "states"` (i.e. when `"spans" in facts`); value exactly
  `f"back-fit of the templates to the drawn grand average by microstate_plot.py, min_segment_ms = {m}; not the analysis's own labels"`
  with `m = spec.get("min_segment_ms", 30)`
- new caption line (states figure only), placed directly after the `- Segmentation: …` line:
  `- Ribbon and state colours: ` + the same `segmentation` string
- `references/microstate.md` new bullet, first bullet of the list under "## Read first, then ask" (before
  "At most 2 rows …"), exactly:
  `- Groups are between-subject: a group × condition design gets one \`states\` figure per group (\`groups: [G]\`).`
- error texts in `brain-plot/erp_plot.py` (the existing prefix stays first, so old substring checks still match):
  - `f"subject IDs appear more than once: {dup} — groups are between-subject (each subject in one group); for group × condition draw one figure per group (groups: [G])"`
  - `f"subjects missing a condition file: {gaps} — every subject needs a file for each listed condition; groups are between-subject: for group × condition draw one figure per group (groups: [G])"`
- no new spec key; no `labels` input

## Files
may change: `brain-plot/microstate_plot.py`, `brain-plot/erp_plot.py`, `brain-plot/references/microstate.md`,
`brain-plot/test/test_microstate.py` / read-only: everything else, including `brain-plot/SKILL.md`,
`brain-plot/references/spec.md`, `docs/rules.md`, `examples/`

## Steps (N = 5)
1. `brain-plot/microstate_plot.py` → `plot()`: right after the line
   `facts["templates_meta"] = [template_meta(p) for p in paths]`, add
   ```python
   if "spans" in facts:  # states figure: the ribbon is drawn here, not read from the analysis
       facts["segmentation"] = (f"back-fit of the templates to the drawn grand average by microstate_plot.py, "
                                f"min_segment_ms = {spec.get('min_segment_ms', 30)}; not the analysis's own labels")
   ```
   It reaches `_run.json` through the existing `**facts`; do not add it to the `json.dumps(dict(...))` call by hand.
2. `brain-plot/microstate_plot.py` → `caption()`: directly after the `L.append(f"- Segmentation: …")` statement
   (the one ending with `time_locked_to` …), add
   `if "segmentation" in facts: L.append("- Ribbon and state colours: " + facts["segmentation"])`.
   `caption()` is called after step 1's assignment, so `facts` already has the key.
3. `brain-plot/references/microstate.md`: insert the Parameters bullet as the first bullet under
   "## Read first, then ask" (immediately before the bullet starting `- At most 2 rows`).
4. `brain-plot/erp_plot.py`: replace the two `die(...)` texts (currently `f"subjects missing a condition file: {gaps}"`
   and `f"subject IDs appear more than once: {dup}"`) with the Parameters texts. Change nothing else in those functions.
5. `brain-plot/test/test_microstate.py`:
   - after the line `assert "thick line = GFP" in cap`, add
     `assert run["segmentation"].endswith("min_segment_ms = 30; not the analysis's own labels") and "- Ribbon and state colours: back-fit" in cap`
     (`run` is the `_run.json` dict already loaded in that block; if the block names it differently, use that name)
   - change `fails(spec(root), "missing a condition file")` to `fails(spec(root), "draw one figure per group (groups: [G])")`

## Check
`python brain-plot/test/test_microstate.py && python brain-plot/test/test_erp_plot.py`

## Don't
- Run scripts in the foreground and wait; before replying, stop any background task still running.
- Reuse existing functions; don't copy existing logic.
- No rm, no git push, no git checkout . / restore . / reset --hard.
- No commits, no other files, no refactors beyond the steps; do not touch `docs/retro_*` or `examples/`.

## Acceptance
- verdict: accepted (codex out of quota; executor and review on wb by user choice, 2026-10-05)
- files: brain-plot/erp_plot.py, brain-plot/microstate_plot.py, brain-plot/references/microstate.md, brain-plot/test/test_microstate.py
- check: `python brain-plot/test/test_microstate.py && python brain-plot/test/test_erp_plot.py` → exit 0 (run by run-card)
- tokens:
  - round 1: exec deepseek-v4.1-flash: fresh 0k, cached 0k, out 0k  (codex-retro-ribbon-groups.jsonl) · review deepseek-v4.1-flash: fresh 0k, cached 0k, out 0k  (codex-review-retro-ribbon-groups.jsonl)
- review findings: 0 real / 0 false positive / 0 missed (medium, deepseek-v4.1-flash)
