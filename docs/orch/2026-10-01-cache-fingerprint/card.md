# cache-fingerprint — input-file fingerprints in TFR/source caches; figure names that tell analyses apart

Review text: `research/astra-review-brainplot.md` findings 2 and 16. Paths are relative to repo root
`C:/dev/brain-plot`; run Python from `C:/dev/brain-plot/brain-plot`.

## Goal
- Replacing a subject's `-epo.fif` (same name, new content) makes TFR and source recompute that subject and the
  source grand average; unchanged files still hit the cache.
- TFR and source file names carry the condition subset and query (`_cond-…`, `_query-…`, via `ep.subset_part`);
  source window figures carry each window's ms range, timelines their time points; explore grids with custom
  channels name the channels. Figures of different analyses no longer archive each other.

## Files
May change: `brain-plot/erp_plot.py` (only the parts in steps 1, 6), `brain-plot/tfr_plot.py`,
`brain-plot/source_plot.py`, `brain-plot/test/test_tfr.py`, `brain-plot/test/test_source.py`, `docs/rules.md` (O3 row).
Read-only: everything else; never any data or `brain_plot_*` output folder.

## Steps

### 1. `erp_plot.py` — shared stamp helper
Add just above `def load(spec):`
```python
def file_stamp(f):
    """Cache identity of an input file: path, size, modification time (a changed file invalidates its cache)."""
    st = Path(f).stat()
    return [str(f), st.st_size, st.st_mtime_ns]
```
In `load()` replace `stamp = [[str(f), f.stat().st_size, f.stat().st_mtime_ns] for f in files]` with
`stamp = [file_stamp(f) for f in files]` (identical values, so existing ERP caches stay valid).

### 2. `tfr_plot.py` — per-subject cache checks the stamp
In `load_and_compute`, the per-subject block currently is:
```python
            cfile = cache_dir / f"{s_id}.npz"
            if cfile.exists():
                cfile.touch()
                with np.load(cfile) as z:
                    times_s, data, nave = z["times"], z[measure], z["nave"]  # read each array once
            else:
```
Replace with:
```python
            cfile = cache_dir / f"{s_id}.npz"
            stamp = json.dumps(ep.file_stamp(f))
            cached = None
            if cfile.exists():
                with np.load(cfile) as z:
                    if "stamp" in z and str(z["stamp"]) == stamp:
                        cached = z["times"], z[measure], z["nave"]  # read each array once
            if cached is not None:
                cfile.touch()
                times_s, data, nave = cached
            else:
```
(the body of the old `else:` stays as is). Change the save line to
`np.savez(cfile, times=times_s, nave=nave, stamp=stamp, **arrays)`. `json` is already imported — check.

### 3. `tfr_plot.py` — file name (finding 16)
In `plot()` replace `{ep.name_part(spec)}` in `out_stem` with `{subset}`, and before the loop over groups that builds
figures (once, near the top of `plot()` after `load_and_compute`) add:
```python
    first_unit = next(iter(ep.select_files(spec)[0].values()))[0]
    subset = ep.subset_part(spec, {"conditions_all": ep.available_conditions(spec, first_unit)}, ("conditions",))
```
(`subset_part` with `parts=("conditions",)` reads only `meta["conditions_all"]`; it already appends the query part
and `name_part(spec)`.)

### 4. `source_plot.py` — per-subject cache and grand average check the stamps (finding 2)
In `load_and_compute`:
- Replace `sorted_subj_str = "_".join(s_ids)` with
  `stamps = {s: json.dumps(ep.file_stamp(active_files[s])) for s in s_ids}` and the `ga_hash` line with
  `ga_hash = hashlib.md5((param_hash + geom + json.dumps(stamps, sort_keys=True)).encode()).hexdigest()[:8]`
  (stamps contain the subject paths, so the subject list is still part of the key).
- Per-subject cache read: change `if "rank" in z and "sfreq" in z:` to
  `if "rank" in z and "sfreq" in z and "stamp" in z and str(z["stamp"]) == stamps[s_id]:`.
- Per-subject `np.savez(subj_cache, ...)`: add `stamp=stamps[s_id],`.
- Do NOT change `param_dict` (no MNE version in the key: the dev build changes its version string often).

### 5. `source_plot.py` — file names (finding 16)
In `plot()` replace the stem block
```python
    if fig_type == "windows":
        win_part = "_" + "-".join(ep.safe(w["name"]) for w in windows)
        stem = f"source-windows_{method}{win_part}{ep.name_part(spec)}"
    else:
        stem = f"source-timeline_{method}{ep.name_part(spec)}"
```
with
```python
    active_files, _ = select_source_files(spec)
    subset = ep.subset_part(spec, {"conditions_all": ep.available_conditions(spec, next(iter(active_files.values())))}, ("conditions",))
    if fig_type == "windows":
        win_part = "_" + "-".join(f"{ep.safe(w['name'])}-{w['tmin_ms']:g}-{w['tmax_ms']:g}ms" for w in windows)
        stem = f"source-windows_{method}{win_part}{subset}"
    else:
        t_pts = spec.get("times_ms", [100, 200, 300, 400, 500, 600, 700, 800])
        stem = f"source-timeline_{method}_{t_pts[0]:g}-{t_pts[-1]:g}ms-n{len(t_pts)}-hw{half_w:g}{subset}"
```
(`half_w` is already defined in the timeline branch above; if it is not in scope here, use
`float(spec.get("half_width_ms", 50.0))`.)

