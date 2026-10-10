# cluster-columns-v4 — centre the topomap row labels; record columns as the house style

## Goal
User review of GN v05: the two-line topomap row labels ("All" / "NoGO − GO", "TD" / "NoGO − GO") are right-aligned
against the maps; the user wants each label centred (both lines centred on each other, the block centred in the label
column left of the maps). The user also approved this columns figure as the house style ("规范"), 8 maps per row
(100-ms bins) kept.

## Risk
low — one `fig.text` call and docs; no data or number changes.

## Files
- may change: `brain-plot/cluster_plot.py`, `brain-plot/references/cluster.md`

## Steps (N = 2)
1. `brain-plot/cluster_plot.py`, `plot_columns()`, the topomap row label call
   `fig.text((left_m - 2.0) / W, (H - (y_top + map_mm / 2.0)) / H, row_label(t["label"]), ha="right", ...)`:
   x → `(left_m - 2.0) / 2.0 / W` (centre of the label column), `ha="center"`, add `multialignment="center"`; keep
   `va="center"` and `fontsize=6`. Nothing else.
2. `brain-plot/references/cluster.md`: in interview round 2 (the `layout` part) add one sentence: recommend
   `layout: "columns"` first — the user's approved house style (2026-10-11: tests as columns, equal L/M/R sub-panels
   by MNE `midline="12z"`, 8 topomaps of 100 ms per row, centred short row labels) — and fall back to `"side"` when
   there are more than 3 tests or `channel_order: "file"`. The code default stays `"side"`.

## Check
```
python brain-plot/test/test_cluster.py
```

## Don't
- No commits. Change only what the steps name.
- "Run scripts in the foreground and wait; before replying, stop any background task still running."
- "Reuse existing functions; don't copy existing logic."
- "No rm, no git push, no git checkout . / restore . / reset --hard."

## Acceptance (draft)
- verdict: TODO (accepted / review pending / rejected)
- files: brain-plot/cluster_plot.py, brain-plot/references/cluster.md
- check: `python brain-plot/test/test_cluster.py` → exit 0 (run by run-card)
- tokens:
  - round 1: exec deepseek-v4.1-flash: fresh 19k, cached 438k, out 3k  (codex-cluster-columns-v4.jsonl)
- review findings: TODO N real / M false positive / K missed (low, no review)
