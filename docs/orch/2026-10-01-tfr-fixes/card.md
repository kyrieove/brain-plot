# tfr-fixes — astra findings 4, 5, 7, 10, 11 (TFR) plus the source half of finding 4

Review text: `research/astra-review-brainplot.md` findings 4, 5, 7, 10, 11. Paths relative to repo root
`C:/dev/brain-plot`; run Python from `C:/dev/brain-plot/brain-plot`.

## Goal
- TFR and source check every subject's input contract (`ep.contract`: channels, types, units, sfreq, positions,
  reference, filter, projectors, time grid) against the first subject, also on cache hits, using one shared
  `ep.check_contract` that ERP uses too. Unreadable files and non-finite values stop the run (no silent skipping).
- TFR edge zone = half the longest wavelet MNE actually builds (±5σ), not `(n_cycles/fmin)/2`.
- TFR accepts only `baseline_mode: "logratio"` (the figure, colour bar and caption say dB).
- TFR `grid` lists every condition exactly once with no empty rows; `channels` has no repeats.
- Every TFR window contains at least one frequency bin and one output time sample, checked before any computing;
  `_run.json` is strict JSON (no NaN).

## Files
May change: `brain-plot/erp_plot.py` (step 1 only), `brain-plot/tfr_plot.py`, `brain-plot/source_plot.py`,
`brain-plot/test/test_tfr.py`, `brain-plot/test/test_source.py`, `docs/rules.md` (TF2, TF4 rows),
`brain-plot/references/tfr.md` (lines 30 and 43), `brain-plot/references/spec.md` (the `baseline_mode` row).
Read-only: everything else; never any data or `brain_plot_*` folder.

## Steps

### 1. `erp_plot.py` — shared contract check (reused by ERP, TFR, source)
Add right after `def contract(ev): ...` ends:
```python
def check_contract(label, k, ref, ref_label):
    """Rule S1: stop unless one input's contract is supported and identical to the reference input's."""
    if k["types"] != ["eeg"] or k["units"] != [int(mne.io.constants.FIFF.FIFF_UNIT_V)]:
        die(f"{label}: only EEG potentials in volts are supported (types {k['types']}, units {k['units']})")
    if k["projs_unapplied"]:
        die(f"{label}: unapplied projectors {k['projs_unapplied']}; apply or remove them upstream")
    if not k["locs_finite"] or k["coord_frames"] != [int(mne.io.constants.FIFF.FIFFV_COORD_HEAD)]:
        die(f"{label}: channel positions missing or not in head coordinates; set the montage upstream")
    diff = [x for x in k if k[x] != ref[x]]
    if diff:
        die(f"{label} differs from {ref_label} in {diff}; the loader does not re-reference, resample or interpolate")
```
In `load()` replace the inline block (from `k = contract(ev)` through the `die(f"{f.name} [{c}] differs from ...")`
lines) with:
```python
                k = contract(ev)
                if ref is None:
                    ref, ref_file, times, info = k, f.name, ev.times, ev.info
                check_contract(f"{f.name} [{c}]", k, ref, ref_file)
```
(The bad-channel check above it stays unchanged. Messages keep their old wording, so ERP tests still match.)

### 2. `tfr_plot.py` — `check_spec` (findings 7, 10)
At the end of `check_spec` add:
```python
    if spec.get("baseline_mode", "logratio") != "logratio":
        ep.die(f"baseline_mode {spec['baseline_mode']!r} is not supported: only 'logratio' (dB) is drawn and labelled")
    if len(set(spec["channels"])) != len(spec["channels"]):
        ep.die(f"channels must not repeat (got {spec['channels']!r}); a repeated channel gets double weight in the ROI mean")
    if "grid" in spec:
        flat = [k for r in spec["grid"] for k in r]
        if not spec["grid"] or any(not r for r in spec["grid"]) or sorted(flat) != sorted(spec["conditions"]):
            ep.die(f"grid must list every condition exactly once with no empty rows (got {spec['grid']!r}, "
                   f"conditions {list(spec['conditions'])})")
```
(The existing per-key "not found in conditions" loop stays before it, so that message still comes first.)

