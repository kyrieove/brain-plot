# cluster-waves-v2-rv — rv fixes for layout "waves" (4 findings + 2 simplifications)

## Goal
In `brain-plot/cluster_plot.py`, with `layout: "waves"`, after the change:
1. `color: "uv"` no longer stops on a test without a difference wave (the waves layout skips such tests itself).
2. A `peak_window_ms` that lies outside the result time axis, partly outside it, or holds no time sample stops with a
   message, before any figure is drawn.
3. A channel repeated inside one `waves_channels` list stops with a message that names the channel.
4. The waves caption says "user-given window <lo>–<hi> ms" when `peak_window_ms` is set; without it the caption text is unchanged.
5. Simplified code, same output: `waves_parts` is one comprehension; the legend handles are taken once after the loop.
Done when `C:/Users/ASUS/miniconda3/envs/mne/python.exe brain-plot/test/test_cluster.py` ends with `OK`.

## Risk
medium — one module plus its test; no numbers that go into a paper change.

## Parameters
- Synthetic test run: time axis 2–800 ms in 2 ms steps (`TIMES_MS` in test_cluster.py).
- Valid test window for `peak_window_ms`: [300, 320] → caption text `user-given window 300–320 ms`.
- Bound tolerance for the window check: 1e-3 ms (same as `ep.sample_mask` in erp_plot.py).
- Default caption text keeps `± 25 ms` (peak window of each cluster).
- `waves_parts(n)` unchanged for every n ≥ 1: 1 → [(1, 1)], 2 → [(2, 2)], 7 → [(6, 2), (1, 1)], 13 → [(6, 2), (6, 2), (1, 1)].
- Blocks per figure part: 6.

## Files
may change: `brain-plot/cluster_plot.py`, `brain-plot/test/test_cluster.py`
read-only: `brain-plot/erp_plot.py`, `docs/cluster-before-after/`, `docs/cluster-layout-compare.html`, `docs/cluster-layout-compare-real.html`, `docs/tfce-mne-vs-standard.html`, `AGENTS.md`, `AGENTS.md.bak-doctor-2026-10-09`

## Steps (N = 7)
1. `brain-plot/cluster_plot.py`, `read_run` (line 175). Change the colour check so it does not apply to the waves layout:
   ```python
       if spec.get("color", "stat") == "uv" and spec.get("layout") != "waves":
   ```
   Rest of the block unchanged. `plot()` already drops tests without a difference wave in the waves branch (`skipped`).

2. `brain-plot/cluster_plot.py`, `plot()`, first lines inside `if layout == "waves":` (line 623, before `want = ...`). Check the window against the result time axis `times`:
   ```python
           if "peak_window_ms" in spec:
               lo, hi = float(spec["peak_window_ms"][0]), float(spec["peak_window_ms"][1])
               if lo < times[0] - 1e-3 or hi > times[-1] + 1e-3:
                   ep.die(f'layout "waves": peak_window_ms [{lo:g}, {hi:g}] lies outside the result time axis '
                          f'{times[0]:g}–{times[-1]:g} ms; give a window inside it')
               if not ep.sample_mask(times, lo, hi).any():
                   ep.die(f'layout "waves": peak_window_ms [{lo:g}, {hi:g}] holds no time sample; give a window '
                          'that contains at least one sample')
   ```
   Bypass paths: `peak_map` is called only from `plot_waves` (line 909), and `plot_waves` only from `plot()`. The check
   runs before both, so no other path reaches the window.

3. `brain-plot/cluster_plot.py`, `check_spec` (lines 68–76, the `waves_channels` branch). After the existing
   `if not (as_list or as_map): ep.die(...)`, add a duplicate check per list. Repeats of one channel across different
   clusters stay allowed:
   ```python
           for names in ([wc] if as_list else list(wc.values())):
               dup = [n for n in dict.fromkeys(names) if names.count(n) > 1]
               if dup:
                   ep.die(f"waves_channels lists {', '.join(dup)} more than once in one list; name each channel once, "
                          "a repeat weights the mean and the CI")
   ```
   Bypass paths: `check_spec` is the first call in `plot()` (line 609) and `waves_channels` is read only through `plot()`.

4. `brain-plot/cluster_plot.py`, `write_caption` (lines 391–395, the `if waves:` branch). Use the user window when the
   spec sets `peak_window_ms`; keep the `Channel marker` line exactly as it is:
   ```python
       if waves:
           win = spec.get("peak_window_ms")
           map_txt = (f"µV difference over the user-given window {win[0]:g}–{win[1]:g} ms" if win else
                      "µV difference over the peak window of each cluster (peak time of the summed |t| over the channels "
                      "of the cluster ± 25 ms, clipped to the cluster window)")
           lines += [f"- **Topomaps**: {map_txt}",
                     <the existing "- **Channel marker**: …" line, unchanged>]
   ```

