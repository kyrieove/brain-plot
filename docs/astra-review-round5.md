Read-only review; no files changed. Checks used numerical assertions, in-memory rendering, and existing outputs. Full filesystem regression and native MNE interpolation were limited by the read-only sandbox.

1. **P1 — Explore silently truncates averaging windows.**  
   [erp_plot.py:885](/C:/dev/brain-plot/brain-plot/erp_plot.py:885): exploratory windows are not checked against the available time range. With data ending at 400 ms, a requested **350–500 ms** window averages **350–400 ms** but remains labelled 350–500 ms. A synthetic time ramp produced 375, confirming the truncated average.  
   **Minimal fix:** preflight every window for finite bounds, containment within the data, and a nonempty sample mask before drawing.

2. **P1 — Explore silently drops requested conditions.**  
   [erp_plot.py:862](/C:/dev/brain-plot/brain-plot/erp_plot.py:862): `zip(colors, styles, labels)` truncates without validation. Seven conditions with `colors: ["red", "blue"]` produced only two traces per channel and two legend entries. The exploratory path also omits the seven-line limit.  
   **Minimal fix:** apply the existing line-count and palette-length checks before rendering; verify the number of traces drawn.

3. **P2 — Topomap-only figures can fail a nonexistent waveform-legend check.**  
   [erp_plot.py:733](/C:/dev/brain-plot/brain-plot/erp_plot.py:733): legend measurement and `single_panel_corner()` run before dispatching on `kind`. Reproduced with `kind: "topo"`, one group, `overlay: "conditions"`, data −200–400 ms, and window 350–390 ms: execution stops because “a gray band reaches into the legend’s strip,” although neither element will be drawn.  
   **Minimal fix:** run waveform legend preparation and its checks only for `combo` and `erp`.

4. **P2 — Explore colour limits omit interpolation overshoot.**  
   [erp_plot.py:888](/C:/dev/brain-plot/brain-plot/erp_plot.py:888): `vmax()` uses sensor values only; `topo_table()` never examines the interpolated image. This repeats the saturation problem already fixed in `plot()`. The existing N400 topomap run, whose code hash matches the current script, records **3.973 µV sensor maximum versus 4.317 µV interpolated maximum**. Exploring those same conditions and the 350–500 ms window therefore clips at least one group’s maps.  
   **Minimal fix:** expand each applicable global/component and main/difference scale to cover its interpolated maps, retaining shared contour levels within that scale.

5. **P2 — An identically zero difference map crashes.**  
   [erp_plot.py:903](/C:/dev/brain-plot/brain-plot/erp_plot.py:903): a zero maximum produces nine identical contour levels. Two identical condition arrays with `differences: [["A", "B"]]` trigger `ValueError: Contour levels must be increasing`. This affects both scale modes.  
   **Minimal fix:** apply the positive minimum scale already used by `plot()`.

6. **P2 — Waveform layouts violate T6 on the default canvas.**  
   [erp_plot.py:477](/C:/dev/brain-plot/brain-plot/erp_plot.py:477), [erp_plot.py:525](/C:/dev/brain-plot/brain-plot/erp_plot.py:525): fixed margins and proportional spacing do not accommodate the fixed-size text. Confirmed through `plot()` with `kind: "erp"`:
   - One panel: letter **a** occupies approximately **123.24–125.86 mm** vertically on a **120 mm** canvas, so it disappears.
   - Seven condition panels: each of the first six facet labels overlaps the following panel’s ROI title.

   **Minimal fix:** reserve physical space for letters, titles, and facet labels inside the specified canvas; reduce panel heights accordingly.

7. **P2 — Component-scale colour bars can extend outside the fixed canvas.**  
   [erp_plot.py:923](/C:/dev/brain-plot/brain-plot/erp_plot.py:923): the bottom margin is in millimetres, but the bar offset is a fraction of figure height. With `topo_scale: "component"`, difference rows, and `height_mm: 180`, bottom tick labels extend approximately **0.65 mm below the canvas**. These horizontal bars also omit the µV unit.  
   **Minimal fix:** reserve bar-and-tick space in physical units inside the canvas and label the units.

8. **P2 — Single-type captions describe elements that do not exist.**  
   [erp_plot.py:805](/C:/dev/brain-plot/brain-plot/erp_plot.py:805): caption generation is unconditional. `kind: "erp"` captions describe topographies, white dots, and a colour scale; `kind: "topo"` captions describe waveform lines, gray bands, and waveform polarity. Both problems appear in the saved N400 previews.  
   **Minimal fix:** condition the relevant caption facts on `kind`, retaining shared scientific metadata.

9. **P2 — Binding rules and QA still assume every figure is a combined figure.**  
   [rules.md:13](/C:/dev/brain-plot/brain-plot/references/rules.md:13), [rules.md:23](/C:/dev/brain-plot/brain-plot/references/rules.md:23), [rules.md:51](/C:/dev/brain-plot/brain-plot/references/rules.md:51): unconditional requirements include one scale per figure, one figure per component, vertically stacked waveforms, maps beside waveforms, and `lines = maps = expected`. These conflict with exploratory component/difference scales, the 3 × 3 overview, and both single-type outputs. [SKILL.md:71](/C:/dev/brain-plot/brain-plot/SKILL.md:71) directs agents to this incompatible QA list; explore produces no `_run.json` to update. [HANDOFF.md:35](/C:/dev/brain-plot/HANDOFF.md:35) acknowledges the missing rules.  
   **Minimal fix:** scope existing rules and QA by command/kind and document the already-approved layouts and exploratory outputs.

10. **P3 — Small remnants remain in code and layout descriptions.**  
    [erp_plot.py:891](/C:/dev/brain-plot/brain-plot/erp_plot.py:891): `head = 17.0` is unused; [erp_plot.py:941](/C:/dev/brain-plot/brain-plot/erp_plot.py:941) binds unused `meta`. The `draw_topo()` docstring at [line 631](/C:/dev/brain-plot/brain-plot/erp_plot.py:631) still promises a near-square grid, while [spec.md:22](/C:/dev/brain-plot/brain-plot/references/spec.md:22) states “2 × 3 for 6 lines” without qualification—even the regression asserts **1 × 6** for six lines and four panels.  
    **Minimal fix:** remove unused bindings and describe the existing adaptive block selection accurately.

**Verdict: Not ready to sign off; silent omissions, window truncation, and layout/contract failures remain.**