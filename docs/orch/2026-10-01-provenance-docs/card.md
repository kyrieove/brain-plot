# provenance-docs — astra findings 13, 17, 18, 19 and the small parts of 20

Review text: `research/astra-review-brainplot.md` findings 13, 17, 18, 19, 20. Paths relative to repo root
`C:/dev/brain-plot`; run Python from `C:/dev/brain-plot/brain-plot`.

## Goal
- Source `_run.json` states the method facts needed to read a dSPM map (13) and carries code hash, library
  versions and input stamps (17). Microstate `_run.json` records trial counts (17). An inset ERP figure's caption no
  longer mentions a gray band that is not drawn (17).
- Environment: mne ≥ 1.7 everywhere it is declared; check_env reports pyvista (source only); fsaverage location is
  no longer the author's hard-coded path; relative `subjects_dir` / `src` / `bem` in a spec resolve from the spec's
  folder (18).
- Rules: module applicability and exceptions are explicit (19).
- Caches: TFR and source cache folders are pruned by real last use; source keeps at most `CACHE_KEEP` folders (20).
- Not in scope (finding 20's larger refactors — shared base classes, run-record framework): skipped on purpose.

## Files
May change: `brain-plot/source_plot.py`, `brain-plot/microstate_plot.py`, `brain-plot/erp_plot.py`,
`brain-plot/tfr_plot.py`, `brain-plot/check_env.py`, `requirements.txt`, `brain-plot/SKILL.md`, `docs/rules.md`,
`brain-plot/references/source.md`, `brain-plot/test/test_source.py`.
Read-only: everything else; never any data or `brain_plot_*` folder.

## Steps

### 1. `erp_plot.py` — shared helpers and two small fixes
a) `read_spec`: change `for k in ("data", "templates"):` to `for k in ("data", "templates", "subjects_dir", "src", "bem"):`
   and its docstring to say "relative `data`, `templates`, `subjects_dir`, `src` and `bem` paths are taken relative
   to the spec file's folder".
b) Add right after `def prune_cache(folder): ...` ends:
   ```python
   def prune_cache_dirs(root, current):
       """Rule O1 for per-parameter cache folders (TFR, source): mark `current` as just used, keep the CACHE_KEEP
       most recently used folders, delete the rest (rebuilt when needed)."""
       os.utime(current)
       for d in sorted([p for p in root.iterdir() if p.is_dir()], key=lambda p: p.stat().st_mtime_ns, reverse=True)[CACHE_KEEP:]:
           if d != current:
               shutil.rmtree(d, ignore_errors=True)
   ```
   Add `import os` / `import shutil` at the top only if not already imported.
c) `caption()`: in the line `band = {"combo": "; gray band = topography window", "erp": "; gray band", "topo": ""}[kind]`
   change the combo entry to `"; topography window" if inset_mode(spec) else "; gray band = topography window"`
   (inset layouts draw no gray band, user 2026-09-30).

### 2. `tfr_plot.py` — use the shared pruning
Replace the block
```python
    tfr_cache_root = ep.out_root(spec) / ".cache" / "tfr"
    if tfr_cache_root.exists():
        for old_dir in sorted(...)[ep.CACHE_KEEP:]:
            if old_dir != cache_dir:
                shutil.rmtree(old_dir, ignore_errors=True)
```
with `ep.prune_cache_dirs(cache_dir.parent, cache_dir)`. Remove `import shutil` from tfr_plot.py if nothing else uses it.

### 3. `source_plot.py`
a) fsaverage location (18). Replace `DEFAULT_SUBJECTS_DIR = r"C:\Users\ASUS\mne_data\MNE-fsaverage-data"` with:
   ```python
   def default_subjects_dir():
       """fsaverage parent folder: MNE's SUBJECTS_DIR config / environment, else where mne.datasets.fetch_fsaverage()
       puts it (MNE_DATA or ~/mne_data); never downloads."""
       candidates = [mne.get_config("SUBJECTS_DIR"),
                     Path(mne.get_config("MNE_DATA") or Path.home() / "mne_data") / "MNE-fsaverage-data"]
       for d in candidates:
           if d and (Path(d) / "fsaverage").is_dir():
               return Path(d)
       ep.die("fsaverage not found: set 'subjects_dir' in the spec (the folder that contains fsaverage), or run "
              "mne.datasets.fetch_fsaverage() once")
   ```
   and in `load_and_compute` change `Path(subjects_dir or spec.get("subjects_dir") or DEFAULT_SUBJECTS_DIR)` to
   `Path(subjects_dir or spec.get("subjects_dir") or default_subjects_dir())`.
