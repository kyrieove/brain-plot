**结论：修复方向正确，但还不宜发布为可复用 skill。** 当前两图的主体计算没有发现新的错误；剩余阻断项集中在输入语义、规格校验、输出覆盖和图形 QA。

全程未修改文件。已查看两张 PNG、SVG、缓存及代码，并执行内存检查；完整回归未运行，因为当前 Python 缺少 `mne`。

**A. 首轮 12 项复核**

| # | 判定 | 当前证据与剩余问题 |
|---|---|---|
| 1 数据契约 | **部分解决** | 时间网格、通道、基线、坏道已有检查。[erp_plot.py:129](C:/dev/brain-plot/brain-plot/erp_plot.py:129)。仍漏单位、坐标系及 Evoked 类型；读取时可能自动应用投影，见 B1。 |
| 2 缓存失效 | **已解决** | 实际文件清单、大小、`mtime_ns`、加载器版本进入键；数组与契约、ID、试次数共同保存。[erp_plot.py:145](C:/dev/brain-plot/brain-plot/erp_plot.py:145)、[erp_plot.py:178](C:/dev/brain-plot/brain-plot/erp_plot.py:178)。归档追溯另见 B6。 |
| 3 静默丢线 | **已解决** | 颜色不足停止，线／图数量断言落实。[erp_plot.py:326](C:/dev/brain-plot/brain-plot/erp_plot.py:326)、[erp_plot.py:407](C:/dev/brain-plot/brain-plot/erp_plot.py:407)。 |
| 4 文档／接口分歧 | **部分解决** | 未知键、`Evoked + query` 已拒绝；但“严格 schema”目前主要检查键名，关键值仍可无效，见 B2。[erp_plot.py:51](C:/dev/brain-plot/brain-plot/erp_plot.py:51)。 |
| 5 ID、排除、SEM | **已解决** | 在已声明的文件命名约定内，精确排除、重复 ID／空组拒绝、单被试不画 SEM 均落实。[erp_plot.py:90](C:/dev/brain-plot/brain-plot/erp_plot.py:90)、[erp_plot.py:344](C:/dev/brain-plot/brain-plot/erp_plot.py:344)。 |
| 6 窗口推荐 | **部分解决** | 限定搜索范围、FWHP 名称和启发式定位已修正。[erp_plot.py:217](C:/dev/brain-plot/brain-plot/erp_plot.py:217)。但 [rules.md:11](C:/dev/brain-plot/brain-plot/references/rules.md:11) 仍把“独立数据上的同一对比定位”一并排除；应限定为不能利用当前待检验数据的目标差异择窗。无需改变本研究窗口。 |
| 7 唯一规则库 | **部分解决** | 主布局冲突已消除；但 [rules.md:14](C:/dev/brain-plot/brain-plot/references/rules.md:14) 仍允许提供统计结果后添加标记，与本任务及 [SKILL.md:67](C:/dev/brain-plot/brain-plot/SKILL.md:67) 冲突。删除该例外即可。 |
| 8 地形图可比性 | **部分解决** | 共用等值线已实现。[erp_plot.py:352](C:/dev/brain-plot/brain-plot/erp_plot.py:352)。`sphere=None` 并非固定数值，实际投影参数未记录，插值超界也未检查，见 B5。 |
| 9 工作流契约 | **部分解决** | 分轮访谈、确认、重确认和交付流程已成形。[SKILL.md:22](C:/dev/brain-plot/brain-plot/SKILL.md:22)。主张／关键比较未进入 spec，运行记录仍缺追溯字段，见 B6。 |
| 10 边界错误 | **部分解决** | 空／越界窗口、非有限值、短显示范围已有处理。[erp_plot.py:311](C:/dev/brain-plot/brain-plot/erp_plot.py:311)。仍有窗口与显示范围脱节、标签碰撞，见 B2、B4。 |
| 11 尺寸与独立阅读 | **部分解决** | SVG 确为 **180 × 110 mm**；窗口、负时间参照及图注事实已补齐。[fig_N2.svg:4](C:/dev/brain-plot/brain-plot/test/out/fig_N2.svg:4)、[fig_N2_caption.md:8](C:/dev/brain-plot/brain-plot/test/out/fig_N2_caption.md:8)。接受原点不重复标“0”；实际裁切／遮挡见 B4。 |
| 12 exemplar／图库 | **已解决** | 旧计划归档、采用／不采用区分、JS 换行修复均到位。[skill-design-plan.md:1](C:/dev/brain-plot/docs/skill-design-plan.md:1)、[exemplars.md:29](C:/dev/brain-plot/research/exemplars.md:29)、[erp-gallery.html:207](C:/dev/brain-plot/research/erp-gallery.html:207)。 |

**B. 新增或仍漏掉的问题，按优先级**

