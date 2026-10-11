STATUS: done

文件改动（仅新增，未提交）：
- `research/cluster-figures/survey-mne.md`（新文件，20 行表格 + Summary / Takeaways for the columns layout / Dropped）
- `research/cluster-figures/figures/mne_01_…jpg` … `mne_20_…png`（20 张结果图；该目录在 `.gitignore` 内，故不计入 `git status`）

无法做/未做的事：
- 全部走免费来源（PMC / 出版社 / mne.tools），未用到你的 Chrome，也没有例外。
- 按要求没有运行 Check（`check_survey.py`）。自己只做了轻量自查：表格 20 行、17 列对齐、每行含 MNE 与 DOI/URL、20 个图片路径全部可打开且最短边 ≥300 px。
- 因范围（仅传感器空间 ERP/EEG/MEG，排除源空间、时频、解码）与“方法须把聚类检验归于 MNE-Python”两个条件，多篇候选被剔除，已在 `## Dropped` 逐条列出；最终表内计数与 20 行完全一致。