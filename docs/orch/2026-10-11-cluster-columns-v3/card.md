# cluster-columns-v3 — shorter topomap row labels, narrower left margin, larger topomaps

## Goal
User review of the GN columns render (v04): the topomap row labels ("TD (N = 31): NoGO − GO") waste width. Drop the
"(N = …)" part (the raster column title above already gives N) and break the label onto two lines at ": "
("TD" / "NoGO − GO"). The left margin (30 mm, set only for those long labels) then shrinks to 20 mm and the freed
width goes to the topomaps (GN: map 15.3 → 16.5 mm) and the raster columns.

## Risk
low — label text and one margin number in `plot_columns()`; no data or number changes.

## Files
- may change: `brain-plot/cluster_plot.py`, `brain-plot/references/cluster.md`

## Steps (N = 3)
1. In `brain-plot/cluster_plot.py` add, next to `group_rows`, a function
   `row_label(label)`: remove every `\s*\(N\s*=\s*\d+\)` match (regex, `re` is already imported), then replace the
   first ": " with "\n"; return the result (a label with neither stays as it is). Docstring: one line saying it builds
   the topomap row label of the columns layout (N is in the raster column title).
2. In `plot_columns()`: `left_m, right_m, top_m = 30.0, 14.0, 12.0` → `left_m, right_m, top_m = 20.0, 14.0, 12.0`;
   in the topomap row loop use `row_label(t["label"])` instead of `t["label"]` for the row text (keep
   `ha="right", va="center", fontsize=6`). The raster column titles keep the full `t["label"]`. `plot_side` unchanged.
3. `brain-plot/references/cluster.md`: in the columns-layout description add one sentence: topomap row labels drop
   "(N = …)" and break at ": " onto two lines.

## Fix 1
Check failed: `columns layout issues: ["text outside the canvas: 'Condition main effect (all)'", "text outside the
canvas: 'Within-TD condition effect'"]` — the test has no spec labels, so the row label is the test name, which has no
": " and stays one ~30-mm line, too wide for the 18 mm left of the maps. In `row_label()` (brain-plot/cluster_plot.py),
after removing "(N = …)", split the label at the first ": " into parts and wrap EACH part with
`textwrap.wrap(part, 12)` (stdlib; add `import textwrap` at the top with the other imports), then join all lines with
"
". GN labels stay "TD" / "NoGO − GO". Update the docstring to say so. Run the Check in the foreground until it
passes. Change nothing else.

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
  - round 1: exec deepseek-v4.1-flash: fresh 18k, cached 422k, out 3k  (codex-cluster-columns-v3.jsonl)
  - Fix 1: exec deepseek-v4.1-flash: fresh 16k, cached 301k, out 3k  (codex-cluster-columns-v3.jsonl)
- review findings: TODO N real / M false positive / K missed (low, no review)