1. **P1｜加载器仍可能改变或误认输入数据。**  
   [erp_plot.py:111](C:/dev/brain-plot/brain-plot/erp_plot.py:111)、[erp_plot.py:122](C:/dev/brain-plot/brain-plot/erp_plot.py:122) 未显式关闭读取时的投影；MNE 默认可应用 SSP，包括待应用的平均参考投影。另一方面，Evoked 按 `comment` 建字典会让同名对象后者覆盖前者，且不验证 `kind`。同名 average／standard_error 的内存替身检查中，函数选择了后者。[MNE 读取语义](https://mne.tools/stable/generated/mne.read_evokeds.html)、[Evoked 类型说明](https://mne.tools/1.6/generated/mne.Evoked.html)。  
   **最小修复：**明确读取投影策略；对待应用投影停止并要求上游处理；只接受 `kind="average"`，同名条件歧义报错；补单位、有限坐标与坐标系检查。不要把 `custom_ref=True` 当作具体参考方案一致的证明。

2. **P1｜无效科学规格会通过校验并产生错误权重或不完整展示。**  
   [erp_plot.py:65](C:/dev/brain-plot/brain-plot/erp_plot.py:65) 接受重复／空 ROI、`window_source:null`、空参考描述；[erp_plot.py:343](C:/dev/brain-plot/brain-plot/erp_plot.py:343) 随后按列表平均，`["Fz","Fz","Cz"]` 就把 Fz 加权两次。现有缓存上，该误填足以改变组均值约 **1.27–1.65 µV**。此外，窗口只检查落在数据内，没有检查落在显示范围内：[erp_plot.py:337](C:/dev/brain-plot/brain-plot/erp_plot.py:337)。  
   **最小修复：**ROI 必须非空且唯一；必要文本必须为非空字符串；数值必须有限；要求窗口完整包含于显示范围。绘图前一次性验证全部成分。

3. **P1｜不同成分可能静默覆盖同一个图文件。**  
   [erp_plot.py:410](C:/dev/brain-plot/brain-plot/erp_plot.py:410) 使用 `with_suffix()`：`P3.early` 与 `P3.late` 都会保存成 `fig_P3.png`，PDF／SVG 同理；重复成分名也未拒绝。图注和 run 文件却可保留不同名称，造成交付错配。  
   **最小修复：**验证成分名及最终输出路径唯一；给完整文件名追加扩展名，不替换名称中的后缀。

4. **P1｜当前 180 mm 成图没有通过自身的无遮挡要求。**  
   实看 [P3 PNG](C:/dev/brain-plot/brain-plot/test/out/fig_P3.png)，NoGo 的 **“800 ms”与 ADHD、RD 均值线相交**；用缓存重建波形坐标后得到相同结果。N2／Go 和 P3／Go 的末端标签也碰到 SEM。两图色标 `µV` 触及右边界并有轻微裁切。原因是 [erp_plot.py:267](C:/dev/brain-plot/brain-plot/erp_plot.py:267) 只在刻度中心比较上下振幅，未检查文字覆盖的整个时间区间；固定右边距亦未验收文字边界：[erp_plot.py:358](C:/dev/brain-plot/brain-plot/erp_plot.py:358)。  
   **最小修复：**测量实际文字 bbox，对均值及 SEM 做碰撞检查；末端标签允许向内对齐并增加偏移；略增色标右侧留白。保留现有绑定布局。180 mm 下色标 **5.5 pt**、图例／刻度 **6 pt** 也应如实记录，不能统称 7 pt。

5. **P1｜“固定投影”尚未成立，饱和检查仍空缺。**  
   [erp_plot.py:43](C:/dev/brain-plot/brain-plot/erp_plot.py:43) 的 `sphere=None` 会随 digitization 信息选择自动拟合或默认球；契约只比较电极坐标，未覆盖这些拟合输入。对于具有不同头形点的输入，选谁作为第一份文件可能影响共同投影。[MNE sphere 定义](https://mne.tools/stable/generated/mne.viz.plot_topomap.html)。色限取传感器极值，而 cubic 插值结果没有超界检查：[erp_plot.py:351](C:/dev/brain-plot/brain-plot/erp_plot.py:351)。  
   **最小修复：**确定并记录共同 sphere 的实际数值；检查可见插值区域超出色限的比例，必要时统一调整图内色限。这里指出的是未完成检查，**不是已证明当前两图地形算错**。

6. **P2｜确认内容与复现记录仍有断层。**  
   访谈询问图的主张和关键比较，但 [spec.md:5](C:/dev/brain-plot/brain-plot/references/spec.md:5) 无对应字段；[erp_plot.py:417](C:/dev/brain-plot/brain-plot/erp_plot.py:417) 未保存输入文件指纹清单、完整通道顺序、加载器／绘图代码／规则版本及 QA 结果。文件指纹只进入缓存键，无法从 run 反查。  
   **最小修复：**把主张、关键比较随确认 spec 保存；将已有输入清单和实际解析参数写入 run，增加明确的 QA 结论。再补一个已知均值、ROI、SEM、地形窗口均值的确定性数值回归；现有测试主要检查数量、字符串和报错，[test_erp_plot.py:50](C:/dev/brain-plot/brain-plot/test/test_erp_plot.py:50) 尚不能证明这些计算正确。

**C. Must fix before release（最多 5 项）**

1. 修复输入语义与投影处理边界（B1）。
2. 完成规格预检，消除 ROI 重复加权和输出覆盖（B2–B3）。
3. 修掉两张实图的标签碰撞、色标裁切，并重新验收 180 mm 输出（B4）。
4. 固定并记录实际投影参数，补插值饱和检查（B5）。
5. 补确认／运行追溯记录及数值回归；删除显著性标记例外（B6、A7）。

**Can wait：**BIDS 文件名支持；独立 localizer 的规则措辞修订；更多 exemplar、复杂图型和封装；面板字母对齐、头轮廓粗细等细节。七条件默认色板实际只有六色、定制颜色又能绕过“最多七线”的文档边界，也应在下一轮统一，但当前会报错或完整绘制，没有重现首轮的静默漏线。