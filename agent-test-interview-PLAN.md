# Task: full brain-plot run from raw data, interviewing the user in chat (agent reproducibility test, part 2)

Use the `brain-plot` skill from the start, as if a user had typed `/brain-plot <data_dir>`. Follow
`C:\dev\brain-plot\brain-plot\SKILL.md` and `references\rules.md`, `references\spec.md` exactly.

## Inputs (READ-ONLY: never delete, move, rename or overwrite anything)
- Data: `D:\1-python_datasets\metaphor production\derivatives\preprocessed_epochs`
- The study's own notes and scripts: `D:\1-python_datasets\metaphor production\derivatives\results_section_en_polished.md`,
  `...\derivatives\stats\`, `...\scripts\` (read what SKILL step 1 needs; do not read `derivatives\figures\brain-plot\`).
- The user answers you in chat, round by round. Anything the user does not answer must be written as
  "TO BE CONFIRMED" in the spec, never invented.
- Python with MNE: `C:\Users\ASUS\miniconda3\envs\mnedev\python.exe`. Your sandbox cannot read `C:\Users\ASUS\.mne`:
  in every command that imports MNE, first set `_MNE_FAKE_HOME_DIR` to `OUT\home` (create it).

## Output (YOUR directory only; it must not exist yet — if it exists, stop)
`OUT` = the directory in your start message. Everything you create goes there.

## Steps (N = 6; append one line per step to `OUT\PROGRESS.md`, e.g. `[██░░░░] 2/6 interview · HH:MM`)
1. Create `OUT`; read the skill files; `[░░░░░░] 0/6 start`.
2. SKILL step 1: run `erp_plot.py inspect` on the data, read the notes; write the facts you found to `OUT\facts.md`.
3. SKILL step 2: interview in rounds. For each round, append your numbered questions with recommended answers to
   `OUT\interview.md`, then STOP and reply with exactly those questions (nothing else). Continue only when the next
   message brings the answers; append them and your decisions to `interview.md`, then ask the next round, until
   the frontier is empty. Then show the spec summary and ask for explicit confirmation, and stop again.
4. SKILL step 3: write the spec to `OUT\n400_spec.json` with `"out": "OUT/fig"`; validate it by running `plot` (step 5).
5. SKILL step 4–5: run `plot` in the foreground; check the PNG against the QA list; write `qa` into `_run.json`.
6. Write `OUT\REPORT.md` (at most 25 lines): decisions that relied on your own recommendation, fields left TO BE
   CONFIRMED, anything in SKILL.md that was unclear.

Run everything in the foreground; before replying make sure no background task is still running. Do not modify files
outside `OUT`. Reply with at most 8 lines.