b) After `cache_dir.mkdir(parents=True, exist_ok=True)` add `ep.prune_cache_dirs(cache_dir.parent, cache_dir)` (20).
c) `run_record` in `plot()` (13, 17): add these keys (keep the existing ones):
   ```python
        "inputs": {s: ep.file_stamp(f) for s, f in select_source_files(spec)[0].items()},
        "code_md5": {f.name: hashlib.md5(f.read_bytes()).hexdigest() for f in (Path(__file__), Path(ep.__file__))},
        "versions": dict(mne=mne.__version__, matplotlib=matplotlib.__version__, numpy=np.__version__),
        "method_facts": {
            "estimate": f"{method} on the fsaverage template (no individual anatomy), loose={params['loose']}, "
                        f"depth={params['depth']}, lambda2={params['lambda2']:.4g} (SNR 3)",
            "orientation": "pick_ori=None: magnitude of the three orientations per vertex (non-negative)",
            "aggregation": "inverse per subject and condition with that subject's real trial count (nave), "
                           "then equal-weight mean over subjects; not a group statistic",
            "trial_counts": "dSPM noise normalisation scales with nave: conditions with different trial counts are "
                            "not directly comparable in brightness (see trials_per_subject_condition)",
            "colour_scale": "each window/time column has its own range from percentiles across its conditions "
                            "(display threshold, not significance); compare colours only within a column",
            "noise_cov": f"from {params['noise_cov_ms'][0]:g} to {params['noise_cov_ms'][1]:g} ms of each epoch "
                         "(relative to the time-locking event; check that this interval holds no stimulus)",
        },
   ```
   If `params` holds these values under other names, read them from `params` / `spec` exactly as `load_and_compute`
   builds `param_dict` (keys `lambda2`, `loose`, `depth`, `noise_cov_ms`).

### 4. `microstate_plot.py` — trial counts in the run record (17)
In the `_run.json` dict add `nave=meta["nave"],` next to `ids=meta["ids"],`.

### 5. Environment (18)
- `requirements.txt`: `mne>=1.6` → `mne>=1.7  # Epochs.compute_tfr (time-frequency) needs 1.7`; add a last line
  `# source maps only: pyvista (3D rendering) and the fsaverage template (mne.datasets.fetch_fsaverage())`.
- `check_env.py`: `"mne": (1, 6)` → `"mne": (1, 7)`; add to `OPTIONAL`:
  `"pyvista": "only for source maps (3D brain rendering); also needs the fsaverage template"`.
- `SKILL.md` "Before the first run": `mne ≥ 1.6` → `mne ≥ 1.7`; append to that bullet: "Source maps also need
  pyvista and the fsaverage template (spec `subjects_dir`, or `mne.datasets.fetch_fsaverage()` once)."

### 6. Rules and docs (19)
- `SKILL.md` Draw step: replace "Outputs per figure: `.png .svg` (fixed physical size, editable SVG text),
  `_caption.md` (facts for the caption), `_run.json`" with "Outputs per figure: `.png .svg` (editable SVG text),
  `_caption.md` (facts for the caption; not for source maps, by user decision), `_run.json`".
- `SKILL.md` line "The style is fixed in code. Never restyle or edit a figure by hand or with ad-hoc matplotlib —
  change the spec." → "The style is fixed in code. You (the agent) never restyle or edit a figure by hand or with
  ad-hoc matplotlib — change the spec. The SVG is editable so that the user can make final manual adjustments."
