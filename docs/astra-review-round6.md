# Round 6 审查：brain-plot（2026-09-26）

范围：只读审查 `brain-plot/`、两份计划、round 5 记录与参考微状态算法；按 `yao-meta-skill` 的 audit mode 审查 skill 路由、评测及信任边界。未改动代码、规则或 skill。两份回归脚本在将 `_MNE_FAKE_HOME_DIR` 指向系统临时目录后均打印 `OK`；首次直接运行仅因本机 `~/.mne/mne-python.json` 无读取权限而在导入 MNE 时失败。

## Round 5 回查

| # | 状态 | 依据 |
|---|---|---|
| 1 窗口截断 | 已修 | `explore()` 对每个窗口检查数据范围与样本掩码；测试覆盖 350–500 ms 越界。 |
| 2 条件被 `zip` 截断 | 已修 | `explore()` 检查 ≤7 条线及颜色数量；测试覆盖七条件、两颜色。 |
| 3 topo 被波形图例阻断 | 已修 | topo 跳过图例准备；测试覆盖单组、末端窗口。 |
| 4 插值色阶溢出 | 已修 | `topo_table()` 读取插值图像峰值后扩大色阶并重画。 |
| 5 零差值图崩溃 | 已修 | 色阶下限 `1e-6`；测试覆盖 global/component。 |
| 6 固定画布文字越界/重叠 | 已修（现有用例） | 字母偏移改为固定点数，面板间距按 13 mm 计算；单面板、七面板测试通过。 |
| 7 分列色条越界、缺 µV | 已修（现有用例） | 色条偏移以 mm 计算，末端刻度带 µV；画布测试通过。 |
| 8 单类型 caption 虚构元素 | 已修 | `caption()` 按 kind 输出；erp/topo 测试分别检查。 |
| 9 规则与 QA 未分作用域 | 已修 | `rules.md` 的 Scope、K1/K2/E1–E3、按 kind 的 QA 已写明。 |
| 10 残留代码/说明 | 已修 | 旧无用绑定移除；`topo_block()` 和 spec 描述为自适应布局。 |

以上“已修”表示本轮静态核对及现有回归用例通过，不代表规则的所有输入边界已被测试覆盖；下面列出新发现。

## Part A：代码与规则审查

1. **P1 — 分条件目录会静默覆盖同一 subject ID 的文件。** `brain-plot/erp_plot.py:174–180`。具体输入：`A/G/s1_a-ave.fif`、`A/G/s1_b-ave.fif`，B 目录也有这两个文件；`split_layout()` 返回 G 组仅 **1** 人，且每个条件只保留字典中后写入的 `s1_b-ave.fif`。这改变样本量和均值，违反 S1/S8；现有测试只覆盖缺失文件。**最小修复：**在写入 `by[group][subject][condition]` 前检查键是否已存在，并报出两个冲突路径；增加重复 ID 回归用例。

2. **P1 — `by-K` 的时间窗口未校验，会静默截断。** `brain-plot/microstate_plot.py:370–380`。具体输入：数据仅到 800 ms，`figure: "by-K"`、`window_ms: [0, 1000]`；`sample_mask()` 只取得 0–800 ms，图仍可生成，caption 断言使用 `[0, 1000]`。`states` 分支在 220–223 行已有校验。**最小修复：**抽出并共用窗口范围和至少两采样点的预检；在 run 中记录实际采样边界，测试超界和空窗口。

3. **P1 — 零范数或非有限模板进入分割而不报错。** `brain-plot/microstate_plot.py:84–88`。具体输入：`centers_k02.npz` 的 `centers` 为 `np.zeros((2, n_channels))`；实测 `load_templates()` 返回全 `NaN`，`argmax()` 随后会把样本归到一个任意状态。模板含 `NaN` 也有同类问题。**最小修复：**归一化前检查所有数值有限、每张中心化地图范数大于 0，否则带文件名停止；增加测试。

