VERDICT: FAIL

- [cluster_plot.py](/C:/dev/brain-plot/brain-plot/cluster_plot.py:215)：µV 差值按 A 条件文件的通道索引和时间采样索引读取 B 文件，且未核对 B 文件的通道与时间轴。若两文件顺序或采样不同，会静默产生错误差值。为 B 文件独立按通道名取序，并按结果时间匹配采样；不匹配时停止。
- [cluster_plot.py](/C:/dev/brain-plot/brain-plot/cluster_plot.py:101)：任务卡要求 `time_axis.csv` 包含 `time_index,time_ms`、`channel_order.csv` 包含 `channel_index,channel`，实现只检查后者各自的名称列。缺少索引列的输入会被接受。将两列也加入必需列检查。
- Bloat：未发现新增的重复 helper、单次使用抽象、死代码或未要求的选项。

预先存在问题：此前未提交改动无法从当前工作树差异中单独归因；未将它们列为本次发现。