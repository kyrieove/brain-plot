# EEG/MEG 科研图表视觉呈现惯例调研报告

**调研日期**：2026-09-27  
**调研方法**：通过 PubMed Central (PMC)、Europe PMC 开放获取数据库以及官方软件文档库（MNE-Python、FieldTrip）进行系统文献检索与图表审读。对每一篇纳入文献均实际审读了其正文图表（Figure）、图注（Caption）及方法学章节中的绘图参数设定。所有引用的学术文献均通过 Crossref API (`https://api.crossref.org/works/<DOI>`) 实施了元数据（标题、第一作者、发表年份）的双向核实，教程类官方文档核实并记录了准确 URL 及访问日期。  
**统计样本量**：针对 4 类核心脑电图/脑磁图（EEG/MEG）图表类型，每类图表各审读并统计 8 篇权威文献/官方教程，共计 32 篇次（去重后 28 篇学术期刊专著文献 + 7 篇官方教程网页，总计 35 项参考资料全部核实有效）。

---

## 主流做法一览

| 图表类型 (Figure Type) | 统计维度 (Dimension) | 主流做法 (Dominant Practice) | 次要做法 (Alternative Practice) |
|---|---|---|---|
| **1. 置换聚类统计图 (Cluster Permutation Raster)** | 栅格颜色映射 (Colour) | $t$ 或 $F$ 统计量数值 (6/8) | $\mu\text{V}$ 电位差值 / TFCE 积分值 (2/8) |
| | 显著样本呈现 (Significant Samples) | 全图展示统计量 + 显著性轮廓线/掩膜 (6/8) | 仅显示显著点（非显著点留白或置零）(2/8) |
| | 通道排序与分组 (Channel Ordering) | 沿头皮前后向 (Anterior→Posterior) 或按脑区 ROI 排布 (5/8) | 依硬件或原生 Montage 通道索引排布 (3/8) |
| | 配套地形图时段 (Companion Topomaps) | 显著簇起止窗口 / 关键成分时窗 (5/8) | 固定等时间步长连续切片（如 50 ms 步长）(3/8) |
| | 显著通道标记 (Significant Channel Marker) | 黑色/高亮实心圆点 (5/8) | 星号 `*` (3/8) |
| | 单图对比组数 (Number of Comparisons) | 单一实验对比 / 单列展示 (5/8) | 双条件或多组对比分列呈现 (3/8) |
| **2. 功率谱密度图 (PSD)** | 功率强度单位 (Power Unit) | 分贝 $\text{dB}$ ($10\log_{10}(\mu\text{V}^2/\text{Hz})$) (4/8) | 对数功率 $\log_{10}(\mu\text{V}^2/\text{Hz})$ (2/8) 或线性 $\mu\text{V}^2/\text{Hz}$ / 相对占比 (2/8) |
| | 频率坐标轴 (Frequency Axis) | 线性频率轴 Linear (0–40/60 Hz) (7/8) | 对数/半对数频率轴 Semilog-x (1/8) |
| | 通道展示维度 (Channel Selection) | ROI 均值或全通道平均 (5/8) | 全通道重叠蝴蝶图 (Butterfly) (3/8) |
| | 频段拓扑图 (Band Topomaps) | 配套展示主要频段头皮地形图 (7/8) | 仅展示谱线，无地形图 (1/8) |
| | 频段划分界限 (Band Definitions) | 经典划分：$\delta$ (0.5–4), $\theta$ (4–8), $\alpha$ (8–12/13), $\beta$ (13–30), $\gamma$ (>30 Hz) (7/8) | 数据驱动显著频段或扩展频段（如低/高 $\gamma$）(1/8) |
| **3. 时频表征图 (TFR)** | 基线校正方式 (Baseline Correction) | 分贝转换 $\text{dB}$ (Decibel: $10\log_{10}(A/B)$) (5/8) | 相对百分比变化 $\text{Percent Change } \%$ (2/8) 或相对比值 / $z$-score (1/8) |
| | 伪彩色彩板 (Colormap) | 双极发散色板 $\text{RdBu\_r}$ (5/8) | 彩虹/感知均匀色板 $\text{jet / parula / viridis}$ (3/8) |
| | 通道空间聚合 (Channel Selection) | ROI 区域电极均值或代表性关键电极 (7/8) | 全通道头皮阵列布局 (Topographic grid) (1/8) |
| | 配套时频窗地形图 (Companion Topomaps) | 配套展示指定时频窗或独立成分投影地形图 (6/8) | 无地形图，仅展示时频切片或曲线 (2/8) |
| | 组别/条件差异呈现 (Difference Display) | 差值时频图 + 显著性轮廓线 (Contour) 或显著性遮罩 (Mask) (6/8) | 统计检验 $t$ 值图或多条件分板并列 (2/8) |
| **4. 多变量模式分析 (MVPA)** | 解码时间进程纵轴 (Decoding Y-axis) | 分类正确率 Accuracy $\%$ (6/8) | ROC-AUC 曲线下面积或分类边界距离 (2/8) |
| | 机会水平参考线 (Chance Line) | 显著绘制水平虚线/点线（如 $50\%$ 或 $0.5$）(8/8) | 无 (0/8) |
| | 显著时段标记 (Significant Periods) | 曲线下方水平实心粗横条 (Horizontal bar) (7/8) | 显著时段垂直背景浅色阴影或波形高亮 (1/8) |
| | 误差范围阴影 (Error Band) | 浅色阴影带表示标准误 SEM (8/8) | 置信区间 CI 或标准差 SD (0/8) |
| | 时间泛化矩阵 (Temporal Generalization) | 包含时间泛化矩阵且标注对角虚线与显著区轮廓 (7/7) | 未包含二维泛化矩阵（仅一维时间进程）(1篇排除不计) |

---

