VERDICT: FAIL

- [P1] [brain-plot/besa_to_run.py](/C:/dev/brain-plot/brain-plot/besa_to_run.py:110): `.avr` 读取要求矩阵形状为 `(channels, samples)` 并转置；card 规定文件行是时间样本、列是通道，真实输入会被拒绝或按反方向解释。改为按 `(npts, nchan)` 读取并保持样本行方向。对应实现见第 110、113 行；新增测试也按通道行生成数据，见 [test_besa.py](/C:/dev/brain-plot/brain-plot/test/test_besa.py:43)，掩盖了与 card 的差异。
- [P1] [brain-plot/besa_to_run.py](/C:/dev/brain-plot/brain-plot/besa_to_run.py:235): 没有核对 Results.dat 的 cluster p-values / values 与 summary 表；显著性和 CSV 使用 summary 的 p 值，而 metadata 的最小 p 值取自 Results.dat。文件不一致时仍会产出互相矛盾的 run，违背 card 要求不一致时停止。逐 cluster 对照两份文件的 p 值和 cluster value，不一致时调用 `ep.die`。相关使用处见第 235、246、256 行。
- [P2] [docs/besa-candidates/spec_besa_columns.json](/C:/dev/brain-plot/docs/besa-candidates/spec_besa_columns.json) 与 [spec_besa_waves.json](/C:/dev/brain-plot/docs/besa-candidates/spec_besa_waves.json)：新增文件不在 card 允许修改的三项文件中。移除这两项任务外新增文件。
- [P2] [docs/orch/2026-10-12-besa-to-run/reply.md](/C:/dev/brain-plot/docs/orch/2026-10-12-besa-to-run/reply.md)：新增 `reply.md`，card 只允许 `card.md` 和 `review.md` 留在该目录。移除该任务外新增文件。

Bloat: `read_summary` 和 `verify` 分别承担解析与一致性校验，均为单次使用；没有发现重复实现的 stdlib 或其他明显冗余。

预先存在的未提交文件：`AGENTS.md.bak-doctor-2026-10-09`、`docs/orch/2026-10-12-besa-to-run/card.md`。