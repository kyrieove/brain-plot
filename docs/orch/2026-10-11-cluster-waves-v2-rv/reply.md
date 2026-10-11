STATUS: done

Files changed:
- `brain-plot/cluster_plot.py` — steps 1–6: uv colour check skips waves layout; waves `peak_window_ms` window check against `times`; duplicate-channel check in `check_spec`; `write_caption` waves branch uses the user window; `waves_parts` body is one comprehension; `plot_waves` takes legend handles once (`axes[0]...`) after the loop.
- `brain-plot/test/test_cluster.py` — step 7: added the `(t)` waves review-fix asserts after the waves-stops block.

Syntax-only check passed on both files (`ast.parse`). No Check run, nothing committed, no other files touched.

Could not do: nothing blocked.