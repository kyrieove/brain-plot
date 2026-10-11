STATUS: done

Files changed:
- `brain-plot/cluster_plot.py` — added `stem_ids(slugs)` next to `bins_of_times` (returns each slug's leading digits; falls back to `[ep.safe(s) for s in slugs]` when any slug lacks leading digits or two ids collide). Used it at all three stem sites: `plot_side` (`..._t{ids[ti]}_topo-...`, `ids` computed once before the loop), `plot_columns` (`..._columns_t{'-t'.join(ids)}_..., ids = stem_ids([...])`), `plot_waves` (`cluster_waves_t{ids[ti]}`, `ids` once before the loop).
- `brain-plot/test/test_cluster.py` — added the step-3 `stem_ids` assertion block before `print("OK")`.

One existing assertion depended on the long names and I changed it (as permitted): the columns-layout check `assert "_columns_t01_" in oc.name and "-t03_" in oc.name` → `assert "_columns_t01-t03_" in oc.name` (the new columns stem is `..._columns_t01-t03_...`). The default-render assertions `"_t01_" in o01.name` / `"_t03_" in o03.name` were left unchanged and still pass.

One small deviation worth flagging: in `plot_side`/`plot_waves` the per-test loop index is named `ti` rather than `i`, because `plot_side` already uses `i` in the inner `for k, (_, i, g) in enumerate(rows)` loop, which runs before the stem line and would clobber an outer `i`. Indexing is still `ids[test_index]` for the i-th test; loops were not otherwise restructured.

Check: `python brain-plot/test/test_cluster.py` ran in the foreground and passed (`OK`, exit 0), with figure names short (`..._t01_topo-bins100ms_v01`, `..._columns_t01-t03_...`, `cluster_waves_t01_v01`). Syntax-only check (`python -m py_compile`) passed on both files before that. No commits. Nothing else I could not do.