### 3. `tfr_plot.py` — edge zone from the real wavelets (finding 5)
In `load_and_compute` replace
```python
    n_cycles, n_cycles_fmin = get_n_cycles(spec, freqs)

    edge_ms = n_cycles_fmin / freqs[0] / 2.0 * 1000.0  # half the longest wavelet
```
with
```python
    n_cycles, _ = get_n_cycles(spec, freqs)
    # half the longest wavelet MNE actually convolves with (±5 sigma, sigma = n_cycles / (2 pi f))
    sfreq = info["sfreq"]
    edge_ms = max((len(w) - 1) / 2.0 for w in mne.time_frequency.morlet(sfreq, freqs, n_cycles=n_cycles)) / sfreq * 1000.0
```
Nothing else in the edge check changes.

### 4. `tfr_plot.py` — windows must contain samples (finding 11)
In `load_and_compute`, right after `decim` is final (after the `if decim is None:` block) add:
```python
    t_out_ms = ep_test.times[::int(decim)] * 1000.0  # compute_tfr keeps every decim-th sample
    for w in spec.get("windows", []):
        n_f = int(((freqs >= w["fmin"] - 1e-6) & (freqs <= w["fmax"] + 1e-6)).sum())
        n_t = int(((t_out_ms >= w["tmin_ms"] - 1e-3) & (t_out_ms <= w["tmax_ms"] + 1e-3)).sum())
        if n_f == 0 or n_t == 0:
            ep.die(f"window {w['name']!r} ({w['fmin']:g}–{w['fmax']:g} Hz, {w['tmin_ms']:g}–{w['tmax_ms']:g} ms) contains "
                   f"{n_f} frequency bins and {n_t} time samples; widen it or change freqs/decim")
```
In `write_run_json` change `json.dumps(data, indent=1, ensure_ascii=False)` to
`json.dumps(data, indent=1, ensure_ascii=False, allow_nan=False)`.

### 5. `tfr_plot.py` — per-subject contract, no skipping, finite data (finding 4)
In `load_and_compute`:
- Before the `for g, fs in groups.items():` loop add `ref_contract, ref_id = None, None`.
- Cache read: change `if "stamp" in z and str(z["stamp"]) == stamp:` to
  `if "stamp" in z and "contract" in z and str(z["stamp"]) == stamp:` and inside it also set
  `k = json.loads(str(z["contract"]))` (keep `cached = ...`).
- Replace
  ```python
                try:
                    ep_sub = mne.read_epochs(f, proj=False, verbose="error")
                except Exception as e:
                    print(f"WARNING: skipping unreadable/incomplete file {f.name}: {e}")
                    continue
  ```
  with
  ```python
                try:
                    ep_sub = mne.read_epochs(f, proj=False, verbose="error")
                except Exception as e:
                    ep.die(f"cannot read {f.name}: {e}; fix the file or list the subject in 'exclude'")
                if ep_sub.info["bads"]:
                    ep.die(f"{f.name}: bad channels {ep_sub.info['bads']} are still marked; resolve them before plotting")
                k = json.loads(json.dumps(ep.contract(ep_sub)))
  ```
  (`k` is computed before `query_epochs`; leave the rest of the branch as is.)
- In that branch's `np.savez(...)` add `contract=json.dumps(k)`.
- Right after the cache-hit / compute `if ... else` (before `for i, c in enumerate(spec["conditions"]):`) add:
  ```python
            if ref_contract is None:
                ref_contract, ref_id = k, f.name
            ep.check_contract(f.name, k, ref_contract, ref_id)
            if not np.isfinite(data).all():
                ep.die(f"{f.name}: non-finite values in the time-frequency data")
  ```

### 6. `source_plot.py` — same contract, no skipping, finite data (finding 4, source half)
In `load_and_compute`:
- Next to `first_times = None` add `ref_contract, ref_id = None, None`.
- Cache read condition: add `and "contract" in z` and inside set `k = json.loads(str(z["contract"]))`.
- Replace the `except Exception as e: print(f"WARNING: skipping unreadable subject {s_id}: {e}")` + `continue` with
  `ep.die(f"cannot read subject {s_id} ({f.name}): {e}; fix the file or list the subject in 'exclude'")`.
