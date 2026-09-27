# Microstate figures (`microstate_plot.py`)

Read after `SKILL.md` when the request is a microstate figure drawn from saved templates. Spec keys: `spec.md`,
section "Microstate spec". The script enforces layout, style, naming and the data contract itself (developer
reference: `docs/rules.md`, rules MS1–MS10) — you don't need those details to draw.

Draw only: templates are read from the analysis (npz `centers`, K × channels, optional `ch_names`) and never
re-fitted; clustering is out of scope. Resting-state figures beyond the template row are not wanted for now.

## Figures

- `figure: "states"` — one K: framed template maps (numbered S1, S2, … in time order) + time panels per condition
  (`blocks`: `butterfly` = all channels + GFP, `gfp` = GFP filled with state colours, `ribbon` = segmentation under the
  butterfly).
- `figure: "by-K"` — one row of templates per K, coloured by template identity across K.

## Read first, then ask

Read the analysis's docs, locked config and model files: templates path, subjects and exclusions, `window_ms`,
`polarity` (`"insensitive"` if the analysis ignored map polarity, e.g. pycrostates), `min_segment_ms`,
`templates_source`. These must match the analysis — never ask the user what the config states.

Ask only: which K (or K range for `by-K`), which conditions (and groups), which blocks.

- At most 2 rows (conditions, or conditions × groups with `per_group`) are stacked. More conditions need a `grid`
  (rows × columns of condition keys, e.g. a 2 × 3 design as 2 rows of 3) — propose one; never stack them.
  `per_group` with more than 2 rows is not supported: one figure per group.
- A grid with more than one column takes one time-panel type (`butterfly` or `gfp`, not both).
- `hatch` (low-GFP hatching) is off; use it only when the user asks.
- Condition labels must be unique; titles carry the condition name only, never n.

## When the script stops

- **Panel shape (MS10)** — it lists every `height_mm` range that works: pick one from those ranges.
- **Too many stacked rows** — use a `grid` (above).
- **`hatch` without pre-stimulus samples** — drop `hatch` or tell the user.
- **Flat channel** — ask whether it is the reference electrode (then `flat_channels`) or a broken channel; never add
  it without that answer.
- **Templates without `ch_names`** — a warning, not a stop: the columns are assumed to follow the data's channel
  order; tell the user, and suggest re-exporting the templates with `ch_names`.

## QA after every render (open each PNG)

1. Maps are framed and numbered in time order; ribbon labels and map labels agree.
2. With `hatch`: hatching only where GFP is at baseline level.
3. No electrode marks on the maps; no n in panel titles.
4. `layout_issues` in `_run.json` is empty, or every entry is reported and fixed where the spec can fix it.
5. `open_items` is empty, or every listed field is reported to the user as open; report a normal-vision
   `colour_distinctness` below 10.
6. Replace the `qa` field in `_run.json` with the result ("passed" or the open problems).
