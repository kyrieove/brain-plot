# display-fixes — astra findings 12, 14, 15 (+ TFR caption facts from 17, TFR window names from 16)

Review text: `research/astra-review-brainplot.md` findings 12, 14, 15 (and the TFR parts of 16, 17). Paths relative
to repo root `C:/dev/brain-plot`; run Python from `C:/dev/brain-plot/brain-plot`.

## Goal
- ERP localizer ROI is defined relative to the peak's prominence, so the peak channel is always in the ROI and a
  positive deflection on a negative offset no longer returns an empty ROI.
- TFR ITC with fewer than 2 trials in any subject × condition stops; the TFR caption states trials per condition
  (min–max, median over subjects), and for ITC the random-phase bias √(π/4n) at the median n; it also states query,
  exclusions and describes an explicit frequency list as such (not "log-spaced").
- Topomap colour limits cover the interpolated image, not only the sensor values: TFR power window rows and
  microstate maps use the interpolated peak; TFR ITC maps use linear interpolation (stays within the data range,
  so within 0–1). `_run.json` records sensor and interpolated maxima for TFR window rows.
- TFR window file-name parts carry their ranges, so two windows with one name but different values never share a name.

## Files
May change: `brain-plot/erp_plot.py` (steps 1–2 only), `brain-plot/tfr_plot.py`, `brain-plot/microstate_plot.py`
(step 5 only), `brain-plot/test/test_erp_plot.py`, `brain-plot/test/test_tfr.py`, `docs/rules.md` (TF4, TF5 rows),
`brain-plot/references/tfr.md`, `brain-plot/references/erp.md` (line 54, the ROI definition).
Read-only: everything else; never any data or `brain_plot_*` folder.

## Steps

### 1. `erp_plot.py` — localizer ROI relative to the peak's prominence (finding 12)
- Import: change `from scipy.signal import find_peaks, peak_widths` to
  `from scipy.signal import find_peaks, peak_prominences, peak_widths`.
- In the localizer (the block with `# ROI = region channels whose value at the peak latency is >= 80 % of the peak`)
  replace that comment and the `roi = [...]` line with:
  ```python
            # ROI = region channels whose deflection at the peak latency, measured from the peak's base (its height
            # minus its prominence), is >= 80 % of the peak's prominence; the peak channel is always included
            prom = float(peak_prominences(y_full, [full_peak_idx])[0][0])
            base = sign * peak_val - prom
            roi = [ch for ch in c["region"] if sign * allsub[info.ch_names.index(ch), full_peak_idx] - base >= 0.8 * prom]
  ```
- Change the ROI print line to
  `print(f"  ROI ({len(roi)} channels, >= 80 % of the peak's prominence {prom:.2f} µV above its base): {', '.join(roi)}")`.

### 2. `erp_plot.py` — shared interpolated-peak helper
Add just after the `TOPO = dict(...)` line's section (any module-level place before first use, e.g. right after
`def common_sphere` ends):
```python
def interp_peak(vec, info, sphere, image_interp=None):
    """Largest |value| of the interpolated topomap image; cubic interpolation can overshoot the sensor values."""
    fig, ax = plt.subplots()
    im, _ = mne.viz.plot_topomap(vec, info, axes=ax, show=False, contours=0, sensors=False,
                                 extrapolate=TOPO["extrapolate"], image_interp=image_interp or TOPO["image_interp"],
                                 sphere=sphere)
    a = im.get_array()
    plt.close(fig)
    return float(np.ma.abs(a).max()) if np.ma.count(a) else 0.0
```

### 3. `tfr_plot.py` — ITC trial floor (finding 14)
In `load_and_compute`, right after `trial_counts[g][s_id] = {...}` add:
```python
            if measure == "itc" and min(trial_counts[g][s_id].values()) < 2:
                ep.die(f"{f.name}: ITC needs at least 2 trials per condition (got {trial_counts[g][s_id]}); "
                       "one trial always gives ITC = 1")
```

