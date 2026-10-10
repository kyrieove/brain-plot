STATUS: done

改动文件（4 个）：
- `brain-plot/cluster_plot.py` — `OPTIONAL`/`check_spec` 新增 `channel_order`（"lmr" | "file"，其他值报错）；新增 `channel_rows()`；`plot()` 改成每个 test 一张图（栅格在左、2 列 topomap 网格在右，行按 左/中/右 分组、组间空行+组名、隔一个通道才标标签）；`write_run_json`/`write_caption` 改为单 test。
- `brain-plot/test/test_cluster.py` — 断言改为每个 test 一张图（`_t01_`、`_t03_`，每图 `layout_issues == []`）；新增 (i) `channel_rows` 分组/顺序断言、(ii) `channel_order: "file"` 渲染、(iii) 非法 `channel_order` 报错。
- `brain-plot/references/cluster.md`、`brain-plot/references/spec.md` — 每 test 一张图、`channel_order`、新命名模式、QA 条目。

已做：step 5 第二步的 GN 渲染（`01`、`03`，spec 写在系统临时目录），两次都无 `WARNING: layout`，两图 `layout_issues` 均为 `[]`。新图路径：
- `C:/Users/ASUS/Dropbox/metaphor_production/gn_manuscript/03-ERP_topomap/03_cluster_inference/brain_plot_01_cluster_based_permutation_0000_0800ms/cluster/cluster_stat-masked_t01_topo-bins100ms_v01.png`
- `.../cluster_stat-masked_t03_topo-bins100ms_v01.png`

语法检查：`python -m py_compile brain-plot/cluster_plot.py brain-plot/test/test_cluster.py` → 通过（`references/*.md` 是 Markdown，无对应语法检查命令）。

未能做：按你的要求**没有运行 Check**（`python brain-plot/test/test_cluster.py`，留给 runner）。未提交。