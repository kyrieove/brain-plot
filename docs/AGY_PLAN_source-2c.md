# AGY PLAN source-2c: LPC → SN (sustained negativity) check; revert the sign rule

Same boundaries and allowed files as `C:\dev\brain-plot\docs\AGY_PLAN_source-1.md`; the check script in step 2 goes
to `S\sn_check.py` with its output `S\sn_check.txt` (S below). Progress: append to
`C:\dev\brain-plot\AGY_PROGRESS_source.md`, first line `[░░░░] 0/4 plan 2c start · HH:MM`.
`S` = `D:\1-python_datasets\metaphor production\derivatives\brain_plot_preprocessed_epochs_verb\specs\`.

User decisions (2026-10-01): (1) the sign rule from plan 2b is wrong — a component's polarity is the direction of its
deflection relative to the neighbouring waveform, not the absolute voltage sign; remove it. (2) The late window is not
an LPC; check whether it is an SN (sustained negativity; literature: Rutter 2012 500–900 ms, Bambini 2019 sustained
frontal negativity, Baiocco 2024 450–850 ms left anterior).

## Steps (N = 4)
1. Revert the plan-2b sign rule in `erp_plot.windows` and its test (back to: a real local extremum of the given
   polarity inside the range, FWHP on the whole waveform). Suites `test_erp_plot.py` `OK`.
2. `S\sn_check.py` (reuse `erp_plot.load` on `S\source_localizer.json` for the collapsed average — all 59 subjects,
   all conditions, equal weights, whole epoch −1…2 s, no xlim crop). Print to `S\sn_check.txt`:
   a. Region means over time, 100-ms bins from 300 to 2000 ms, for FRONTAL = Fp1 Fp2 AF7 AF3 AFz AF4 AF8 F7 F5 F3 F1
      Fz F2 F4 F6 F8, CENTRAL = FC3 FC1 FC2 FC4 C3 C1 Cz C2 C4, POSTERIOR = P3 P1 Pz P2 P4 PO3 POz PO4 O1 Oz O2; also
      LEFT-FRONTAL (F7 F5 F3 AF7 AF3) vs RIGHT-FRONTAL (F8 F6 F4 AF8 AF4).
   b. For each 100-ms bin 500–1000 ms, the 5 most negative channels.
   c. SN window: on the FRONTAL mean, the contiguous interval containing its minimum within 500–1000 ms during which
      the value stays below 50 % of that minimum (whole epoch axis, not clipped to 500–1000). Print min latency, value,
      interval.
   d. Between the N400 peak (428 ms, Cz) and the SN minimum: does the FRONTAL/CENTRAL mean return toward 0 (print the
      least negative value between them)?
   e. 1000–2000 ms: keeps falling, flat, or returning toward 0 (print the FRONTAL mean at 1000, 1500, 2000 ms)?
   Do not interpret beyond printing; one line "criteria" at the end: sustained ≥ 300 ms (yes/no), frontal more
   negative than posterior (yes/no), separated from N400 (yes/no), still falling at 2000 ms (yes/no).
3. Update `S\source_localizer.json`: replace the LPC component with nothing (the localizer stays for P200/N400);
   write `S\source_windows.json` windows = P200 and N400 from the localizer + `{"name": "SN", "tmin_ms": <c start>,
   "tmax_ms": <c end>}`; add a spec text key only if the script accepts one — otherwise record the SN window's origin
   in `S\sn_check.txt`. Render `source_plot.py plot S\source_windows.json`.
4. Suites: all five `OK`. Open the PNG and confirm every cell shows a brain.

## Reply (≤ 10 lines)
The criteria line and the key numbers of `sn_check.txt` (a, c, d, e); the three windows; PNG path; suites.
