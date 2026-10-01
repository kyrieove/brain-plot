# source-fixes — fix astra review findings 1, 3, 6, 8, 9 in source_plot.py

Review text: `research/astra-review-brainplot.md` (findings 1, 3, 6, 8, 9). All paths below are relative to the
repo root `C:/dev/brain-plot`; run Python from `C:/dev/brain-plot/brain-plot`.

## Goal
- The time axis of every reconstructed Evoked/STC uses the real post-decimation sampling rate (no `sfreq = 100` overwrite);
  decimation never violates `lowpass <= new_sfreq / 3`.
- The evoked is no longer cropped to −200…1000 ms; any window / timeline point that is not fully inside the data
  stops the run before any brain is rendered.
- The forward solution is never borrowed from a sibling cache folder; the cached forward is keyed by the electrode
  geometry and by src/BEM file identity (path + size + mtime); src/BEM objects passed in are never persisted.
  Subjects whose electrode positions differ from the first subject stop the run.
- Brain overlays use a hard threshold: values ≤ fmin transparent, everything above opaque (no alpha ramp).
- Duplicate window names (source `windows`, TFR `windows`) and duplicate `times_ms` stop the run in `check_spec`.

## Files
May change: `brain-plot/source_plot.py`, `brain-plot/test/test_source.py`, `brain-plot/tfr_plot.py` (one check only),
`docs/rules.md` (SRC1, SRC4, SRC6 rows only).
Read-only: everything else. Never touch any data folder or `brain_plot_*` output folder.

## Steps

### 1. `source_plot.py` — new module-level helpers (put them just above `class BrainRenderer`)
```python
def pick_decim(sfreq, lowpass):
    """Integer decimation toward ~100 Hz that keeps lowpass <= new sfreq / 3 (anti-aliasing)."""
    decim = max(1, int(round(sfreq / 100.0)))
    while decim > 1 and lowpass is not None and lowpass > sfreq / decim / 3.0:
        decim -= 1
    return decim


def geometry_key(info):
    """Hash of channel names, kinds and electrode positions; the forward solution depends on these."""
    chs = [(ch["ch_name"], int(ch["kind"]), [round(float(x), 6) for x in ch["loc"][:3]]) for ch in info["chs"]]
    return hashlib.md5(json.dumps(chs).encode()).hexdigest()[:8]


def file_id(path):
    """Identity of a src/BEM file: resolved path, size and modification time."""
    p = Path(path).resolve()
    st = p.stat()
    return f"{p}|{st.st_size}|{st.st_mtime_ns}"


def threshold_cmap():
    """hot with the lowest LUT entry fully transparent: values <= fmin are hidden, everything above is opaque (SRC4)."""
    lut = matplotlib.colormaps["hot"](np.linspace(0.0, 1.0, 256))
    lut[0, 3] = 0.0
    return matplotlib.colors.ListedColormap(lut)
```
(`hashlib`, `json`, `matplotlib`, `np`, `Path` are already imported — check, add nothing else.)

### 2. `BrainRenderer.render` — hard threshold (finding 8)
In the `b.add_data(...)` call replace `transparent=True, colormap="hot"` with
`transparent=False, colormap=threshold_cmap()`. Nothing else in `render` changes. The matplotlib colour bar in
`plot()` stays `cmap="hot"` with `Normalize(fmin, fmax)` — it now matches the brain (linear fmin→fmax, no alpha).
(Verified: MNE 1.13 `calculate_lut(..., transparent=False)` keeps the colormap's own alpha channel, so entry 0 has
alpha 0 and entries 1… alpha 1; values below fmin are clipped to entry 0.)

### 3. `check_spec` — unique names (finding 9)
- In the `fig_type == "windows"` block, after the per-window loop add:
  ```python
  names = [w["name"] for w in windows]
  if len(set(names)) != len(names):
      ep.die(f"window names must be unique (got {names!r})")
  ```
- In the `fig_type == "timeline"` block, after the `times_ms` type check add:
  ```python
  if len(set(times)) != len(times):
      ep.die(f"times_ms must not repeat (got {times!r})")
  ```
