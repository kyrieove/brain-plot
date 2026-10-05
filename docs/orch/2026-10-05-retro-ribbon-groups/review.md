VERDICT: PASS

No problems found. All five steps are implemented exactly as the card specifies, and the exact strings match:
- `brain-plot/microstate_plot.py:577-579` — `segmentation` set after `templates_meta`, gated on `"spans" in facts`; string ends `min_segment_ms = {spec.get('min_segment_ms', 30)}; not the analysis's own labels`. Reaches `_run.json` via `**facts`; `json.dumps` untouched. ✓
- `brain-plot/microstate_plot.py:525` — caption line directly after the `- Segmentation:` append, before the butterfly line. ✓
- `brain-plot/references/microstate.md:27` — bullet is the first list bullet under "Read first, then ask", before `- At most 2 rows`. ✓
- `brain-plot/erp_plot.py:381,430` — both `die` texts match the Parameters strings byte-for-byte; old prefixes kept first, nothing else changed in those functions. ✓
- `brain-plot/test/test_microstate.py:151,232` — new assert uses the correct in-block names `run`/`cap`; the `fails(...)` substring switched to the new error tail. In the block at 226-232, deleting G2's `A` files leaves G2 subjects with only `B`, so `split_layout` fires the missing-condition message — the asserted substring is the one that fires. ✓

`"spans" in facts` is a sound states-figure test: only `plot_states` puts `spans` in `facts` (microstate_plot.py:430); `plot_by_k` does not. Diff stays within the card's file list; no copied code, no new helper, no dead code, no junk.

Bloat added: none.

Pre-existing (not from this diff): the tree carries unrelated untracked `docs/orch/…`, `docs/retro_…`, `docs/orchestrate-recommendations-2026-10-05.md` and `examples/…/*_caption.md` files that predate this task.