### 4. `tfr_plot.py` — topomap limits, ITC interpolation, window names (findings 15, 16)
In `plot()`, in the window-row loop:
- After `max_topo = ...` add
  ```python
            itc_interp = "linear" if measure == "itc" else ep.TOPO["image_interp"]  # linear stays within the data range (0–1)
            interp_max = max(ep.interp_peak(val, info, sphere, itc_interp) for val in row_topos)
  ```
  and change `v_row = float(np.ceil(max_topo * dec) / dec) or 1.0` to
  `v_row = float(np.ceil(max(max_topo, interp_max) * dec) / dec) or 1.0`.
- Change the `color_limits[...]` line to
  `color_limits[f"window_{w['name']}"] = dict(v=v_row, vmin=lo_row, vmax=v_row, sensor_max=float(max_topo), interp_max=interp_max, image_interp=itc_interp)`.
- In that row's `mne.viz.plot_topomap(...)` call change `image_interp=ep.TOPO["image_interp"]` to `image_interp=itc_interp`.
- Change `win_part` to
  `win_part = ("_" + "-".join(f"{ep.safe(w['name'])}-{w['fmin']:g}-{w['fmax']:g}Hz-{w['tmin_ms']:g}-{w['tmax_ms']:g}ms" for w in windows)) if windows else ""`.

### 5. `microstate_plot.py` — map limits cover the interpolation (finding 15)
- In `plot_states`: `vmax = float(np.abs(centers).max())` →
  `vmax = max(ep.interp_peak(c, info, sphere) for c in centers)  # cubic overshoot must not saturate`.
- In `plot_by_k`: `vmax = max(float(np.abs(c).max()) for _, c, _ in rows)` →
  `vmax = max(ep.interp_peak(v, info, sphere) for _, c, _ in rows for v in c)`.
(`info` and `sphere` are parameters of both functions.)

### 6. `tfr_plot.py` — caption facts (findings 14, 17)
- Signature: `def write_caption_md(out, spec, group, n_subj, tf_params, trials):` and the call in `plot()`:
  `write_caption_md(out, spec, g, len(subs), tf_params, trial_counts[g])` (`trial_counts` is already in scope there).
- Frequencies line: replace the fixed `f"- **Frequencies**: ... ({f_info['n']} log-spaced)"` with
  ```python
        f"- **Frequencies**: {f_info['fmin']:.1f}–{f_info['fmax']:.1f} Hz, {f_info['n']} "
        + ("log-spaced" if isinstance(spec.get("freqs", {}), dict) else "listed: " + ", ".join(f"{x:g}" for x in spec["freqs"])),
  ```
- After the `ROI channels` line add, in this order:
  ```python
    for c in spec["conditions"]:
        ns = sorted(t[c] for t in trials.values())
        med = float(np.median(ns))
        line = f"- **Trials, {spec['conditions'][c]}**: {ns[0]}–{ns[-1]} per subject (median {med:g})"
        if spec["measure"] == "itc":
            line += f"; random phase alone gives ITC ≈ {np.sqrt(np.pi / (4 * med)):.2f} at the median"
        lines.append(line)
    if spec.get("query"):
        lines.append(f"- **Trial selection**: `{spec['query']}`")
    if spec.get("exclude"):
        lines.append(f"- **Excluded**: {spec['exclude']}")
  ```
  (`lines` is the list being built; use `.append` after the `lines.extend([...])` that holds ROI channels.)

### 7. Docs
- `references/erp.md` line 54 (localizer ROI): replace the ">= 80 % of the peak" definition with the prominence-based one
  (deflection from the peak's base >= 80 % of its prominence; peak channel always included).
- `docs/rules.md` TF4/TF5: add "Topomap colour limits cover the interpolated image (cubic for power; ITC maps use
  linear interpolation, which stays within 0–1). ITC needs >= 2 trials per subject and condition; the caption gives
  trials per condition and the random-phase ITC bias √(π/4n)."
- `references/tfr.md`: one bullet in the QA/check list: "ITC: compare conditions only with similar trial counts — the
  caption's bias value shows how much ITC random phase alone produces."

