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
- Subject inputs are `*-epo.fif`, `*-ave.fif` or epoched EEGLAB `*.set` (+ `.fdt`). Read them only through `erp_plot.read_epochs_any`,
  `read_info_any` and `is_epochs`; never call `mne.read_epochs` / `mne.io.read_info` on a subject file. For `.set` the condition is the
  event at latency 0 (MNE joins multi-event epochs as `a/b`), and baseline / filter are `None` (captions say "not recorded").
- `cluster_plot.py` reads a run folder; `brain-plot/besa_to_run.py convert` builds one from a BESA Statistics result (test: `test/test_besa.py`).
- `brain-plot/test/data/eeglab/` holds real EEGLAB-authored fixtures: read-only; regenerate with `make_eeglab_fixture.m`
  (`D:\1\application\matlab_eeglab\bin\matlab.exe -batch "run('<path>')"`, EEGLAB in `D:\1\application\eeglab\eeglab2025.0.0`).
- Python = conda env `mne` (Python 3.12, MNE dev main; pyvistaqt pinned 0.12.0 — 0.13.1 renders black 3D screenshots). MNE needs a writable `~/.mne`; in a sandbox set `_MNE_FAKE_HOME_DIR` to a temp dir.

## Hard rules
- Reuse existing helpers in the module; never copy a block that already exists. Keep the house style
  (`docs/rules.md`) — e.g. ERP default negative up, cross axes.
- Subject data (`D:\…\derivatives\…`) is read-only. Outputs go to `brain_plot_<data folder>/` next to the data,
  never over an existing file (re-renders get `_vNN+1`).
- Leave no junk: temp profiles, caches and scratch files go to the system temp dir, not the repo root.
