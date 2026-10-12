VERDICT: FAIL

1. [P1] brain-plot/erp_plot.py:395 — 新增 `.set` 支持未将外置 `.fdt` 纳入缓存标识；只更新 `.fdt` 时，ERP、TFR、source 会复用旧计算结果。修复：共享 `file_stamp()` 同时记录引用的 `.fdt`。证据：615 行 `return [str(f), st.st_size, st.st_mtime_ns]`；623 行 `stamp = [file_stamp(f) for f in files]`。

2. [P1] brain-plot/test/test_erp_plot.py:553 — 删除预期文本首字母，绕过步骤 7h 要求的完整图注文案检查。修复：断言完整的 `baseline and filter not recorded (EEGLAB .set)`，并解决 card 中 Parameters 与步骤 4 大小写要求的冲突。证据：`assert "aseline and filter not recorded (EEGLAB .set)" in cap`。

3. [P1] brain-plot/test/test_erp_plot.py:544 — 步骤 7g 要求读取真实夹具的通道列表并使用前两个通道，实际硬编码了不同选择，跳过指定步骤。修复：用 `mne.read_epochs_eeglab()` 读取一个夹具，取 `ch_names[:2]`。证据：`ch = ["Cz", "Pz"]`，546 行将其传入 `channels=ch`。

4. [P2] docs/orch/2026-10-12-eeglab-set-input/reply.md:1 — 新增文件超出 card 的 Files 范围，也不属于获准的 card.md/review.md 例外。修复：移除该新增文件，将必要记录放入允许的 review.md。证据：未跟踪文件差异新增 `+STATUS: done`。

膨胀：未确认新增的重复实现、单次使用抽象、死代码或未请求选项。

既有问题（不计入 verdict）：card 的小写精确图注文案与步骤 4 首字母大写代码相冲突；此前未提交文件无可用基线，未归责于本次任务。