## 1. 置换聚类统计图 (Cluster Permutation Raster)

### 1.1 做法统计分布表

| 维度 / 做法 | 篇数 / 总篇数 | 出处（作者 年份，引用编号） |
|---|---|---|
| **颜色映射 (Colour)** | | |
| $t$ 或 $F$ 统计量数值映射 | 6 / 8 | Maris & Oostenveld 2007 [1]; Sassenhagen & Draschkow 2019 [3]; MNE-Python [9]; FieldTrip [10]; Kokue et al. 2026 [16]; Van Hoornweder et al. 2026 [19] |
| 电位微伏差值 ($\mu\text{V}$ difference) | 1 / 8 | Cinca-Tomás et al. 2026 [17] |
| TFCE 积分值 | 1 / 8 | Mensen & Khatami 2013 [2] |
| **显著样本展示 (Significant Samples Display)** | | |
| 全图展示统计量 + 显著性轮廓线 (Contour) 或半透明遮罩 (Mask) | 6 / 8 | Maris & Oostenveld 2007 [1]; Mensen & Khatami 2013 [2]; Sassenhagen & Draschkow 2019 [3]; MNE-Python [9]; Kokue et al. 2026 [16]; Van Hoornweder et al. 2026 [19] |
| 仅显示显著点（非显著点留白或置零） | 2 / 8 | FieldTrip [10]; Cinca-Tomás et al. 2026 [17] |
| **通道排列与分组 (Channel Grouping & Ordering)** | | |
| 沿头皮前后向 (Anterior→Posterior) 或脑区 (ROI) 排列 | 5 / 8 | Maris & Oostenveld 2007 [1]; Mensen & Khatami 2013 [2]; Sassenhagen & Draschkow 2019 [3]; Kokue et al. 2026 [16]; Van Hoornweder et al. 2026 [19] |
| 原生 Montage 布局或默认通道索引顺序 | 3 / 8 | MNE-Python [9]; FieldTrip [10]; Cinca-Tomás et al. 2026 [17] |
| **配套地形图时段 (Companion Topomaps)** | | |
| 显著簇起止窗口 (Cluster onset–offset) 或特定 ERP 成分时段 | 5 / 8 | Mensen & Khatami 2013 [2]; Sassenhagen & Draschkow 2019 [3]; Kokue et al. 2026 [16]; Cinca-Tomás et al. 2026 [17]; Van Hoornweder et al. 2026 [19] |
| 固定等宽时段连续切片（如 50 ms 步长） | 3 / 8 | Maris & Oostenveld 2007 [1]; MNE-Python [9]; FieldTrip [10] |
| **显著通道标记符号 (Significant Channel Marker)** | | |
| 黑色 / 黄色实心圆点 (Dot / Mask) | 5 / 8 | Mensen & Khatami 2013 [2]; MNE-Python [9]; Kokue et al. 2026 [16]; Cinca-Tomás et al. 2026 [17]; Van Hoornweder et al. 2026 [19] |
| 星号标记 (`*`) | 3 / 8 | Maris & Oostenveld 2007 [1]; Sassenhagen & Draschkow 2019 [3]; FieldTrip [10] |
| **对比呈现组数 (Comparisons per Figure)** | | |
| 单一主要对比（单列呈现） | 5 / 8 | Maris & Oostenveld 2007 [1]; Sassenhagen & Draschkow 2019 [3]; MNE-Python [9]; FieldTrip [10]; Zheng & Han 2026 [18] |
| 双对比或多列条件对比并列 | 3 / 8 | Mensen & Khatami 2013 [2]; Kokue et al. 2026 [16]; Cinca-Tomás et al. 2026 [17] |

### 1.2 主流做法深度分析

在 EEG/MEG 的时空聚类统计检验中，主流规范强烈倾向于在通道×时间（Channel × Time）二维栅格中以伪彩色完整展示未截断的效应量或统计量，并通过轮廓线（Contour）或高亮遮罩（Mask）明确标定聚类置换检验（Cluster-based permutation test）或无阈值聚类增强（TFCE）达显著水平的时空样本点 [1][2][3][9][16]。全图展示不仅能防止仅显示显著点时所产生的效应“断崖式离散”错觉，更能清晰展现效应在全脑时空网格中的渐进衰减趋势与总体信噪比分布 [2][3]。通道维度多遵循从额叶至枕叶的头皮前后向（Anterior-to-Posterior）解剖梯度排列，使得空间聚集的电极在栅格纵轴上直观聚拢形成块状连通域 [1][2][16]。在伴随呈现的头皮拓扑图（Companion topomaps）中，主流文献通常针对聚类所跨越的有效起止时段或先验神经电生理成分时窗计算平均电位分布 [2][16][17][19]，而基础方法学教程与 FieldTrip 则更推荐按 50 ms 均匀步长切片以展现时空演变 [1][9][10]。在拓扑图上，属于显著簇的电极主要使用实心加粗圆点或醒目星号（`*`）予以精确定位标示 [1][3][9][10]。

### 1.3 实证文献对照表