4. **P2 — MS10 只检查第一块时间面板的宽高比。** `brain-plot/microstate_plot.py:276–281`。具体输入：现有测试的 `width_mm: 254`、`height_mm: 143`、两行、`blocks: ["topo", "butterfly", "gfp", "ribbon"]`；按 `layout()` 算，butterfly 为约 **110.8 × 55.3 mm = 2.00**，GFP 为约 **85.2 × 55.3 mm = 1.54**，违反 1.8 下限但测试通过。**最小修复：**对 `widths` 全部计算比例，推荐高度也要求全部通过；把该用例的两个比例纳入测试。

5. **P2 — ERP 网格的灰色窗口没有组件名。** `brain-plot/erp_plot.py:1024–1026`。具体输入：`kind: "erp"`、`layout: "grid"`、`components: [{"name":"N400","tmin_ms":350,"tmax_ms":500,"window_source":"a priori"}]`；每格只画灰带，未写 `N400`，而 L8 要求组件名在灰带上。**最小修复：**给网格窗口添加组件标签，并在多窗口/窄面板用例检查标签与画布边界。

6. **P2 — 仅 GFP 面板时接受 `ribbon` 却不画。** `brain-plot/microstate_plot.py:43–50,325–339`。具体输入：`blocks: ["topo", "gfp", "ribbon"]`；文件名和 spec 宣称有 ribbon，绘图分支只在 `p == "butterfly"` 时创建 ribbon。违反 MS6/MS8，属于误导输出。**最小修复：**若指定 `ribbon`，要求 `butterfly`；或在 GFP 下实现 ribbon，并为两种合法组合写检查。

7. **P2 — GFP 填色与低 GFP 斜线向下一个状态多取一个采样。** `brain-plot/microstate_plot.py:319–323`。具体输入：采样标签 `[S1,S1,S2,S2]`；第一段 `(a,b)=(0,2)` 使用 `t[a:b+1]`，连同 S2 的首采样按 S1 颜色填充；低 GFP 段同样如此。边界处显示状态与 `_run.json` 的标签不一致。**最小修复：**用区间边界或 step 型多边形构造不重叠的 `[a,b)` 填色/斜线；测试交界采样的颜色归属。

8. **P2 — 版本移动发生在新图成功保存前。** `brain-plot/erp_plot.py:137–149,925–927`、`brain-plot/microstate_plot.py:436–439`。具体输入：已有 `ERP-grid-…_v01`，再次绘制时给 `colors: ["not-a-color", …]`；`versioned()` 先把 v01 移进 `_history`，随后 Matplotlib 因非法颜色报错，当前目录没有新图。O2 的“新 render 才递增并归档旧版本”在失败时不成立。**最小修复：**先向临时前缀完成绘制、caption 和 run，全部成功后再分配版本并移动旧文件；加失败路径测试。

9. **P2 — 微状态 `grid` 可用一列绕过“不堆叠多条件”的规则。** `brain-plot/microstate_plot.py:59–63,234–246`。具体输入：六个条件，`grid: [["A"],["B"],["C"],["D"],["E"],["F"]]`；因提供了 grid 不触发“超过两行”报错，`C=1` 后仍把六行堆叠，违反 MS9 的“never stack six conditions”。**最小修复：**多于两条件时要求 grid 至少两列且检查行数上限/可读性；增加一列六行反例。

10. **P3 — 已撤销的 localizer 仍出现在输出规则。** `brain-plot/references/rules.md:62`。具体输入：代理按 O1 的 `localizer/`、`data_log.md` 去准备输出，尽管 `docs/plan-2026-09-26.md:3` 已明确取消内置 localizer 和 data log。代码不产生这些文件，但规则容易造成工作流漂移。**最小修复：**从当前 O1 删除这两个撤销项，或显式标为历史方案。

科学方法核对：ERP 的被试等权均值与被试内 ROI 均值路径符合 S2；微状态 `segment()` 的中心化、单位范数、signed/absolute 匹配及短段迭代合并，与 `signed_microstate.py:26–40,270–274,311–349` 和 `gen_fig_per_k_independent.py:96–105` 的核心方法一致。`display_order()` 依每行最长段的中位起止点排序，与参考图 `gen_fig_per_k_independent.py:108–151` 一致。发现 2、3 会使 caption 的窗口/分割方法陈述失真。测试空白主要是重复 subject ID、by-K 越界、退化模板、第二时间面板比例、GFP 边界和失败后版本状态。

