VERDICT: FAIL

1. `brain-plot/source_plot.py:669`：`lambda2=0` 未被禁止，MNE 支持该值，但新增 SNR 表达式 `0.0 ** -0.5` 会抛出 `ZeroDivisionError`，导致图片已保存却无法写出 `_run.json`。修复：零值时记录无限 SNR，正值时再计算负半次幂。
2. `brain-plot/source_plot.py:670`：当 spec 设置 `loose=0`，逆解为固定方向、有符号结果；新增说明却始终声称“三个方向的非负模”，会误导 Methods。修复：按实际方向约束生成说明，并同步 `brain-plot/references/source.md:63`。后续 8bd40b6 未修复此处。
3. `HANDOFF.md:25`、`docs/review-log.md:530`、`docs/orch/2026-10-01-provenance-docs/card.md:1`：89f3553 修改或创建了任务卡白名单之外的文件，违反“everything else read-only”。修复：从本任务改动中移除这些文件的变更。