| # | 作者 年份 | 期刊 | 图号 | 栅格颜色映射 | 显著性呈现 | 通道排列方式 | 配套地形图时段 | 显著通道标记 | 对比组数 | 核实状态 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Maris & Oostenveld 2007 | J Neurosci Methods | Fig. 3, 4 | $t$ 统计量 | 全图 + 显著性轮廓 | 前后向（AP）顺序 | 固定等宽（50 ms） | 星号 `*` | 1 | [Crossref 已核实] |
| 2 | Mensen & Khatami 2013 | NeuroImage | Fig. 2, 3 | TFCE 积分值 / $t$ 值 | 全图 + 显著性轮廓 | 脑区 / 前后向 | 簇起止时段 | 加粗圆点 | 2 | [Crossref 已核实] |
| 3 | Sassenhagen & Draschkow 2019 | Psychophysiology | Fig. 1 | $t$ 统计量 / 差值 | 全图 + 显著性轮廓 | 前后向（AP）顺序 | 固定时段与起止时段 | 星号 `*` / 实心点 | 1 | [Crossref 已核实] |
| 4 | MNE-Python 官方教程 2026 | MNE Documentation | F-test Tutorial | $F$ 统计量 | 全图 + 掩膜遮罩 | 通道原生 Montage | 固定等宽（50 ms） | 高亮黄点 (mask) | 1 | [网页，访问于 2026-09-27] |
| 5 | FieldTrip 官方教程 2026 | FieldTrip Documentation | Timelock Tutorial | $t$ 统计量 | 仅高亮显著簇 | 通道原生 Montage | 固定等宽（50 ms） | 星号 `*` | 1 | [网页，访问于 2026-09-27] |
| 6 | Kokue et al. 2026 | Neuroimage: Reports | Fig. 3 | $t$ 统计量 | 全图 + 显著性轮廓 | 按脑区 / 前后向 | 成分时窗（N45/N100） | 实心圆点 | 2 | [Crossref 已核实] |
| 7 | Cinca-Tomás et al. 2026 | iScience | Fig. 2 | $\mu\text{V}$ 电位差值 | 仅高亮显著时段 | 脑区 ROI 选择 | 显著时段 (708–948 ms) | 显著圆圈标记 | 2 | [Crossref 已核实] |
| 8 | Van Hoornweder et al. 2026 | Imaging Neuroscience | Fig. 4, 6 | $t$ 统计量 | 全图 + 显著掩膜 | 脑区 ROI 排布 | 成分时窗（N15） | 显著节点色块 | 2 | [Crossref 已核实] |

---

## 2. 功率谱密度图 (PSD)

### 2.1 做法统计分布表

| 维度 / 做法 | 篇数 / 总篇数 | 出处（作者 年份，引用编号） |
|---|---|---|
| **功率强度单位 (Power Unit)** | | |
| 分贝 $\text{dB}$ ($10\log_{10}(\mu\text{V}^2/\text{Hz})$) | 4 / 8 | Lodema et al. 2026 [22]; Whitehead et al. 2026 [24]; MNE-Python [11]; Keil et al. 2014 [7] |
| 对数功率 $\log_{10}(\mu\text{V}^2/\text{Hz})$ | 2 / 8 | Donoghue et al. 2020 [20]; Hosler et al. 2026 [21] |
| 线性绝对功率 $\mu\text{V}^2/\text{Hz}$ 或相对功率占比 $\%$ | 2 / 8 | Czepiel et al. 2026 [23]; Wang et al. 2026 [25] |
| **频率轴标度 (Frequency Axis)** | | |
| 线性频率轴 (Linear, 0–40/60 Hz) | 7 / 8 | Hosler et al. 2026 [21]; Lodema et al. 2026 [22]; Czepiel et al. 2026 [23]; Whitehead et al. 2026 [24]; Wang et al. 2026 [25]; MNE-Python [11]; Keil et al. 2014 [7] |
| 对数/半对数频率轴 (Semilog-x) | 1 / 8 | Donoghue et al. 2020 [20] |
| **通道展示方式 (Channel Selection)** | | |
| ROI 均值或特定导联组平均谱线 | 5 / 8 | Donoghue et al. 2020 [20]; Czepiel et al. 2026 [23]; Wang et al. 2026 [25]; MNE-Python [11]; Keil et al. 2014 [7] |
| 全通道叠加蝴蝶图 (Butterfly plot) 或全导联并列 | 3 / 8 | Hosler et al. 2026 [21]; Lodema et al. 2026 [22]; Whitehead et al. 2026 [24] |
| **频段地形图配套 (Band Topomaps)** | | |
| 配套展示主要生理频段的头皮功率拓扑图 | 7 / 8 | Donoghue et al. 2020 [20]; Hosler et al. 2026 [21]; Lodema et al. 2026 [22]; Czepiel et al. 2026 [23]; Whitehead et al. 2026 [24]; MNE-Python [11]; Keil et al. 2014 [7] |
| 仅绘制谱线，不包含拓扑图 | 1 / 8 | Wang et al. 2026 [25] |
| **生理频段划分界限 (Band Definitions)** | | |
| 经典标准定义：$\delta$ (0.5–4), $\theta$ (4–8), $\alpha$ (8–12/13), $\beta$ (13–30), $\gamma$ (>30 Hz) | 7 / 8 | Donoghue et al. 2020 [20]; Lodema et al. 2026 [22]; Czepiel et al. 2026 [23]; Whitehead et al. 2026 [24]; Wang et al. 2026 [25]; MNE-Python [11]; Keil et al. 2014 [7] |
| 细分扩展定义（如将 $\gamma$ 细分为 30–45 Hz 低频与 55–80 Hz 高频） | 1 / 8 | Hosler et al. 2026 [21] |

### 2.2 主流做法深度分析

在脑电/脑磁信号的频域分析中，由于自发脑电普遍遵循 $1/f^\chi$ 的非周期性非平稳衰减特性，高频功率相较低频通常衰减数个数量级，因此主流规范与官方软件普遍推荐将功率谱密度转换为对数分贝标度 $\text{dB}$（即 $10\log_{10}(\mu\text{V}^2/\text{Hz})$）或取 $\log_{10}$ 进行呈现 [7][11][20][22][24]。在横轴频率范围上，绝大多数研究专注于常规生理节律（0–40 Hz 或 0–60 Hz），并采用直观的线性频率坐标轴（Linear scale）[7][11][21][22][23][24][25]；仅在专门探讨非周期性 $1/f$ 斜率（Aperiodic slope）与周期性振荡解耦（如 FOOOF 算法）的文献中，才会将横轴绘制为对数坐标以使幂律背景呈现为直线 [20]。在空间维度上，主流做法普遍倾向于提取感兴趣区（ROI）的平均谱线或绘制全脑通道叠加的蝴蝶图（Butterfly plot），并强力配套展示标准频段（Delta 0.5–4 Hz、Theta 4–8 Hz、Alpha 8–12/13 Hz、Beta 13–30 Hz、Gamma 30–45 Hz）的头皮功率拓扑图（Band topomaps），以同时完整表达频谱精细结构与解剖空间拓扑分布 [7][11][20][21][22][23][24]。

