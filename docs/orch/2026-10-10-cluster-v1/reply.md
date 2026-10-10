STATUS: done

Files changed:
- `brain-plot/cluster_plot.py:416` — stem now `cluster_{color}-{display}_{'-'.join('t' + n for n in nums)}_topo-{topo_part}` (leading numbers get a `t` prefix → `t01-t03`).
- `brain-plot/test/test_cluster.py:117` — expected fragment changed from `"-t01-t03_"` to `"_t01-t03_"`.

Fix 2 step 3 (re-read test_cluster.py after line 117 and `plot()` against Parameters / Step 5 asserts c–e): no other mismatch found. Verified the helpers `ep.sample_mask`/`x_ticks`/`lectter`/`interp_peak`/`common_sphere`/`text` exist with the used signatures, the bins/clusters map paths, colour scales, contour overlay and all four stop messages.

Syntax-only check: `python -m py_compile` on both changed files → OK. Did not run the Check.

Could not do: nothing — the Check is left to the runner as instructed.