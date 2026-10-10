STATUS: done

Files changed:
- `brain-plot/cluster_plot.py` — Step 1：`time_axis.csv` 要求 `time_index,time_ms`，`channel_order.csv` 要求 `channel_index,channel`（:101、:104）；Step 2：`diff_uv` 新增局部 `sampled(ev, fname)`，A、B 两文件各自按名取道、各自取最近样本，旧的内联索引/取时块已删除（:203–226）；Step 3：`bins_of_times` 改为半开样本掩码、丢弃空箱、标签取箱内首末样本并四舍五入（:305–322），`raster_h = max(60.0, 1.5 * n_ch)`（:300），通道标签 `fontsize=4`（:358），topomap 标记 `markersize=1.2, markeredgewidth=0.25`（:394–395）。
- `brain-plot/test/test_cluster.py` — 新增 (f) 把某被试的 GO（B）文件通道倒序后 Cz 仍为 2.0±0.1 µV；(g) 去掉 `time_index` 的 `time_axis.csv` 触发停止；(h) 默认渲染的 SVG 含 `2–100 ms` 且不含 `2–102 ms`；原有 (a)–(e) 断言未改。
- Step 5 渲染输出（新增，放在数据文件夹旁的模块输出目录，未覆盖旧文件）：`C:\Users\ASUS\Dropbox\metaphor_production\gn_manuscript\03-ERP_topomap\03_cluster_inference\brain_plot_01_cluster_based_permutation_0000_0800ms\cluster\cluster_stat-masked_t01-t03_topo-bins100ms_v02` 的 `.png/.svg/_run.json/_caption.md`。

Could not do / not done:
- 按指示未运行 Check（`python brain-plot/test/test_cluster.py`），留给 runner 退出后执行。
- 真实 GN 渲染未打印任何 `WARNING: layout` 行，故未改动 Parameters（栅格高度/字号保持卡片值）。
- 两个改动文件已做语法检查（`python -m py_compile`）通过。

图：`C:\Users\ASUS\Dropbox\metaphor_production\gn_manuscript\03-ERP_topomap\03_cluster_inference\brain_plot_01_cluster_based_permutation_0000_0800ms\cluster\cluster_stat-masked_t01-t03_topo-bins100ms_v02.png`