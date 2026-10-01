# brain-plot 独立审查

审查日期：2026-10-01。基准：`04959bfc687c59f079f79a4a10bee0a68c1b0c98` 的当前工作区；行号对应本次读取版本。

已按要求先读 AGENTS.md、HANDOFF.md 的 State / Next、SKILL.md、docs/rules.md，再通读四个模块和五个测试文件，并核对最新 review-log、模块说明及依赖声明。没有修改代码、提交或切换分支，没有访问真实被试数据，也没有运行整套测试或长时间渲染。临时合成数据、缓存和 MNE 配置均放在系统临时目录。本次唯一持久新增文件为本报告。

总体判断：ERP 与微状态复用的数据加载器已有较完整的契约检查，ERP 的 V→µV、被试等权平均和被试间 SEM 实现正确；TFR 默认先逐被试计算平均功率、做 `10 log10(P / baseline)`、再等权平均，顺序也合理。主要风险集中在新增 TFR / source 绕过共同数据契约、缓存不随数据更新，以及源定位时间轴。**下列第 1–7 条应在继续将这些模块用于论文输出前修复。** 第 13、14 条是方法解释风险，不是把合法估计器判作计算错误。

严重度：P1＝可静默改变数据、时间、空间对应或量纲；P2＝特定输入下错误、方法报告不足或功能不可用；P3＝维护与测试结构问题。共 20 条，按严重度排序。

1. **[P1，已复现] source 将抽取后的数据强行解释为 100 Hz，峰潜伏期和窗口平均错误。**

   **位置：** [source_plot.py:300](C:/dev/brain-plot/brain-plot/source_plot.py:300)、[source_plot.py:331](C:/dev/brain-plot/brain-plot/source_plot.py:331)、[source_plot.py:347](C:/dev/brain-plot/brain-plot/source_plot.py:347)。

   `round(sfreq / 100)` 后调用 `decimate` 只保证接近 100 Hz；随后却把 `info_sub['sfreq']` 固定成 100，并以该 Info 重新创建 Evoked。250 Hz 输入抽取两倍后实际为 125 Hz。本次使用同一段 MNE 操作复现：真实 400 ms 峰被标为 550 ms，实际结束于 1000 ms 的数组被标至 1300 ms；512 Hz 输入也出现偏移。并且 `decimate` 本身不做抗混叠滤波，代码没有检查输入低通是否适合目标采样率。

   **修法：** 保留真实抽取后的 sfreq、tmin 与 Info，缓存这些元数据；每个重建对象的 `times` 必须与缓存时间数组一致。最小安全方案是保持原采样率；若确需降采样，应在明确的抗混叠条件下进行，不能改写标签来模拟重采样。

   **测试缺口：** [test_source.py:18](C:/dev/brain-plot/brain-plot/test/test_source.py:18) 和 [test_source.py:75](C:/dev/brain-plot/brain-plot/test/test_source.py:75) 只用 100 Hz，必然漏过此错误。增加 250 / 512 / 1000 Hz 已知脉冲，断言完整时间轴和窗口索引，而不只检查图文件存在。

2. **[P1，已复现] TFR 与 source 缓存不包含输入文件指纹，重做预处理后仍使用旧结果。**

   **位置：** [tfr_plot.py:130](C:/dev/brain-plot/brain-plot/tfr_plot.py:130)、[tfr_plot.py:153](C:/dev/brain-plot/brain-plot/tfr_plot.py:153)；[source_plot.py:188](C:/dev/brain-plot/brain-plot/source_plot.py:188)、[source_plot.py:205](C:/dev/brain-plot/brain-plot/source_plot.py:205)、[source_plot.py:238](C:/dev/brain-plot/brain-plot/source_plot.py:238)。

   TFR 键只有计算参数和 subject ID；source 的被试缓存及总平均键也没有 FIF 路径、大小、修改时间或内容摘要。更新同名 FIF、修改坏导处理或重做基线后，可直接命中旧数组。source 总平均命中甚至在重新读入被试数据前返回。与 [SKILL.md:46](C:/dev/brain-plot/brain-plot/SKILL.md:46)“输入文件变化即失效”相反。

   **核验：** 临时目录中替换同名 FIF，两个模块都返回与原结果逐元素完全相同的缓存值；改用新缓存目录后结果改变。source 核验替换了昂贵的 forward / inverse 调用，仅测试真实的读入和缓存控制流程，没有据此声称验证逆解数值。

   **修法：** 复用 [erp_plot.py:533](C:/dev/brain-plot/brain-plot/erp_plot.py:533) 的文件指纹模式，加计算实现版本和相关 MNE 版本；总平均键依赖各被试缓存身份，不能只依赖被试名单。缓存同时保存通道和时间元数据，命中时检查。

   **测试缺口：** [test_tfr.py:118](C:/dev/brain-plot/brain-plot/test/test_tfr.py:118) 只验证命中，没有验证失效。分别测试改变一个输入、一个计算参数，以及不应影响计算的图形参数。