- Directly after the successful `ep_sub = mne.read_epochs(...)` add the same two lines as TFR:
  bad-channel stop and `k = json.loads(json.dumps(ep.contract(ep_sub)))` (before re-referencing/baseline: those are
  the module's controlled transformations).
- Add `contract=json.dumps(k),` to that subject's `np.savez(subj_cache, ...)`.
- Right after the existing `first_ch_names` check add:
  ```python
        if ref_contract is None:
            ref_contract, ref_id = k, s_id
        ep.check_contract(f"subject {s_id}", k, ref_contract, f"subject {ref_id}")
        if not np.isfinite(evoked_data).all():
            ep.die(f"subject {s_id}: non-finite values in the evoked data")
  ```

### 7. Docs
- `docs/rules.md` TF2: replace "half the longest wavelet duration, `(n_cycles / fmin) / 2` s" with
  "half the longest wavelet MNE builds: 5 σ with σ = n_cycles / (2π·fmin), e.g. 396 ms at 3 Hz with 1.5 cycles".
- `docs/rules.md` TF4: replace "baseline default logratio" with "baseline mode logratio only (other modes stop)";
  append "Grid lists every condition exactly once; ROI channels do not repeat; every window must contain at least
  one frequency bin and time sample. Inputs pass the S1 contract per subject (also on cache hits); unreadable files stop."
- `references/tfr.md` line 30: "`baseline_mode`: only `\"logratio\"` (dB = 10 × log10(power / baseline); power only); other modes stop."
  Line 43: replace "`(n_cycles/fmin)/2` seconds" with "5 σ, σ = n_cycles / (2π·fmin)".
- `references/spec.md` `baseline_mode` row description: "Only `\"logratio\"` (dB); other values stop. Measure `\"power\"` only."

### 8. Tests
a) `test/test_tfr.py`, in the "4. Stop cases" section after stop case 5 (before the cache-invalidation block):
```python
        # review 2026-10-01: unit, grid, ROI, edge zone from real wavelets, empty windows
        assert_stops({**base_spec, "baseline_mode": "ratio"}, "only 'logratio'")
        assert_stops({**base_spec, "grid": [["burst", "phase"]]}, "exactly once")
        assert_stops({**base_spec, "grid": [["burst", "burst", "phase", "noise"]]}, "exactly once")
        assert_stops({**base_spec, "grid": [["burst", "phase", "noise"], []]}, "exactly once")
        assert_stops({**base_spec, "channels": ["Fz", "Fz", "Cz"]}, "must not repeat")
        assert_stops({**base_spec, "baseline_ms": [-680, -400]}, "reaches into the edge zone")  # 250 < 320 < 396 ms
        assert_stops({**base_spec, "freqs": [4, 8, 13, 30],
                      "windows": [{"name": "gap", "fmin": 9, "fmax": 10, "tmin_ms": 300, "tmax_ms": 600}]}, "0 frequency bins")
        w = mne.time_frequency.morlet(250.0, [3.0], n_cycles=1.5)[0]
        assert abs((len(w) - 1) / 2 / 250.0 * 1000 - 396) < 5, len(w)
        print("TFR stops: logratio only, grid coverage, ROI repeats, real wavelet edge, empty window")
```
b) Same file, at the very end of `run_tests()` inside the `with` block (after the condition-subset check; these
damage the data, so they go last):
```python
        # S1 contract: a subject with the same shape but reordered channels stops; an unreadable file stops
        files = sorted(data_dir.rglob("*-epo.fif"))
        e = mne.read_epochs(files[1], verbose="error")
        e.reorder_channels(list(reversed(e.ch_names)))
        e.save(files[1], overwrite=True, verbose="error")
        assert_stops(base_spec, "differs from")
        files[1].write_bytes(b"not a fif file")
        assert_stops(base_spec, "cannot read")
        print("TFR contract: reordered channels and unreadable file stop")
```
If `files[0]` and `files[1]` are in different groups and the contract check is per group, that is fine — the
reference is the first subject overall.
c) `test/test_source.py`, in `main()` after assertion (l), inside the `with` block:
```python
        # (m) unreadable subject file stops instead of being skipped
        data_dir_bad = Path(tmp_dir) / "data_bad"
        data_dir_bad.mkdir()
        make_synthetic_dataset(data_dir_bad, fwd, src, st_label, info, name="sub01")
        (data_dir_bad / "sub02-epo.fif").write_bytes(b"not a fif file")
        try:
            sp.load_and_compute(dict(spec_win, data=str(data_dir_bad)), subjects_dir=SUBJECTS_DIR, src=src, bem=bem, fwd=fwd)
            raise AssertionError("unreadable subject was skipped")
        except SystemExit as e:
            assert "cannot read" in str(e), e
        print("assertion (m) passed: unreadable subject stops")
```
If `select_source_files` itself already stops on the broken file with another message, accept that message
instead (assert on what it prints) — but it must stop, not skip.

