# Playbook: source-localization module (codex desktop + agy CLI, no Claude)

Written 2026-09-30 by Claude from the time-frequency (TFR) run, so the next module can follow the same path without
Claude. Everything here is for agents; talk to the user in Chinese (`AGENTS.md`).

## Roles
| Who | Does | Never |
|---|---|---|
| **User** | answers the interview, approves the plan, looks at every figure, says when to merge and push | — |
| **Codex desktop** (the brain; was Claude's role) | reads, interviews the user, writes `docs/PLAN-source-module.md` and every agy PLAN, does the literature (text only), reviews agy's work on the real files, commits | writes module code itself (a one-line fix is fine) |
| **agy CLI** (the hands) | implements from a PLAN file, runs long computations, writes a progress file | decides scope, merges, pushes |

## How codex runs agy (PowerShell)
```powershell
& "C:/Users/ASUS/AppData/Local/agy/bin/agy.exe" -p "Implement exactly C:\dev\brain-plot\docs\AGY_PLAN_source-1.md. Reply as that file says." --model gemini-3.8-flash-high --dangerously-skip-permissions --output-format json
```
- Take `conversation_id` from the reply (the JSON starts at the first `{`; idle lines may come before it). Every later
  call in the same task adds `--conversation <id>` (80 % of the start-up cost comes from cache).
- `-p` and stdin exclude each other. For a read-only question: pipe the text in and drop `-p` and the permissions flag.
- Codex's sandbox must allow the agy process (network + writing inside the repo and the output folder).
- Record `git status --short` before each write call; afterwards `git diff --stat` may only name the PLAN's files.
- If flash gets the same thing wrong twice, retry with `--model gemini-3.1-pro-high`.

Every agy PLAN contains these lines (each one comes from a failure):
1. "Run every script in the foreground and wait for it; before you reply, make sure no background task is still
   running." (agy otherwise idles 30 min waiting for its own background task.)
2. "Reuse existing functions (`erp_plot` loader, `query_epochs`, `layout_issues`, output naming and versioning,
   `tfr_plot` cache); do not copy existing logic." (agy copied an x-tick loop in the TFR run.)
3. The exact list of files it may create or change, and the test commands that must print `OK`.
4. Numbered steps with a fixed total N; after each step append `[██░░░] 2/N <what> · HH:MM` to
   `C:\dev\brain-plot\AGY_PROGRESS_<task>.md` (first line `[░░░░░] 0/N start · HH:MM`).
5. Data folders are read-only: never delete, move or overwrite; new outputs only in the named output folder.
   Jobs over 10 min are resumable (per-subject cache; a finished subject is skipped on restart).
6. `n_jobs` ≤ 2 for anything parallel (AutoReject with `n_jobs=-1` ran 16 workers on 15 GB and lost 8 subjects).
7. "Reply in ≤ 10 lines: status, files changed, test output, anything you could not do."

## Stages (same order as TFR; each ends at a gate)

### 0. Start
Branch `source` from `main`. Read: `HANDOFF.md` (Next section), `docs/rules.md` (TF1–TF8 and O1–O3),
`brain-plot/tfr_plot.py` (the template: loader via `erp_plot`, npz cache, fixed canvas, `_run.json`, outputs),
`brain-plot/references/tfr.md`, the TFR section of `brain-plot/references/spec.md`, `brain-plot/test/test_tfr.py`.
Use `grep -n` / line ranges, not whole-file dumps.

### 1. Interview → plan (gate: the user says the plan is OK)
Ask in rounds of ≤ 3 questions, each with a recommended default first. Write the answers into
`docs/PLAN-source-module.md` (decisions, out of scope, file list, tests). Decisions to settle:

| # | Decision | Recommended default (the user may change it) |
|---|---|---|
| D1 | Figure type | cortical maps on inflated fsaverage: rows = conditions (or groups), columns = views (lh lateral, rh lateral; medial/ventral optional), one figure per time window; optional second type: ROI time courses (aparc labels) |
| D2 | Inverse method | dSPM, `lambda2 = 1/9` (evoked SNR 3), `loose=0.2`, `depth=0.8`, magnitude of the vector (sLORETA / eLORETA as options) |
| D3 | Forward model | fsaverage template (no individual MRIs): `~/mne_data/MNE-fsaverage-data/fsaverage/bem/fsaverage-5120-5120-5120-bem-sol.fif`, `fsaverage-ico-5-src.fif`, trans `"fsaverage"`; montage read from the files (63 EEG channels, digitisation present). One forward for all subjects → no morphing |
| D4 | Reference | data are linked mastoids (TP9/TP10, `custom_ref_applied`); source needs the average-reference projection (`set_eeg_reference("average", projection=True)`) inside the module |
| D5 | Noise covariance | from pre-stimulus samples of the epochs, window before the trial's **first** stimulus (TFR lesson: a fixation cross 500 ms before the marker sat in the default baseline). Same open question as the TFR baseline — ask, do not pick |
| D6 | Group average | per-subject evoked → STC (cached npz per subject), equal-weight mean across subjects of the per-subject STCs |
| D7 | Windows | from the analysis (ERP specs: N1 120–200 ms, N400 300–500 ms after the verb); never read off the grand average |
| D8 | Colour scale | one scale shared by all maps of a figure; dSPM is ≥ 0 → one-sided colormap, limits from percentiles of the shown values; one colour bar at the right edge (house style) |
| D9 | Rendering | pyvista off-screen screenshots (pyvista 0.48 is installed) assembled in matplotlib on the fixed mm canvas; all text drawn by matplotlib, none in 3D; no electrode marks |
| D10 | Caption | states: template head model, 63 channels, method, λ², noise-cov window, N per group — spatial resolution is coarse |