3. **[P1，静态确认] source 会从任意兄弟缓存目录拿 forward，可能使用错误的头模型或电极几何。**

   **位置：** [source_plot.py:158](C:/dev/brain-plot/brain-plot/source_plot.py:158)、[source_plot.py:198](C:/dev/brain-plot/brain-plot/source_plot.py:198)、[source_plot.py:209](C:/dev/brain-plot/brain-plot/source_plot.py:209)。

   src / BEM 的身份仅取 basename，传入对象则固定叫 `custom-src` / `custom-bem`。新参数目录没有 forward 时，代码直接读取 `sibling_fwds[0]`，不比较源顶点、BEM、电导率、电极位置或变换。即使更换文件名产生了新参数目录，仍可能复制旧 forward；同名不同内容更不会失效。源定位的空间解释依赖这些信息，不能以“通道名相同”替代。

   **修法：** forward 使用独立几何键，覆盖有序通道位置/类型、坐标系、trans、src 顶点及 BEM 内容；只复用完全匹配的键。对传入对象计算稳定摘要或禁用持久复用，校验 forward 与当前 src 的顶点一致。

   **测试缺口：** [test_source.py:79](C:/dev/brain-plot/brain-plot/test/test_source.py:79) 先建 forward 再注入，绕过了生产缓存选择。用 mock 测试改变 montage、BEM、同名 src 时不得复用，单改 lambda2 时可以复用。

4. **[P1，部分已复现] TFR / source 没有落实 S1，可能按数组位置平均不同电极、时间或参考的数据。**

   **位置：** [tfr_plot.py:90](C:/dev/brain-plot/brain-plot/tfr_plot.py:90)、[tfr_plot.py:149](C:/dev/brain-plot/brain-plot/tfr_plot.py:149)、[tfr_plot.py:181](C:/dev/brain-plot/brain-plot/tfr_plot.py:181)；[source_plot.py:276](C:/dev/brain-plot/brain-plot/source_plot.py:276)、[source_plot.py:326](C:/dev/brain-plot/brain-plot/source_plot.py:326)、[source_plot.py:355](C:/dev/brain-plot/brain-plot/source_plot.py:355)。规则见 [docs/rules.md:14](C:/dev/brain-plot/docs/rules.md:14)、[docs/rules.md:92](C:/dev/brain-plot/docs/rules.md:92)、[docs/rules.md:107](C:/dev/brain-plot/docs/rules.md:107)。

   TFR 用首文件 Info 解读所有被试数组，没有逐被试比较通道顺序/位置、单位、参考、投影、滤波和时间网格；相同 shape 不等于相同测量。本次将第二被试通道倒序，`load_and_compute` 照常纳入两人。source 只比较通道名，不比较位置及时间轴，也没有共同的有限值检查。两者遇到不可读文件还会 warning 后跳过，改变有效样本，而 SKILL 宣称输入问题会停止；首次成功后这种缩减样本还能进入缓存。

   **修法：** 提取并复用 ERP 的契约验证，先检查每个 Epochs 的原始契约，再做模块允许的转换；缓存后重新验证身份。source 的平均参考/基线处理应明确列为受控例外，处理后再检查一致性。不可读被试默认停止，由明确排除名单决定样本。

   **测试缺口：** 用同 shape 的错序通道、偏移 tmin、不同 montage/参考/滤波、NaN 和不可读第二文件做负例；断言指出具体被试及字段，且不得生成总平均。

