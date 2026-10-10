# cluster-columns-v2 — equal sub-panels sized by the largest group

## Goal
Continue `docs/orch/2026-10-11-cluster-columns/card.md` (its Fix 2 is in the working tree, uncommitted: MNE
`midline="12z"` grouping via `hemi_by_name`, equal sub-panel heights). The Check now fails:
`columns layout issues: ["texts overlap: 'Fz' × 'Pz'"]`. On the 6-channel synthetic montage the averaged height
`1.2 * total / 3` = 2.4 mm is too short for the 4-row Midline group.

## Risk
low — one number formula in `plot_columns()`; GN grows ~2 mm in height.

## Files
- may change: `brain-plot/cluster_plot.py`

## Steps (N = 1)
1. In `plot_columns()` replace `h = 1.2 * sum(len(gr) for _, gr in groups) / len(groups)` with
   `h = 1.2 * max(len(gr) for _, gr in groups)` (keep `sub_h = [h] * len(groups)`). Change nothing else.

## Check
```
python brain-plot/test/test_cluster.py
```

## Don't
- No commits. Change only the line in step 1; do not touch Fix 2's other edits.
- "Run scripts in the foreground and wait; before replying, stop any background task still running."
- "Reuse existing functions; don't copy existing logic."
- "No rm, no git push, no git checkout . / restore . / reset --hard."

## Acceptance (draft)
- verdict: TODO (accepted / review pending / rejected)
- files: brain-plot/cluster_plot.py
- check: `python brain-plot/test/test_cluster.py` → exit 0 (run by run-card)
- tokens:
  - round 1: exec deepseek-v4.1-flash: fresh 2k, cached 198k, out 1k  (codex-cluster-columns-v2.jsonl)
- review findings: TODO N real / M false positive / K missed (low, no review)
