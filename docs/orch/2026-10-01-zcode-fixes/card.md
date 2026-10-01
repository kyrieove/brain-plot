# zcode-fixes — zcode review A1, A3 and the OCR low finding

Paths relative to repo root `C:/dev/brain-plot`; run Python from `C:/dev/brain-plot/brain-plot`.

## Goal
- `evals/cases.md` trigger table matches the description: source maps (dSPM on fsaverage) load the skill; a truly
  unsupported source request does not; TFR and source each have a positive trigger case.
- `SKILL.md` points to the examples in a way that works when the skill is installed through a link.
- The STC time-axis check in `source_plot.py` stops with `ep.die` instead of an `assert`.

## Files
May change: `brain-plot/evals/cases.md`, `brain-plot/SKILL.md`, `brain-plot/source_plot.py`. Nothing else.

## Steps
1. `brain-plot/evals/cases.md`, trigger table: replace row 8
   `| 8 | 画源定位结果的脑图 | do not load (source data unsupported) |` with
   `| 8 | 我有自己做好的 .stc 文件（个体 MRI），直接画出来 | do not load (only dSPM on fsaverage from epochs is drawn) |`
   and add after it:
   `| 8a | 画 θ 频段的时频图和 ITC，Fz/Cz 的 ROI | load; TFR branch (`tfr_plot.py`) |`
   `| 8b | 用 dSPM 在 fsaverage 上画 N400 窗口的源定位脑图 | load; source branch (`source_plot.py`) |`
2. `brain-plot/SKILL.md`: replace
   "Worked specs: `../examples/specs/` (run `../examples/make_demo_data.py`\nfirst for synthetic data)." with
   "Worked specs: `examples/specs/` in the repository root, one level above this skill's real folder (the installed
   skill folder may be a link — resolve it first; run `examples/make_demo_data.py` there for synthetic data, or use
   the synthetic data the `test/` scripts build)."
3. `brain-plot/source_plot.py`: replace
   `assert np.allclose(stc.times, times_sub), "STC time axis differs from cached evoked times"` with
   ```python
            if not np.allclose(stc.times, times_sub):
                ep.die(f"subject {s_id}: STC time axis differs from the evoked time axis "
                       f"({len(stc.times)} vs {len(times_sub)} samples)")
   ```

## Check
```bash
cd C:/dev/brain-plot/brain-plot && python test/test_source.py
```
Prints `OK`.

## Don't
No commits; no other files; no other wording changes.

## Acceptance
Verdict: accepted (docs + 3-line code change; Claude read the diff, no codex review needed). test_source `OK`. agy 83 s.
Sources: zcode review (A1, A3; A2 left open) and open-code-review low finding (source_plot.py assert).
