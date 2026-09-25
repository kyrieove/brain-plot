# brain-plot — handoff (2026-09-26)

## State
`brain-plot` skill v1 is finished and in use. Four astra (gpt-6-astra) review rounds plus two real datasets; every
fix is logged in `docs/review-log.md`. Regression checks pass.

## Use
- In any session: `/brain-plot <data_dir>` (skill linked at `~/.claude/skills/brain-plot` → `C:\dev\brain-plot\brain-plot`).
- Flow: inspect data + read the study's notes → interview in rounds → confirm spec → `erp_plot.py plot` → visual QA
  → write `qa` into `_run.json`, report `open_items`.
- Python: conda env `mnedev` (`C:\Users\ASUS\miniconda3\envs\mnedev\python.exe`).
- Tests: `python brain-plot/test/test_erp_plot.py` → `OK`.
- Single-type figures: `kind: "erp"` (180 × 120 mm) or `"topo"` (block shape adapts to line and panel count, `topo_block`). User-chosen 2026-09-25.
- Before windows are known: `erp_plot.py explore <spec>` → 3 × 3 waveforms (F3 Fz F4 / C3 Cz C4 / P3 Pz P4, legend
  under the grid) + condition × component topomap table (global scale, optional difference maps). User-approved
  2026-09-25; example `...\figures\brain-plot\explore\v2.json`.

## Key files
| File | What |
|---|---|
| `brain-plot/SKILL.md` | workflow for any agent |
| `brain-plot/references/rules.md` | the only rule list (U = user rule, binding) |
| `brain-plot/references/spec.md` | spec keys |
| `brain-plot/erp_plot.py` | all computing and drawing |
| `brain-plot/test/fig_main.json` | example spec (synthetic paths, Go/NoGo layout) |
| `D:\1-python_datasets\metaphor production\derivatives\figures\brain-plot\` | N400 main + P200/N300/LPC supplementary (specs, PNG/PDF/SVG, `_run.json`) |
| `research/exemplars.md`, `research/erp-gallery.html` | design sources |
| `docs/astra-review-*.md`, `docs/review-log.md` | reviews and every change |

## Next (start here in the new session)
1. astra round 5 fixed 2026-09-26 (see `docs/review-log.md`). Round 6 review → `docs/astra-review-round6.md`;
   read it, show the user, fix.

## Rejected by the user (don't redo)
- Explore: core-channel page + 4/6/8/9 electrode pages (replaced by one 3 × 3); legend as a right-hand column.
- Topo-only: one row per panel ("grid" layout); compact centred layout (too cramped); 8 mm colour bar.
- Waveform-only at 89 mm width.

## Open
- Metaphor dataset: `time_locked_to` (which event is 0 ms) and the N400 `claim` still marked to be confirmed
  (user said no caption needed).
- Supplementary P200/N300/LPC reuse Pz, CPz; P200 is usually fronto-central — change if the user wants.
- Not supported in v1 (script stops): difference waves, lateralised components, CSD/source/TF, significance marks,
  > 7 overlaid lines.

## Known pitfalls
- Claude's Bash tool needs `BASH_ENV` (set in `~/.claude/settings.json`) to get `mnedev` as `python`; takes effect
  in new sessions. Otherwise call the full path.
- `codex` on PATH is a launcher for the newest desktop-bundled CLI (`~/bin/codex{,.cmd}`); MCP codex uses
  `cmd /c codex mcp-server`. astra review: `codex exec --skip-git-repo-check -m gpt-6-astra -c model_reasoning_effort=xhigh -s read-only -o <file> - < prompt` (the folder is not a git repo; without the flag codex exits at once).
- Never fill `reference` / `time_locked_to` from memory: read the preprocessing script (metaphor data: linked
  mastoids TP9/TP10, `scripts/preprocess_eeg.py:382`).