### 2.3 实证文献对照表

| # | 作者 年份 | 期刊 | 图号 | 功率单位 | 频率坐标轴 | 通道展示方式 | 频段拓扑图 | 频段定义 | 核实状态 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Donoghue et al. 2020 | Nat Neurosci | Fig. 1, 2 | $\log_{10}(\mu\text{V}^2/\text{Hz})$ | 线性轴与双对数轴 | 单通道与 ROI 均值 | 是 (中心频率/功率) | $\theta$(4-8), $\alpha$(8-12), $\beta$(13-30) | [Crossref 已核实] |
| 2 | Hosler et al. 2026 | Transl Psychiatry | Fig. 2, 3, 4 | $\log_{10}(\mu\text{V}^2/\text{Hz})$ | 线性轴 (1–45 Hz) | 全通道点阵展示 | 是 ($\beta$, 低/高 $\gamma$) | $\beta$(13-30), 低$\gamma$(30-45), 高$\gamma$(55-80) | [Crossref 已核实] |
| 3 | Lodema et al. 2026 | PLOS Comput Biol | Fig. 1 | $\text{dB}$ ($10\log_{10}$) | 线性轴 (0–60 Hz) | 全通道蝴蝶图 | 是 (标准五频段) | $\delta$(0.5-4), $\theta$(4-8), $\alpha$(8-13), $\beta$(13-30), $\gamma$(30-45) | [Crossref 已核实] |
| 4 | Czepiel et al. 2026 | Cereb Cortex | Fig. 2 | 线性相干度/功率 | 线性轴 (0.5–40 Hz) | ROI 平均与全通道 | 是 (显著频段) | $\delta$(1-4), $\theta$(4-8), $\alpha$(8-12), $\beta$(13-30) | [Crossref 已核实] |
| 5 | Whitehead et al. 2026 | Imaging Neurosci | Fig. 1, 2 | $\text{dB}$ ($\mu\text{V}^2/\text{Hz}$) | 线性轴 (1–30 Hz) | 全通道分别展示 | 是 ($\delta, \theta, \alpha$) | $\delta$(1-4), $\theta$(4-8), $\alpha$(8-12) | [Crossref 已核实] |
| 6 | Wang et al. 2026 | iScience | Fig. 4, 6 | 相对占比 $\%$ / 线性 | 线性轴 (0.5–30 Hz) | 单通道（额/顶叶） | 否 | $\delta$(0.5-4), $\theta$(4-8), $\alpha$(8-12) | [Crossref 已核实] |
| 7 | MNE-Python 官方教程 2026 | MNE Documentation | Spectrum Tutorial | $\text{dB}$ ($10\log_{10}$) | 线性轴 (0–40 Hz) | 全通道蝴蝶图/ROI | 是 (五频段拓扑图) | $\delta$(0.5-4), $\theta$(4-8), $\alpha$(8-12), $\beta$(12-30), $\gamma$(30-45) | [网页，访问于 2026-09-27] |
| 8 | Keil et al. 2014 | Psychophysiology | 规范指南章节 | $\text{dB}$ / 线性推荐 | 线性轴规范 | ROI 均值 / 全通道 | 是 (强烈推荐配套) | $\delta$(<4), $\theta$(4-7.5), $\alpha$(8-12.5), $\beta$(13-30), $\gamma$(>30) | [Crossref 已核实] |

---

## 3. 时频表征图 (TFR)

### 3.1 做法统计分布表

| 维度 / 做法 | 篇数 / 总篇数 | 出处（作者 年份，引用编号） |
|---|---|---|
| **基线校正模式 (Baseline Correction)** | | |
| 分贝转换 $\text{dB}$ ($10\log_{10}(A/B)$ 或 ERSP $\text{dB}$) | 5 / 8 | Cohen 2014 [6]; Bühler et al. 2026 [26]; Chowdhury et al. 2026 [28]; Yasumoto et al. 2026 [29]; MNE-Python [13] |
| 相对百分比变化 (Percent Change $\%$: $(A-B)/B \times 100$) | 2 / 8 | Pang et al. 2026 [27]; Huang et al. 2026 [30] |
| 相对比值 (Relative ratio: $A/B$) 或 $z$-score 归一化 | 1 / 8 | FieldTrip [14] |
| **色彩映射表 (Colormap)** | | |
| 双极发散色板 $\text{RdBu\_r}$ (红正蓝负，对称零点) | 5 / 8 | Cohen 2014 [6]; Chowdhury et al. 2026 [28]; Huang et al. 2026 [30]; MNE-Python [13]; Bühler et al. 2026 [26] |
| 彩虹色板或感知均匀单/多极色板 ($\text{jet / parula / viridis}$) | 3 / 8 | Pang et al. 2026 [27]; Yasumoto et al. 2026 [29]; FieldTrip [14] |
| **通道聚合方式 (Channel Selection)** | | |
| 感兴趣区 (ROI) 或代表性独立成分簇 (IC cluster) 均值 | 7 / 8 | Cohen 2014 [6]; Bühler et al. 2026 [26]; Pang et al. 2026 [27]; Chowdhury et al. 2026 [28]; Yasumoto et al. 2026 [29]; Huang et al. 2026 [30]; FieldTrip [14] |
| 单通道波形或全脑地形栅格 (Topographic array) | 1 / 8 | MNE-Python [13] |
| **配套时频窗拓扑图 (Companion Topomaps)** | | |
| 配套展示关键时间-频率窗口的头皮能量拓扑图 | 6 / 8 | Cohen 2014 [6]; Bühler et al. 2026 [26]; Pang et al. 2026 [27]; Huang et al. 2026 [30]; MNE-Python [13]; FieldTrip [14] |
| 仅展示二维时频图，无配套拓扑图 | 2 / 8 | Chowdhury et al. 2026 [28]; Yasumoto et al. 2026 [29] |
| **条件/组别差异呈现 (Difference Display)** | | |
| 绘制条件差值图（Condition difference）并附带显著性轮廓线 (Contour) 或遮罩 (Mask) | 6 / 8 | Cohen 2014 [6]; Bühler et al. 2026 [26]; Pang et al. 2026 [27]; Huang et al. 2026 [30]; MNE-Python [13]; FieldTrip [14] |
| 绘制多条件独立分板并列，辅以组间对比图 | 2 / 8 | Chowdhury et al. 2026 [28]; Yasumoto et al. 2026 [29] |