- `tfr_plot.py` `check_spec`: after the `for w in spec["windows"]:` loop (still inside `if "windows" in spec:`), add
  the same unique-name check using `spec["windows"]`.

### 4. `load_and_compute` — src/BEM identity (finding 3)
- Path branches: `src_name = file_id(src)` / `file_id(src_path)`; `bem_name = file_id(bem)` / `file_id(bem_path)`.
- Object branches keep `"custom-src"` / `"custom-bem"`.
- After both blocks: `persist_fwd = src_name != "custom-src" and bem_name != "custom-bem"`.
- In `param_dict` change `"cache_version": 2` → `3` (old caches hold cropped, mislabelled data and must not be read).

### 5. `load_and_compute` — move the grand-average cache check before the forward (no behaviour change)
Move the whole `# Check if grand average is already cached` block (the `if ga_cache.exists(): ...return ...`) so it
sits directly after `ga_cache = ...` and before `# Forward solution`. Keep `first_ch_names = None`,
`trial_counts = {}`, `valid_ids = []` above it (the early return uses `trial_counts`/`valid_ids` names only after
reassigning them, so just keep the three initialisations right before the moved block).

### 6. `load_and_compute` — forward solution (finding 3)
Replace the whole `# Forward solution` block (from `fwd_file = ...` to the end of the `else:` that writes the
forward) with:
```python
    # Forward solution: one per electrode geometry, never borrowed from another parameter folder
    first_info = mne.io.read_info(active_files[s_ids[0]], verbose="error")
    geom = geometry_key(first_info)
    fwd_file = cache_dir / f"fwd-{geom}.fif"
    if fwd is not None:
        fwd_sol = fwd
    elif persist_fwd and fwd_file.exists():
        fwd_sol = mne.read_forward_solution(fwd_file, verbose="error")
    else:
        ev_proto = mne.EvokedArray(np.zeros((len(first_info["ch_names"]), 1)), first_info, tmin=0)
        ev_proto.set_eeg_reference("average", projection=True)
        fwd_sol = mne.make_forward_solution(
            ev_proto.info, trans="fsaverage", src=src_obj, bem=bem_obj,
            eeg=True, meg=False, mindist=5.0, n_jobs=2, verbose="error",
        )
        if persist_fwd:
            mne.write_forward_solution(fwd_file, fwd_sol, overwrite=True, verbose="error")
```
(The old `sibling_fwds` lookup and the `first_info["sfreq"] = 100.0` hack are gone.)

### 7. `load_and_compute` — per-subject evoked: real sfreq, no crop (findings 1, 6)
In the `if not cache_valid:` branch replace
```python
            sfreq = ep_sub.info["sfreq"]
            decim = max(1, int(round(sfreq / 100.0)))
            t_min_crop = ...
            t_max_crop = ...
            evokeds = [ep_sub[c].average().crop(tmin=t_min_crop, tmax=t_max_crop).decimate(decim) for c in cond_keys]
```
with
```python
            decim = pick_decim(ep_sub.info["sfreq"], ep_sub.info["lowpass"])
            evokeds = [ep_sub[c].average().decimate(decim) for c in cond_keys]
```
and after `times_sub = evokeds[0].times` add `sfreq_sub = float(evokeds[0].info["sfreq"])`.
- `np.savez(subj_cache, ...)`: add `sfreq=sfreq_sub`.
- Cache read: require it — change `if "rank" in z:` to `if "rank" in z and "sfreq" in z:` and add
  `sfreq_sub = float(z["sfreq"])` inside.
- After `info_sub = mne.io.read_info(f, verbose="error")`:
  - add `if geometry_key(info_sub) != geom: ep.die(f"subject {s_id} electrode positions differ from the first subject; the shared forward solution would be wrong")`
  - change `info_sub["sfreq"] = 100.0` → `info_sub["sfreq"] = sfreq_sub`.
- Add one sanity line right after `stc = mne.minimum_norm.apply_inverse(...)`:
  `assert np.allclose(stc.times, times_sub), "STC time axis differs from cached evoked times"`.

