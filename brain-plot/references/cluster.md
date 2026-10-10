# Cluster-permutation result figures (`cluster_plot.py`)

Read after `SKILL.md` when the request is a figure of saved cluster-permutation results. One figure per test: the
channel × time raster on the left, the µV-difference topomaps in a 2-column grid on the right. Spec keys: `spec.md`.
Draws only: the module never computes a test, threshold or p-value; the only computed number is the µV mean
difference. Developer reference: `docs/rules.md`.

## Command

| Command | Use |
|---|---|
| `python cluster_plot.py plot <spec.json>` | Read a saved cluster run and draw one figure per test. |

## Interview rounds

Read the run's own notes first (`run_metadata.json`, `test_metadata.json`): they settle the tests, the difference
definition and the counts.

| Round | Decide |
|---|---|
| 1 | Which tests become figures (`tests`: the test folder names, in order) and their titles (`labels`: `{folder: title}`, default the test's own `name`). |
| 2 | What the colour shows (`color`: `"stat"` (default) for the test statistic, `"uv"` for the µV difference), how significance appears (`display`: `"masked"` (default) colours only significant samples, `"contour"` outlines them), the topomaps (`topo`: `"bins"` (default) or `"clusters"`; `topo_bin_ms`, default 100), the raster row order (`channel_order`: `"lmr"` (default) groups left / midline / right, `"file"` keeps the result-file order) and the canvas width (`width_mm`, default 180). |

Never ask (settled by house conventions; leave out or use the default):
- **Style** — the raster row order (default left / midline / right from `channel_order.csv`), colormaps (`RdBu_r` for
  t / µV, `Reds` for F), the white-dot channel marker on the maps, one colour bar per raster and one per map grid,
  panel letters.
- **Statistics** — the module copies the tail, forming threshold, permutation count and cluster p-values from the run
  files; it never recomputes them.
- **µV difference** — the subjects and A − B come from `test_metadata.kind` and `run_metadata.difference_definition`;
  do not invent them.

## When the script stops

Fix the cause, never work around it; tell the user when the fix changes the figure:
- **`test <slug> (kind ...) has no single difference wave`** — `color: "uv"` was asked for a test with no single
  difference (e.g. an interaction); use `color: "stat"`.
- **`unsupported spec keys`** — remove or rename the key (see `spec.md`).
- **`test folder <slug> not found`** — fix the folder name; the message lists the folders that exist.
- **`observed_statistic ... and mask ... must both be (len(time_axis), len(channel_order))`** — the saved arrays do
  not match the run's axes; re-export the test.
- **`... missing channel(s) ...` / `cannot find the manifest root` / `participant ... is missing a ... file`** — the
  manifest and the evoked files disagree; fix the run folder or the manifest.

## QA after every `plot` render (open each PNG)

1. **No overlaps**: titles, panel letters, channel labels and map time ranges must be cleanly separated.
2. **Channel labels legible**: every other channel is a y tick label in display order; the rows are grouped left /
   midline / right (or in file order with `channel_order: "file"`), row 0 at the top.
3. **Maps ≥ 15 mm, every other channel labelled, group names readable**: the map grid sits beside the raster with
   maps at least 15 mm across.
4. **Colour bar per side**: one bar beside the raster and one beside the map grid, the statistic (t/F) or µV named.
5. **White dots**: significant channels are marked on the maps (a map with no significant channel is bare).
6. **Run record**: `layout_issues` in `_run.json` must be empty.
