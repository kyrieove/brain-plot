STATUS: done

Files changed:
- `brain-plot/cluster_plot.py` — `plot_columns()` row-label `fig.text`: x → `(left_m - 2.0) / 2.0 / W`, `ha="center"`, added `multialignment="center"` (kept `va="center"`, `fontsize=6`).
- `brain-plot/references/cluster.md` — interview round 2 (`layout`): added the sentence recommending `layout: "columns"` first as the approved house style and falling back to `"side"` for >3 tests or `channel_order: "file"`; code default stays `"side"`.

Syntax check: `python -m py_compile brain-plot/cluster_plot.py` → OK. `references/cluster.md` is Markdown (no compiler); no syntax check applied.

Could not do: nothing. Ran only the two step edits; did not run the Check, did not commit.