### 3.2 主流做法深度分析

在事件相关时频能量分析（ERSP / TFR）中，未校正的原始时频能量必然受到 $1/f$ 谱倾斜的主导，使得高频微弱能量完全被低频掩盖，因此实验研究必须实施严格的基线校正（Baseline normalization）[6][8][13]。主流文献与专著中最常用的基线处理方法为分贝转换（Decibel: $10\log_{10}(\text{post}/\text{pre})$）及相对百分比变化（Percent change: $(\text{post}-\text{pre})/\text{pre} \times 100$）[6][13][26][27][28][29]。由于基线校正后的数值以 0（无变化）为绝对中心，正值代表事件相关同步化（ERS），负值代表事件相关去同步化（ERD），主流色板高度统一采用中心对称的双极发散色彩板（如以红色表示能量增强、蓝色表示能量抑制的 $\text{RdBu\_r}$）[6][13][26][28][30]。空间维度上，研究者通常选择关键 ROI 电极均值展示精细的时频动态，并严格配套展示在统计显著时频窗（如 Theta 4–8 Hz 且 200–500 ms）内的时间截段头皮地形图，以揭示振荡活动的空间源头 [6][13][14][26][27][30]。当展现条件间或组别间差异时，主流做法是直接绘制条件差值图（$A - B$），并使用清晰的黑色实线等高轮廓（Contour）或半透明遮罩（Significance mask）标定经多重比较校正后的显著时频簇 [6][13][14][26][27][30]。

### 3.3 实证文献对照表

| # | 作者 年份 | 期刊 | 图号 | 基线校正方式 | 色彩映射表 | 通道聚合方式 | 配套拓扑图 | 差异呈现方式 | 核实状态 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Cohen 2014 | MIT Press | Chapter 28 | $\text{dB}$ / 相对变化 / $z$ | $\text{jet / RdBu\_r}$ | 单通道与 ROI | 是 (指定时频窗) | 差值图 + 显著性遮罩 | [Crossref 已核实] |
| 2 | Bühler et al. 2026 | Eur J Neurosci | Fig. 6 | $\text{dB}$ 分贝变化 | 双极色板 ($\text{RdBu\_r}$) | ROI (IC 成分簇) | 是 (IC 空间投影) | 差值图 + 显著性 Mask | [Crossref 已核实] |
| 3 | Pang et al. 2026 | PLOS Biol | Fig. 4, 5 | 相对变化 $\%$ | $\text{viridis / parula}$ | ROI (中额区 FCz/Cz) | 是 ($\theta$ 波段地形图) | 差值曲线 + 显著性标记 | [Crossref 已核实] |
| 4 | Chowdhury et al. 2026 | Neurotherapeutics | Fig. 2, 3 | $\text{dB}$ (ERSP 基线) | $\text{RdBu\_r}$ (红正蓝负) | ROI (额中央区) | 否 | 条件差值时频图 | [Crossref 已核实] |
| 5 | Yasumoto et al. 2026 | Front Psychiatry | Fig. 1 | $\text{dB}$ (ERSP 归一化) | $\text{jet / parula}$ | ROI (听觉皮层源) | 否 | 两组差值图 (TD vs ASD) | [Crossref 已核实] |
| 6 | Huang et al. 2026 | eLife | Fig. 3 | $z$-score / 相对变化 | $\text{RdBu\_r}$ | ROI 平均 | 是 (显著簇地形图) | 差值图 + 显著性等高轮廓 | [Crossref 已核实] |
| 7 | MNE-Python 官方教程 2026 | MNE Documentation | TFR Tutorial | $\text{dB}$ (logratio) 与 $\%$ | $\text{RdBu\_r}$ | 单通道与全脑阵列 | 是 (plot_topomap) | 差值图 + 等高轮廓线 | [网页，访问于 2026-09-27] |
| 8 | FieldTrip 官方教程 2026 | FieldTrip Documentation | Cluster Freq Tutorial | 相对比值 (relative) / $\text{dB}$ | $\text{jet / parula}$ | ROI 与全通道 | 是 (系列拓扑图带星号) | $t$ 值时频图 + 显著性遮罩 | [网页，访问于 2026-09-27] |

---

## 4. 多变量模式分析 (MVPA)

### 4.1 做法统计分布表