### 8. `plot()` — windows must lie inside the data (finding 6)
Before `renderer = BrainRenderer(s_dir, src_obj)` add a validation loop over all windows, so the run stops before
rendering anything:
```python
    step_ms = float(times_ms[1] - times_ms[0])
    for w in windows:
        if w["tmin_ms"] < times_ms[0] - step_ms / 2 or w["tmax_ms"] > times_ms[-1] + step_ms / 2:
            ep.die(f"window {w['name']} [{w['tmin_ms']:g}, {w['tmax_ms']:g}] ms is not fully inside the data "
                   f"[{times_ms[0]:.0f}, {times_ms[-1]:.0f}] ms")
```
In the existing render loop keep the `t_mask` / `not np.any(t_mask)` check, and add to `lim` the actual first and
last sample used: `lim = dict(fmin=fmin, fmid=fmid, fmax=fmax, samples_ms=[float(times_ms[t_mask][0]), float(times_ms[t_mask][-1])])`.

### 9. `docs/rules.md` — keep the rules true
- SRC1: replace "one template forward solution calculated from the first subject's montage and cached" with
  "one template forward solution calculated from the first subject's montage and cached per electrode geometry and src/BEM file identity (never reused across geometries); subjects with different electrode positions stop the script".
- SRC4: after "cortex below fmin is transparent" add "(hard step: one fully transparent LUT entry, everything above opaque; no alpha ramp)".
- SRC6: append "Evokeds keep the full epoch and are decimated toward ~100 Hz only while lowpass <= new sfreq / 3; the real sampling rate is cached and used. Windows not fully inside the data stop the script; window names must be unique."

### 10. `test/test_source.py` — tests
a) `make_synthetic_dataset`: add keyword params `sfreq=100.0, tmax_s=1.0, peak_s=0.3, lowpass=None` and use them:
```python
    info = info.copy()
    with info._unlock():
        info["sfreq"] = sfreq
        info["lowpass"] = lowpass if lowpass is not None else sfreq / 2.0
    times = np.arange(int(round(-0.2 * sfreq)), int(round(tmax_s * sfreq)) + 1) / sfreq
    ...
    pulse = np.exp(-((times - peak_s) / 0.05) ** 2)
    ...
    stc = mne.SourceEstimate(stc_data, vertices=[lh_v, rh_v], tmin=times[0], tstep=1.0 / sfreq)
```
and an extra param `name="sub01"` used for the file name (`f"{name}-epo.fif"`). Existing calls keep defaults.

b) New function `test_pure_helpers()` (no data), called first in `main()` after `test_source_layout_selfcheck()`:
```python
def test_pure_helpers():
    assert sp.pick_decim(500, 30) == 5
    assert sp.pick_decim(250, 40) == 2
    assert sp.pick_decim(250, 100) == 1
    assert sp.pick_decim(1000, 40) == 8
    assert sp.pick_decim(512, 30) == 5
    from mne.viz._brain.colormap import calculate_lut
    lut = calculate_lut(sp.threshold_cmap(), 1.0, 1.0, 2.0, 3.0, transparent=False)
    assert lut[0, 3] == 0 and np.all(lut[1:, 3] > 0.99), lut[:3]
    base = {"data": ".", "conditions": {"a": "A"}}
    for bad in (
        dict(base, figure="windows", windows=[{"name": "N4", "tmin_ms": 300, "tmax_ms": 400},
                                             {"name": "N4", "tmin_ms": 400, "tmax_ms": 500}]),
        dict(base, figure="timeline", times_ms=[100, 100]),
    ):
        try:
            sp.check_spec(bad)
            raise AssertionError(f"accepted duplicate names: {bad}")
        except SystemExit as e:
            assert "unique" in str(e) or "repeat" in str(e), e
    print("assertion (helpers) passed: decimation guard, hard-threshold LUT, duplicate names stopped")
```
If `check_spec` on these dicts dies for an unrelated reason (e.g. `data` must exist), read `check_spec` and add only
the keys it requires — the assert on the message will tell you.