## Part B：`yao-meta-skill` audit mode（只提发现与修复建议）

11. **P2 — trigger 缺少近邻排除语，路由质量未证实。** `brain-plot/SKILL.md:3`。具体输入：正例“画 ERP 波形图/头皮地形图/微状态图”，负例“对 ERP 做统计检验”“预处理 EEG 并重参考”；description 包含 ERP、组件和窗口等词，却没有明确“只绘图，不做统计或预处理”，可能被近邻请求触发。**最小修复：**在 description 的触发句中写清绘图动作及统计/预处理排除；用中英文正例、负例和混合请求做 trigger holdout。此为路由风险，尚无实测误触发率。

12. **P2 — 主执行骨架与微状态分支的路由次序不清。** `brain-plot/SKILL.md:8–10,24–29,77–82`。具体输入：“根据保存的微状态模板画 K=5 地图和 GFP”；开头说 `erp_plot.py` “does all computing and drawing”，随后先给 ERP 的 `inspect`/`plot` 路径，直到文末才引出 `microstate_plot.py`。代理可能用错 spec 或命令。**最小修复：**开头给一行判断：ERP waveform/topomap/combo/explore → `erp_plot.py`，保存模板的 microstate/by-K → `microstate_plot.py`；把“all”限定为 ERP 分支。

13. **P2 — 缺少 skill 级 trigger 和输出评测。** `brain-plot/SKILL.md:3,60–82`；现有 `brain-plot/test/` 只有脚本回归，无 `evals/`。具体输入：给代理“只要预处理 ERP”“用已有模板画 2×3 微状态图”“画 ERP 网格且窗口来源未定”三种请求，目前没有会在错误路由、跳过确认或未检查 PNG 时失败的 skill 评测。**最小修复：**先建立少量正/负/近邻 trigger case，以及用临时合成数据的输出 case，断言脚本选择、spec 确认、路径、QA 与禁止虚构统计结果；保留独立 holdout。脚本 `OK` 不能替代这些 agent 行为检查。

14. **P2 — 安装和执行的副作用边界未交代。** `brain-plot/SKILL.md:9–11,60–74`、`brain-plot/erp_plot.py:123–125,137–149,325–330`。具体输入：用户在共享 `derivatives/ev` 上第一次按 skill 运行 `plot`；脚本读取所有 FIF，并在相邻的 `derivatives/brain-plot/` 建缓存、图像和 run，后续重绘还会移动旧版本。入口只概述输出目录，未提示缓存、历史移动、运行依赖及使用可信本地副本。**最小修复：**在 skill 的执行前说明固定写入位置、`.cache`、`_history/`、所需 Python/MNE 环境和脚本来源；首次运行先展示即将使用的数据/spec/输出根。无需增加无关的权限流程。

15. **P2 — skill 的接口说明没有覆盖不同分支的关键差异。** `brain-plot/SKILL.md:49–53,77–82`、`brain-plot/references/spec.md:49–66`。具体输入：“我还不知道 ERP 窗口，先用 windows 看候选”若沿用 `kind: "erp"` 的 band spec（band 没有 `channels`），`windows()` 却按 `c["channels"]` 读取，报 `KeyError`；同时微状态不要求 ERP 的 `claim`/`key_comparison`，其确认步骤不同。**最小修复：**在 SKILL 的命令路由处注明 `windows` 需要带 ROI `channels` 的 combo/topo 组件搜索 spec，或让命令接受独立候选窗口格式；给 ERP、explore、microstate 各一个最小可运行 spec 链接/例子。此处是接口使用风险，脚本错误处理也可单独完善。

**结论：不建议签收 round 6；两套既有测试虽通过，仍有会静默改动样本或时间范围的 P1 问题，以及未被覆盖的布局与 skill 路由风险。**
