STATUS: done

文件改动（6 个，均只做卡片列的改动；五个 .py 都过了 `py_compile` 语法检查）：
- `brain-plot/erp_plot.py` — 加 `is_epochs` / `eeglab_locking_types` / `read_epochs_any`（步骤 1）；各处 epochs 判断与读取、`find_groups` glob、`discover` 错误文案（步骤 2）；`contract(ev, eeglab=False)` 与 `baseline_filter_text`（步骤 3）；图注三行、`inspect` 的 `.set` note、docstring 第 8 行（步骤 4）。
- `brain-plot/microstate_plot.py` — 图注改用 `ep.baseline_filter_text`（步骤 5）。
- `brain-plot/tfr_plot.py`、`brain-plot/source_plot.py` — 读取换 `ep.read_epochs_any`，`contract` 传 `eeglab=`；source 的判断换 `ep.is_epochs`（步骤 6）。
- `brain-plot/test/test_erp_plot.py` — 新增块 `# 10. EEGLAB .set input`，含合成往返 a–d、真实夹具 e–f、图副本上的 load/plot g–h、`inspect` i、连续 `.set` 报错 j（步骤 7）。
- `brain-plot/SKILL.md` — 首行 description 加 `or epoched EEGLAB .set files`（步骤 8）。

未能做/未做：
- 按指示未运行 Check（留给 runner）。
- 未提交、未切换分支，未动其他任何文件；`__pycache__` 已被 `.gitignore` 忽略。
- 无阻塞项。