c) Inside `main()`'s `with tempfile.TemporaryDirectory()` block, after assertion (f2), add:
```python
        # (g) 250 Hz input, epoch to 1.5 s: real sfreq kept, no crop, peak latency right
        data_dir_250 = Path(tmp_dir) / "data_250"
        data_dir_250.mkdir()
        make_synthetic_dataset(data_dir_250, fwd, src, st_label, info, sfreq=250.0, tmax_s=1.5, peak_s=0.4, lowpass=40.0)
        spec_250 = dict(base_spec, data=str(data_dir_250), figure="windows",
                        windows=[{"name": "P4", "tmin_ms": 350, "tmax_ms": 450}])
        ga_250, t_250, *_ = sp.load_and_compute(spec_250, subjects_dir=SUBJECTS_DIR, src=src, bem=bem, fwd=fwd)
        assert np.allclose(np.diff(t_250), 1.0 / 125.0), np.diff(t_250)[:3]
        assert t_250[-1] > 1.49, t_250[-1]
        peak_ms = t_250[np.argmax(ga_250[0].max(axis=0))] * 1000.0
        assert abs(peak_ms - 400.0) <= 16.0, peak_ms
        print(f"assertion (g) passed: 250 Hz kept as 125 Hz, epoch to {t_250[-1]:.2f} s, peak at {peak_ms:.0f} ms")

        # (h) window beyond the data stops before rendering
        renders = [0]
        orig_render = sp.BrainRenderer.render
        def counting_render(self, *a, **k):
            renders[0] += 1
            return orig_render(self, *a, **k)
        sp.BrainRenderer.render = counting_render
        try:
            for wins in ([{"name": "late", "tmin_ms": 900, "tmax_ms": 1200}],
                         [{"name": "ok", "tmin_ms": 250, "tmax_ms": 350}, {"name": "early", "tmin_ms": -400, "tmax_ms": -100}]):
                try:
                    sp.plot(dict(spec_win, windows=wins), subjects_dir=SUBJECTS_DIR, src=src, bem=bem, fwd=fwd)
                    raise AssertionError(f"accepted out-of-range window {wins}")
                except SystemExit as e:
                    assert "not fully inside" in str(e), e
        finally:
            sp.BrainRenderer.render = orig_render
        assert renders[0] == 0, renders[0]
        print("assertion (h) passed: out-of-range windows stop before any rendering")

        # (i) src/BEM objects passed in: forward computed, never written to the cache
        sp.load_and_compute(dict(spec_win, baseline_ms=[-150, 0]), subjects_dir=SUBJECTS_DIR, src=src, bem=bem)
        written = list((ep.out_root(spec_win) / ".cache" / "source").glob("*/fwd-*.fif"))
        assert written == [], written
        print("assertion (i) passed: forward from custom src/BEM objects not persisted")
```
(The `baseline_ms` change in (i) only forces a fresh parameter folder so the grand-average cache does not return
before the forward step.)

## Check
```bash
cd C:/dev/brain-plot/brain-plot && python test/test_source.py && python -c "import sys; sys.path.insert(0,'.'); import tfr_plot as t; s={'data':'.','conditions':{'a':'A'},'measure':'power','channels':['Cz'],'windows':[{'name':'a','fmin':4,'fmax':8,'tmin_ms':0,'tmax_ms':100},{'name':'a','fmin':8,'fmax':12,'tmin_ms':0,'tmax_ms':100}]}
try:
    t.check_spec(s); print('FAIL: tfr accepted duplicate window names')
except SystemExit as e:
    print('tfr dup check:', e)"
```
Expected: test_source prints every assertion line and `OK`; the TFR line prints a message containing `unique`
(if it dies for another missing key, add that key to the dict and rerun — do not change `check_spec` for it).
If an MNE home-dir permission error appears, prefix with `_MNE_FAKE_HOME_DIR=C:/dev/brain-plot/.mne-test-profile`.