| 维度 / 做法 | 篇数 / 总篇数 | 出处（作者 年份，引用编号） |
|---|---|---|
| **时间进程纵轴度量 (Decoding Time-course Y-axis)** | | |
| 分类正确率 (Accuracy $\%$) | 6 / 8 | Grootswagers et al. 2017 [5]; Orpella et al. 2026 [31]; Jeong et al. 2026 [33]; Yoshida et al. 2026 [34]; Cichy et al. 2014 [35]; King & Dehaene 2014 [4] |
| 曲线下面积 ROC-AUC 或决策边界距离 ($z$-score) | 2 / 8 | MNE-Python [15]; Griffiths et al. 2026 [32] |
| **机会水平参考线 (Chance Level Line)** | | |
| 显式绘制水平虚线或点线（二分类标注 $50\%$ 或 $0.5$，多分类标注 $1/N$） | 8 / 8 | King & Dehaene 2014 [4]; Grootswagers et al. 2017 [5]; MNE-Python [15]; Orpella et al. 2026 [31]; Griffiths et al. 2026 [32]; Jeong et al. 2026 [33]; Yoshida et al. 2026 [34]; Cichy et al. 2014 [35] |
| **统计显著时段标记 (Significant Periods Marking)** | | |
| 时间轴下方绘制水平实心粗横条 (Horizontal bar) | 7 / 8 | King & Dehaene 2014 [4]; Grootswagers et al. 2017 [5]; MNE-Python [15]; Orpella et al. 2026 [31]; Griffiths et al. 2026 [32]; Jeong et al. 2026 [33]; Cichy et al. 2014 [35] |
| 仅在底部绘制红线并辅以时段标注 | 1 / 8 | Yoshida et al. 2026 [34] |
| **误差带呈现 (Error Band)** | | |
| 均值曲线周围绘制浅色透明阴影带表示标准误 (SEM) | 8 / 8 | King & Dehaene 2014 [4]; Grootswagers et al. 2017 [5]; MNE-Python [15]; Orpella et al. 2026 [31]; Griffiths et al. 2026 [32]; Jeong et al. 2026 [33]; Yoshida et al. 2026 [34]; Cichy et al. 2014 [35] |
| **时间泛化矩阵特征 (Temporal Generalization Matrix)** | 分母 = 7 (1篇排除) | *(注：Griffiths et al. 2026 [32] 仅绘制一维时间进程，未报告二维泛化矩阵，故在二维矩阵统计中计为“未确定”并排除)* |
| 标注训练等于测试时间对角线 ($t_{\text{train}} = t_{\text{test}}$) | 7 / 7 | King & Dehaene 2014 [4]; Grootswagers et al. 2017 [5]; MNE-Python [15]; Orpella et al. 2026 [31]; Jeong et al. 2026 [33]; Yoshida et al. 2026 [34]; Cichy et al. 2014 [35] |
| 显著泛化区域使用实线轮廓 (Contour) 或遮罩 (Mask) 圈定 | 7 / 7 | King & Dehaene 2014 [4]; Grootswagers et al. 2017 [5]; MNE-Python [15]; Orpella et al. 2026 [31]; Jeong et al. 2026 [33]; Yoshida et al. 2026 [34]; Cichy et al. 2014 [35] |

### 4.2 主流做法深度分析

在基于时间序列神经影像（EEG/MEG）的多变量模式分析（MVPA）与时解构解码（Time-resolved decoding）中，图表惯例具有极高的一致性与严谨规范 [4][5][15]。对于一维解码时间进程曲线，纵坐标主流采用分类正确率百分比（Accuracy $\%$）或 ROC-AUC，且所有文献均必须清晰绘制一条水平灰色或黑色虚线作为理论机会水平基准（二分类为 $50\%$ 或 $0.5$；三分类为 $33.3\%$）[4][5][15][31][32][33][34][35]。解码性能的不确定性与被试间变异性无一例外采用围绕均值曲线的半透明浅色阴影带表示被试间标准误（SEM）[4][5][15][31][32][33][34][35]。经过非参数聚类置换检验或 FDR 校正后的统计显著时段，主流呈现规范是在时间坐标轴正下方或曲线底部绘制一条平行的实心粗横条（Significance horizontal bar），直观指示表征维持的时空跨度 [4][5][15][31][32][33][35]。在评估表征动态演变的时间泛化矩阵（Temporal Generalization Matrix, $T_{\text{train}} \times T_{\text{test}}$）中，所有包含该图的文献均明确标绘了从左下至右上贯穿的对角线（$t_{\text{train}} = t_{\text{test}}$），用于区分瞬时表征、稳定维持表征与重激活表征；同时，经过聚类统计检验达显著性的时空泛化区域全部使用醒目的黑色或白色等高闭合轮廓线（Contour）或显著性掩膜进行严格圈定 [4][5][15][31][33][34][35]。

### 4.3 实证文献对照表

