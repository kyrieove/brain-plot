# brain-plot — handoff (2026-09-26, end of day)

Start of every new session: read this file, then `docs/review-log.md` (newest entries at the bottom).

## State
Two branches, both working, tests pass, everything committed and pushed
(https://github.com/kyrieove/brain-plot, public, branch `main`).
- **ERP** (`erp_plot.py`): `combo` (waveforms + maps per component), `topo` (maps only), `erp` (waveforms by channel:
  `roi` mean / `single` incl. `channels: "all"` / `grid`, gray bands only if asked), `explore` (3 × 3 overview +
  topomap table), `windows` (candidate windows, optional helper). The skill only draws — no localizer (user decision
  2026-09-26: windows come from the analysis).
- **Microstate** (`microstate_plot.py`, plan `docs/plan-microstate.md`, rules MS1–MS10): `figure: "states"` (template
  maps + butterfly or GFP + segmentation ribbon; ≤ 2 conditions stacked with maps left, more need `grid` with maps on
  top; one time-panel type per multi-column grid) and `"by-K"` (template rows across K, identity colours). Reads saved
  templates (npz `centers`, optional `ch_names`), never re-fits.
- Outputs (both branches, rules O1–O3): `brain-plot/` next to the data folder → `ERP/`, `topo/`, `ERP_topo/`,
  `microstate/`, `specs/`; names say what the figure is; re-renders get `_vNN+1`, old versions move to `_history/`.

## Next (start here)
Done on 2026-09-26 (details in `docs/review-log.md`, newest at the bottom): Lancet palette kept, T7 warns on normal
vision only; per-panel caption facts (S9); flat-channel stop with `flat_channels` (S10); GFP label clear of traces
(MS7c); reviewer-risk QA dropped (QA 6 = baseline visibility + dominated map scale only); caption fields optional
(local commit 29b50c7); interview: always ask `claim`/`key_comparison`, never ask `time_locked_to`/`reference`/display
range. Verified locally: both suites OK, GN K5 v05 and metaphor N400 v03 pass QA.

1. Sync first if the local clone is behind: `git fetch origin && git merge --ff-only origin/claude/bold-gates-u9nx46`
   (the cloud branch holds the latest doc-only commits; main = 29b50c7 until then).
2. Open question for the user (asked, not answered): interview round 2 still checks "whether the intended message fits
   the statistics" and says to flag a mismatch — at odds with "writing concerns are not the figure's". Drop it?
3. Metaphor N400 spec: `time_locked_to` is "TO BE CONFIRMED" → under the new rule read it from the scripts or delete
   the key (no question to the user); `claim` still marked to be confirmed.
4. Optional: round 7 review on the round-6 fixes (brief `docs/review-request-round6.md`); run `brain-plot/evals/cases.md`
   in fresh sessions (manual); `qa` of the metaphor v01 figures still PENDING (superseded versions may not need it).
5. Local commits show author `xburner23412`, not `kyrieove` — check `git config user.name/user.email` if unintended.

## Use
- Any session: `/brain-plot <data_dir>` (skill linked at `~/.claude/skills/brain-plot` → `C:\dev\brain-plot\brain-plot`).
- Python: `C:\Users\ASUS\miniconda3\envs\mnedev\python.exe` (conda env `mnedev`, MNE dev — pycrostates 0.6.1 was added
  with `--no-deps` on 2026-09-26; MNE untouched).
- Tests: `python brain-plot/test/test_erp_plot.py` and `python brain-plot/test/test_microstate.py` → both `OK`.
- Commit + push after every tested change set (user rule); commit messages end with the Co-Authored-By line.
- `CLAUDE.md`: all user-facing text in Chinese; files for agents stay English.
- Cloud sessions work on a fresh clone (branch `claude/bold-gates-u9nx46`); the user merges it locally and runs
  anything that needs the real data, pasting results back.

## Key files
| File | What |
|---|---|
| `brain-plot/SKILL.md` | workflow for any agent (ERP interview rounds; microstate section) |
| `brain-plot/references/rules.md` | the only rule list: S, L, K, E, T, O, MS (U = user rule, binding) |
| `brain-plot/references/spec.md` | spec keys for plot / explore / microstate |
| `brain-plot/erp_plot.py`, `brain-plot/microstate_plot.py` | all computing and drawing |
| `docs/plan-2026-09-26.md`, `docs/plan-microstate.md` | agreed plans (the first one revised: no localizer) |
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
  panel width:height 1.8–3.5; hatch low-GFP samples, no text note; resting-state figures beyond the template row are
  not wanted for now.
- Interview: always ask `claim` and `key_comparison` (they decide type, components, overlay, line pairing); never ask
  `time_locked_to`, `reference` (read from scripts, else omit) or the display range (whole epoch). All four stay optional
  in the spec.
- Figure QA stays about the figure: no reviewer-risk / manuscript-level checks (window justification, claim vs
  statistics, K choice) — user, 2026-09-26.
- Rejected earlier: explore paging, right-hand legend column, topo "grid"/compact layouts, 8-mm colour bar, 89-mm
  waveform-only figure.

## Open
- Metaphor: `time_locked_to` and the N400 `claim` still "to be confirmed". Supplementary P200/N300/LPC reuse Pz, CPz.
- Not supported (script stops): difference waves, lateralised components, CSD/source/TF, significance marks,
  > 7 overlaid lines.
- Codex's abandoned localizer lives in branch `codex/step3-localize-erp` (703f52a) and `git stash@{0}`; not merged.

## Known pitfalls
- Heredoc Python in Git Bash eats backslashes (`\n`, `\1`, `\b`): write patch scripts to a file with raw strings.
- `codex exec` needs `--skip-git-repo-check` outside git repos; it failed with 401 / timeouts on 2026-09-26.
  agy (`C:/Users/ASUS/AppData/Local/agy/bin/agy.exe`, see the agy-delegate skill) worked for data tasks.
- `gh repo create --public` is blocked by the auto-mode classifier: the user runs outward-facing commands.
- Cloud container (Linux, matplotlib 3.11): `inside_canvas` fails with `FigureCanvasBase ... get_renderer`; use
  `matplotlib<3.11` + `MPLBACKEND=Agg`. Even then the ERP 2 × 2 grid (`test_erp_plot.py:181`) puts its "ms" label
  ~10 px past the right edge without Arial (also on unchanged code); on the Windows env both suites pass.
- Never fill `reference` / `time_locked_to` from memory: read the preprocessing script (metaphor: linked mastoids
  TP9/TP10, `scripts/preprocess_eeg.py:382`).