## Don't
- No commits. No files other than those listed. Don't delete `.cache` folders of real data.
- No refactors beyond the steps; don't touch the layout code, `source_layout_issues`, or TFR beyond step 3.
- Reuse `ep.die`, `ep.out_root`, `hashlib`/`json` already imported — don't add dependencies or copy helpers from `erp_plot.py`.
- Don't change the colour-bar code except reading `lim` (it already uses `Normalize(fmin, fmax)` + `"hot"`).
- Run only the Check command (not other test files).

## Fix 1
codex review (`review.md`) FAIL, two real findings. Do exactly these steps in `brain-plot/source_plot.py` and
`brain-plot/test/test_source.py`; nothing else (ignore the `.mne-test-profile` finding — pre-existing, not this card).

1. Geometry check before the grand-average cache (finding 1). In `load_and_compute`:
   - Move the two lines `first_info = mne.io.read_info(active_files[s_ids[0]], verbose="error")` and
     `geom = geometry_key(first_info)` from the `# Forward solution` block up to directly after
     `cache_dir.mkdir(parents=True, exist_ok=True)`, and right after them add:
     ```python
         for s_id in s_ids[1:]:
             if geometry_key(mne.io.read_info(active_files[s_id], verbose="error")) != geom:
                 ep.die(f"subject {s_id} electrode positions differ from the first subject; the shared forward solution would be wrong")
     ```
   - Change the `ga_hash` line to include the geometry:
     `ga_hash = hashlib.md5((param_hash + geom + sorted_subj_str).encode()).hexdigest()[:8]`
   - In the per-subject loop delete the now-redundant two lines
     `if geometry_key(info_sub) != geom:` / `ep.die(...)` (keep `info_sub = mne.io.read_info(...)`).
2. Same time grid for all subjects (finding 2). Next to `first_ch_names = None` add `first_times = None`. Right after
   the `elif ch_names != first_ch_names: ep.die(...)` lines add:
   ```python
           if first_times is None:
               first_times = times_sub
           elif len(times_sub) != len(first_times) or not np.allclose(times_sub, first_times):
               ep.die(f"subject {s_id} time axis differs from the first subject "
                      f"({len(times_sub)} samples from {times_sub[0] * 1000:.0f} ms vs {len(first_times)} from {first_times[0] * 1000:.0f} ms); "
                      "use the same sampling rate, lowpass and epoch window for all subjects")
   ```
3. Test, in `main()` after assertion (i):
   ```python
           # (j) subjects with different time grids stop instead of being averaged
           data_dir_mix = Path(tmp_dir) / "data_mix"
           data_dir_mix.mkdir()
           make_synthetic_dataset(data_dir_mix, fwd, src, st_label, info, name="sub01")
           make_synthetic_dataset(data_dir_mix, fwd, src, st_label, info, sfreq=250.0, lowpass=40.0, name="sub02")
           try:
               sp.load_and_compute(dict(spec_win, data=str(data_dir_mix)), subjects_dir=SUBJECTS_DIR, src=src, bem=bem, fwd=fwd)
               raise AssertionError("averaged subjects with different time grids")
           except SystemExit as e:
               assert "time axis differs" in str(e), e
           print("assertion (j) passed: different time grids stopped")
   ```
   If `select_source_files` does not pick up `sub02-epo.fif` from that folder, read it and rename the files to what it
   expects — don't change `select_source_files`.

Check: the same Check command as above. Don't: no commits, no other files, no other refactors.

## Acceptance
Verdict: accepted after Fix 1 (codex gpt-6.1-sol review: FAIL on 2 real findings — GA cache bypassed the geometry
check; subjects with different time grids were averaged — both fixed in Fix 1; third finding `.mne-test-profile`
is pre-existing, out of scope). Files: `brain-plot/source_plot.py`, `brain-plot/test/test_source.py`,
`brain-plot/tfr_plot.py`, `docs/rules.md`. Check: `python test/test_source.py` all assertions (layout, helpers,
a–j) passed + `OK`; TFR duplicate window names stop. agy: main 307 s, Fix 1 216 s.
Real-data figures not re-rendered yet: `cache_version` 3 forces a full recompute (59 subjects).