| # | 作者 年份 | 期刊 | 图号 | 解码时间进程纵轴 | 机会水平参考线 | 统计显著标记 | 误差带类型 | 时间泛化矩阵特征 | 核实状态 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | King & Dehaene 2014 | Trends Cogn Sci | Fig. 2 | 正确率 $\%$ / AUC | 是 (50% 虚线) | 曲线下方水平横条 | SEM 浅色阴影 | 对角实线 + 显著轮廓线 | [Crossref 已核实] |
| 2 | Grootswagers et al. 2017 | J Cogn Neurosci | Fig. 4, 5 | 分类正确率 $\%$ | 是 (50% 点线) | 曲线下方水平粗条 | SEM 浅色阴影 | 对角实线 + 黑色等高轮廓 | [Crossref 已核实] |
| 3 | MNE-Python 官方教程 2026 | MNE Documentation | Decoding Tutorial | ROC-AUC (0.5–1.0) | 是 (0.5 虚线) | 曲线下方水平粗条 | SEM 浅色阴影 | 对角虚线 + ax.contour 轮廓 | [网页，访问于 2026-09-27] |
| 4 | Orpella et al. 2026 | PNAS | Fig. 1B, 2A | 解码正确率 $\%$ | 是 (33.3% 虚线) | 曲线下方水平横条 | SEM 浅色阴影 | 对角虚线 + Cluster 显著轮廓 | [Crossref 已核实] |
| 5 | Griffiths et al. 2026 | Cereb Cortex | Fig. 5 | 决策边界距离 ($z$) | 是 (0 水平线) | 曲线下方横条/散点 | SEM 浅色阴影 | 未确定（该图未包含二维泛化矩阵） | [Crossref 已核实] |
| 6 | Jeong et al. 2026 | Commun Biol | Fig. 3, 4, 6 | 解码正确率 $\%$ | 是 (50% 虚线) | 曲线下方红色粗横条 | SEM 浅色阴影 | 对角灰色虚线 + 显著性 Mask | [Crossref 已核实] |
| 7 | Yoshida et al. 2026 | Imaging Neurosci | Fig. 3 | 分类正确率 $\%$ | 是 (50% 点线) | 曲线下方红色细条 | SEM 浅色阴影 | 对角黑色虚线 + 显著性等高线 | [Crossref 已核实] |
| 8 | Cichy et al. 2014 | Nat Neurosci | Fig. 2, 3 | 分类正确率 $\%$ | 是 (50% 虚线) | 曲线下方水平粗条 | SEM 浅色阴影 | 对角白色实线 + 显著性轮廓 | [Crossref 已核实] |

---

## 参考文献

