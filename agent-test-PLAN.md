# Task: draw one figure with the brain-plot skill (agent reproducibility test)

You are testing whether an agent can use the `brain-plot` skill on its own. Follow the skill exactly.

## Inputs (READ-ONLY — never delete, move, rename or overwrite anything here)
- Skill: `C:\dev\brain-plot\brain-plot\SKILL.md` (read it first), `references\rules.md`, `references\spec.md`,
  script `C:\dev\brain-plot\brain-plot\erp_plot.py`.
- Data: `D:\1-python_datasets\metaphor production\derivatives\preprocessed_epochs` (60 `*-epo.fif`).
- Confirmed spec: `D:\1-python_datasets\metaphor production\derivatives\figures\brain-plot\n400_spec.json`.
  The interview (SKILL step 2) and confirmation (step 3) were already done with the user; do NOT change any
  scientific field. Only the output location changes (below).
- Python with MNE: `C:\Users\ASUS\miniconda3\envs\mnedev\python.exe` (plain `python` may be a different interpreter).

## Output (YOUR directory only; it must not exist yet — if it exists, stop)
`OUT` = the directory named in your start message. Everything you create goes there, nothing anywhere else.

## Steps (N = 5; append one line per step to `OUT\PROGRESS.md`, e.g. `[██░░░] 2/5 plotted · HH:MM`)
1. Create `OUT`. Read SKILL.md, rules.md, spec.md. Write `OUT\PROGRESS.md` with `[░░░░░] 0/5 start · HH:MM`.
2. Copy the confirmed spec to `OUT\n400_spec.json`, changing only `"out"` to `OUT/fig` (forward slashes).
3. Run in the foreground and wait for it to finish:
   `C:\Users\ASUS\miniconda3\envs\mnedev\python.exe C:\dev\brain-plot\brain-plot\erp_plot.py plot OUT\n400_spec.json`
   If it stops with an ERROR, do not work around it: record the message and stop.
4. SKILL step 5: open `OUT\fig_N400.png`, go through the QA list at the end of rules.md item by item, write the
   result into the `qa` field of `OUT\fig_N400_run.json`, and note every `open_items` entry.
5. Write `OUT\REPORT.md` (at most 25 lines): what you did per skill step, QA result per checklist item, open
   items, anything in SKILL.md/rules.md that was unclear or that you had to guess. Do not restyle or edit the image.

Rules: run everything in the foreground; before replying make sure no background task is still running (stop it if
so). Do not modify files outside `OUT`. Reply with at most 8 lines: status, output paths, QA verdict, unclear points.