5. **[P1，已复现] TFR 的边界安全区小于 MNE Morlet 的实际支持范围，基线仍可受边缘影响。**

   **位置：** [tfr_plot.py:98](C:/dev/brain-plot/brain-plot/tfr_plot.py:98)、[tfr_plot.py:112](C:/dev/brain-plot/brain-plot/tfr_plot.py:112)；[docs/rules.md:97](C:/dev/brain-plot/docs/rules.md:97)。

   `(n_cycles / f) / 2` 是所用“周期时长”的一半，不是 MNE 截断小波的一半。MNE 的 Morlet 支持范围约为 ±5σ，其中 σ＝n_cycles/(2πf)。默认 `n_cycles=freqs/2`、250 Hz 下，本次实际生成的小波半长度为 **396 ms**，代码仅留 **250 ms**。对于 −1000 ms 起始的 epoch，−750 ms 会被接受，但仍落在卷积边缘区。不能将“通过检查”报告为使用了完整小波。公式依据：[MNE 官方实现说明](https://github.com/mne-tools/mne-python/blob/main/mne/utils/docs.py)。

   **修法：** 从实际生成的小波长度计算每个频率的半支持范围，再取最大值。若有意使用更短的有效支持阈值，应明确其衰减标准及残余误差，不能称为完整半波长。此外，“基线早于第一刺激”还应考虑小波向未来延伸的范围。

   **测试缺口：** [test_tfr.py:161](C:/dev/brain-plot/brain-plot/test/test_tfr.py:161) 只覆盖明显贴边窗口。增加恰处于 250–396 ms 距离区间的边界案例，以实际小波数组而不是代码原公式作为测试基准。

6. **[P1，静态确认] source 固定截成 −200…1000 ms，再对越界窗口静默取交集，图题仍写完整窗口。**

   **位置：** [source_plot.py:302](C:/dev/brain-plot/brain-plot/source_plot.py:302)、[source_plot.py:444](C:/dev/brain-plot/brain-plot/source_plot.py:444)、[source_plot.py:515](C:/dev/brain-plot/brain-plot/source_plot.py:515)。

   用户数据即使延伸到 2000 ms，代码也只保留到 1000 ms。绘图只检查 `t_mask.any()`，不检查完整上下界。请求 800–1200 ms 时，可能实际只平均 800–1000 ms，却标注 800–1200 ms；timeline 的 `half_width_ms` 同样受影响。结合第 1 条还可能选择到错误的真实时间段。

   **修法：** 根据已确认 windows / timeline 保留需要的时间范围，或保持完整 epoch；绘图前检查每个窗口完全位于实际时间网格内且包含样本。记录请求范围与实际首末样本，任何截断须显式处理，不能默许。

   **测试缺口：** 覆盖一端越界、完全越界、数据有晚期但内部 crop 将其删除、时间点窗口的两端越界；应在调用 3D renderer 前停止。

7. **[P1，已复现] TFR 的非 logratio 基线结果统一标为 dB，量纲错误。**

   **位置：** [tfr_plot.py:109](C:/dev/brain-plot/brain-plot/tfr_plot.py:109)、[tfr_plot.py:177](C:/dev/brain-plot/brain-plot/tfr_plot.py:177)、[tfr_plot.py:229](C:/dev/brain-plot/brain-plot/tfr_plot.py:229)、[tfr_plot.py:401](C:/dev/brain-plot/brain-plot/tfr_plot.py:401)、[tfr_plot.py:449](C:/dev/brain-plot/brain-plot/tfr_plot.py:449)。

   `baseline_mode` 被直接传给 MNE，允许 ratio、mean、percent、zscore 等。只有 logratio 分支乘 10，caption 和两种色条却无条件写 dB。ratio 是比值，mean 是功率差，zscore 是标准化值，都不是 dB。本次直接调用 caption 函数确认 ratio 仍产生 `Total power (dB relative to baseline)`。

   **修法：** 若 house style 只支持 dB，最简单是仅接受 logratio；若保留其他模式，集中定义模式→变换、单位、中心值与色标范围，并统一应用到正文面板、topomap 和 caption。

   **测试缺口：** 每个允许模式用已知 baseline/响应值验证数值和单位，例如 2 倍功率应为约 3.0103 dB 或 ratio 2，不能共享 dB 标签。

8. **[P2，API 行为已核实] source 仍是渐变透明，违反“硬阈值”，且脑图颜色与不透明色条不一致。**

   **位置：** [source_plot.py:136](C:/dev/brain-plot/brain-plot/source_plot.py:136)、[source_plot.py:544](C:/dev/brain-plot/brain-plot/source_plot.py:544)；[docs/rules.md:114](C:/dev/brain-plot/docs/rules.md:114)。

   `transparent=True` 明确要求 fmin–fmid 之间线性增加透明度；因此刚高于阈值的值与灰色皮层混合，不是阈值以上统一不透明。独立 Matplotlib `hot` 色条没有这层混色。官方文档和本机函数 docstring 一致：[MNE Brain.add_data](https://mne.tools/stable/generated/mne.viz.Brain.html#mne.viz.Brain.add_data)。review-log 虽声称已改硬阈值，当前代码仍未实现。

   **修法：** 使用明确的阈值 mask / 阶跃 alpha LUT，关闭自动 alpha 渐变，使低于 fmin 为透明、以上为不透明；不能只改成 `transparent=False` 就认为低值已隐藏。让色条与实际映射一致。

   **测试缺口：** [test_source.py:44](C:/dev/brain-plot/brain-plot/test/test_source.py:44) 的有色像素数测试无法识别 alpha 斜坡。增加 fmin 两侧及 fmin–fmid 内的 LUT 数值测试，再保留一个小型渲染集成测试。

9. **[P2，静态确认] source 窗口名重复会覆盖色标记录，先画的脑图配上后一个窗口的色条。**

   **位置：** [source_plot.py:66](C:/dev/brain-plot/brain-plot/source_plot.py:66)、[source_plot.py:457](C:/dev/brain-plot/brain-plot/source_plot.py:457)、[source_plot.py:540](C:/dev/brain-plot/brain-plot/source_plot.py:540)。

   validator 不要求 window name 唯一；两段都叫 N400 时，各自按自己的分位数画脑图，却以同一个 `window_N400` 键存储范围。绘制所有色条时再次查此字典，两个色条都拿到最后一个范围。这是实际的数值映射错误，不只是标签重复。TFR 的同名窗口也会覆盖 `_run.json` 中的 scale 记录。

   **修法：** 校验窗口名非空且唯一，或以稳定窗口 ID 存储并让每列携带自己的范围；不应只靠人类可读标签关联数值。

   **测试缺口：** 两个同名、数值范围相差十倍的窗口应在计算/渲染前报错；若允许同名，逐列核对 renderer 使用的范围、色条范围与 run 记录一致。

10. **[P2，已复现] TFR 条件网格可漏画/重复画条件，ROI 可重复通道并改变权重。**

    **位置：** [tfr_plot.py:39](C:/dev/brain-plot/brain-plot/tfr_plot.py:39)、[tfr_plot.py:41](C:/dev/brain-plot/brain-plot/tfr_plot.py:41)、[tfr_plot.py:287](C:/dev/brain-plot/brain-plot/tfr_plot.py:287)、[tfr_plot.py:319](C:/dev/brain-plot/brain-plot/tfr_plot.py:319)。

    网格只检查键存在；`conditions={A,B}` 下 `grid=[[A]]` 和 `grid=[[A,A,B]]` 都通过。本次也确认重复 channels 能通过；`[Fz,Fz,Cz]` 把 Fz 权重变为 2/3。图、caption 和 spec 因而不能保证表达同一组比较。

    **修法：** 复用 ERP / microstate 已有的唯一性和完整覆盖校验，要求网格扁平化后恰好覆盖每个条件一次，ROI 无重复；验证实际面板数量。空行/空网格应给出明确错误或明确默认规则。

    **测试缺口：** [test_tfr.py:183](C:/dev/brain-plot/brain-plot/test/test_tfr.py:183) 只测未知条件。补遗漏、重复、空行、重复通道与合法重排。

11. **[P2，静态确认并核验空掩码] TFR 窗口通过连续边界校验，却可能不包含任何离散频点或时间点。**

    **位置：** [tfr_plot.py:120](C:/dev/brain-plot/brain-plot/tfr_plot.py:120)、[tfr_plot.py:271](C:/dev/brain-plot/brain-plot/tfr_plot.py:271)、[tfr_plot.py:412](C:/dev/brain-plot/brain-plot/tfr_plot.py:412)。

    `freqs=[4,8,13,30]` 下的 9–10 Hz 窗口位于频率边界内部，能通过检查，但 f_mask 为空；301–302 ms 的窄窗也可能落在抽取后的两个样本之间。随后 `.mean()` 产生 NaN，再传入色限/绘图；JSON 写入也未禁用 NaN。用户可能在计算完所有被试后才遇到难理解的错误。

    **修法：** 对实际输出时间轴、实际频点使用统一 window selector，要求 mask 非空，并记录实际采样边界及点数；所有累计和色标值检查有限性，run 使用严格 JSON。不要自动扩大科学窗口。

    **测试缺口：** 加稀疏显式频率列表、decim 后无样本窗口、仅一个频点/时间点、以及 NaN 输入的负例。

12. **[P2，已复现] ERP localizer 支持相对极性峰，但 ROI 阈值仍依赖绝对电压，能返回空 ROI。**

    **位置：** [erp_plot.py:703](C:/dev/brain-plot/brain-plot/erp_plot.py:703)、[erp_plot.py:717](C:/dev/brain-plot/brain-plot/erp_plot.py:717)；[test_erp_plot.py:344](C:/dev/brain-plot/brain-plot/test/test_erp_plot.py:344)。

    峰检测允许负电位上的正向局部凸起，但 ROI 条件仍是 `sign * value >= 0.8 * sign * peak_val`。例如 +向峰的绝对电位为 −4 µV，连峰通道也不满足 −4 ≥ −3.2。本次 −5 µV 偏移加正高斯峰，输出了 300 ms 峰和 264–336 ms 窗口，但 `roi: []`。已有测试恰好构造了这种信号，却没断言 ROI。

    **修法：** 将 ROI 定义与峰的相对突出度/明确参考水平保持一致，或在无法可靠推导时不自动提出 ROI；必须保证返回的 ROI 合法并解释选择标准，不能默默把科学定义换成绝对值。

    **测试缺口：** 对同一局部峰施加正/负 DC 偏移，断言符合所选定义的 ROI，至少包括峰通道；再测试负向峰的对称情形。

13. **[P2，方法解释风险] dSPM 条件间试次数不同会影响噪声归一化值，等权平均不等于统一的源强或组水平统计量。**

    **位置：** [source_plot.py:307](C:/dev/brain-plot/brain-plot/source_plot.py:307)、[source_plot.py:347](C:/dev/brain-plot/brain-plot/source_plot.py:347)、[source_plot.py:369](C:/dev/brain-plot/brain-plot/source_plot.py:369)、[source_plot.py:566](C:/dev/brain-plot/brain-plot/source_plot.py:566)。

    代码将真实 nave 交给 `apply_inverse`，这是 MNE 正常用法；问题是论文解释契约不完整。dSPM 随 nave 的噪声归一化尺度变化，不能将不等试次数下的亮度差直接等同于神经电流增强。`pick_ori=None` 对 loose 源取幅值，逐被试取模再平均是非负的描述性量；平均后的图也不是组水平 z 检验或显著性图。官方例子明确说明 nave 的缩放影响：[MNE dSPM 单试次示例](https://mne.tools/1.12/auto_examples/inverse/compute_mne_inverse_epochs_in_label.html)。按列各自分位数定标又意味着不能只看颜色跨时间比较强弱。

    参数方面，`lambda2=1/9` 对应采用 SNR=3 的设定，`loose=0.2`、`depth=0.8` 不能仅因是固定值就判为错误，但也不是由当前数据验证出来的参数。代码已经逐被试估计 rank 并传入 covariance / inverse，这是正确方向。噪声窗 `[-200,0]` 只保证相对 marker 非正，是否属于无刺激噪声仍须对照实际试次时间线；本次没有真实数据证据来判断该默认窗适不适合具体实验。

    **修法：** 保留真实 nave；在 source 的 run/交付方法事实中明确“噪声归一化幅值、先取模后被试等权平均、试次数不同、各列独立范围、分位数仅为显示阈值、模板解剖”，并记录参数选择依据及噪声窗的实验事件背景。若目标是比较源强，需在分析阶段决定匹配试次数或其他估计方案，不能在绘图层偷偷改 nave。无需违背用户决定增写 source caption 文件。

    **测试缺口：** 固定 Evoked 数据和 covariance，改变 nave，记录符合 MNE 的变化；验证输出方法元数据包含 orientation、聚合顺序和 scale scope。现有半球测试不能证明这些解释成立。

14. **[P2，方法风险已用数值示例核验] ITC 没有暴露试次数偏差，单试次条件甚至恒为 1。**

    **位置：** [tfr_plot.py:167](C:/dev/brain-plot/brain-plot/tfr_plot.py:167)、[tfr_plot.py:182](C:/dev/brain-plot/brain-plot/tfr_plot.py:182)、[tfr_plot.py:228](C:/dev/brain-plot/brain-plot/tfr_plot.py:228)。

    当前 ITC 是逐被试的试次相位一致性，再平均被试；该顺序本身合理，但 ITC 的有限试次正偏差不会因被试等权而消失。caption 只有被试 N，没有每条件 trials 或不足试次数提示。本次对均匀独立相位做 10,000 次重复，N=1/5/50 的平均 ITC 约为 1.000/0.401/0.125，即没有锁相也能出现明显亮度差。相关原始研究：[Vinck et al., 2010](https://pubmed.ncbi.nlm.nih.gov/20114076/)。

    **修法：** 图注事实写出逐条件试次数分布与偏差提示，对单试次 ITC 停止或显式判为不可解释；需要条件比较时由上游分析决定试次匹配/敏感性分析。不要自动下采样试次或将 ITC 换成另一指标而保持原标签。

    **测试缺口：** [test_tfr.py:30](C:/dev/brain-plot/brain-plot/test/test_tfr.py:30) 所有条件固定 40 trials。增加同一相位分布、不同 trial count 的数值测试和 caption 检查。

15. **[P2，静态确认] TFR 与微状态地形图只按传感器值定色限，三次插值过冲会饱和；ITC 还可能产生超出物理范围的插值。**

    **位置：** [tfr_plot.py:416](C:/dev/brain-plot/brain-plot/tfr_plot.py:416)、[tfr_plot.py:438](C:/dev/brain-plot/brain-plot/tfr_plot.py:438)；[microstate_plot.py:225](C:/dev/brain-plot/brain-plot/microstate_plot.py:225)、[microstate_plot.py:365](C:/dev/brain-plot/brain-plot/microstate_plot.py:365)、[microstate_plot.py:490](C:/dev/brain-plot/brain-plot/microstate_plot.py:490)。

    两者都沿用 `image_interp='cubic'`，色限却只取输入向量最大值。ERP 已在 [erp_plot.py:1730](C:/dev/brain-plot/brain-plot/erp_plot.py:1730) 显式处理同一过冲问题。新增模块没有检测或记录，局部极值可被色限截平；对于 ITC，插值也没有保持 [0,1] 的保证。微状态模板是无单位归一化向量，其饱和同样影响模板形状的视觉比较。

    **修法：** 复用地形图插值范围检查：对有符号量共同扩展色限并固定 contour levels；对 ITC 采用有明确范围保持策略的插值/显示方案，说明处理而非把超界数当真值。保存 sensor range 与 displayed interpolation range。

    **测试缺口：** 用可产生插值过冲的合成空间图验证最终范围，ITC 加 0/1 极值场；不只核验“没有电极点”和 layout clean。本条未额外执行地形图渲染。

16. **[P2，静态确认] TFR / source / explore 的文件身份遗漏条件与 query，不同分析会互相归档。**

    **位置：** [tfr_plot.py:453](C:/dev/brain-plot/brain-plot/tfr_plot.py:453)、[source_plot.py:551](C:/dev/brain-plot/brain-plot/source_plot.py:551)、[erp_plot.py:2120](C:/dev/brain-plot/brain-plot/erp_plot.py:2120)；规则 [docs/rules.md:71](C:/dev/brain-plot/docs/rules.md:71)。

    这些路径只拼 `name_part()`，它包含轴风格、极性和 time lock，不包含条件/query。TFR 同一 ROI/group 下的全部试次与 `acc == 1` 同名；source 全条件与条件子集同名；source 的 windows 数值范围、timeline 时点也缺失。新图于是将另一科学问题的旧图移入 `_history`，被当成“同图新版本”。explore 的同尺寸不同 channel grid 也共享 stem。

    **修法：** 复用并扩展 `subset_part()` 或定义一个小的 figure identity helper，纳入条件/组选择、query、实际窗口和必要通道信息；科学身份与纯布局版本分开。

    **测试缺口：** 将 [test_erp_plot.py:366](C:/dev/brain-plot/brain-plot/test/test_erp_plot.py:366) 的“不应互相归档”测试推广到三条路径，并覆盖相同窗口名但不同数值。

17. **[P2，静态确认] caption / run 的事实记录与图不完全一致，审计无法仅凭交付物复现。**

    **位置：** [erp_plot.py:1864](C:/dev/brain-plot/brain-plot/erp_plot.py:1864)、[erp_plot.py:1908](C:/dev/brain-plot/brain-plot/erp_plot.py:1908)；[tfr_plot.py:199](C:/dev/brain-plot/brain-plot/tfr_plot.py:199)、[tfr_plot.py:228](C:/dev/brain-plot/brain-plot/tfr_plot.py:228)；[microstate_plot.py:506](C:/dev/brain-plot/brain-plot/microstate_plot.py:506)、[microstate_plot.py:577](C:/dev/brain-plot/brain-plot/microstate_plot.py:577)；[source_plot.py:566](C:/dev/brain-plot/brain-plot/source_plot.py:566)。

    ERP inset 实际不画灰带，caption 仍写 `gray band`。TFR caption 没有 S9 的 Whole figure / Panels、排除原因、query、逐条件 trials，还把显式任意频率列表称为 log-spaced。微状态 caption/run 未保存 loader 已有的 nave，无法核对实际 trial 数。source run 缺代码摘要、库版本和输入文件指纹；所有窗口缺实际首末样本事实。后两项尤其妨碍识别缓存或版本变化。

    **修法：** 从实际绘图结果生成 caption facts；公共 provenance 记录输入指纹、版本、有效参数、被试及 trials，模块补充特殊字段。TFR 保留完整频率数组与 spacing 描述，ERP 按布局决定有无 gray band。source 保持无 caption 的既定约定，将方法事实写入 run。

    **测试缺口：** 增加图形元素→caption 的正反断言、频率列表描述、excluded/query/nave 和 source provenance 字段验证。已有 inset 测试只检查 caption 字母/面板文本，没检查不存在的灰带描述。

18. **[P2，已核实版本要求] 声明的最小环境无法运行全部模块，source 还依赖作者机器路径。**

    **位置：** [requirements.txt:2](C:/dev/brain-plot/requirements.txt:2)、[check_env.py:11](C:/dev/brain-plot/brain-plot/check_env.py:11)、[SKILL.md:23](C:/dev/brain-plot/brain-plot/SKILL.md:23)；[tfr_plot.py:167](C:/dev/brain-plot/brain-plot/tfr_plot.py:167)、[source_plot.py:19](C:/dev/brain-plot/brain-plot/source_plot.py:19)、[source_plot.py:32](C:/dev/brain-plot/brain-plot/source_plot.py:32)。

    项目允许 mne 1.6，但 `Epochs.compute_tfr` 自 1.7 才有；本机 API docstring 也明确 `versionadded:: 1.7`，见 [MNE Epochs API](https://mne.tools/stable/generated/mne.Epochs.html#mne.Epochs.compute_tfr)。source 无条件 import pyvista，requirements 和 check_env 都未覆盖 3D 依赖及可用 backend，环境检查可能报 OK 而模块无法导入。fsaverage 默认路径硬编码为 `C:\Users\ASUS\...`，测试也沿用该路径。另有 `subjects_dir/src/bem` 相对路径不走 `read_spec` 的 spec 目录解析。

    **修法：** 按模块声明/检查真实最小版本与 3D 依赖，统一可配置的 fsaverage 数据路径及相对路径解析；测试以 fixture 路径注入。不要让常规 ERP 用户为未用到的 source 承担全部依赖，也不要自动下载模板来掩盖缺失配置。

    **测试缺口：** 在声明的最小依赖环境做 import / API smoke test；无 pyvista、无 fsaverage、从另一个 cwd 读取同一个 spec 时，验证清楚的诊断与路径行为。

19. **[P2，文档冲突] 规则的继承/例外不清晰，skill 会收到相互排斥的操作要求。**

    **位置：** [SKILL.md:29](C:/dev/brain-plot/brain-plot/SKILL.md:29)、[SKILL.md:43](C:/dev/brain-plot/brain-plot/SKILL.md:43)；[docs/rules.md:14](C:/dev/brain-plot/docs/rules.md:14)、[docs/rules.md:53](C:/dev/brain-plot/docs/rules.md:53)、[docs/rules.md:54](C:/dev/brain-plot/docs/rules.md:54)、[docs/rules.md:100](C:/dev/brain-plot/docs/rules.md:100)、[docs/rules.md:107](C:/dev/brain-plot/docs/rules.md:107)、[docs/rules.md:115](C:/dev/brain-plot/docs/rules.md:115)。

    具体冲突如下：SKILL 说每图四件套且 fixed physical size，而 source 规则明确无 caption、按内容决定高度及宽度上限；S1 声明 loader 不重参考/不重采样，source 又声明继承 S1，但实际新增 average-reference projection、baseline、decimation；T6 说画布绝不由内容决定，TF7 / SRC5 又明确自动高度/内容宽度；TF5 要求窗口 topomap 对称尺度，但 ITC 代码正确采用 0…v；SKILL 禁止手工编辑图，而 T5 解释 SVG 就是为了手调。ERP inset 也实际采用自动高度，与 T6 的绝对表述不符。

    **修法：** 增加明确的模块适用表和例外优先级，保留已经确认的具体行为；例如将 S1 拆成“输入一致性”与“允许的模块变换”，将固定字号/输出分辨率和固定画布区分，TF5 按 measure 区分，SKILL Draw 步骤引用模块输出契约。说明手工编辑限制约束的是 agent 还是用户。

    **测试缺口：** 用四模块各一个最小 spec 核验输出文件契约；补 agent eval，检查 source 不被要求补 caption、ITC 不被错误改成负色阶、内容布局不被当成违规修复。

20. **[P3，维护与测试结构] 应合并的是科学契约和输出基础逻辑，现有测试过度绑定完整渲染。**

    **位置：** [erp_plot.py:514](C:/dev/brain-plot/brain-plot/erp_plot.py:514)、[erp_plot.py:584](C:/dev/brain-plot/brain-plot/erp_plot.py:584)、[erp_plot.py:800](C:/dev/brain-plot/brain-plot/erp_plot.py:800)、[erp_plot.py:1173](C:/dev/brain-plot/brain-plot/erp_plot.py:1173)、[erp_plot.py:1788](C:/dev/brain-plot/brain-plot/erp_plot.py:1788)；[microstate_plot.py:199](C:/dev/brain-plot/brain-plot/microstate_plot.py:199)、[tfr_plot.py:79](C:/dev/brain-plot/brain-plot/tfr_plot.py:79)、[source_plot.py:152](C:/dev/brain-plot/brain-plot/source_plot.py:152)、[source_plot.py:469](C:/dev/brain-plot/brain-plot/source_plot.py:469)。测试位置：[test_tfr.py:70](C:/dev/brain-plot/brain-plot/test/test_tfr.py:70)、[test_source.py:67](C:/dev/brain-plot/brain-plot/test/test_source.py:67)。

    **为什么重要：** 三套 loader/cache 的分叉已经产生第 1–4 条；数值验证混在 render 测试里，使轻量回归也需要 fsaverage、VTK 和多图输出。source 测试仅一个被试，无法证明跨被试等权与时间/空间一致性；TFR 所有条件等 trial count，无法区分正确的被试等权与错误的 trial 加权；ERP 现有数值及布局测试较好，应保留独立断言。

    **建议最小合并范围：**

    - `validate_input_contract` / `input_fingerprint`：从 ERP 现有 helper 提取，供所有原始输入和缓存验证；各模块仍保留自己的计算步骤。
    - `checked_window_mask`：复用 `sample_mask` 的容差，增加完整范围/非空检查及实际样本事实；频率 mask 可沿用同一检查原则。
    - `cache_key` / `prune_cache`：统一身份与访问时间规则。TFR 只 touch 文件却按目录 mtime 淘汰，未严格实现最近使用；source 完全没有 pruning，与“保留六个缓存”承诺不符。应区分模型共享缓存和参数运行缓存，明确容量规则。
    - `write_run_record` / `figure_identity`：公共字段集中维护，模块只补扩展字段；继续复用已有 `versioned` / `archive`，不另造并行实现。
    - `text_widths_mm`、地形图范围检测：微状态测字宽、ERP 测字宽及 source probe 重复；可以合并小函数。四种布局与四种科学估计器不宜强行统一成大型基类。

    **修法与验证：** 先为第 1–19 条添加不渲染的针对性回归，再做小步提取。数值层用不等 trial 数/不等组样本数、已知均值和时间轴；缓存层用临时 FIF 与 mock 计算器；绘图层仅保留代表性几何/色条集成测试。source 的 rank 测试还应补一个可独立计算的小型逆解数值基准，不能只以“最大值不超过三倍”作为准确性证明。不要复制实现公式作为唯一测试答案。

本次轻量核验环境为 conda `mnedev`，Python 3.10.20、MNE `1.13.0.dev208+gd491745d9`。已实际核验：source 时间轴构造、两模块同名输入更新后的旧缓存、TFR 通道倒序被接受、遗漏/重复网格与重复 ROI 校验、Morlet 实际长度、Brain 透明度 API、ratio caption、空频率 mask、ERP 空 ROI、ITC 的 trial-count 数值示例。未运行真实数据逆解、完整 3D 渲染或五套全量测试；本报告不宣称既有测试全部通过，也不推断现有真实论文图已受到每一项问题影响。