- `docs/rules.md`: right under the `# ` title (before the first table) insert:
  ```markdown
  **Scope and exceptions.** ERP rules (S, L, K, T, O) apply to `erp_plot.py`; each other module's section says which
  shared rules it inherits. Where a module rule and a shared rule differ, the module rule wins, and the differences
  are deliberate: S1's "never re-references, resamples or interpolates" is about the loaders' input contract — source
  applies its own declared transformations after that check (average-reference projection, baseline, decimation,
  SRC6); T6's fixed canvas is the ERP default — ERP inset grids (L12), TFR (TF7), microstate (MS10) and source (SRC5)
  derive height (source also width) from content as their rules state; TF5's symmetric scale applies to power,
  ITC uses 0…v (TF4); source writes no `_caption.md` (SRC6).
  ```
- `docs/rules.md` TF5 row: replace "with a shared symmetric color scale" with "with a shared color scale (symmetric
  ±v for power, 0…v for ITC)".
- `references/source.md`: add a short section "## Reading the map (state in Methods)" listing the five
  `method_facts` points of step 3c in one bullet each, plus: "Matching trial counts across conditions is an
  analysis decision taken upstream; the plot never changes nave."

### 7. Test — `test/test_source.py`
a) Replace `SUBJECTS_DIR = sp.DEFAULT_SUBJECTS_DIR` with `SUBJECTS_DIR = str(sp.default_subjects_dir())`.
b) In `main()` after the last assertion, inside the `with` block:
```python
        # (o) run record carries method facts and provenance
        out_o = sp.plot(spec_win, subjects_dir=SUBJECTS_DIR, src=src, bem=bem, fwd=fwd)[0]
        run_o = json.loads(Path(f"{out_o}_run.json").read_text(encoding="utf8"))
        assert {"estimate", "orientation", "aggregation", "trial_counts", "colour_scale", "noise_cov"} <= set(run_o["method_facts"]), run_o.keys()
        assert run_o["inputs"] and run_o["code_md5"] and run_o["versions"]["mne"], run_o.keys()
        assert len(list((ep.out_root(spec_win) / ".cache" / "source").iterdir())) <= ep.CACHE_KEEP
        print("assertion (o) passed: method facts, provenance, source cache pruned")
```

## Check
```bash
cd C:/dev/brain-plot/brain-plot && python check_env.py && python test/test_source.py && python test/test_tfr.py && python test/test_erp_plot.py && python test/test_microstate.py
```
check_env prints OK (pyvista listed); every test prints `OK` without a traceback.

## Don't
- No commits; no files outside the list; no refactors beyond the steps; no automatic downloads.
- Reuse `ep.file_stamp`, `ep.prune_cache_dirs`, `ep.inset_mode` — no local copies.
- Don't add a source `_caption.md`; don't change figure layouts or file names.
- Run only the Check command.

## Fix 1
Claude review (Codex quota out): one finding. `method_facts["estimate"]` hard-codes "(SNR 3)", which is wrong when a
spec sets another `lambda2`. Only `brain-plot/source_plot.py` and `brain-plot/references/source.md`:
1. `source_plot.py`, in `method_facts["estimate"]`, replace `lambda2={params['lambda2']:.4g} (SNR 3)` with
   `lambda2={params['lambda2']:.4g} (SNR {params['lambda2'] ** -0.5:.3g})`.
2. `references/source.md`, the "Estimate" bullet: replace "lambda2 (SNR 3)" with "lambda2 (SNR = 1/√lambda2; 3 by default)".
Check: `cd C:/dev/brain-plot/brain-plot && python test/test_source.py` prints assertion (o) and `OK`.
Don't: no commits, no other files.

## Acceptance
Verdict: accepted after Fix 1. Codex quota out, so Claude reviewed the diff: one finding (SNR hard-coded as 3) fixed
in Fix 1. Check re-run by Claude: check_env `OK` (pyvista listed), test_source (a–o), test_tfr, test_erp_plot,
test_microstate all `OK`. agy 458 s + Fix 1. Finding 20's larger refactors (shared base classes, run-record
framework) deliberately skipped: the shared pieces that mattered (contract check, file stamp, cache-dir pruning,
interpolated peak) are already in `erp_plot.py`.
