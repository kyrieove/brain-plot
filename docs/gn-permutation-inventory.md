# Go/No-Go 论文现有 Cluster-Permutation 与 TFCE 分析全量清查清单

- **日期**：2026-09-27
- **数据源目录（只读）**：`C:\Users\ASUS\Dropbox\metaphor_production\gn_manuscript`
- **核查方法**：只读静态扫描与 Python 只读检查（`numpy.load(..., allow_pickle=True)`、`scipy.io.loadmat`、`pandas.read_csv`；执行时设置 `PYTHONDONTWRITEBYTECODE=1`，工作目录保持在外部，未对源目录写入任何字节或缓存）。

---

## 一览总表 (Summary Table)

| 脚本路径 (Script) | 核心函数 (Function) | 统计检验类型 (Test) | 阈值 / TFCE 参数 (Threshold/TFCE) | 置换次数 (n_perm) | 检验尾向 (Tail) | 数据类型 (Data Type) | 核心输出文件 (Result File) |
|---|---|---|---|---|---|---|---|
| `03-ERP_topomap/00_code/run_cluster_based_permutation.py` | `mne.stats.spatio_temporal_cluster_1samp_test`<br>`mne.stats.spatio_temporal_cluster_test` | 配对差值单样本 t 检验<br>组间单因素方差分析 F 检验 | t: $p<0.05$ 双尾 ($t\approx1.986\sim2.093$)<br>F: $p<0.05$ 单尾 ($F=2.705$) | 5000 | t: 0 (双尾)<br>F: 1 (单尾) | 传感器 ERP 差值时序波形 (µV) | `03-ERP_topomap/03_cluster_inference/01_cluster_based_permutation_0000_0800ms/{test}/all_cluster_indices.npz` |
| `10-ERP_stats/01_v1_tfce/code/stats_engine.py`<br>(驱动: `04_rq0.py`, `05_rq1_diff.py`, `06_rq1_avg.py`) | 自定义快速时空 TFCE 引擎<br>(Freedman-Lane 符号翻转与置换 scheme) | RQ0: 条件配对差值符号翻转 t 检验<br>RQ1: 4组单因素 ANCOVA F 检验 (控制性别)<br>RQ1 post-hoc: 组间独立样本 t 检验 (控制性别, Holm 校正) | TFCE: $H=2.0, E=0.5, dh=0.2$<br>从 0 开始连续积分 | 5000 | RQ0: 0 (双尾)<br>RQ1 F: 1 (单尾)<br>RQ1 t: 0 (双尾) | 传感器 ERP 差值与均值波形 (µV) | `10-ERP_stats/01_v1_tfce/data/rq0_results.npz`<br>`10-ERP_stats/01_v1_tfce/data/rq1_diff_results.npz`<br>`10-ERP_stats/01_v1_tfce/data/rq1_avg_results.npz` |
| `08-MVPA/run_mvpa.py`<br>(另见 `08-MVPA/frozen_mvpa/stats.py`) | `mne.stats.permutation_cluster_1samp_test`<br>(frozen_mvpa: `onesample_cluster_test`, `twosample_cluster_test`, `omnibus_cluster_test`, `correlation_cluster_test`) | 解码准确率 vs 机会水平(50%)单样本检验<br>组间两样本检验<br>组间单因素方差检验<br>行为 RT 偏相关置换检验 | `run_mvpa.py`: `threshold=None`（按 MNE 默认值推断：双尾 $p<0.05$ 对应 $t$ 临界值）<br>`frozen_mvpa`: 点水平 $\alpha=0.05$ 临界值 | `run_mvpa.py`: 1000<br>`frozen_mvpa`: 1000~5000 | 0 (双尾) / 1 (单尾) | MVPA 时间分辨解码准确率 / AUC / 2D TG 矩阵 | `08-MVPA/results/frozen_tracer/stats/dev/mask_overall_accuracy.npz`<br>`08-MVPA/results/frozen_tracer/stats/dev/mask_group_TD.npz` |
| `figures_drawio/source_localization/05_roi_timecourses_balanced/plot_balanced_roi_timecourses.py` | `mne.stats.permutation_cluster_1samp_test` | 3个双侧皮层 ROI 上的 NoGo − Go 配对差值单样本 t 检验 (FWER 跨 3 ROI 校正) | $p<0.05$ 双尾 ($t=1.9855$, $df=94$) | 5000 | 0 (双尾) | 皮层 ROI dSPM 幅值时序波形 | `figures_drawio/source_localization/05_roi_timecourses_balanced/data/paired_cluster_results.csv` |
| `notebooks/batch_source_localization.ipynb` (Cell 9) | `mne.stats.spatio_temporal_cluster_1samp_test` | TD 组皮层表面逐顶点 NoGo − Go 差值单样本 t 检验 | 点水平双尾 $p<0.001$ ($t=3.6460$, $df=30$) | 5000 | 0 (双尾) | 皮层表面逐顶点 dSPM 幅值 (stc) | `06-source analysis/source_statistics/TD_NoGo_minus_GO_cluster/TD_NoGo-minus-GO_spatiotemporal_cluster_000-800ms.npz` |
| `05-microstate_GA/code/run_condition_tanova_duration.py`<br>(源自 `04-Ragu/Ragu_statistics/TANOVA_results.mat`) | 地形图方差分析 TANOVA 置换检验 + 持续时间簇校正 (Duration cluster correction) | 条件主效应 (NoGO vs GO) 地形图全脑全异度 (GMD) 被试内符号置换检验 | 点水平 $\alpha=0.05$；时间簇最小临界持续时间 51 帧 (102.0 ms) | 5000 | 不涉及（GMD 距离检验） | GFP 标准化全脑电位地形图 (Topography) | `05-microstate_GA/01_main_v7_GFP2_k_selection/condition_tanova/run_record.json`<br>`05-microstate_GA/01_main_v7_GFP2_k_selection/condition_tanova/condition_tanova_p_timecourse.csv` |

