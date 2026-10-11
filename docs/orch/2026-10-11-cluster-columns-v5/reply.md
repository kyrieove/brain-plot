STATUS: done

Files changed (3):
- `brain-plot/cluster_plot.py` — step 1 `MARK_FRAC = 0.5` above `maps_of`, bins branch uses `t["mask"][m].mean(0) >= MARK_FRAC`, docstring updated; step 2 outline moved out of the `else` branch so both displays contour the significant region (guarded by `sig.any() and not sig.all()`), docstring updated; step 3 new `cluster_notes(t, cap=5)`; step 4 `notes`/`ann_h` added into `H` and `topo_top` and the per-column note `fig.text` loop after the raster loop; step 5 `write_caption` masked text and bins channel-marker wording.
- `brain-plot/references/cluster.md` — rule 5 white-dot wording for bins; new column rule 10 (cluster notes + masked outline).
- `brain-plot/test/test_cluster.py` — step 6 block (bins marker 3/5 vs 1/5, `cluster_notes` cap/format/p<0.001/no-cluster).

Step 6(c): no existing assertions in `test_cluster.py` relied on the old any-sample marking (or on the old caption wording) — searched, none updated.

Could not do: nothing. Card Check `python brain-plot/test/test_cluster.py` passed in the foreground with `OK` (exit 0), columns `layout_issues` empty; syntax-only `py_compile` on both Python files also passed. No commits made. (`AGENTS.md` shows as modified in `git status` but was already so before this session — not touched by me.)