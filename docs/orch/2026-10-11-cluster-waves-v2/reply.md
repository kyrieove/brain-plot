STATUS: done

Files changed:
- `brain-plot/cluster_plot.py` — `waves_parts` 改为 1 块单列、2–6 块双列、每部分最多 6 块（奇数块落在左列）；同步 `plot_waves` 的说明文字。`plot_waves` 的两列奇数块摆放、整幅色条、`ceil(k/2)` 行高原代码已满足 Fix 1 第 2 步，无需改动。
- `brain-plot/test/test_cluster.py` — `waves_parts` 断言更新为 1→(1,1)、2→(2,2)、3→(3,2)、4→(4,2)、6→(6,2)、7→(6,2),(1,1)、13→(6,2),(6,2),(1,1)。
- `brain-plot/references/cluster.md`、`brain-plot/references/spec.md`、`docs/plan-waves-v2.md` — 把 “1–3 单列、4–6 双列” 改为 “1 块单列、2–6 块双列（三簇 = 2 + 1）、多于 6 拆成每部分 6 块”。

无法完成/未做：无。未运行 Check，未提交。

语法检查：`python -m py_compile brain-plot/cluster_plot.py brain-plot/test/test_cluster.py` → exit 0；改动仅两个 `.py` 文件（其余为 `.md`）。