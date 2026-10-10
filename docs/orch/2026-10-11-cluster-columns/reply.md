STATUS: done

Files changed:
- `brain-plot/cluster_plot.py` — new `hemi_by_name()` helper (last char lower-cased: 1/2/z → Midline, other odd digit → Left, other even digit → Right); `channel_rows(..., mode="lmr")` now assigns by name with a fallback to the position rule (no channel dropped); docstring cites the MNE rule. `plot_columns()`: `sub_h = [1.2 * sum(len(gr)…)/len(groups)] * len(groups)` (equal sub-panel heights, total raster height unchanged).
- `brain-plot/test/test_cluster.py` — extra pure-name assertions in case (i) via `hemi_by_name`: FC1/C2/Fz → Midline, C3/TP9 → Left, C4/TP10 → Right (existing (i) assertion untouched).
- `brain-plot/references/cluster.md` — round-2 `channel_order` line, QA item 2 and QA item 7 now state the MNE `make_1020_channel_selections(midline="12z")` rule and equal-height sub-panels.
- `brain-plot/references/spec.md` — `channel_order` and `layout` rows updated likewise.

Syntax-only check: `python -m py_compile brain-plot/cluster_plot.py brain-plot/test/test_cluster.py` → exit 0 (`__pycache__/` is gitignored). Markdown files have no applicable syntax check.

Could not do:
- Did not run the Check (`python brain-plot/test/test_cluster.py`) — per instruction, the runner runs it.
- Did not run the docs/step-5 GN render — those steps are outside Fix 2 and the card says do exactly Fix 2.