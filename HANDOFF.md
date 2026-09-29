# brain-plot — handoff (2026-09-29)

Start of every new session: read this file, then `docs/review-log.md` (newest entries at the bottom).

## State
Two modules, both working, three test suites pass, everything committed and pushed
(https://github.com/kyrieove/brain-plot, public, branch `main` = `e35e8a7`; `claude/brave-cannon-ci83tc` = `main` + this handoff commit).
- **ERP** (`erp_plot.py`): `combo` (waveforms + maps per component), `topo` (maps only), `erp` (waveforms by channel:
  `roi` mean / `single` incl. `channels: "all"` / `grid`, gray bands only if asked), `explore` (3 × 3 overview +
  topomap table), `windows` (candidate windows, optional helper). The skill only draws — no localizer.
- **Microstate** (`microstate_plot.py`, plan `docs/plan-microstate.md`, rules MS1–MS10): `figure: "states"` (template
  maps + butterfly or GFP + segmentation ribbon; ≤ 2 conditions stacked, more need `grid`) and `"by-K"` (template rows
  across K, identity colours). Reads saved templates (npz `centers`, optional `ch_names`), never re-fits.
- **Skill text (split 2026-09-27)**: `SKILL.md` = router + common workflow (inspect → interview → confirm → draw →
  QA); agent-facing `references/erp.md`, `references/microstate.md` (what to ask / never ask, stops, QA lists) and
  `references/spec.md`; the full rule table is `docs/rules.md` (developer reference, not read by the agent; rule IDs
  in script messages point there).
- **Code layout**: `erp_plot.py` (1569 lines) doubles as the shared core — `microstate_plot.py` imports ~18 of its
  functions (`load`, `read_spec`, `versioned`/`archive`, `colour_check`, `report_layout`, `die`, …). A separate
  `core.py` is planned only for when new modules resume.
- Outputs (rules O1–O3): `brain-plot/` next to the data folder → `ERP/`, `topo/`, `ERP_topo/`, `microstate/`,
  `specs/`, `.cache/`; names say what the figure is; re-renders get `_vNN+1`, old versions move to `_history/`.
- Latest accepted renders: metaphor N400 v04, GN K5 v07.

## Next (start here)
**Waiting on the user:** the Antigravity run in `docs/prompts/split-real-run.md` (split skill, full draw + QA on
metaphor N400 and GN K5; report `C:\dev\agent-test-split-real-2026-09-29.md`). `main` already reached `e35e8a7`, so
its step 0 may have run; ask the user for the report. Then: fix anything the report finds in `SKILL.md` /
`erp.md` / `microstate.md` (not in `docs/rules.md` alone), and check that N400 v05 / K5 v08 match v04 / v07.

Recent (details in `docs/review-log.md`):
- 2026-09-29: two one-off agent test plans archived to `docs/archive/`. Architecture reviewed with the user (summary
  under State). The user declined installing `addyosmani/agent-skills`.
- 2026-09-27: new modules (PSD, TFR, cluster/raster, MVPA) paused by the user; round-1 decisions and the unanswered
  round-2 questions are in `docs/plan-modules.md`. agy's literature survey (`docs/research-figure-conventions.md`)
  failed a spot-check (one DOI not found, one paper only a preprint, the MNE tutorial has no raster): don't cite its
  counts. `docs/gn-permutation-inventory.md` (GN cluster/TFCE result files) is a reliable inventory for later.
  Rules split done and verified locally (three suites OK on Windows; dry-run interviews for eval cases 9/10 pass);
  `microstate.md` now says to ask for `polarity` / `min_segment_ms` / `window_ms` when no file states them.

Optional, not urgent:
1. `core.py` extraction — only when new modules resume (round-1 item 5, code part).
2. GN templates `centers_k05.npz` have no `ch_names` → warning on every run; re-export them with `ch_names` upstream.
3. `hatch: true`: ribbon S# labels are hard to read over the hatching.
4. Run `brain-plot/evals/cases.md` in fresh sessions (manual).
5. External audit (commit c6eee87): items not taken are listed in the review log — don't redo them.
6. Local commits show author `xburner23412`, not `kyrieove` — check `git config user.name/user.email` if unintended.

## Use
- Any session: `/brain-plot <data_dir>` (skill linked at `~/.claude/skills/brain-plot` → `C:\dev\brain-plot\brain-plot`).
- Python: `C:\Users\ASUS\miniconda3\envs\mnedev\python.exe` (conda env `mnedev`, MNE dev — pycrostates 0.6.1 was added
  with `--no-deps` on 2026-09-26; MNE untouched).
- Tests: `python brain-plot/test/test_erp_plot.py`, `test_microstate.py`, `test_layout.py` → each `OK`. Tests whose
  outcome depends on text width must hold in both fonts (Arial on Windows, DejaVu in the cloud).
- Commit + push after every tested change set (user rule); commit messages end with the Co-Authored-By line.
- `CLAUDE.md` (binding): all user-facing text in Chinese (files for agents stay English); every new figure is sent into
  the chat with SendUserFile (`display: "render"`), paths only as a footnote.
- Cloud sessions work on a fresh clone, each on its own `claude/…` branch (last: `claude/brave-cannon-ci83tc`). The
  user brings it into local `main` through Antigravity (step 0 of each prompt: fast-forward merge, then push `main`)
  and runs anything that needs the real data, pasting results back.

## Key files
| File | What |
|---|---|
| `brain-plot/SKILL.md` | lean router + common workflow (inspect → interview → confirm → draw → QA) |
| `brain-plot/references/erp.md`, `microstate.md` | agent-facing module files: what to ask / never ask, stops, QA lists |
| `docs/rules.md` | the only rule list: S, L, K, E, T, O, MS (U = user rule, binding); developer reference, not read by the agent (split 2026-09-27) |
| `brain-plot/references/spec.md` | spec keys for plot / explore / microstate |
| `brain-plot/erp_plot.py`, `brain-plot/microstate_plot.py` | all computing and drawing |
| `docs/plan-2026-09-26.md`, `docs/plan-microstate.md` | agreed plans (the first one revised: no localizer) |
| `docs/plan-modules.md` | new modules: principle, round-1 decisions, paused round 2 |
| `docs/prompts/` | Antigravity prompts waiting to be run |
| `docs/archive/` | retired one-off plans (outdated paths) |
| `docs/review-log.md`, `docs/astra-review-*.md` | every change with its reason; external reviews |

## Example data and outputs
| Data | Outputs |
|---|---|
| Metaphor ERP `D:\1-python_datasets\metaphor production\derivatives\preprocessed_epochs` (60 subj, 6 conditions, WM groups) | `…\derivatives\brain-plot\` (N400 + P200/N300/LPC combo, erp ROI/grid, explore, microstate test); specs in `specs\` |
| Metaphor microstate test (10 random subj, v10 method, K 3–8) | `…\derivatives\microstate_test_n10\` (templates, GA, REPORT, specs incl. `states_k5_grid*.json`) |
| GN Go/NoGo `C:\Users\ASUS\Dropbox\metaphor_production\gn_manuscript\01-evokeds_grand_averages\evokeds_single_subject` (130 subj, v10 templates) | `…\01-evokeds_grand_averages\brain-plot\microstate\` (K5 states, GFP slide, by-K 3–9); specs in its `specs\`. Note: its `.cache` (77 MB) syncs to Dropbox |
| Resting test `D:\1-python_datasets\77_microstate\a_clean_2s` (pycrostates K = 4, 10 subj) | `…\77_microstate\pycrostates_k4_n10\`, figure `…\77_microstate\brain-plot\microstate\topo-by-K_K4_v02` |

## User decisions to respect (don't redo)
- Paper figures: condition names only in titles/legends, never N (L10, MS7d). No electrode marks on maps (L11).
  PNG + SVG only (T5). Fixed canvas from the spec (T6).
- ERP: no localizer; `windows`/`explore` stay optional. Explore: one 3 × 3 page, legend under the grid.
  Topo-only: block layout, 4-mm colour bar.
- Microstate: never stack more than 2 conditions (use `grid`); butterfly and GFP not both in a multi-column grid;
  panel width:height 1.8–3.5; no low-GFP hatching unless the spec says `hatch: true` (user saw K5 v06 without it and
  approved); resting-state figures beyond the template row are not wanted for now.
- Interview: always ask `claim` and `key_comparison` (they decide type, components, overlay, line pairing); never ask
  `time_locked_to`, `reference` (read from scripts, else omit), the display range (whole epoch), statistics, the
  figure's role, the journal (ask width), where a window comes from, or style (polarity, colours: house defaults unless
  the user asks). Everything that only feeds the caption is optional
  in the spec; unknown → leave it out, never "to be confirmed".
- The skill only draws: it does not judge the analysis (window choice, statistics, K choice). A script stop is only
  for things that change or break the drawing (data contract, layout, spec syntax).
- Figure QA stays about the figure: no reviewer-risk / manuscript-level checks (window justification, claim vs
  statistics, K choice) — user, 2026-09-26.
- New modules paused (user, 2026-09-27): only ERP and microstate for now.
- Local work stays with Antigravity (user, 2026-09-29): cloud subagents run in the cloud container and cannot reach
  the local data, the `mnedev` env or Arial, so they don't replace it.
- Rejected earlier: explore paging, right-hand legend column, topo "grid"/compact layouts, 8-mm colour bar, 89-mm
  waveform-only figure.

## Open
- Metaphor: `n400_spec.json` has no `time_locked_to`/`claim` any more (deleted 2026-09-26). Supplementary
  P200/N300/LPC reuse Pz, CPz. Repetition maps show red extremes at the left temporal edge (FT9/T7) — possibly a
  noisy channel; reported once, not acted on.
- Not supported (script stops): difference waves, lateralised components, CSD/source/TF, significance marks,
  > 7 overlaid lines.
- Codex's abandoned localizer lives in branch `codex/step3-localize-erp` (703f52a) and `git stash@{0}`; not merged.

## Known pitfalls
- Heredoc Python in Git Bash eats backslashes (`\n`, `\1`, `\b`): write patch scripts to a file, and
  still use the Edit tool for any replacement whose text contains a backslash (a script file mangled one on 2026-09-26).
- `codex exec` needs `--skip-git-repo-check` outside git repos; it failed with 401 / timeouts on 2026-09-26.
  agy (`C:/Users/ASUS/AppData/Local/agy/bin/agy.exe`, see the agy-delegate skill) worked for data tasks.
- Local work goes to Antigravity, not a local Claude session (user, 2026-09-27): the cloud session writes a
  self-contained prompt, the user runs it in Antigravity and pastes the result back. Claude quota is shared across
  sessions; a local Claude session doing a 308,887-file snapshot plus two progress monitors used it up in minutes.
  In prompts: no full-tree snapshots or monitors, read-only on data folders, write results to a named file.
- Cloud container: `api.crossref.org` and `mne.tools` are blocked by the network policy (WebSearch still works);
  Python packages are not preinstalled: `pip install "matplotlib<3.11" mne scipy pandas`, run tests with
  `MPLBACKEND=Agg`.
- `gh repo create --public` is blocked by the auto-mode classifier: the user runs outward-facing commands.
- Cloud container (Linux, matplotlib 3.11): `inside_canvas` fails with `FigureCanvasBase ... get_renderer`; use
  `matplotlib<3.11` + `MPLBACKEND=Agg`. Even then the ERP 2 × 2 grid (`test_erp_plot.py:181`) puts its "ms" label
  ~10 px past the right edge without Arial (also on unchanged code); on the Windows env both suites pass.
- Never fill `reference` / `time_locked_to` from memory: read the preprocessing script (metaphor: linked mastoids
  TP9/TP10, `scripts/preprocess_eeg.py:382`).
