# Cluster-permutation result figures (`cluster_plot.py`)

Read after `SKILL.md` when the request is a figure of saved cluster-permutation results. Three layouts (`layout`):
`"side"` (default) draws one figure per test — the channel × time raster on the left, the µV-difference topomaps in a
2-column grid on the right; `"columns"` draws ONE figure for all tests (the user's reference, 2026-10-11) — one column
per test whose three stacked sub-panels are the Left / Midline / Right raster rows, with one shared raster colour bar,
and below it one row of topomaps per test with one shared map colour bar. Topomap row labels drop "(N = …)" and break
at ": " onto two lines. `"waves"` draws ONE figure per test, one row per significant cluster: a µV-difference topomap
(the cluster's channels marked white) beside the two compared conditions' grand-average waveforms over the cluster's
channels (each with a 95 % CI band, the cluster window shaded gray, colours from `difference_definition`), needs
every test to have a single difference wave, and takes `polarity` (`"negative_up"` default, `"positive_up"`). Spec
keys: `spec.md`.
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
| 2 | What the colour shows (`color`: `"stat"` (default) for the test statistic, `"uv"` for the µV difference), how significance appears (`display`: `"masked"` (default) colours only significant samples, `"contour"` outlines them), the topomaps (`topo`: `"bins"` (default) or `"clusters"`; `topo_bin_ms`, default 100), the raster row order (`channel_order`: `"lmr"` (default) groups left / midline / right by the channel name as MNE `make_1020_channel_selections(midline="12z")` reads it — names ending in 1, 2 or z are Midline, other odd digits Left, other even digits Right; `"file"` keeps the result-file order), the canvas width (`width_mm`, default 180) and the layout (`layout`: `"side"` (default) one figure per test, `"columns"` one figure for all tests — `columns` needs `channel_order: "lmr"`, at most 3 tests and, under `color: "stat"`, one statistic across the tests). Recommend `layout: "columns"` first — the user's approved house style (2026-10-11: tests as columns, equal L/M/R sub-panels by MNE `midline="12z"`, 8 topomaps of 100 ms per row, centred short row labels) — and fall back to `"side"` when there are more than 3 tests or `channel_order: "file"`. The code default stays `"side"`. Offer `layout: "waves"` (the user's reference, 2026-10-11) when the user wants to "show the two compared conditions per cluster": one figure per test, one row per significant cluster with the µV-difference topomap and the two conditions' waveforms over the cluster's channels (95 % CI bands, cluster window shaded); it needs every test to have a single difference wave (kinds `condition_pooled` / `condition_group`, so not an F interaction) and at least one significant cluster per test; output `cluster/cluster_waves_t<NN>[_lock-<event>]_vNN`. |

Never ask (settled by house conventions; leave out or use the default):
- **Style** — the raster row order (default left / midline / right from `channel_order.csv`), colormaps (`RdBu_r` for
  t / µV, `Reds` for F), the white-dot channel marker on the maps, one colour bar per raster and one per map grid
  (`columns`: one shared bar per block), panel letters.
- **Statistics** — the module copies the tail, forming threshold, permutation count and cluster p-values from the run
  files; it never recomputes them.
- **µV difference** — the subjects and A − B come from `test_metadata.kind` and `run_metadata.difference_definition`;
  do not invent them.

## When the script stops

Fix the cause, never work around it; tell the user when the fix changes the figure:
- **`layout must be 'side', 'columns' or 'waves'`** — fix the value.
- **`polarity must be 'positive_up' or 'negative_up'`** — fix the value.
- **`layout "columns" splits the raster by hemisphere; set channel_order to "lmr"`** — the columns layout splits the
  raster rows into Left / Midline / Right, so it needs `channel_order: "lmr"` (drop `"file"`).
- **`layout "columns" draws one column per test; it holds at most 3 tests`** — draw fewer tests per figure.
- **`layout "columns" shares one colour scale; tests mix t and F`** — under `color: "stat"` give the columns tests one
  statistic, or split them across figures.
- **`layout "waves" draws condition waveforms; test <slug> (kind <kind>) has no single difference wave`** — the waves
  layout draws the two conditions of a difference wave; drop the test or use `layout: "side"`.
- **`layout "waves": test <slug> has no significant cluster; drop it from tests`** — the waves layout draws one row per
  cluster; drop a test without a cluster.
- **`test <slug> (kind ...) has no single difference wave`** — `color: "uv"` was asked for a test with no single
  difference (e.g. an interaction); use `color: "stat"`.
- **`unsupported spec keys`** — remove or rename the key (see `spec.md`).
- **`test folder <slug> not found`** — fix the folder name; the message lists the folders that exist.
- **`observed_statistic ... and mask ... must both be (len(time_axis), len(channel_order))`** — the saved arrays do
  not match the run's axes; re-export the test.
- **`... missing channel(s) ...` / `cannot find the manifest root` / `participant ... is missing a ... file`** — the
  manifest and the evoked files disagree; fix the run folder or the manifest.

## QA after every `plot` render (open each PNG)

Visual QA: first look at the changed region with `python brain-plot/test/qa_crop.py <png> x0 y0 x1 y1` (0-1 fractions); view the whole figure only for the final acceptance.

1. **No overlaps**: titles, panel letters, channel labels and map time ranges must be cleanly separated.
2. **Channel labels legible**: every other channel is a y tick label in display order; the rows are grouped left /
   midline / right by the channel name (MNE `make_1020_channel_selections(midline="12z")`; or in file order with
   `channel_order: "file"`), row 0 at the top.
3. **Maps ≥ 15 mm, every other channel labelled, group names readable**: the map grid sits beside the raster with
   maps at least 15 mm across.
4. **Colour bar per side**: one bar beside the raster and one beside the map grid, the statistic (t/F) or µV named.
5. **White dots**: significant channels are marked on the maps (a map with no significant channel is bare); under
   `topo: "bins"` a channel is marked only when it is significant in at least half of the bin's samples.
6. **Run record**: `layout_issues` in `_run.json` must be empty.

`layout: "columns"` also:
7. **Three sub-panels per column**: each test column stacks Left, Midline and Right at EQUAL height (the three groups
   share the raster block's height, whatever their row counts); only the bottom sub-panel carries the x tick labels
   and "Time (ms)"; the group names sit once, left of the first column.
8. **One colour bar per block**: a single shared raster bar right of the last column and a single shared map bar
   spanning the map block; a test with no maps shows "no significant cluster" in its row.
9. **Map labels readable**: the row label (test title) sits left of each row's first map, every map carries its time
   label, and the panel letters run across the columns and then down the rows.
10. **Cluster notes and outline**: each column lists its significant clusters (cluster id, time window, p) under its
    raster (at most 5 lines, then `+ N more (see caption)`); the masked raster outlines each significant region in black.
