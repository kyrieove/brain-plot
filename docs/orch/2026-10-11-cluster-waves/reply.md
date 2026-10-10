STATUS: done

Files changed:
- `brain-plot/cluster_plot.py` — Fix 1 applied:
  - `bottom_m` 12 → 18 mm (drives both the `H` formula and the legend anchor); `cluster_plot.py:782`
  - removed the per-axes `ax.legend(...)`; the first row now keeps its two line handles; `cluster_plot.py:826`
  - added one `fig.legend(handles, [a, b], ncol=2, frameon=False, fontsize=5, loc="upper center", bbox_to_anchor=((wave_x + wave_w / 2) / W, (bottom_m - 8.0) / H))` after all rows are drawn; `cluster_plot.py:835`

Syntax-only check: `python -m py_compile brain-plot/cluster_plot.py` → pass.

Could not do / skipped by instruction: the Check (`python brain-plot/test/test_cluster.py`) and the step-5 GN re-render were not run — the runner runs the Check after exit. No commit made.