---

## 逐项详细清查 (Detailed Inventory)

### 1. `03-ERP_topomap/00_code/run_cluster_based_permutation.py`
（同族伴随脚本：`audit_cluster_reliability.py` 严格敏感性复核；`plot_cluster_results_mne_style.py` 绘图渲染）

#### (1) 脚本与参数配置 (Script & Parameters)
- **文件绝对路径**：`C:\Users\ASUS\Dropbox\metaphor_production\gn_manuscript\03-ERP_topomap\00_code\run_cluster_based_permutation.py`
- **调用函数**：
  - `mne.stats.spatio_temporal_cluster_1samp_test` (L462)
  - `mne.stats.spatio_temporal_cluster_test` (L482)
- **检验类型与统计量函数**：
  - 单样本条件效应检验（配对差值）：$t$ 检验，`stat_fun` 采用默认值（按 MNE 官方文档推断为 `mne.stats.ttest_1samp_no_p`）。
  - 组间交互/组间效应检验：单因素 ANOVA $F$ 检验，`stat_fun` 采用默认值（按 MNE 官方文档推断为 `mne.stats.f_oneway`）。
- **参数代码引证（含行号）**：
  - 时间窗口：0–800 ms（截取为 400 个采样点，采样率 500 Hz，每个时间步 2 ms）。
    ```python
    53: TMIN = 0.0
    54: TMAX = 0.8
    146: evoked.crop(tmin=TMIN, tmax=TMAX, include_tmax=False)
    ```
  - 通道配置：64 个 EEG 传感器（读取自输入 Evoked FIF 文件信息）。
    ```python
    152: channels = list(info["ch_names"])
    ```
  - 空间与时间邻接 (Adjacency)：
    ```python
    603: adjacency, adjacency_names = mne.channels.find_ch_adjacency(info, ch_type="eeg")
    470: max_step=1,
    490: max_step=1,
    ```
  - 形成阈值 (Cluster-forming threshold) 与置换参数：
    ```python
    56: FORMING_ALPHA = 0.05
    461: threshold = float(stats.t.ppf(1 - FORMING_ALPHA / 2, df=df1))
    481: threshold = float(stats.f.ppf(1 - FORMING_ALPHA, dfn=df1, dfd=df2))
    465: n_permutations=args.n_permutations,  # 默认值 5000（L573: default=5000）
    466: tail=0,  # t 检验双尾
    486: tail=1,  # F 检验单尾
    469: seed=test_spec["seed"],  # 基础种子 SEED=42 (L57)
    471: out_type="indices",
    472: buffer_size=512,
    ```
  - 严格敏感性分析参数（见 `audit_cluster_reliability.py`）：
    ```python
    560: mod.FORMING_ALPHA = 0.01  # 敏感性检验下 cluster-forming threshold 收紧至 alpha=0.01
    ```

#### (2) 比较设计 (Comparisons)
脚本完整运行 6 项预设检验（`GROUPS = ["TD", "MD", "ADHD", "RD"]`）：
1. `01_condition_main_effect_all`: 全体被试（$N=95$）条件主效应 NoGO − GO（双尾 $t$ 检验）。
2. `02_condition_by_group_interaction`: 条件 × 组别交互项（4 组单因素 ANOVA $F$ 检验）。
3. `03_within_td_condition_effect`: TD 组内（$n=31$）NoGO − GO（双尾 $t$ 检验）。
4. `04_within_md_condition_effect`: MD 组内（$n=23$）NoGO − GO（双尾 $t$ 检验）。
5. `05_within_adhd_condition_effect`: ADHD 组内（$n=20$）NoGO − GO（双尾 $t$ 检验）。
6. `06_within_rd_condition_effect`: RD 组内（$n=21$）NoGO − GO（双尾 $t$ 检验）。
- 事后检验（`posthoc_01_td_vs_md`, `posthoc_02_td_vs_adhd`, `posthoc_03_td_vs_rd`）：代码中设定为“当且仅当交互项显著时触发”（L657-658）。实测交互项检验无显著簇（最小簇 $p=0.459$），故未触发执行。

