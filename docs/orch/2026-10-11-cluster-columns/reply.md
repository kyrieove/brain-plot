STATUS: done

文件改动：`brain-plot/cluster_plot.py`（仅 `plot_columns()` 内三处数值）
- 顶部图行距 `map_mm + 7.0` → `map_mm + 11.0`（`H` 公式、`y_top`、`map_bar_h`）
- 光栅与顶部图之间的留白 `raster_block + 10.0 + 16.0` → `raster_block + 10.0 + 6.0`（`topo_top`、`H` 公式）
- 组名横向位置 `(left_m - 19.0) / W` → `(left_m - 12.0) / W`（`left_m = 30.0` 保持不变）

已对 `brain-plot/cluster_plot.py` 做仅语法检查（`python -m py_compile`，通过）。`plot_side` 未改动。

未做（按你的要求）：未跑 Check（`python brain-plot/test/test_cluster.py`），未按卡里 Fix 1 的 GN 重渲染，未提交。