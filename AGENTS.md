# Project rules (codex, agy)

- Talk to the user in Chinese, always (progress notes, questions, reports). Files for agents, code, comments and
  commit messages stay English.
- When a prompt hands you a task card or plan file, do exactly that and write only the files it names (code only
  when the file allows it). Do not commit, push or switch branches, and do not start other work.
- Otherwise, start of a session: read `HANDOFF.md` (the Next section), then the newest entries of `docs/review-log.md`.
- Every new figure: open it in the chat for the user; give its full path as a footnote.

## Map
- Skill router: `brain-plot/SKILL.md`; per-module docs: `brain-plot/references/*.md`; the only rule list: `docs/rules.md`.
- Run the test for the module you touched.
- Python = conda env `mne` (Python 3.12, MNE dev main; pyvistaqt pinned 0.12.0 — 0.13.1 renders black 3D screenshots). MNE needs a writable `~/.mne`; in a sandbox set `_MNE_FAKE_HOME_DIR` to a temp dir.

## Hard rules
- Reuse existing helpers in the module; never copy a block that already exists. Keep the house style
  (`docs/rules.md`) — e.g. ERP default negative up, cross axes.
- Subject data (`D:\…\derivatives\…`) is read-only. Outputs go to `brain_plot_<data folder>/` next to the data,
  never over an existing file (re-renders get `_vNN+1`).
- Leave no junk: temp profiles, caches and scratch files go to the system temp dir, not the repo root.
