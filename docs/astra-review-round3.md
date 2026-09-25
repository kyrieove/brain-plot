已查看两张 PNG，全程未修改项目文件。**指定回归脚本已尝试运行，但只读沙箱禁止创建临时目录，完整回归未完成；其中纯数值断言已单独通过。** 93 份输入文件的大小、修改时间及当前代码哈希均与运行记录一致。

**A. Round-2 复核**

| 项目 | 判定 | 证据及剩余 |
|---|---|---|
| B1 输入语义 | 已解决 | 显式 `proj=False`，拒绝重复 comment、非 average、未应用投影及无效单位／坐标。[erp_plot.py:127](C:/dev/brain-plot/brain-plot/erp_plot.py:127)、[189](C:/dev/brain-plot/brain-plot/erp_plot.py:189)。 |
| B2 规格校验 | 已解决 | 原列的重复／空 ROI、空必要文本、非有限窗口、窗口超出显示范围均已拦截；全部成分先预检。[erp_plot.py:65](C:/dev/brain-plot/brain-plot/erp_plot.py:65)、[477](C:/dev/brain-plot/brain-plot/erp_plot.py:477)。 |
| B3 输出覆盖 | 部分解决 | 点号和完全重名已处理，但 Windows 大小写碰撞仍存在，见下文。[erp_plot.py:69](C:/dev/brain-plot/brain-plot/erp_plot.py:69)、[505](C:/dev/brain-plot/brain-plot/erp_plot.py:505)。 |
| B4 碰撞／裁切 | 已解决 | 两张 PNG 的末端刻度已避开曲线／SEM，色标单位完整；180 × 110 mm，绑定布局保留。[erp_plot.py:299](C:/dev/brain-plot/brain-plot/erp_plot.py:299)、[382](C:/dev/brain-plot/brain-plot/erp_plot.py:382)。 |
| B5 投影／饱和 | 部分解决 | sphere 已明确记录，插值超限会扩色限；但保留了允许 ≤2% 超限的缺口。[erp_plot.py:366](C:/dev/brain-plot/brain-plot/erp_plot.py:366)、[498](C:/dev/brain-plot/brain-plot/erp_plot.py:498)。 |
| B6 追溯／数值回归 | 部分解决 | 追溯字段及数值断言已补；但 N2 的“窗口一致”QA 结论错误，需重验。[erp_plot.py:512](C:/dev/brain-plot/brain-plot/erp_plot.py:512)、[test_erp_plot.py:44](C:/dev/brain-plot/brain-plot/test/test_erp_plot.py:44)、[fig_N2_run.json:745](C:/dev/brain-plot/brain-plot/test/out/fig_N2_run.json:745)。 |
| A6 窗口规则 | 已解决 | 已允许独立数据定位，禁止利用当前目标差异择窗。[rules.md:11](C:/dev/brain-plot/brain-plot/references/rules.md:11)。 |
| A7 统计标记例外 | 已解决 | 明确 v1 不画显著性标记。[rules.md:14](C:/dev/brain-plot/brain-plot/references/rules.md:14)。 |

**B. 剩余问题，按优先级**

1. **P1｜当前 N2 地形平均窗口与原分析不一致。**  
   [erp_plot.py:457](C:/dev/brain-plot/brain-plot/erp_plot.py:457)、[488](C:/dev/brain-plot/brain-plot/erp_plot.py:488) 把半个采样间隔当作边界容差：305–355 ms 实际选入 **304–356 ms、27 点**；原分析采用 **306–354 ms、25 点**（[03_erp_extract.py:176](C:/Users/ASUS/Dropbox/metaphor_production/gn_manuscript/11-final_analysis/01_v1/code/03_erp_extract.py:176)）。缓存复算，地形值最大改变约 **0.18 µV**。[图注第 11 行](C:/dev/brain-plot/brain-plot/test/out/fig_N2_caption.md:11)虽披露实际边界，仍声称灰带与地形窗口相同。  
   **最小修复：**按原分析使用微小浮点容差，避免半采样扩窗；增加实际时间轴选点断言，重绘 N2 并更新 QA。无需重新择窗。

2. **P1｜Windows 上仍可静默覆盖成分输出。**  
   内存复现：`N2`／`n2` 均通过校验，却指向同一文件；数字 `1`／字符串 `"1"` 也如此。原因是按原始值去重，却用字符串生成路径。[erp_plot.py:69](C:/dev/brain-plot/brain-plot/erp_plot.py:69)、[75](C:/dev/brain-plot/brain-plot/erp_plot.py:75)、[505](C:/dev/brain-plot/brain-plot/erp_plot.py:505)。  
   **最小修复：**名称必须是字符串；写任何文件前，按目标文件系统规则检查全部最终输出路径唯一。

3. **P2｜“覆盖插值范围”的承诺仍有例外。**  
   [erp_plot.py:498](C:/dev/brain-plot/brain-plot/erp_plot.py:498) 仅在 `peak > 1.02 × v` 时扩色限，较小超限仍被截色，与 [rules.md:13](C:/dev/brain-plot/brain-plot/references/rules.md:13) 不符。**当前两图已扩色限，不受此分支影响。**  
   **最小修复：**色限始终覆盖插值最大值，并对最终范围作断言。

**C. Verdict：No，暂不发布 v1。**

必须修复上述三项；随后完整运行回归，重新验收 N2 及更新运行记录。当前两图的排版本身已可接受，无需改变绑定布局。

可等待：七个无序条件的默认色板补齐（目前只有六色，会明确报错）；规则文件哈希／显式加载器版本补录；面板字母对齐和头轮廓粗细微调。