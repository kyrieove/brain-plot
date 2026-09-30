# brain-plot — handoff (2026-09-30, end of day)

Start of every new session: read this file, then `docs/review-log.md` (newest entries at the bottom).

## State
Two branches, both working, tests pass, everything committed and pushed
(https://github.com/kyrieove/brain-plot, public, branch `main`).
- **ERP** (`erp_plot.py`): `combo` (waveforms + maps per component), `topo` (maps only), `erp` (waveforms by channel:
  `roi` mean / `single` incl. `channels: "all"` / `grid`, gray bands only if asked), `explore` (3 × 3 overview +
  topomap table), `windows` (candidate windows, optional helper). The skill only draws — no localizer (user decision
  2026-09-26: windows come from the analysis). Every waveform figure takes `axes: "cross"` (default) or `"box"`.
- **Microstate** (`microstate_plot.py`, plan `docs/plan-microstate.md`, rules MS1–MS10): `figure: "states"` (template
  maps + butterfly or GFP + segmentation ribbon; ≤ 2 conditions stacked with maps left, more need `grid` with maps on
  top; one time-panel type per multi-column grid) and `"by-K"` (template rows across K, identity colours). Reads saved
  templates (npz `centers`, optional `ch_names`), never re-fits.
- Outputs (both branches, rules O1–O3): `brain-plot/` next to the data folder → `ERP/`, `topo/`, `ERP_topo/`,
  `microstate/`, `specs/`; names say what the figure is; re-renders get `_vNN+1`, old versions move to `_history/`.

## Next (start here)
- 2026-09-30 afternoon (local, branch **`tfr`**, NOT pushed, not merged — user: "暂不推送"): **time-frequency module**.
  Plan agreed with the user via /grilling. Roles: Claude plans + reviews, codex (gpt-6-luna, max) = literature,
  agy = implementation. Done:
  1. Survey `research/tfr/survey.md` (12 papers, all DOIs checked on Crossref, 3 figures opened and checked; the other
     rows are text-only hints). Chosen layout: ROI TF maps in a condition grid per group + optional band × window
     topomap rows, one colour bar at the right; dB (logratio), baseline −500…−200 ms (literature default).
  2. New verb-locked epochs (S15–20, −1…2 s, 0.1–45 Hz, AutoReject local after ICA, else = `scripts/preprocess_eeg.py`)
     in `D:\…\metaphor production\derivatives\preprocessed_epochs_verb\` (script in `_code\`, resumable). First pass
     lost 8 subjects to out-of-memory (AutoReject `n_jobs=-1` = 16 workers on 15 GB); `n_jobs` set to 2; a background
     chain (`chain.sh` in the session scratchpad) reruns the failures, then re-renders both TFR specs with all subjects.
     Done: all 60 subjects (second pass 0 failures). TFR figures re-rendered with all subjects: power v06, ITC v04
     (HWM 29, LWM 30); sub27 excluded in both specs (acc is 3 on every trial in the xlsx → no `acc == 1` trials).
  3. `brain-plot/tfr_plot.py` + `test/test_tfr.py` + `references/tfr.md` + spec/rules/SKILL entries (commits `f824a9d`,
     `f689321`); suites erp/layout/tfr OK. Real data specs `…\brain-plot\specs\tfr_verb_power.json`, `tfr_verb_itc.json`
     (ROI Fz, Cz — FCz is not in the data; query `acc == 1`; theta 4–8 Hz 200–500 ms window as a demo).
  **Open for the user:** (a) all conditions show a strong phase-locked event ~400 ms BEFORE the verb marker (ITC up to
  0.78, broadband stripe in power) — inside the baseline window; an untriggered display onset or a marker delay? The
  baseline may need to move once the user says what happens there. (b) ROI / windows of the demo figures are
  placeholders, not analysis choices. (c) Merge `tfr` into `main` and push only after the user has seen the figures.
  Cost note: agy used 1.2 M (preprocessing), 4.6 M + 7.1 M (TFR module + 2 fixes, mostly waiting on tests) tokens;
  codex 0.76 M (first run failed on image downloads — give codex text-only tasks).
- 2026-09-30 (local, all on `main`, pushed; last commit `501553f`; three suites OK on Windows):
  1. Fast-forwarded local `main` to `origin/main` (inset layout from the cloud); the old uncommitted local
     `erp_plot.py` change (explore topo-table tweaks) merged cleanly — the 2026-09-29 "commit before pulling" note is done.
  2. **Inset combo revised with the user** on the metaphor N400 figure A (v02–v17; v17 accepted, "先这样"): no gray
     band (name in the title `N400 · Pz, CPz`), no window text, one colour bar at the figure's right edge, maps at the
     lower right as large as fits (≤ 27 % of the panel width; the y-range grows down ≤ 2×; planner tries sizes largest
     first), square panels, map labels 5 pt. Rules L12/L13 rewritten. Commit `6ec961c`.
  3. **ERP line colours = Lancet** (ggsci, in order, any line count; rule T3), same family as microstate.
  4. **`axes: "box"`** (left + bottom axes, outward ticks, `Time (ms)` / `Amplitude (µV)`, 0-µV line, dotted 0-ms
     line) for every ERP waveform figure: combo side/inset, erp roi/single/grid, explore (grid: titles on the outer
     panels only). Implemented by agy from Claude's PLAN (~20 min, 2.26 M tokens, mostly waiting for tests); two
     defects found in review and fixed (missing 0 tick; legend over outside tick labels → `obstacles_of` uses tight
     boxes). User: "还不错 先这样". Commits `b1d9add`, `501553f`.
  Real-data specs added in `…\derivatives\brain-plot\specs\`: `n400_inset_2x3.json` (inset, cross) and `*_box.json`
  (inset v19, side combo v09, ERP grid 3×3 v01). Open: inset figure B (panels = groups, six lines) still stops, not
  re-tried; README figures not redrawn with the new colours / inset / box. Nothing pending; next = the user's pick.
- 2026-09-29 end of day (cloud; merged to `main`): **ERP combo, maps inside the waveforms** (`map_placement: "inset"`
  + `grid`, rules L12/L13, `docs/review-log.md` last entries). Built with the user over five rounds on synthetic
  figures; layout rules: maps of a panel in one row (never two stacked), colour bar 0.9 mm right of or under the maps,
  nothing over the gray band / curves / axes / texts, spacing between panels tightens when the block does not fit,
  `inset_audit` in `_run.json`, independent geometry test; suites OK in DejaVu and in Liberation Sans (Arial metrics).
  Lesson (user): new layout behaviour goes into rules and self-checks, not one complaint at a time.
  Real-data run (local agent, Antigravity, worktree of the branch at `4811d80`, metaphor N400, `n400_spec.json` as base;
  RESULT.md in `C:\dev\brain-plot-inset-results\`): 3 suites OK on Windows. **Figure A** (2 × 3 design: `overlay:
  "groups"`, `grid` Hmet Hlit Hrep / Lmet Llit Lrep, no colors/linestyles): drawn, 180 × 120 mm, two maps side by side
  (7.0 mm) with the colour bar under them, tier 0, audit 30 parts / 0 clashes, layout_issues empty; the agent judged it
  clean — **the user looked at it and found problems (not yet listed)**. **Figure B** (accepted N400 layout, panels = 2
  groups, six lines each, `colors`/`linestyles` kept): the script stops ("no free place for 6 maps in one row … panels
  tried 74 × 51, 79 × 54 mm"): map labels like "Repetition (high)" are ~18 mm wide, three columns need panels ≳ 90 mm.
  Idea, not done: wrap long map labels at the space (two lines, column ~10 mm) so B fits. Other open points: README
  figures not redrawn; side layout untouched.
- 2026-09-29 (cloud, branch `claude/loving-johnson-7x5qrn`): full draw + QA run with the split skill on the synthetic
  demo (microstate K4): PNG and `qa` steps exercised, both files read fine. It showed the butterfly "GFP" label sitting
  on a boundary line; a placement fix and its code-review follow-ups were written, then the user dropped the label
  altogether ("GFP 这个不要了"): butterfly panels carry no "GFP" text (MS7c), the caption facts say "thick line = GFP",
  the placement code and its tests are deleted (details and what is superseded: `docs/review-log.md`, last two
  entries). Three suites OK in the cloud. Open: README image `docs/images/example-microstate-butterfly.png` (real
  metaphor data) still shows the old "GFP" labels — re-render locally. Next: the user is studying how to extend
  brain-plot; nothing is pending from the cloud side (new modules stay paused, see below).
- 2026-09-27 (cloud, branch `claude/brave-cannon-ci83tc`): new modules (PSD, TFR, cluster/raster, MVPA) paused by
  the user; round-2 questions stay unanswered in `docs/plan-modules.md` (agy's literature survey failed a spot-check:
  don't cite its cluster counts). Rules split done: lean `SKILL.md`, agent-facing `references/erp.md` and
  `references/microstate.md`, full table moved to `docs/rules.md` (developer reference). Verified locally
  (Antigravity): three suites OK on Windows, dry-run interviews for eval cases 9/10 pass; local `main` = `daf4662`,
  pushed. Not yet exercised on real data: a full run (draw + QA) with the split skill — optional next step.
- 2026-09-26 (cloud, late): independent audit fixed — layout self-check (`layout_issues`), min panel height and y-tick
  spacing, µV headroom, grid band/title, polarity-insensitive identity, subset file names (LOADER_VERSION 4: the
  first run per dataset re-reads the files), microstate default heights, cache pruning, `check_env.py`, new
  `test/test_layout.py` (table at the end of the review log). test_layout's range-omission case made
  font-independent after it failed under Arial (8bcbf7e). Verified locally by the user: three suites OK on Windows
  (mnedev, Arial), metaphor N400 and GN K5 re-rendered and checked.
State at end of 2026-09-26: local `main` = GitHub `main` = cloud branch `claude/bold-gates-u9nx46` = `8bcbf7e` (plus this
handoff). Three suites OK on Windows (matplotlib 3.10, Arial) and in the cloud (matplotlib 3.10/3.11, DejaVu Sans).
Tests whose outcome depends on text width must hold in both fonts (Arial on Windows, DejaVu in the cloud).

Done today (details in `docs/review-log.md`, newest at the bottom):
- Palette: Lancet kept; T7 warns on normal vision only, compares colour + line style, strict JSON (no Infinity).
- Captions: `## Whole figure` + `## Panels` by drawn letters (S9); every caption-only field optional.
- Loader: flat-channel stop with `flat_channels` (S10); BIDS subject IDs; `inspect` covers every input layout.
- Interview: always ask `claim` / `key_comparison` (they decide type, components, overlay, line pairing); never ask
  time-locking, reference, display range (whole epoch), polarity or colours. Reviewer-risk QA dropped (user: writing
  concerns, not figure concerns); QA 6 = baseline visibility + dominated map scale.
- Microstate: GFP label clear of traces (MS7c; the label itself was dropped 2026-09-29); hatching opt-in; unique condition labels; one boundary definition
  (half-way between samples) for ribbon, dotted lines, spans and caption; template md5 + channel-order note; MS4 text
  matches the code (checked on 9 real specs).
- Sharing: README (en + zh-CN) with the user's metaphor figures, `examples/` synthetic install check,
  `requirements.txt`, spec-relative paths. Repo stays public; classmates get the GitHub link. `CLAUDE.md` stays as is
  (user decision).
- Latest accepted renders: metaphor N400 v04, GN K5 v07 (boundaries 1 ms earlier than v06, numbering unchanged).

Nothing is waiting on the user. Optional:
1. `hatch: true`: ribbon S# labels are hard to read over the hatching.
2. GN templates `centers_k05.npz` have no `ch_names` → warning on every run; re-export them with `ch_names` upstream.
3. Run `brain-plot/evals/cases.md` in fresh sessions (manual); optional round 7 review.
4. External audit (`docs/`, commit c6eee87): items not taken are listed in the review log (user decisions / out of
   scope) — don't redo them.
5. Local commits show author `xburner23412`, not `kyrieove` — check `git config user.name/user.email` if unintended.

## Use
- Any session: `/brain-plot <data_dir>` (skill linked at `~/.claude/skills/brain-plot` → `C:\dev\brain-plot\brain-plot`).
- Python: `C:\Users\ASUS\miniconda3\envs\mnedev\python.exe` (conda env `mnedev`, MNE dev — pycrostates 0.6.1 was added
  with `--no-deps` on 2026-09-26; MNE untouched).
- Tests: `python brain-plot/test/test_erp_plot.py` and `python brain-plot/test/test_microstate.py` → both `OK`.
- Commit + push after every tested change set (user rule); commit messages end with the Co-Authored-By line.
- `CLAUDE.md` (binding): all user-facing text in Chinese (files for agents stay English); every new figure is sent into
  the chat with SendUserFile (`display: "render"`), paths only as a footnote.
- Cloud sessions work on a fresh clone (branch `claude/bold-gates-u9nx46`); the user merges it locally and runs
  anything that needs the real data, pasting results back. After local commits, the local agent fast-forwards the cloud
  branch itself (`git push origin main:claude/bold-gates-u9nx46`, only if it is an ancestor of main) — don't ask the
  user to do it.

## Key files
| File | What |
|---|---|
| `brain-plot/SKILL.md` | lean router + common workflow (inspect → interview → confirm → draw → QA) |
| `brain-plot/references/erp.md`, `microstate.md` | agent-facing module files: what to ask / never ask, stops, QA lists |
| `docs/rules.md` | the only rule list: S, L, K, E, T, O, MS (U = user rule, binding); developer reference, not read by the agent (split 2026-09-27) |
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
- ERP inset layout (2026-09-29): several combos in ONE figure in a grid (never a figure per panel, never only stacked
  1–2 panels); colour bar belongs to each map block, 0.9 mm wide; nothing of a map block may overlap the gray band,
  curves, axes or texts — enforced by the planner and a self-check, stop instead of shipping an overlap (L13); two maps are
  never stacked; a block that does not fit → tighter spacing between panels first (user: "自适应调整子图之间的间距").
- Paper figures: condition names only in titles/legends, never N (L10, MS7d). No electrode marks on maps (L11).
  PNG + SVG only (T5). Fixed canvas from the spec (T6).
- ERP: no localizer; `windows`/`explore` stay optional. Explore: one 3 × 3 page, legend under the grid.
  Topo-only: block layout, 4-mm colour bar.
- Microstate: no "GFP" text label on butterfly panels (user, 2026-09-29; the caption names the thick line); never stack more than 2 conditions (use `grid`); butterfly and GFP not both in a multi-column grid;
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
- Cloud can mimic the Windows font: Liberation Sans has Arial's metrics. Run every suite twice before pushing a layout
  change, once as is (DejaVu) and once through a wrapper that sets `erp_plot.STYLE["font.sans-serif"] = ["Liberation Sans"]`
  before `runpy`-ing the test file (2026-09-29: the "3 panels in a row need tighter spacing" assertion held only in DejaVu;
  it now scans widths, because where the switch happens depends on the font).
- Heredoc Python in Git Bash eats backslashes (`\n`, `\1`, `\b`): write patch scripts to a file, and
  still use the Edit tool for any replacement whose text contains a backslash (a script file mangled one on 2026-09-26).
- `codex exec` needs `--skip-git-repo-check` outside git repos; it failed with 401 / timeouts on 2026-09-26.
  agy (`C:/Users/ASUS/AppData/Local/agy/bin/agy.exe`, see the agy-delegate skill) worked for data tasks.
- Local work goes to Antigravity, not a local Claude session (user, 2026-09-27): the cloud session writes a
  self-contained prompt, the user runs it in Antigravity and pastes the result back. Claude quota is shared across
  sessions; a local Claude session doing a 308,887-file snapshot plus two progress monitors used it up in minutes.
  In prompts: no full-tree snapshots or monitors, read-only on data folders, write results to a named file.
- `gh repo create --public` is blocked by the auto-mode classifier: the user runs outward-facing commands.
- Cloud container (Linux, matplotlib 3.11): `inside_canvas` fails with `FigureCanvasBase ... get_renderer`; use
  `matplotlib<3.11` + `MPLBACKEND=Agg`. Even then the ERP 2 × 2 grid (`test_erp_plot.py:181`) puts its "ms" label
  ~10 px past the right edge without Arial (also on unchanged code); on the Windows env both suites pass.
- Never fill `reference` / `time_locked_to` from memory: read the preprocessing script (metaphor: linked mastoids
  TP9/TP10, `scripts/preprocess_eeg.py:382`).