#### (3) 结果文件与变量清查 (Result Files)
结果存储根目录：`C:\Users\ASUS\Dropbox\metaphor_production\gn_manuscript\03-ERP_topomap\03_cluster_inference\01_cluster_based_permutation_0000_0800ms\`

每个检验子目录（`01_condition_main_effect_all` ~ `06_within_rd_condition_effect`）均产出以下标准文件：

| 文件名 (File) | 格式 | 磁盘存在 | 文件大小 | 变量/键名 (Key) | 形状 (Shape) | 数据类型 (Dtype) | 含义与说明 |
|---|---|---|---|---|---|---|---|
| `all_cluster_indices.npz` | NPZ | 是 | 9 ~ 18 KB | `cluster_p_values`<br>`cluster_{i}_time_indices`<br>`cluster_{i}_channel_indices` | `(n_clusters,)`<br>`(n_voxels,)`<br>`(n_voxels,)` | float64<br>int64<br>int64 | 所有簇的 $p$ 值以及每个簇在时空网格上的时间点索引和通道索引 |
| `observed_statistic.npy` | NPY | 是 | 102,528 B | 数组本体 | `(400, 64)` | float32 | 观测统计量时空矩阵（400 时间点 × 64 通道，为 $t$ 值或 $F$ 值） |
| `cluster_p_values.npy` | NPY | 是 | 150 ~ 380 B | 数组本体 | `(n_clusters,)` | float64 | 所有已检出簇的 Monte Carlo 置换 $p$ 值 |
| `null_max_cluster_distribution.npy` | NPY | 是 | 40,128 B | 数组本体 | `(5000,)` | float64 | 5000 次置换中记录的最大簇质量原假设分布 ($H_0$) |
| `significant_cluster_union_mask.npy` | NPY | 是 | 25,728 B | 数组本体 | `(400, 64)` | bool | 显著簇 ($p<0.05$) 在时空矩阵上的并集布尔掩码 |
| `cluster_summary_all.csv` | CSV | 是 | 1.8 ~ 6.5 KB | 表格字段 | 16 列 | - | 包含 cluster_id, p_cluster, significant_p_lt_0_05, time_start_ms, time_end_ms, duration_ms_inclusive, channels, cluster_mass, peak_stat, peak_time_ms, peak_channel 等完整指标 |
| `cluster_summary_significant.csv` | CSV | 是 | 0.3 ~ 2.4 KB | 表格字段 | 16 列 | - | 仅过滤保留 $p<0.05$ 显著簇的摘要表 |
| `test_metadata.json` | JSON | 是 | ~1.5 KB | 键值对 | - | - | 单项检验元数据（阈值、置换数、种子、显著簇数等） |

根目录下全局文件：
- `eeg_sensor_adjacency.npz`: 64 通道 EEG Delaunay 三角剖分稀疏相邻矩阵（CSR matrix, 713 B）。
- `all_tests_summary.csv`: 6 项检验汇总表。
- `significant_clusters_all_tests.csv`: 跨检验所有显著簇扁平总表。
- `input_manifest.csv`: 95 名被试文件路径与哈希。

**元数据完整性判定**：
- `times` 已保存？：**部分**（NPY/NPZ 二进制数组中未保存时间刻度数组；但在对应的 CSV 摘要表与根目录 `run_metadata.json` 中保存了 `time_start_ms`, `time_end_ms`, `peak_time_ms` 及 `[0.0, 800.0]` ms 范围）。
- 通道名已保存？：**部分**（NPY/NPZ 二进制数组中未保存通道名；但在 CSV 摘要表 `channels` 列以分号分隔字符串形式保存了所有涉及通道名称）。

#### (4) 已绘制图表 (Figures)
1. 脚本内置图表（保存在各检验子目录下）：
   - `cluster_statistic_overview.png`: 观测统计量时空分布全景热图及显著簇掩码覆盖区。
   - `significant_cluster_{id:03d}.png`: 显著簇详图（如 `01_condition_main_effect_all` 中的 cluster 005, 008, 009；各组组内检验对应的显著簇拓扑图与光栅图）。
2. MNE 风格图族（保存在 `03_cluster_inference/02_mne_style_figures/`，由 `plot_cluster_results_mne_style.py` 绘制）：
   - `mne_style_masked_channel_time.png`: 6 个检验的通道 × 时间显著掩码矩阵图。
   - `mne_style_topomap_N2_300_400ms.png`, `mne_style_topomap_P3_Cz_450_650ms.png`, `mne_style_topomap_P3_Pz_400_600ms.png`: 关键窗口地形图。
   - `mne_style_cluster_{id}_joint.png`: 显著簇诱发波形与地形图联合展示图。
3. 审查与诊断图（保存在 `03_cluster_inference/03_reliability_audit/`，由 `audit_cluster_reliability.py` 绘制）：
   - `bridge_{test}_cluster_{id}.png`: 簇持续时间与有效传感器数量诊断光栅图。
   - `a_priori_{ROI}_difference_by_group.png`: Central P3, Frontal N2, Parietal LPP 差异组间对比图。

---

### 2. `10-ERP_stats/01_v1_tfce/`
（核心引擎：`stats_engine.py`；分析脚本：`01_build_data.py`, `04_rq0.py`, `05_rq1_diff.py`, `06_rq1_avg.py`；校验与制图：`02a/b`, `03a/b`, `07_descriptives_figures.py`, `08_report_and_check.py`）

#### (1) 脚本与参数配置 (Script & Parameters)
- **文件绝对路径**：`C:\Users\ASUS\Dropbox\metaphor_production\gn_manuscript\10-ERP_stats\01_v1_tfce\code\stats_engine.py`
- **调用函数**：
  - 补丁优化 MNE 核心空间聚类算法：`cluster_level._fast_get_clusters_spatial` (L12-34)
  - 组合时空相邻矩阵：`mne.stats.combine_adjacency(n_times, spatial_adj)` (`stats_engine.py` L61)
  - 自定义 TFCE 积分计算：`compute_tfce` (`stats_engine.py` L65-108)
  - 置换引擎：
    - `run_rq0_tfce` (`stats_engine.py` L110-156)
    - `run_rq1_f_tfce` (`stats_engine.py` L174-239)
    - `run_rq1_posthoc_tfce` (`stats_engine.py` L242-307)
- **检验类型与统计量函数**：
  - RQ0: 配对差值双尾符号翻转 $t$ 检验（Sign-flip test on paired differences）。
  - RQ1 F: 4 组单因素 ANCOVA $F$ 检验，通过 Freedman-Lane 置换方案严格控制居中性别协变量 `sex_c`。
  - RQ1 post-hoc: 组间两样本独立 $t$ 检验（控制性别），经 Holm-Bonferroni 多重比较校正。
- **参数代码引证（含行号）**：
  - TFCE 参数：
    ```python
    7: TFCE_PARAMS = dict(start=0, step=0.2, h_power=2, e_power=0.5)
    65: def compute_tfce(stat_map, tail, adj_st, tfce_params=None, H=2.0, E=0.5, dh=0.2):
    ```
  - 置换次数与种子：
    ```python
    110: def run_rq0_tfce(diff_data, adj_st, n_perm=5000, seed=20260924, n_jobs=12):
    174: def run_rq1_f_tfce(Y, group, sex_c, adj_st, n_perm=5000, seed=20260924, n_jobs=12):
    242: def run_rq1_posthoc_tfce(Y, group, sex_c, adj_st, target_group='MD', n_perm=5000, seed=20260924, n_jobs=12):
    ```
    （在 `05_rq1_diff.py` 和 `06_rq1_avg.py` 中将 5000 次置换拆分为 10 个批次，每批 500 次并行执行以支持断点恢复）。
  - 尾向设定 (Tail) 与 FWER 校正：
    ```python
    112: # tail=0 for two-tailed (t-test), 1 for one-tailed positive (F-test)
    155: p_fwer = np.mean(H0[:, None, None] >= np.abs(tfce_obs)[None, :, :], axis=0)  # 双尾 p 取 |TFCE|
    ```
  - 时间窗口与通道：
    ```python
    # 01_build_data.py
    95: # Crop to 0.0 - 0.8 s, convert to uV, shape (n_subj, n_times, n_ch)
    109: evoked.crop(0.0, 0.8, include_tmax=True)  # 401 个时间点 (0~800 ms)
    122: spatial_adj, _ = mne.channels.find_ch_adjacency(evoked.info, ch_type='eeg')  # 64 通道
    ```

#### (2) 比较设计 (Comparisons)
1. **RQ0（效应量存在性）**：
   - 样本量：$N=128$（在 130 名入组被试中剔除 NoGO nave < 20 的 2 名被试 0797 和 1938）。
   - 对比：全体被试内的 `NoGO - GO` 配对条件差异。
2. **RQ1 diff（条件差异的组间变异）**：
   - 样本量：$N=93$（TD=31, MD=23, RD=19, ADHD=20），均具有有效性别标签。
   - 对比对象：个体差值波 `Y_diff = nogo_data - go_data`。
   - 检验：4 组间单因素 ANCOVA $F$ 检验；3 组事后对比：`MD vs TD`, `RD vs TD`, `ADHD vs TD`（控制性别协变量，采用 Holm 校正）。
3. **RQ1 avg（基础反应的组间变异）**：
   - 样本量：$N=93$。
   - 对比对象：个体均值波 `Y_avg = (nogo_data + go_data) / 2.0`。
   - 检验：4 组间单因素 ANCOVA $F$ 检验及 3 组事后独立样本对比（控制性别，Holm 校正）。

#### (3) 结果文件与变量清查 (Result Files)
结果存储目录：`C:\Users\ASUS\Dropbox\metaphor_production\gn_manuscript\10-ERP_stats\01_v1_tfce\`

| 文件路径 (Path) | 格式 | 磁盘存在 | 大小 | 变量名 (Key) | 形状 (Shape) | 类型 (Dtype) | 含义与说明 |
|---|---|---|---|---|---|---|---|
| `data/arrays.npz` | NPZ | 是 | 101,365,372 B | `diff`<br>`avg`<br>`GO`<br>`NoGO`<br>`ids`<br>`group`<br>`sex_c`<br>`in_rq1`<br>`times`<br>`ch_names`<br>`ch_adjacency` | `(128, 401, 64)`<br>`(128, 401, 64)`<br>`(128, 401, 64)`<br>`(128, 401, 64)`<br>`(128,)`<br>`(128,)`<br>`(128,)`<br>`(128,)`<br>`(401,)`<br>`(64,)`<br>`()` | float64<br>float64<br>float64<br>float64<br><U4<br><U7<br>float64<br>bool<br>float64<br><U4<br>object | 原始分析对齐数组：包含单被试波形、条件差值波、组别标签、性别中心化协变量、时间轴、通道名称及空间邻接图 |
| `data/rq0_results.npz` | NPZ | 是 | 281,854 B | `t_obs`<br>`tfce_obs`<br>`p_fwer`<br>`H0` | `(401, 64)`<br>`(401, 64)`<br>`(401, 64)`<br>`(5000,)` | float64<br>float64<br>float64<br>float64 | RQ0 观测 $t$ 值时空图、观测 TFCE 积分值时空图、FWER 校正后 $p$ 值时空图、5000 次置换的最大 TFCE 原假设分布 |
| `data/rq1_diff_results.npz` | NPZ | 是 | 1,044,994 B | `F_obs`, `tfce_f`, `p_f_fwer`, `H0_f`<br>`t_md`, `tfce_md`, `p_md_fwer`, `p_md_holm`, `H0_md`<br>`t_rd`, `tfce_rd`, `p_rd_fwer`, `p_rd_holm`, `H0_rd`<br>`t_adhd`, `tfce_adhd`, `p_adhd_fwer`, `p_adhd_holm`, `H0_adhd` | 各统计图均为 `(401, 64)`；<br>各 H0 均为 `(5000,)` | 全部 float64 | RQ1 差值波的主效应 $F$ 检验及三组事后 $t$ 检验的完整观测值、TFCE、FWER $p$ 值、Holm 校正 $p$ 值及 $H_0$ 分布 |
| `data/rq1_avg_results.npz` | NPZ | 是 | 1,045,025 B | 与 `rq1_diff_results.npz` 键名与结构完全一致 | 同上 | 全部 float64 | RQ1 均值波的主效应 $F$ 检验及三组事后 $t$ 检验结果集合 |
| `tables/*.csv.gz` | CSV.GZ | 是 | 350 ~ 385 KB | `time_ms`, `channel`, `stat`, `tfce`, `p_fwer`, `p_holm` | 25,664 行 (401×64) | - | 逐点（pointwise）统计量明细表 |
| `tables/*_summary.csv` | CSV | 是 | ~240 B | 汇总指标 | 1 行 | - | 覆盖窗口、最大值、显著通道数等汇总指标 |

**元数据完整性判定**：
- `times` 已保存？：**部分**（统计结果 NPZ 如 `rq0_results.npz` 内部未打包 `times`；但在同目录的 `data/arrays.npz` 中完整保存了 `times` (shape=(401,))，且所有导出 CSV 均包含 `time_ms` 列）。
- 通道名已保存？：**部分**（统计结果 NPZ 内部未打包；但在同目录的 `data/arrays.npz` 中完整保存了 `ch_names` (shape=(64,))，且所有导出 CSV 均包含 `channel` 列）。

#### (4) 已绘制图表 (Figures)
存储于 `10-ERP_stats/01_v1_tfce/figures/`：
- `fig1_rq0_waves.png`: RQ0 全脑波形与条件差值总览图。
- `fig2_rq0_tfce.png`: RQ0 TFCE 显著性时空分布图（呈现显著的 N2 与 P3 时空簇）。
- `fig3_rq1_diff.png`: RQ1 差异波的组间 $F$ 检验及事后对比 TFCE 图。
- `fig4_rq1_avg.png`: RQ1 均值波的组间 $F$ 检验及事后对比 TFCE 图。
- 补充材料逐点对比图：`figS_rq1_diff_F_pointwise.png`, `figS_rq1_diff_MD_vs_TD_pointwise.png`, `figS_rq1_diff_RD_vs_TD_pointwise.png`, `figS_rq1_diff_ADHD_vs_TD_pointwise.png`, 及对应的 `figS_rq1_avg_*_pointwise.png`。
- 仿真效度验证图：`figS_simulation.png`（模拟数据下的假阳性率与信号恢复率验证）。

---

### 3. `08-MVPA/run_mvpa.py` 与 `08-MVPA/frozen_mvpa/`

#### (1) 脚本与参数配置 (Script & Parameters)
- **文件绝对路径**：
  - `C:\Users\ASUS\Dropbox\metaphor_production\gn_manuscript\08-MVPA\run_mvpa.py`
  - `C:\Users\ASUS\Dropbox\metaphor_production\gn_manuscript\08-MVPA\frozen_mvpa\stats.py` 与 `stats_run.py`
- **调用函数**：
  - `run_mvpa.py`: `mne.stats.permutation_cluster_1samp_test` (L293)
  - `frozen_mvpa/stats.py`: 自定义 `onesample_cluster_test` (L150), `twosample_cluster_test` (L198), `omnibus_cluster_test` (L238), `correlation_cluster_test` (L312)
- **检验类型与统计量函数**：
  - 1D 解码准确率时序单样本 $t$ 检验（检验是否显著高于机会水平 50%）。
  - 2D 时间泛化（Temporal Generalization, TG）矩阵聚类置换检验。
  - 组间差异 $F$ 检验与事后对比。
- **参数代码引证（含行号）**：
  - `run_mvpa.py`:
    ```python
    293: _, clusters, p_values, _ = mne.stats.permutation_cluster_1samp_test(
    294:     values - CHANCE,  # CHANCE = 0.50
    295:     n_permutations=permutations,  # 默认 1000 (L414)
    296:     tail=0,
    297:     threshold=None,  # 按 MNE 默认值推断：选取双尾 p<0.05 对应 t 阈值
    298:     out_type="mask",
    299:     seed=seed,
    300:     verbose=False,
    301: )
    ```
  - `frozen_mvpa/stats.py`:
    ```python
    20: CROSS_2D = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], dtype=bool)  # 2D 4-连通邻接
    30: def _label_clusters(stat: np.ndarray, thresh: float, structure=None):
    39: def _sign_flip_maps(D: np.ndarray, n_perm: int, seed: int, chunk: int = 500) -> np.ndarray:
    ```
  - 时间窗口：-0.2 到 0.8 s (-200 到 800 ms，包含 120 个时间采样点)。
  - 通道：全脑 EEG 传感器模式作为解码特征（统计检验针对跨通道分类准确率时序进行）。

#### (2) 比较设计 (Comparisons)
- 总体准确率检验：全体被试解码率 vs 50%（含基线控制窗检查 `prestim_control`）。
- 组别内检验：TD, MD, ADHD, RD 各自的解码准确率 vs 机会水平。
- 组别间比较：ANOVA $F$ 检验及各临床组 vs TD 的事后比较。
- 行为关联：解码准确率与 Go 反应时（RT）的置换相关检验。

#### (3) 结果文件与变量清查 (Result Files)
结果存储路径：`C:\Users\ASUS\Dropbox\metaphor_production\gn_manuscript\08-MVPA\results\frozen_tracer\stats\dev\`

| 文件名 (File) | 格式 | 磁盘存在 | 大小 | 变量名 (Key) | 形状 (Shape) | 类型 (Dtype) | 含义与说明 |
|---|---|---|---|---|---|---|---|
| `mask_overall_accuracy.npz` | NPZ | 是 | 1,016 B | `mask`<br>`times` | `(120,)`<br>`(120,)` | bool<br>float64 | 全体被试解码准确率达到显著水平 ($p<0.05$) 的时间点布尔掩码与时间刻度 |
| `mask_group_TD.npz` | NPZ | 是 | 1,016 B | `mask`<br>`times` | `(120,)`<br>`(120,)` | bool<br>float64 | TD 组内部解码达到显著水平的时间点布尔掩码与时间刻度 |
| `overall_accuracy_clusters.csv` | CSV | 是 | 1,118 B | 表格字段 | 8 列 | - | 全体被试显著簇摘要（包含 cluster_id, start, end, length, direction, mass, p） |
| `overall_auc_clusters.csv` | CSV | 是 | 1,112 B | 表格字段 | 8 列 | - | 全体被试 AUC 显著簇摘要 |
| `group_TD_clusters.csv` | CSV | 是 | 1,076 B | 表格字段 | 8 列 | - | TD 组解码显著簇摘要 |
| `summary.json` | JSON | 是 | 29,572 B | 键值对 | - | - | 全部分析模块统计指标汇总字典 |

**元数据完整性判定**：
- `times` 已保存？：**是**（NPZ 内有 `times` 键，CSV 表格内有精确起止时间）。
- 通道名已保存？：**不涉及**（MVPA 统计对象为跨电极特征的标量解码准确率，无单通道维度）。

#### (4) 已绘制图表 (Figures)
存储于 `08-MVPA/results/frozen_tracer/figures/`：
- `fig01_decoding_overall.png`: 跨被试总体解码准确率时序图（含显著时段底纹）。
- `fig02_decoding_groups.png`: 四组各自的时间分辨解码准确率曲线。
- `fig03_auc_overall.png`: 总体 AUC 曲线图。
- `fig04_group_differences.png`: 组间差异检验图。
- `fig05_tg_overall.png`, `fig06_tg_groups.png`: 2D 时间泛化矩阵热图。
- `fig09_rt_association.png`: 解码表现与行为反应时关联图。

---

### 4. `figures_drawio/source_localization/05_roi_timecourses_balanced/plot_balanced_roi_timecourses.py`

#### (1) 脚本与参数配置 (Script & Parameters)
- **文件绝对路径**：`C:\Users\ASUS\Dropbox\metaphor_production\gn_manuscript\figures_drawio\source_localization\05_roi_timecourses_balanced\plot_balanced_roi_timecourses.py`
- **调用函数**：`mne.stats.permutation_cluster_1samp_test` (L156)
- **检验类型与统计量函数**：配对差值单样本 $t$ 检验（`difference = nogo[roi] - go[roi]`，L155）；`stat_fun` 采用默认值（按 MNE 文档推断为 `mne.stats.ttest_1samp_no_p`）。
- **参数代码引证（含行号）**：
  ```python
  43: TMIN, TMAX = 0.0, 0.8
  44: N_PERMUTATIONS = 5000
  45: RANDOM_SEED = 42
  46: ALPHA = 0.05
  47: FAMILY_ALPHA = ALPHA / len(ROI_PARCELS)  # 0.05 / 3 = 0.0167 (FWER 校正)
  151: threshold = stats.t.ppf(1.0 - ALPHA / 2.0, go[next(iter(go))].shape[0] - 1)  # t=1.9855
  156: t_values, clusters, p_values, _ = mne.stats.permutation_cluster_1samp_test(
  157:     difference,
  158:     threshold=threshold,
  159:     n_permutations=N_PERMUTATIONS,
  160:     tail=0,
  161:     out_type="mask",
  162:     seed=RANDOM_SEED,
  163:     n_jobs=1,
  164:     verbose=False,
  165: )
  ```
  - 空间邻接：无（1D 时间序列聚类，`adjacency=None`，按 MNE 默认值推断）。
  - 通道/区域：3 个双侧皮层 ROI（`Visual`: V1~V4; `ACC / pre-SMA`: a24, p24, 6ma 等; `Parietal`: IPS1, 7AL 等）。
  - 数据类型：皮层源估计 dSPM 幅值时序（非负标量幅值）。

#### (2) 比较设计 (Comparisons)
- 纳入全体 95 名被试（TD: 31, ADHD: 20, MD: 23, RD: 21）。
- 在每个预设 ROI 内检验 NoGo vs Go 的配对差异（$N=95$ 配对单样本 $t$ 检验），并在 3 个 ROI 族系间实施 Bonferroni-FWER 校正（显著性临界设为 $\alpha = 0.0167$）。

#### (3) 结果文件与变量清查 (Result Files)
结果存储目录：`C:\Users\ASUS\Dropbox\metaphor_production\gn_manuscript\figures_drawio\source_localization\05_roi_timecourses_balanced\data\`

| 文件名 (File) | 格式 | 磁盘存在 | 大小 | 变量名/字段 (Fields) | 形状/行数 | 数据类型 | 含义与说明 |
|---|---|---|---|---|---|---|---|
| `paired_cluster_results.csv` | CSV | 是 | 1,235 B | `roi`, `cluster`, `start_ms`, `end_ms`, `duration_ms`, `cluster_mass_abs_t`, `p_value`, `significant_within_roi_p05`, `significant_fwer_3roi_p0167` | 15 行 (含表头) | - | 检出的所有时间簇详细指标表：Visual 检出 2 个显著簇 (114–310 ms, $p=0.0012$; 410–800 ms, $p=0.0002$)，ACC 及 Parietal 簇未达到 FWER 显著阈值 |
| `roi_timecourses_long.csv` | CSV | 是 | 6,396,446 B | `participant`, `group`, `roi`, `time_ms`, `go_dspm`, `nogo_dspm`, `diff_dspm` | 114,286 行 | - | 单被试长格式时间序列数据表 |
| `sample_indices.csv` | CSV | 是 | 2,735 B | `participant`, `group` | 96 行 | - | 被试入组样本清单 |

**元数据完整性判定**：
- `times` 已保存？：**是**（`paired_cluster_results.csv` 中保存了起止毫秒与持续时间；`roi_timecourses_long.csv` 保存了完整时间采样点）。
- 通道名已保存？：**是**（以明确的 ROI 名称 `Visual`, `ACC / pre-SMA`, `Parietal` 保存）。

#### (4) 已绘制图表 (Figures)
存储于 `figures_drawio/source_localization/05_roi_timecourses_balanced/figures/`：
- `figure_balanced_roi_timecourses.png` (877 KB) & `.svg` (73 KB): 3 个 ROI 的 Go/NoGo 源幅值时间波形图（含 95% 置信区间及通过 FWER 校正的显著时间簇条带）。
- `figure_balanced_roi_differences.png` (741 KB) & `.svg` (67 KB): 3 个 ROI 的 NoGo − Go 差值波形图。

---

### 5. `notebooks/batch_source_localization.ipynb` (Cell 9)

#### (1) 脚本与参数配置 (Script & Parameters)
- **文件绝对路径**：`C:\Users\ASUS\Dropbox\metaphor_production\gn_manuscript\notebooks\batch_source_localization.ipynb` (代码单元 9)
- **调用函数**：`mne.stats.spatio_temporal_cluster_1samp_test` (Cell 9, L12, L435)
- **检验类型与统计量函数**：TD 组皮层逐顶点时空差值单样本 $t$ 检验；`stat_fun` 采用默认值（按 MNE 文档推断为 `mne.stats.ttest_1samp_no_p`）。
- **参数代码引证（含行号）**：
  ```python
  53: TEST_TMIN = 0.000
  54: TEST_TMAX = 0.800
  58: CLUSTER_FORMING_P = 0.001
  61: CLUSTER_ALPHA = 0.05
  64: TAIL = 0
  67: N_PERMUTATIONS = 5000
  70: SEED = 42
  74: N_JOBS = -1
  77: MAX_STEP = 1
  396: adjacency = mne.spatial_src_adjacency(SRC)  # 源空间表面空间邻接矩阵
  415: t_threshold = stats.t.ppf(1.0 - CLUSTER_FORMING_P / 2.0, df=df)  # df=30, t=3.6460
  434: T_obs, clusters, cluster_p_values, H0 = (
  435:     spatio_temporal_cluster_1samp_test(
  436:         X=X,  # shape=(31, 401, 5124)
  438:         threshold=t_threshold,
  440:         n_permutations=N_PERMUTATIONS,
  442:         tail=TAIL,
  444:         adjacency=adjacency,
  446:         max_step=MAX_STEP,
  448:         out_type="indices",
  450:         check_disjoint=True,
  452:         step_down_p=0,
  454:         t_power=1,
  456:         buffer_size=1000,
  458:         n_jobs=N_JOBS,
  460:         seed=SEED,
  462:         verbose=True,
  463:     )
  464: )
  ```
  - 空间邻接：`Parviainen_7-11` 模板源空间（`oct-6` 表面网格），5124 个顶点，相邻矩阵形状 `(5124, 5124)`。
  - 数据类型：单被试 NoGo − Go 平衡 dSPM 源估计幅值矩阵。

#### (2) 比较设计 (Comparisons)
- 针对 TD 正常发育组（$n=31$），在 0–800 ms 窗口内对全皮层表面所有 5124 个源顶点检验 NoGo 幅值是否显著高于/低于 Go 幅值。

#### (3) 结果文件与变量清查 (Result Files)
结果存储路径：`C:\Users\ASUS\Dropbox\metaphor_production\gn_manuscript\06-source analysis\source_statistics\TD_NoGo_minus_GO_cluster\TD_NoGo-minus-GO_spatiotemporal_cluster_000-800ms.npz`

| 文件格式 | 磁盘存在 | 文件大小 | 变量名 (Key) | 形状 (Shape) | 数据类型 (Dtype) | 含义与说明 |
|---|---|---|---|---|---|---|
| NPZ | 是 | 15,891,547 B | `T_obs`<br>`cluster_p_values`<br>`H0`<br>`times`<br>`lh_vertices`<br>`rh_vertices`<br>`contrast_files`<br>`n_subjects`<br>`cluster_forming_p`<br>`cluster_alpha`<br>`n_permutations` | `(401, 5124)`<br>`(1004,)`<br>`(5000,)`<br>`(401,)`<br>`(2562,)`<br>`(2562,)`<br>`(31,)`<br>`()`<br>`()`<br>`()`<br>`()` | float64<br>float64<br>float64<br>float64<br>int64<br>int64<br><U154<br>int64<br>float64<br>float64<br>int64 | 观测 $t$ 值时空场矩阵 (401 时间点 × 5124 顶点)、全部 1004 个检出簇的置换 $p$ 值、5000 次置换的最大簇 $t$ 和分布、时间数组 (0~0.8 s)、左右脑表面顶点索引列表、输入单被试文件路径及统计参数 |

**元数据完整性判定**：
- `times` 已保存？：**是**（直接打包于 `times` 键中，401 个采样点）。
- 通道名已保存？：**否**（源空间数据无通道名，保存的是左右半球几何顶点编号 `lh_vertices`, `rh_vertices`）。

#### (4) 已绘制图表 (Figures)
- 交互渲染：Notebook 代码中通过 PyVista 调用 `stc_cluster_summary.plot(...)` 直接在 Notebook 交互界面中展示 3D 皮层显著簇拓扑分布。
- 磁盘图像导出：**未找到**（脚本仅在 Notebook 内存中渲染，未将静态 PNG 写入磁盘）。

---

### 6. `05-microstate_GA/code/run_condition_tanova_duration.py` 与 `04-Ragu/Ragu_statistics/`

#### (1) 脚本与参数配置 (Script & Parameters)
- **文件绝对路径**：
  - 重算校验脚本：`C:\Users\ASUS\Dropbox\metaphor_production\gn_manuscript\05-microstate_GA\code\run_condition_tanova_duration.py`
  - 原始 Ragu 结果文件：`C:\Users\ASUS\Dropbox\metaphor_production\gn_manuscript\04-Ragu\Ragu_statistics\TANOVA_results.mat`
- **检验类型**：
  - 基于全脑地形图全异度（Global Map Dissimilarity, GMD）的地形图方差分析（TANOVA），采用被试内条件标签置换方案（5000 次置换）。
  - 多重比较校正方法：时间持续时间簇阈值法（Duration-corrected cluster extent），即统计置换原假设下连续显著时间帧的最长持续时间分布（Longest run of consecutive significant frames）。
- **参数代码引证（含行号）**：
  ```python
  # 05-microstate_GA/code/run_condition_tanova_duration.py
  77: def gmd(a: np.ndarray, b: np.ndarray, axis: int) -> np.ndarray:
  78:     """Global map dissimilarity between two map sets, each normalised first."""
  83: def longest_true_run(mask: np.ndarray) -> np.ndarray:
  84:     """Longest run of consecutive True per row of a (nRuns, nTime) mask."""
  108: ap.add_argument("--window", type=float, nargs=2, default=[0.0, 800.0], ...)
  111: ap.add_argument("--iterations", type=int, default=5000)
  112: ap.add_argument("--alpha", type=float, default=0.05)
  113: ap.add_argument("--seed", type=int, default=42)
  114: ap.add_argument("--group-weighting", choices=["equal", "none"], default="equal")
  ```

#### (2) 比较设计 (Comparisons)
- 95 名被试（TD: 31, MD: 23, RD: 21, ADHD: 20），对比 Go vs NoGo 的地形图拓扑差异（条件主效应）。

#### (3) 结果文件与变量清查 (Result Files)
1. 重算输出目录：`05-microstate_GA/01_main_v7_GFP2_k_selection/condition_tanova/`
   - `condition_tanova_p_timecourse.csv` (15,483 B, 存在: 是): 包含逐帧 $p$ 值、观测 GMD、显著掩码。
   - `run_record.json` (714 B, 存在: 是): 记录临界持续时间为 51 帧（102.0 ms），观测最大连续显著时程为 361 帧（80.0–800.0 ms），经验 $p = 0.0002$。
2. 原始 Ragu 数据文件：`04-Ragu/Ragu_statistics/TANOVA_results.mat` (200,396,425 B, 存在: 是)
   - 核心变量：
     - `rd.V`: `(95, 2, 64, 601)` float64（95 被试 × 2 条件 × 64 通道 × 601 时间点原始数据）。
     - `rd.PTanova`: `(2, 4, 601, 5000)` float64（置换 $p$ 值分布矩阵）。
     - `rd.TanovaEffectSize`: `(2, 4, 601, 5000)` float64。
     - `rd.CritDuration`: `(2, 4)` float64。
     - `rd.Channel`: `(64,)` object（通道名列表）。
     - `rd.time`: `(601,)` int16（时间点刻度）。
- `times` 已保存？：**是**（保存在 `rd.time` 与 CSV 导出表中）。
- 通道名已保存？：**是**（保存在 `rd.Channel` 中）。

#### (4) 已绘制图表 (Figures)
存储于 `04-Ragu/Ragu_statistics/TCT+TANOVA/`：
- `TCT_01` 至 `TCT_08` 系列 PNG（各组在 GO 与 NoGO 下的地形图一致性检验图及持续时间阈值标注，如 `TCT_01_ADHD__GO_Overall_p__0.0002_(min_duration__302_ms).png`）。
- `TCT_results_02_Group_Main_Effect.png`, `TCT_results_05_Condition_Effect.png`: 条件效应与组别效应地形图检验曲线。

---

## 扫描范围与遗漏说明 (Scan Scope & Boundaries)

### 检索策略与模式匹配
1. **脚本扫描**：
   - 后缀范围：`.py`, `.m`, `.R`, `.ipynb`, `.sh`
   - 检索关键词：`permutation_cluster`, `spatio_temporal_cluster`, `cluster_test`, `TFCE`, `tfce`, `threshold=dict(start`, `ft_timelockstatistics`, `ft_freqstatistics`, `ft_statistics_montecarlo`, `clusterstat`, `n_permutations`, `numrandomization`, `permutation`。
   - 命中 52 个相关文件，经代码逻辑深入排查后，精准锁定上述 6 套涉及聚类置换 / TFCE 统计推断的核心流程。
2. **结果文件扫描**：
   - 匹配模式：文件名中包含 `perm`, `cluster`, `tfce`, `clust`, `stat` 的非原始数据文件。

### 跳过与忽略的目录与内容
1. **版本控制与缓存目录**：`.git/`, `.pytest_cache/`, `__pycache__/`, `node_modules/`。
2. **巨量代理与折叠单位中间缓存**：`05-microstate_GA/01_main_v7_GFP2_k_selection/surrogate_adjacent/*/fold_units/` 等目录（单文件夹包含数千个中间折叠单元文件，非最终统计推断产物）。
3. **纯原始与预处理数据**：`00-done_epochs/` 下庞大的单被试 Raw/Epochs 文件，未被直接作为统计推断输出引用。
4. **非聚类置换的相关分析**：
   - `06-source analysis/brain_plots/analyze_td_go_nogo_preliminary.py`: 该脚本包含 100,000 次置换检验，但其为针对特定预选 ROI 标量均值的单点符号翻转置换检验，不包含时间或空间聚类（Non-cluster pointwise permutation），特此记录。