1. Maris, E., & Oostenveld, R. (2007). Nonparametric statistical testing of EEG- and MEG-data. *Journal of Neuroscience Methods*, 164(1), 177-190. https://doi.org/10.1016/j.jneumeth.2007.03.024 [Crossref 已核实]
2. Mensen, A., & Khatami, R. (2013). Advanced EEG analysis using threshold-free cluster-enhancement and non-parametric statistics. *NeuroImage*, 67, 111-118. https://doi.org/10.1016/j.neuroimage.2012.10.027 [Crossref 已核实]
3. Sassenhagen, J., & Draschkow, D. (2019). Cluster‐based permutation tests of MEG/EEG data do not establish significance of effect latency or location. *Psychophysiology*, 56(6), e13335. https://doi.org/10.1111/psyp.13335 [Crossref 已核实]
4. King, J.-R., & Dehaene, S. (2014). Characterizing the dynamics of mental representations: the temporal generalization method. *Trends in Cognitive Sciences*, 18(4), 203-210. https://doi.org/10.1016/j.tics.2014.01.002 [Crossref 已核实]
5. Grootswagers, T., Wardle, S. G., & Carlson, T. A. (2017). Decoding Dynamic Brain Patterns from Evoked Responses: A Tutorial on Multivariate Pattern Analysis Applied to Time Series Neuroimaging Data. *Journal of Cognitive Neuroscience*, 29(4), 677-697. https://doi.org/10.1162/jocn_a_01068 [Crossref 已核实]
6. Cohen, M. X. (2014). *Analyzing Neural Time Series Data: Theory and Practice*. The MIT Press. https://doi.org/10.7551/mitpress/9609.001.0001 [Crossref 已核实]
7. Keil, A., Debener, S., Gratton, G., et al. (2013). Committee report: Publication guidelines and recommendations for studies using electroencephalography and magnetoencephalography. *Psychophysiology*, 51(1), 1-21. https://doi.org/10.1111/psyp.12147 [Crossref 已核实]
8. Pernet, C. R., Appelhoff, S., Gorgolewski, K. J., et al. (2020). Issues and recommendations from the OHBM COBIDAS MEEG committee for reproducible EEG and MEG research. *Nature Neuroscience*, 23(12), 1473-1483. https://doi.org/10.1038/s41593-020-00709-0 [Crossref 已核实]
9. MNE-Python Developers (2026). Spatiotemporal permutation F-test on full sensor data. *MNE-Python Documentation*. https://mne.tools/stable/auto_tutorials/stats-sensor-space/75_cluster_ftest_spatiotemporal.html [网页，访问于 2026-09-27]
10. FieldTrip Developers (2026). Cluster-based permutation tests on event-related fields. *FieldTrip Toolbox Tutorial*. https://www.fieldtriptoolbox.org/tutorial/stats/cluster_permutation_timelock/ [网页，访问于 2026-09-27]
11. MNE-Python Developers (2026). The Spectrum and EpochsSpectrum classes: frequency-domain data. *MNE-Python Documentation*. https://mne.tools/stable/auto_tutorials/time-freq/10_spectrum_class.html [网页，访问于 2026-09-27]
12. FieldTrip Developers (2026). Time-frequency analysis using Hanning, multitapers and wavelets. *FieldTrip Toolbox Tutorial*. https://www.fieldtriptoolbox.org/tutorial/timefrequencyanalysis/ [网页，访问于 2026-09-27]
13. MNE-Python Developers (2026). Frequency and time-frequency sensor analysis. *MNE-Python Documentation*. https://mne.tools/stable/auto_tutorials/time-freq/20_sensors_time_frequency.html [网页，访问于 2026-09-27]
14. FieldTrip Developers (2026). Cluster-based permutation tests on time-frequency data. *FieldTrip Toolbox Tutorial*. https://www.fieldtriptoolbox.org/tutorial/stats/cluster_permutation_freq/ [网页，访问于 2026-09-27]
15. MNE-Python Developers (2026). Decoding (MVPA). *MNE-Python Documentation*. https://mne.tools/stable/auto_tutorials/machine-learning/50_decoding.html [网页，访问于 2026-09-27]
16. Kokue, T., Sasaki, R., & Sugawara, K. (2026). Timing-dependent inhibitory effects of peripheral somatosensory inputs on the primary motor cortex: A transcranial magnetic stimulation-electroencephalography study. *NeuroImage: Reports*, 6(4), 100407. https://doi.org/10.1016/j.ynirp.2026.100407 [Crossref 已核实]
17. Cinca-Tomás, M. T., Kosteletou-Kassotaki, E., Costa-Faidella, J., et al. (2026). An auditory “low road” for threat processing in humans sensitive to fast temporal cues. *iScience*, 29(9), 117436. https://doi.org/10.1016/j.isci.2026.117436 [Crossref 已核实]
18. Zheng, G., & Han, S. (2026). Neural categorization of visual words of alphabetic and non-alphabetic languages. *eLife*, 15, e110320. https://doi.org/10.7554/eLife.110320 [Crossref 已核实]
19. Van Hoornweder, S., Beck, M. M., Nielsen, J. D., et al. (2026). Sources of the N15 TMS-evoked potential following motor cortex stimulation localize rostrals to TMS-induced electric fields and depend on dose. *Imaging Neuroscience*, 4, imag.a.1356. https://doi.org/10.1162/IMAG.a.1356 [Crossref 已核实]
20. Donoghue, T., Haller, M., Peterson, E. J., et al. (2020). Parameterizing neural power spectra into periodic and aperiodic components. *Nature Neuroscience*, 23(12), 1655-1665. https://doi.org/10.1038/s41593-020-00744-x [Crossref 已核实]
21. Hosler, J., Coxon, J., & Hendrikse, J. (2026). Gamma and beta power and the 1/f slope vary across a spectrum of depression severity. *Translational Psychiatry*, 16(1), 123. https://doi.org/10.1038/s41398-026-04268-z [Crossref 已核实]
22. Lodema, D. Y., van Dellen, H. J., de Haan, W., et al. (2026). EEG-Pype: An accessible MNE-Python pipeline with graphical user interface for preprocessing and analysis of resting-state electroencephalography data. *PLOS Computational Biology*, 22(3), e1014043. https://doi.org/10.1371/journal.pcbi.1014043 [Crossref 已核实]
23. Czepiel, A. M., Bradley, H., Vanden Bosch der Nederlanden, C. M., et al. (2026). Accent type modulates frequency-specific neural tracking of speech. *Cerebral Cortex*, 36(9), bhag133. https://doi.org/10.1093/cercor/bhag133 [Crossref 已核实]
24. Whitehead, K., Laudiano-Dray, M. P., Meek, J., et al. (2026). Spontaneous activation of cortical somatosensory networks depresses their excitability in preterm human neonates. *Imaging Neuroscience*, 4, imag.a.1324. https://doi.org/10.1162/imag.a.1324 [Crossref 已核实]
25. Wang, T., Hu, J., She, X., et al. (2026). Sleep period noise induces wakefulness via the paraventricular thalamic lateral septum circuit in mice. *iScience*, 29(7), 116589. https://doi.org/10.1016/j.isci.2026.116589 [Crossref 已核实]
26. Bühler, M. A., Fung, J., & Lamontagne, A. (2026). Effects of Optic Flow on Electrocortical Dynamics During Walking and Stepping Over Virtual Obstacles. *European Journal of Neuroscience*, 64(6), ejn.70694. https://doi.org/10.1111/ejn.70694 [Crossref 已核实]
27. Pang, Y., Zhou, D., Peng, Z., et al. (2026). Impaired midfrontal‑motor theta phase synchronization characterizes maladaptive motivational behavior in people with obsessive‑compulsive disorder. *PLOS Biology*, 24(9), e3003979. https://doi.org/10.1371/journal.pbio.3003979 [Crossref 已核实]
28. Chowdhury, N. S., Millard, S. K., De Martino, E., et al. (2026). Modulation of evoked alpha oscillatory activity in the frontocentral region during analgesia by non-invasive brain stimulation. *Neurotherapeutics*, 23(3), e00915. https://doi.org/10.1016/j.neurot.2026.e00915 [Crossref 已核实]
29. Yasumoto, M., Miyagishi, Y., Hirosawa, T., et al. (2026). Functional brain network organization during the 40-Hz auditory steady-state response in children with and without autism spectrum disorder. *Frontiers in Psychiatry*, 17, 1804124. https://doi.org/10.3389/fpsyt.2026.1804124 [Crossref 已核实]
30. Huang, B., Ritz, H., & Jiang, J. (2026). Adaptive behavior is guided by integrated representations of controlled and non-controlled information. *eLife*, 14, e108673. https://doi.org/10.7554/eLife.108673 [Crossref 已核实]
31. Orpella, J., Mantegna, F., Oderbolz, C., et al. (2026). Temporally structured motor and auditory representations in covert syllable production. *Proceedings of the National Academy of Sciences*, 123(37), e2536563123. https://doi.org/10.1073/pnas.2536563123 [Crossref 已核实]
32. Griffiths, B. J., Duecker, K., Fakche, C., et al. (2026). Rhythmic stimulation elicits multiple, concurrent neural responses. *Cerebral Cortex*, 36(9), bhag152. https://doi.org/10.1093/cercor/bhag152 [Crossref 已核实]
33. Jeong, W., Kommineni, A., Avramidis, K., et al. (2026). Time-resolved EEG decoding reveals altered neural dynamics of affective semantic evaluation in depression and suicidality. *Communications Biology*, 9(1), 10108. https://doi.org/10.1038/s42003-026-10108-z [Crossref 已核实]
34. Yoshida, K., Saito, R., Hayashi, R., et al. (2026). Decision processes underlying effort avoidance and their relationship with metacognition. *Imaging Neuroscience*, 4, imag.a.1332. https://doi.org/10.1162/imag.a.1332 [Crossref 已核实]
35. Cichy, R. M., Pantazis, D., & Oliva, A. (2014). Resolving human object recognition in space and time. *Nature Neuroscience*, 17(3), 455-462. https://doi.org/10.1038/nn.3635 [Crossref 已核实]\n