# Cluster-permutation result figures (`cluster_plot.py`)

Read after `SKILL.md` when the request is a figure of saved cluster-permutation results (a channel × time raster per
test with a row of µV-difference topomaps underneath). Spec keys: `spec.md`. Draws only: the module never computes a
test, threshold or p-value; the only computed number is the µV mean difference. Developer reference: `docs/rules.md`.

## Command

| Command | Use |
|---|---|
| `python cluster_plot.py plot <spec.json>` | Read a saved cluster run and draw one figure. |

## Interview rounds

Read the run's own notes first (`run_metadata.json`, `test_metadata.json`): they settle the tests, the difference
definition and the counts.

| Round | Decide |
|---|---|
| 1 | Which tests become columns (`tests`: the test folder names, in order) and their titles (`labels`: `{folder: title}`, default the test's own `name`). |
| 2 | What the colour shows (`color`: `"stat"` (default) for the test statistic, `"uv"` for the µV difference), how significance appears (`display`: `"masked"` (default) colours only significant samples, `"contour"` outlines them), the topomap row (`topo`: `"bins"` (default) or `"clusters"`; `topo_bin_ms`, default 100) and the canvas width (`width_mm`, default 180). |

Never ask (settled by house conventions; leave out or use the default):
- **Style** — channel order (the run's own `channel_order.csv`), colormaps (`RdBu_r` for t / µV, `Reds` for F), the
  white-dot channel marker on the maps, one colour bar per column, panel letters.
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

1. **No overlaps**: column titles, panel letters, channel labels and map time ranges must be cleanly separated.
2. **Channel labels legible**: every channel of `channel_order.csv` is a y tick, in order, row 0 at the top.
3. **Colour bar per column**: one bar beside each raster and one beside each map block, the statistic (t/F) or µV named.
4. **White dots**: significant channels are marked on the maps (a map with no significant channel is bare).
5. **Run record**: `layout_issues` in `_run.json` must be empty.
