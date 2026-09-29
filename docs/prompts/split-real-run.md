# Antigravity prompt: split skill, full run on real data (written 2026-09-29)

Purpose: the rules split (2026-09-27) was checked only by dry-run interviews; this run exercises draw + QA with
the new `SKILL.md` / `erp.md` / `microstate.md` on two figures that were already accepted (metaphor N400 v04,
GN K5 v07). Paste the prompt below into Antigravity; the result comes back as
`C:\dev\agent-test-split-real-2026-09-29.md`.

```
Task: exercise the split brain-plot skill end to end (draw + QA) on two figures that were already accepted.
Python: C:\Users\ASUS\miniconda3\envs\mnedev\python.exe. Repo: C:\dev\brain-plot.

0. git pull --ff-only origin main; then git fetch origin <cloud branch> and
   git merge --ff-only origin/<cloud branch>; git push origin main. Stop if not a fast-forward.
1. Act as the agent: read ONLY brain-plot/SKILL.md, the module file it routes to, and references/spec.md.
   Do not open docs/rules.md. The specs below were confirmed by the user earlier: skip the interview.
2. ERP: run `erp_plot.py plot` on the metaphor N400 spec in
   D:\1-python_datasets\metaphor production\derivatives\brain-plot\specs\ (the N400 combo spec; list the folder
   and pick it). Microstate: run `microstate_plot.py plot` on the GN K5 states spec in
   C:\Users\ASUS\Dropbox\metaphor_production\gn_manuscript\01-evokeds_grand_averages\brain-plot\specs\ (the K5
   states spec whose last render is v07). New versions are expected (N400 v05, K5 v08); older ones move to _history.
3. For each new PNG, go through the QA list of its module file item by item, exactly as written; fill the `qa`
   field of its _run.json. Compare with the previous accepted version in _history (N400 v04, K5 v07): same layout,
   labels, boundaries and numbering? List every visible difference.
4. Report: commands and their printed output (warnings included); QA item by item (pass / problem + one line);
   differences vs the previous version; anything in SKILL.md / erp.md / microstate.md that was unclear, missing,
   or that you needed docs/rules.md for.
Write the report to C:\dev\agent-test-split-real-2026-09-29.md. Read-only on the data folders (only the
brain-plot\ output folders get new files). Do not edit or commit any repo file.
```