Out of scope unless the user asks: statistics / cluster tests / thresholds from p-values (house: descriptive only),
individual MRIs, beamformers / source-space TF, connectivity, difference maps (ERP does not draw difference waves
either — ask).

### 2. Literature (gate: codex spot-checks 3 rows on the article page)
Run `research/source/TASK-survey.md` (figure layout) and `research/source/TASK-metaphor.md` (metaphor studies).
Text only: the TFR survey's first codex run failed on image downloads. Check every DOI on
`https://api.crossref.org/works/<doi>`. Feed the summary back into D1/D2/D8 before the plan is final.

### 3. agy PLAN 1 — module (form B, write access to the repo)
Codex writes `docs/AGY_PLAN_source-1.md`. Allowed files: `brain-plot/src_plot.py` (new),
`brain-plot/test/test_src.py` (new), `brain-plot/references/source.md` (new), `brain-plot/references/spec.md`
(new section), `brain-plot/SKILL.md` (one router row), `docs/rules.md` (new SRC rules). Tests must be fast and need
no real data (small synthetic evoked on the fsaverage montage; a coarse source space is fine for tests). Required
self-checks, each with a test:
- **Hemisphere check**: a simulated source in the left temporal lobe must be brightest in the lh-lateral panel.
- Noise-cov window inside the epoch and before 0 ms; stop with a clear message otherwise.
- Channels without positions / reference not average → stop with a message naming the fix.
- `layout_issues` empty (reuse `erp_plot`'s check), outputs under `SRC/` in the O1–O3 naming.

### 4. Codex review (gate: all of the below hold)
1. `git diff --stat` names only the allowed files; read the diff; delete copied logic and dead code.
2. Suites print `OK`: `test_erp_plot.py`, `test_microstate.py`, `test_layout.py`, `test_tfr.py`, `test_src.py`.
3. Real-data smoke run on 3 subjects; open every PNG (lh/rh labels right? maps cut off? colour bar present?).
4. **Recompute one number independently**: for one subject, compute the dSPM value of one aparc label in the N400
   window with plain `mne.minimum_norm` in a scratch script and compare with the module's cache (agy's own self-checks
   only show it did what it understood).
5. Report findings to the user; fixes go back to agy with `--conversation <id>`.

### 5. agy PLAN 2 — real data (form C: data read-only, new outputs only)
Codex writes `docs/AGY_PLAN_source-2.md`: specs in
`D:\1-python_datasets\metaphor production\derivatives\brain_plot_preprocessed_epochs_verb\specs\src_*.json`, all
subjects except sub27, `query: "acc == 1"`, group_by WM, `time_locked_to: "verb onset"`. Resumable, `n_jobs` ≤ 2.
Show the user every figure (path + open it in the chat).

### 6. Rounds with the user
Each change: codex writes a short PLAN delta → agy with `--conversation` → codex review (stage 4 steps 1–3).
User lesson (2026-09-29): a new layout behaviour goes into rules and a self-check, not one complaint at a time.

### 7. Finish (only when the user says so)
Merge `source` into `main`, push. Update `HANDOFF.md` (State + Next), `docs/review-log.md` (what changed and why),
`docs/rules.md`, the README module list if the user wants it. Commit messages in English.

## Facts and traps for this data
- Data: `D:\1-python_datasets\metaphor production\derivatives\preprocessed_epochs_verb\` (60 subjects, −1…2 s,
  500 Hz, 63 EEG channels incl. TP9/TP10, montage present). Python: `C:\Users\ASUS\miniconda3\envs\mnedev\python.exe`
  (MNE 1.13 dev, pyvista 0.48, nibabel; no nilearn).
- Markers: S15–20 = **verb onset** (0 ms), S1–6 = 2500-ms blank after the verb (+350 ms), S7–12 = sound prompt
  (+2900 ms). Conditions Hmet, Hlit, Hrep, Lmet, Llit, Lrep (H/L = SND high/low, not the WM group).
- sub27: `acc` is 3 on every trial → no `acc == 1` trials; exclude with a reason in `exclude` (user still checks).
- Open with the user (see `HANDOFF.md` "Waiting on the user"): baseline window, condition labels. Source figures share
  the baseline question (D5).
- Windows refused direct folder renames under `D:\…` once: create the new folder, move the contents.
- Tests whose outcome depends on text width must pass with Arial (Windows).
- Git Bash heredocs eat backslashes; write scripts to files.
- Verify on the real files, never from agy's report.
