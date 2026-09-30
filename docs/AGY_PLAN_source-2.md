# AGY PLAN source-2: windows from the localizer, then the main source figure

Same boundaries as `C:\dev\brain-plot\docs\AGY_PLAN_source-1.md` (read its "Boundaries" section again). In this plan
you change NO code: you only write the spec/output files named below and run existing commands. If a command stops,
report its message and stop; do not edit code.
Progress: append to `C:\dev\brain-plot\AGY_PROGRESS_source.md`, format `[██░░] 2/4 <what> · HH:MM`, first line
`[░░░░] 0/4 plan 2 start · HH:MM`. Specs folder below: `S = D:\1-python_datasets\metaphor production\derivatives\brain_plot_preprocessed_epochs_verb\specs\`.

## Steps (N = 4)
1. Write `S\source_localizer.json`: the keys `data`, `conditions`, `query`, `exclude`, `time_locked_to` exactly as in
   `S\source_timeline.json`, plus `"xlim_ms": [-200, 1000]` and
   ```json
   "components": [
     {"name": "P200", "polarity": "positive", "tmin_ms": 150, "tmax_ms": 300,
      "region": ["F3","F1","Fz","F2","F4","FC3","FC1","FC2","FC4","C3","C1","Cz","C2","C4"],
      "window_source": "fronto-central P2 (Zhao et al. 2011; weak support in the metaphor literature); window from the collapsed localizer"},
     {"name": "N400", "polarity": "negative", "tmin_ms": 300, "tmax_ms": 550,
      "region": ["F3","Fz","F4","C3","Cz","C4","P3","Pz","P4"],
      "window_source": "N400 sites of Li et al. 2022 (verb-locked Chinese metaphors); window from the collapsed localizer"},
     {"name": "LPC", "polarity": "positive", "tmin_ms": 500, "tmax_ms": 900,
      "region": ["F3","Fz","F4","C3","Cz","C4","P3","Pz","P4"],
      "window_source": "P600/LPC sites of Li et al. 2022; window from the collapsed localizer"}
   ]
   ```
   (If `erp_plot.py windows` rejects a key such as `window_source` here, drop that key and note it.)
2. Run `python C:\dev\brain-plot\brain-plot\erp_plot.py windows S\source_localizer.json` and save its full console
   output to `S\source_localizer_output.txt`.
3. Write `S\source_windows.json` = `S\source_timeline.json` with `"figure": "windows"` and `"windows"` = the entries of
   the `WINDOWS_JSON` line (keys `name`, `tmin_ms`, `tmax_ms` only; round to whole ms). A component the localizer did
   not find is left out and named in the reply. Remove timeline-only keys if the script rejects them.
4. Run `python C:\dev\brain-plot\brain-plot\source_plot.py plot S\source_windows.json`. Check its `_run.json`:
   `layout_issues` empty.

## Reply (≤ 10 lines)
The three windows (peak channel, peak ms, window, ROI) and any GFP WARNING line; PNG path; `layout_issues`; anything
that stopped.
