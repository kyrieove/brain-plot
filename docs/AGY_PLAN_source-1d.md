# AGY PLAN source-1d: blank brains after the first map

Same boundaries and allowed files as `C:\dev\brain-plot\docs\AGY_PLAN_source-1.md`.
Progress: append to `C:\dev\brain-plot\AGY_PROGRESS_source.md`, first line `[░░░] 0/3 blank-render fix start · HH:MM`.

Defect (Claude, looking at `…\brain_plot_preprocessed_epochs_verb\source\source-timeline_dSPM_lock-verbonset_v03.png`):
only the first L/R pair (Metaphor (high), 100 ms) shows a brain; all 94 other images are pure white. `layout_issues`
is empty, so nothing caught it. It started with PLAN 1b (remove_data / show=False / the try-except around add_data).
Also: the `except ValueError` fallback to `transparent=True` silently changes the look — remove it; if `add_data`
fails, let it raise. Remove any hand-edited colour table (`b._data["ctable"]`) unless it is the only way to get the
hard threshold; if you keep it, say why in a comment.

## Steps (N = 3)
1. Find the cause (e.g. screenshot of a Brain whose data layer was removed, a render window of size 0 after the
   first screenshot, offscreen state) and fix it so that every map is rendered. Simplest robust option if needed:
   one fresh `Brain` per image (slower is acceptable), closed right after its screenshot.
2. New self-check in `source_plot.py`: every screenshot must contain cortex — at least 20 % of its pixels non-white
   before trimming; otherwise stop with `ep.die("blank brain image: <figure> <row> <column> <hemi>")`. Record
   `render_check: "ok"` in `_run.json`. Test in `test_source.py`: a figure with ≥ 3 rows × ≥ 2 columns — every
   image passes the check (the check itself must be exercised: monkeypatch one screenshot to white → the script stops).
   All five suites `OK`.
3. Re-run the real timeline spec. Then open the PNG yourself and confirm every cell shows a brain. Report the path.

## Reply (≤ 6 lines)