5. `brain-plot/cluster_plot.py`, `waves_parts` (lines 450–458). Keep the docstring; replace the body with:
   ```python
       return [(min(6, n - i), 1 if n - i == 1 else 2) for i in range(0, n, 6)]
   ```
   Same output for every n ≥ 1 (a drawable test always has at least one cluster). Existing asserts at test_cluster.py
   lines 254–260 check it.

6. `brain-plot/cluster_plot.py`, `plot_waves` (lines 944, 966–967, 980). Delete `handles = None` (line 944) and the
   pair `if handles is None:` / `handles = ax.get_legend_handles_labels()[0]` (lines 966–967). Then, after the
   `for j, ax in enumerate(axes):` loop and before `fig.legend(handles, ...)`, add one line:
   ```python
               handles = axes[0].get_legend_handles_labels()[0]
   ```
   Keep the legend position and the legend labels unchanged.

7. `brain-plot/test/test_cluster.py`, `run_tests`. Insert after the waves-stops block (after line 246, before the
   `# (p) cluster_peak, recommend_channels …` comment at line 248). `wave_ch` is defined at line 205; `assert_stops`
   (line 172) checks that the match text is a substring of the SystemExit message:
   ```python
           # (t) waves review fixes: uv colour needs no difference wave, window inside the time axis, no repeated channel
           outs_uv = cluster_plot.plot({**spec, "tests": [T01, T02, T03], "layout": "waves",
                                        "waves_channels": wave_ch, "color": "uv"})
           assert len(outs_uv) == 2, outs_uv
           assert_stops({**spec, "layout": "waves", "waves_channels": wave_ch, "peak_window_ms": [700, 900]},
                        "outside the result time axis")
           assert_stops({**spec, "layout": "waves", "waves_channels": wave_ch, "peak_window_ms": [900, 1000]},
                        "outside the result time axis")
           assert_stops({**spec, "layout": "waves", "waves_channels": wave_ch, "peak_window_ms": [301, 301.5]},
                        "no time sample")
           assert_stops({**spec, "layout": "waves", "waves_channels": ["Cz", "Cz"]}, "more than once")
           assert_stops({**spec, "layout": "waves",
                         "waves_channels": {f"{T01}/1": ["Cz", "Cz"], f"{T03}/1": ["Pz"]}}, "more than once")
           outs_pw = cluster_plot.plot({**spec, "layout": "waves", "waves_channels": wave_ch,
                                        "peak_window_ms": [300, 320]})
           cap_pw = Path(f"{outs_pw[0]}_caption.md").read_text(encoding="utf8")
           assert "user-given window 300–320 ms" in cap_pw and "± 25 ms" not in cap_pw, cap_pw
           print("cluster waves review fixes: uv colour ok, window outside / no sample stops, repeated channel stops, caption window")
   ```
   Do not change any existing assert in the file.

## Check
`C:/Users/ASUS/miniconda3/envs/mne/python.exe brain-plot/test/test_cluster.py`
(the full path matters: on this machine bare `python` is LibreOffice's). The last line must be `OK`.

## Don't
- No commits.
- No rm, no git push, no git checkout . / restore . / reset --hard.
- Only the two files in `## Files`. Leave every other uncommitted file alone, in particular `AGENTS.md`,
  `AGENTS.md.bak-doctor-2026-10-09`, `docs/cluster-before-after/`, `docs/cluster-layout-compare*.html`, `docs/tfce-mne-vs-standard.html`.
- No refactors beyond the seven steps. No change to figure geometry, the figure stems, the default caption text, the `Channel marker` caption line, or the non-waves layouts.
- Reuse existing functions; don't copy existing logic. (`ep.die`, `ep.sample_mask`, `dict.fromkeys` are the ones this card names.)
- Do not touch any real data folder or any spec under `specs\`; the test builds its own synthetic run in a temp folder.
- Run scripts in the foreground and wait; before replying, stop any background task still running.

## Acceptance
- verdict: accepted
- claude check: re-ran the Check myself, last line `OK`, exit 0. Read the diff (cluster_plot.py 33 lines, test 19 lines): steps 1–7 as written, nothing outside Files. The legend handles now come from `axes[0].get_legend_handles_labels()`; the fill, axvspan and axvline artists carry no label, so the handles are the same two labelled lines as before. Figures were not opened: the test uses a synthetic run in a temp folder, and the real-data re-render stays with the user.
- files: brain-plot/cluster_plot.py, brain-plot/test/test_cluster.py
- check: `C:/Users/ASUS/miniconda3/envs/mne/python.exe brain-plot/test/test_cluster.py` → exit 0 (run by run-card)
- tokens:
  - round 1: exec deepseek-v4.1-flash: fresh 31k, cached 1322k, out 9k  (codex-cluster-waves-v2-rv.jsonl) · review gpt-6-luna: fresh 50k, cached 219k, out 2k  (codex-review-cluster-waves-v2-rv.jsonl)
- review findings: 0 real / 1 false positive / 0 missed (medium, gpt-6-luna). False positive: [P2] "reply.md is an unauthorised new file". reply.md is the runner's own per-task file, not an executor edit, so it stays.
