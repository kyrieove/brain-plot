# cluster-v1-v2 — fix the luna review findings and the first real render of cluster_plot.py

## Goal
`brain-plot/cluster_plot.py` (written by card `docs/orch/2026-10-10-cluster-v1/`) is correct for B files whose
channel order differs from A, checks the index columns, draws channel labels that do not overlap (the GN render had
57 layout issues, all overlapping channel names), uses non-overlapping topomap bins with honest labels, and smaller
channel markers. `python brain-plot/test/test_cluster.py` prints `OK` and covers the new cases.

## Risk
medium — the µV difference code changes; Claude recomputes Oz 702–800 ms on GN test 01 again (expected 7.765 µV,
plain-numpy value from 2026-10-10).

## Parameters
- Raster rows: raster height = max(60 mm, 1.5 mm × n_ch); channel tick labels fontsize 4 (64 channels → 96 mm).
- Topomap bins: half-open [a, a + step) by sample, the last bin closed at the last sample; a sample belongs to exactly
  one bin. Label = `"<first sample>–<last sample> ms"` of that bin, both rounded to integers (`f"{x:.0f}"`): GN gives
  `2–100 ms`, `102–200 ms`, …, `702–800 ms`.
- Channel marker on topomaps: `markersize=1.2`, `markeredgewidth=0.25` (rest unchanged: white face, black edge).
- Required CSV columns: `time_axis.csv` → `time_index`, `time_ms`; `channel_order.csv` → `channel_index`, `channel`.

## Files
may change: `brain-plot/cluster_plot.py`, `brain-plot/test/test_cluster.py`
read-only: `brain-plot/erp_plot.py`, `docs/orch/2026-10-10-cluster-v1/card.md`, `C:\Users\ASUS\Dropbox\metaphor_production\gn_manuscript\03-ERP_topomap\03_cluster_inference\01_cluster_based_permutation_0000_0800ms\`, `C:\Users\ASUS\Dropbox\metaphor_production\gn_manuscript\01-evokeds_grand_averages\`

## Steps (N = 5)
1. `cluster_plot.py:101` and `:104` — `require_columns` with both columns from Parameters for each file.
2. `cluster_plot.py` `diff_uv` (lines ~201–218): compute channel indices and the sample indices separately for each
   file. Write one local helper inside `diff_uv`, e.g.
   ```python
   def sampled(ev, fname):
       """(n_ch, n_times) µV of `ev` at the run's channels and result times; stops on a mismatch."""
       missing = [c for c in ch_names if c not in ev.ch_names]
       if missing: ep.die(...)          # same message style as picked_info
       idx = [ev.ch_names.index(c) for c in ch_names]
       d = np.abs(ev.times[None, :] * 1000.0 - times_ms[:, None])
       worst, half = float(d.min(1).max()), 0.5 / ev.info["sfreq"] * 1000.0
       if worst > half: ep.die(...)     # the existing message, naming fname
       return ev.data[idx][:, d.argmin(1)] * 1e6
   ```
   and use `diff = sampled(ev_a, file_a) - sampled(ev_b, file_b)`. Remove the old inline index/time code (no copy left).
3. `cluster_plot.py` `bins_of_times` / `maps_of` (lines ~305–316): build bins as sample masks per Parameters, e.g.
   `edges = times[0] + step * np.arange(nbins + 1)`; bin i = `(times >= edges[i] - 1e-3) & (times < edges[i + 1] - 1e-3)`,
   last bin also includes `times[-1]`; drop empty bins; label from `times[m][0]` and `times[m][-1]`. Raster height and
   tick label fontsize per Parameters (`raster_h` at line ~300, `set_yticklabels` at ~358); marker per Parameters (~395).
4. `test_cluster.py`: (f) save one participant's B (`GO`) file with channels reversed
   (`ev.reorder_channels(list(reversed(ev.ch_names)))`) before computing, and assert the 2.0 ± 0.1 µV at Cz still holds;
   (g) a `time_axis.csv` without `time_index` stops; (h) the default render's `_caption.md` or `_run.json` / returned
   bins contain `2–100 ms` and no two bins share a sample (check via a small call of the bin helper if it is reachable,
   else via the label text in the SVG: `"2–100 ms" in svg_text and "2–102 ms" not in svg_text`); keep every existing
   assert unchanged and `layout_issues == []`.
5. Run the Check yourself in the foreground (`python brain-plot/test/test_cluster.py`) until it prints `OK`; then
   render the real GN figure once (read-only input; output goes to the module's own output folder next to it, which
   is allowed): write the spec to the system temp dir as
   `{"data": "C:/Users/ASUS/Dropbox/metaphor_production/gn_manuscript/03-ERP_topomap/03_cluster_inference/01_cluster_based_permutation_0000_0800ms", "tests": ["01_condition_main_effect_all", "03_within_td_condition_effect"], "labels": {"01_condition_main_effect_all": "All (N = 95): NoGO − GO", "03_within_td_condition_effect": "TD (N = 31): NoGO − GO"}}`
   and run `python brain-plot/cluster_plot.py plot <that spec>`; it must print no `WARNING: layout` line. If it does,
   adjust only the Parameters values above (row height, fontsize) and say so in the reply.

## Check
```
python brain-plot/test/test_cluster.py
```

## Don't
- No commits. Write only the two files under "may change" (plus the GN render's own outputs in step 5).
- Never write, move or delete anything else under `gn_manuscript`.
- Do not change behaviour the steps do not name; do not weaken existing asserts.
- "Run scripts in the foreground and wait; before replying, stop any background task still running."
- "Reuse existing functions; don't copy existing logic."
- "No rm, no git push, no git checkout . / restore . / reset --hard."

## Acceptance
- verdict: accepted (recompute: Oz 702-800 ms, GN test 01 = 7.765 uV, equal to an independent plain-numpy value; GN render v02 layout_issues [])
- files: brain-plot/cluster_plot.py, brain-plot/test/test_cluster.py
- check: `python brain-plot/test/test_cluster.py` → exit 0 (run by run-card)
- tokens:
  - round 1: exec deepseek-v4.1-flash: fresh 52k, cached 2264k, out 23k  (codex-cluster-v1-v2.jsonl) · review gpt-6-luna: fresh 47k, cached 162k, out 1k  (codex-review-cluster-v1-v2.jsonl)
- review findings: 0 real / 0 false positive / 0 missed (medium, gpt-6-luna)

