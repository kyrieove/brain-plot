# Retro 2026-10-05 — brain-plot use in gn_manuscript (v17 microstate figures)

Source: one Claude Code session in `gn_manuscript` (v17 K=5 figures, v14 resume). Candidates, most severe first. Nothing implemented yet.

Re-assessed after user challenge ("are these fixes reasonable?"). Kept 2 of 5.

1. **Say what the ribbon is (caption).** `states` ribbons are a brain-plot back-fit (`min_segment_ms`), which is the right thing with templates only — and it matches the project's planned back-fit better than the clustering-stage labels. The failure was the agent reading a display ribbon as a result. Fix: `_caption.md` and `_run.json` state "ribbon = back-fit of the templates to the drawn GA, min_segment_ms = …". No `labels` input (YAGNI).
2. **Group × condition limit, stated where the agent looks (navigation).** One line in `references/microstate.md` "Read first": "groups are between-subject: group × condition → one `states` figure per group (`groups: [G]`)". Reword the two load errors (`subject IDs appear more than once`, `subjects missing a condition file`) to name that cause and that remedy.

Dropped:
- by-K colour limit: brain-plot already fails immediately; the 26 min was v14's own compute, and the K=2–20 range was the v14 spec's choice. Fix belongs in v14 (narrower K range). Colour reuse would break the fixed style.
- template/data match key: one agent error the interview already caught; a new spec key for it is speculative.

Environment findings outside brain-plot (gn_manuscript / orchestrate):
- interpreter: brain-plot `check_env` passes only with `C:/Users/ASUS/.conda/envs/hpm/python.exe` (the project's `py` env is 3.9) — cache this in the project HANDOFF.
- orchestrate runner `--fix` copies the whole may-change scope as a base; with a multi-GB, Dropbox-backed scope it crashed before the executor started. Use hashes/sizes for git-ignored or large scopes.
- `run-long` stale `.exit` on `--resume` — fixed 2026-10-05 (`D:/2/dev/orch-runner/docs/orch/2026-10-05-runlong-stale-exit/`).
- gn_manuscript HANDOFF says the new Codex binary is under `AppData/Local/OpenAI/Codex/bin/<hash>/codex.exe`; that binary rejects `gpt-6.1-sol`. The working one is `codex` on PATH (`C:/Users/ASUS/bin/codex`, 0.160.0). Stale line to prune.
