仍有需要修复的一致性问题。已查看六张 PNG，输出记录的代码哈希均匹配当前脚本；未修改文件。完整回归因需要可写临时目录未运行，以下结合静态检查、只读测量及内存桩复现。

1. **P1：重画循环可能保存未通过检查的图。**  
   [erp_plot.py:687](/C:/dev/brain-plot/brain-plot/erp_plot.py:687)：最后一次重画后仍可执行 `v = peak`，使 L697 的检查失效；循环结束也不检查 `leg_ok`。内存桩已复现：图按色限 3 绘制，记录写成 4，图例碰撞仍进入保存。**最小修复：同轮处理色限和间隙更新；次数耗尽即停止；保存前检查实际绘制色限及 `leg_ok`。**

2. **P1：可选图例模式绕过了完整验收。**  
   [erp_plot.py:490](/C:/dev/brain-plot/brain-plot/erp_plot.py:490)、[erp_plot.py:545](/C:/dev/brain-plot/brain-plot/erp_plot.py:545)：`upper_left` 不预检灰带，重叠时 `legend_room()` 返回 `-inf`，扩轴最终报 NaN/Inf；`outside` 使用第二数据集的六个标签时，图例左端到 −26.5 mm，且压住 ROI 标题，仍返回成功。**最小修复：合并各模式的最终碰撞／画布边界检查；灰带阻挡时直接停止，禁止进入扩轴循环。**这些模式仍在 U/L7 中，不能当死选项删除。

3. **P2：球体没有兑现“不越过头圈”，20 次循环也多余。**  
   [erp_plot.py:499](/C:/dev/brain-plot/brain-plot/erp_plot.py:499)：固定原点时，当前 MNE 的投影坐标不随半径变化；循环实际只是在重复计算。更关键的是 [MNE topomap.py:808](/C:/Users/ASUS/miniconda3/envs/mnedev/Lib/site-packages/mne/viz/topomap.py:808) 会额外留出 1%。实测 N400 头圈半径 **104.182 mm**，着色裁剪半径 **105.223 mm**。**最小修复：一次计算投影半径，纳入这 1% 余量，并验证裁剪半径不大于头圈。**

4. **P2：“8 mm 间隙”实际为约 12.29 mm。**  
   [erp_plot.py:463](/C:/dev/brain-plot/brain-plot/erp_plot.py:463)：`gap` 是比例权重，另叠加 `wspace=0.06`；色条预留的 8 mm 又与实际权重不一致。180 mm 图中，两种布局的波形—地图列间距均实测约 12.29 mm。**最小修复：统一用毫米分配四列，设 `wspace=0`；[rules.md:26](/C:/dev/brain-plot/brain-plot/references/rules.md:26) 写明“默认 8 mm，L7 回退时加宽”。**

5. **P2：T1 有两处代码例外未写进规则。**  
   [erp_plot.py:353](/C:/dev/brain-plot/brain-plot/erp_plot.py:353)：`negative_up` 把 µV 放到轴底部，违反“顶部”。L370 的 `len(xt) <= 2` 又允许两个标签在未满足 3 pt 间距时退出。**最小修复：µV 始终用轴坐标顶部；删除“两标签免检”条件。**当前六张图未触发后者。

6. **P2：输出仍有“待确认”，却自动宣称“已确认”。**  
   [fig_N400_caption.md:3](</D:/1-python_datasets/metaphor production/derivatives/figures/brain-plot/fig_N400_caption.md:3>) 同一句同时出现 `confirmed with the author` 与 `to be confirmed`；L13 的时间锁定事件也未确认。四张第二数据集图均保留该事件占位。  
   [rules.md:49](/C:/dev/brain-plot/brain-plot/references/rules.md:49) 只检查已不再使用的 `NOT RECORDED`，漏掉现行占位词。**最小修复：QA 改查所有未确认科学字段；[erp_plot.py:724](/C:/dev/brain-plot/brain-plot/erp_plot.py:724) 删除自动附加的“已确认”断言，输出记录列明待确认项。**

7. **P3：现行说明还有旧布局残留。**  
   [exemplars.md:35](/C:/dev/brain-plot/research/exemplars.md:35)—L38 仍说采用面板内图例、带 n 标签、SEM 带，并在“不采用网格”后又说“保留网格”。**删除这些现行采纳声明，保留范例描述并指向 rules.md。**  
   [erp_plot.py:483](/C:/dev/brain-plot/brain-plot/erp_plot.py:483) 的“所有成分图统一图例位置”仅适用于 `right`，应缩小措辞；`side` 的 LPC 回退已明确按图决定。[rules.md:38](/C:/dev/brain-plot/brain-plot/references/rules.md:38) 的包络应改成“可见波形；仅 `error=sem` 时包含 SEM”。

8. **P3：输入契约文字未完全同步。**  
   [spec.md:9](/C:/dev/brain-plot/brain-plot/references/spec.md:9) 说 ID 截到首个 `_`／`-`，[erp_plot.py:103](/C:/dev/brain-plot/brain-plot/erp_plot.py:103) 还截 `.`；spec L11 未说明组件名忽略大小写判重。L22 的默认组顺序也未说明 `group_by` 实际按文件首次遇到的值排序。**最小修复：补齐这些现有行为的说明，避免隐含改变参考组。**

9. **P3：可直接删除／合并的代码。**  
   [erp_plot.py:51](/C:/dev/brain-plot/brain-plot/erp_plot.py:51) 的 `need_components=False` 无调用；L525 的 `idx`、L568 的 `col`、L721 的 `info` 参数未使用；L646/L651 的线条三元组第三项在移除 n 标签后已无人读取。**删除。**  
   [erp_plot.py:438](/C:/dev/brain-plot/brain-plot/erp_plot.py:438) 与 L470 为同一个单列图例建两张测量图；宽度留白又分散成 `+3`、`+5`。**合并为一次 bbox 测量和一处留白计算。**`legend_size` 前三项仍供内嵌模式使用，不是死字段。

10. **P3：测试没有真正覆盖新默认行为。**  
    [test_erp_plot.py:29](/C:/dev/brain-plot/brain-plot/test/test_erp_plot.py:29) 默认夹具仍强制 `upper_left`；L81 的 `side` 仅检查“不抛错”，没有图例存在、碰撞或加宽回退断言。**最小修复：把该用例改成省略 `legend` 的默认路径验证，并补上上述失败分支断言；保留明确测试旧模式的用例。**

- **delete**：无用参数／变量、线条 n 字段、范例中的旧采纳声明。
- **merge**：图例尺寸测量、最终碰撞验收、重画更新、毫米布局计算。
- **reword**：QA 占位检查、确认状态、`choose_corner` 范围、输入契约。
- **keep**：U 规则允许的图例选项、SEM 可选功能、`nice_ticks` 扩轴分支、现有数值／缓存测试、已标明归档的计划与历史日志。当前无 “Rectangle band” 残留；请求窗口与实际采样边界、无 n 标签和默认无误差带均已同步。