### 6. `erp_plot.py` — explore grid names its channels (finding 16)
In `explore()` change the grid stem
`f"ERP-grid-{shape}_conditions_{safe(g)}{name_part(spec)}"` to
`f"ERP-grid-{shape}{chan}_conditions_{safe(g)}{name_part(spec)}"` and, right after `root, shape = ...`, add
`chan = "" if rows == EXPLORE_CHANNELS else "_" + "-".join(safe(c) for r in rows for c in r)`
(default grid keeps its old name; existing tests depend on it).

### 7. `docs/rules.md` — O3 row
Append to the O3 cell (before the final `| U | Code |`): " TFR and source names carry the same subset parts;
source window figures add each window's range (`P200-152-272ms`), timelines their first–last point, count and
half-width; explore grids with non-default channels name them. TFR and source caches are keyed on each input file's
path, size and modification time (a replaced file is recomputed)."

### 8. Tests
a) `test/test_source.py`, in `main()` after assertion (j), inside the `with` block:
```python
        # (k) a replaced input file is recomputed, not served from the cache
        f01 = Path(data_dir) / "sub01-epo.fif"
        ga_before = sp.load_and_compute(spec_win, subjects_dir=SUBJECTS_DIR, src=src, bem=bem, fwd=fwd)[0]
        e01 = mne.read_epochs(f01, proj=False, verbose="error")
        d01 = e01.get_data()
        d01[:, :, e01.times > 0] *= 0.5
        mne.EpochsArray(d01, e01.info, events=e01.events, event_id=e01.event_id, tmin=e01.times[0],
                        baseline=None).save(f01, overwrite=True, verbose="error")
        ga_after = sp.load_and_compute(spec_win, subjects_dir=SUBJECTS_DIR, src=src, bem=bem, fwd=fwd)[0]
        assert not np.allclose(ga_before, ga_after), "replaced input served from cache"
        print("assertion (k) passed: replaced input file recomputed")

        # (l) same window name, different range / condition subset -> different names
        o1 = sp.plot(dict(spec_win, windows=[{"name": "N", "tmin_ms": 250, "tmax_ms": 350}]), subjects_dir=SUBJECTS_DIR, src=src, bem=bem, fwd=fwd)[0]
        o2 = sp.plot(dict(spec_win, windows=[{"name": "N", "tmin_ms": 300, "tmax_ms": 400}]), subjects_dir=SUBJECTS_DIR, src=src, bem=bem, fwd=fwd)[0]
        assert o1.name != o2.name and Path(f"{o1}.png").exists() and Path(f"{o2}.png").exists(), (o1, o2)
        assert "N-250-350ms" in o1.name and "_cond-condA" in o1.name, o1.name
        print(f"assertion (l) passed: distinct names {o1.name} / {o2.name}")
```
b) `test/test_tfr.py`, at the end of `run_tests()` inside the `with` block (after all existing checks):
```python
        # cache invalidated when an input file changes
        f = sorted(data_dir.rglob("*-epo.fif"))[0]
        g_f = f.parent.name
        ga1 = tfr_plot.load_and_compute(base_spec)[0]
        e = mne.read_epochs(f, verbose="error")
        d = e.get_data()
        d[:, :, e.times > 0] *= 3.0
        mne.EpochsArray(d, e.info, events=e.events, event_id=e.event_id, tmin=e.times[0], verbose=False).save(f, overwrite=True)
        ga2 = tfr_plot.load_and_compute(base_spec)[0]
        assert not np.allclose(ga1[g_f, "burst"], ga2[g_f, "burst"]), "replaced input served from TFR cache"
        print("TFR cache invalidated by a replaced input file")

        # a condition subset is part of the file name
        outs = tfr_plot.plot(dict(base_spec, conditions={"burst": "10 Hz Burst"}))
        assert all("_cond-burst" in Path(o).name for o in outs), outs
        print("TFR condition subset named")
```
If `base_spec` was mutated earlier in the test, build these from a fresh copy of the original dict. If grand-average
keys are not `(group, condition)` with the folder name as group, print `list(ga1)` once and use the right key.

## Check
```bash
cd C:/dev/brain-plot/brain-plot && python test/test_source.py && python test/test_tfr.py && python test/test_erp_plot.py
```
All three must end without a traceback (test_source prints `OK`, assertions (k) and (l) included). If an MNE home
permission error appears, prefix `_MNE_FAKE_HOME_DIR=C:/dev/brain-plot/.mne-test-profile`.

## Don't
- No commits; no files outside the list; no refactors beyond the steps.
- Reuse `ep.file_stamp`, `ep.subset_part`, `ep.available_conditions` — don't write local copies.
- Don't touch `source_plot.file_id` (src/BEM identity from the previous card) or the source `param_dict`.
- Don't change ERP figure names other than the explore grid with non-default channels.
- Run only the Check command.

## Acceptance
Verdict: accepted, no fix needed (codex gpt-6.1-sol: `VERDICT: PASS`). Files: `brain-plot/erp_plot.py`,
`brain-plot/tfr_plot.py`, `brain-plot/source_plot.py`, `brain-plot/test/test_source.py`, `brain-plot/test/test_tfr.py`,
`docs/rules.md`. Check (re-run by Claude): test_source (a–l) `OK`, test_tfr `OK` incl. cache invalidation and
`_cond-burst` name, test_erp_plot `OK`. agy 352 s. Source caches built before this card lack stamps: the next real
source render recomputes all subjects once.