### 8. Tests
a) `test/test_erp_plot.py`, in the localizer section (3) (relative polarity, `-5e-6 + 1e-6 * exp(...)` signal), after
the existing assertions on `out_relative` add:
```python
        assert "ROI (2 channels" in out_relative and "Cz, Pz" in out_relative, out_relative
```
and right after it a negative mirror on a positive offset:
```python
        neg_sig = 5e-6 - 1e-6 * np.exp(-0.5 * ((t_loc - 0.3) / 0.03) ** 2)
        neg_ev = mne.EvokedArray(np.stack([neg_sig, neg_sig]), rel_info, tmin=-0.2, comment="A", nave=10)
        mne.write_evokeds(root_loc / "G1" / "sub1-ave.fif", [neg_ev], overwrite=True, verbose="error")
        buf_neg = io.StringIO()
        with contextlib.redirect_stdout(buf_neg):
            ep.windows(dict(**spec_loc, components=[dict(name="N3_relative", region=["Cz", "Pz"], polarity="negative", tmin_ms=200, tmax_ms=400)]))
        assert "ROI (2 channels" in buf_neg.getvalue(), buf_neg.getvalue()
```
If `spec_loc` / `root_loc` / the file layout differ from what this assumes, mirror exactly how the existing relative
case writes its file and calls `ep.windows`; if the relative case restores the original file afterwards, do the same.
b) `test/test_tfr.py`, right after the "TFR stops: ..." print added by the previous card (before the
cache-invalidation block):
```python
        # display facts: interpolated limits, ITC bounds, caption trials, ITC trial floor
        outs = tfr_plot.plot(base_spec)
        lim = json.loads(Path(f"{outs[0]}_run.json").read_text(encoding="utf8"))["color_limits"]["window_alpha"]
        assert lim["v"] >= lim["interp_max"] - 1e-9 and lim["v"] >= lim["sensor_max"] - 1e-9, lim
        outs_itc = tfr_plot.plot({**base_spec, "measure": "itc"})
        lim_itc = json.loads(Path(f"{outs_itc[0]}_run.json").read_text(encoding="utf8"))["color_limits"]["window_alpha"]
        assert lim_itc["interp_max"] <= 1.0 + 1e-9 and lim_itc["image_interp"] == "linear", lim_itc
        cap = Path(f"{outs_itc[0]}_caption.md").read_text(encoding="utf8")
        assert "Trials, 10 Hz Burst" in cap and "random phase alone gives ITC" in cap, cap
        assert "-8-12Hz-300-600ms" in Path(outs[0]).name, outs[0]
        f0 = sorted(data_dir.rglob("*-epo.fif"))[0]
        orig = f0.read_bytes()
        e0 = mne.read_epochs(f0, verbose="error")
        keep = [i for i, ev in enumerate(e0.events[:, 2]) if ev != e0.event_id["phase"]] + \
               [int(np.where(e0.events[:, 2] == e0.event_id["phase"])[0][0])]
        e0[sorted(keep)].save(f0, overwrite=True, verbose="error")
        assert_stops({**base_spec, "measure": "itc"}, "at least 2 trials")
        f0.write_bytes(orig)
        print("TFR display: interpolated limits, ITC in 0–1, caption trials, window ranges, ITC trial floor")
```

## Check
```bash
cd C:/dev/brain-plot/brain-plot && python test/test_tfr.py && python test/test_erp_plot.py && python test/test_microstate.py
```
All end without a traceback and print `OK`.

## Don't
- No commits; no files outside the list; no refactors beyond the steps.
- Reuse `ep.interp_peak` everywhere (no local copies); don't change ERP's own overshoot loop.
- Don't change source files or figure layouts.
- Run only the Check command.

## Acceptance
Verdict: accepted. codex review not run — Codex usage limit reached (`You've hit your usage limit`, 2026-10-01
~19:05 local); Claude reviewed the diff line by line instead: steps 1–8 followed, `ep.interp_peak` defined once and
reused in TFR and microstate, no extra files. Check re-run by Claude: test_tfr (incl. "TFR display: ..."),
test_erp_plot, test_microstate all `OK`. agy 488 s. Effect on existing figures: microstate and TFR power topomap
limits can grow slightly (interpolated peak), TFR ITC maps are now linear-interpolated, TFR window file names carry
ranges, localizer ROI may differ for peaks on an offset.