## Check
```bash
cd C:/dev/brain-plot/brain-plot && python test/test_tfr.py && python test/test_source.py && python test/test_erp_plot.py
```
All three end without a traceback and print `OK`.

## Don't
- No commits; no files outside the list; no refactors beyond the steps.
- Reuse `ep.contract` / `ep.check_contract` — no copied contract logic in TFR or source.
- Don't change figure layout, colour scales or file names. Don't touch `research/`.
- If an existing test now fails because it relied on the old, too-small edge zone, adjust only that test's numbers
  and say so in the reply.
- Run only the Check command.

## Fix 1
codex review FAIL, one finding: the source grand-average cache hit returns before any contract / finite check, so
grand averages written by older code (which never checked contracts) are still served. Grand averages written by
the new code are safe (every subject passed `ep.check_contract` and the finite check before the sum, and the key
holds every input file's stamp), so mark them and refuse unmarked ones. Only `brain-plot/source_plot.py` and
`brain-plot/test/test_source.py`.

1. `source_plot.py` `load_and_compute`, grand-average cache read: change
   `if "subject_p99" in z and "outlier_subjects" in z and "rank" in z:` to
   `if "subject_p99" in z and "outlier_subjects" in z and "rank" in z and "contract" in z:`
   (add a comment: `# "contract": written only after every subject passed the S1 contract and finite checks`).
2. Same function, the final grand-average `np.savez(ga_cache, ...)`: add `contract=json.dumps(ref_contract),`.
3. `test_source.py`, in `main()` after assertion (m):
   ```python
        # (n) a grand-average cache without the contract mark (older code) is not served
        ga_ok = sp.load_and_compute(spec_win, subjects_dir=SUBJECTS_DIR, src=src, bem=bem, fwd=fwd)[0]
        ga_files = list((ep.out_root(spec_win) / ".cache" / "source").glob("*/grand_avg_*.npz"))
        assert ga_files, "no grand-average cache written"
        for gf in ga_files:
            with np.load(gf, allow_pickle=True) as z:
                old = {k: z[k] for k in z.files if k != "contract"}
            old["data"] = np.zeros_like(old["data"])
            np.savez(gf, **old)
        ga_again = sp.load_and_compute(spec_win, subjects_dir=SUBJECTS_DIR, src=src, bem=bem, fwd=fwd)[0]
        assert np.allclose(ga_again, ga_ok) and np.abs(ga_again).max() > 0, "unmarked grand-average cache was served"
        print("assertion (n) passed: unmarked grand-average cache recomputed")
   ```
   (`np.savez(gf, ...)` keeps the same file name because `gf` ends in `.npz`.)

Check: `cd C:/dev/brain-plot/brain-plot && python test/test_source.py` prints all assertions incl. (n) and `OK`.
Don't: no commits, no other files.

## Acceptance
Verdict: accepted after Fix 1 (codex gpt-6.1-sol FAIL, one finding: source grand-average cache hit bypassed the
contract checks — fixed by a `contract` mark that only new, fully checked grand averages carry). Files:
`brain-plot/erp_plot.py`, `tfr_plot.py`, `source_plot.py`, `test/test_tfr.py`, `test/test_source.py`,
`references/tfr.md`, `references/spec.md`, `docs/rules.md`. Check re-run by Claude: test_tfr, test_source (a–n),
test_erp_plot all `OK`. agy 674 s + Fix 1 110 s. Note: source test (j) now accepts the contract message
("differs from") as well, because the contract check (sfreq) fires before the time-axis check.
