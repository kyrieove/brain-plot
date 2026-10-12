# eeglab-set-input — accept epoched EEGLAB .set files wherever the modules read -epo.fif

## Goal
A data folder (flat, or group sub-folders) of per-subject epoched EEGLAB files `<subject>.set` (+ optional `.fdt`) works in the
ERP, TFR and source modules like a folder of `<subject>-epo.fif`. Two EEGLAB facts shape the design (both measured on real
EEGLAB-authored files, see Parameters):
1. An EEGLAB epoch can hold several events (stimulus + response). MNE then names the epoch `square/rt` and its `/` tag
   matching makes conditions overlap. brain-plot must label each epoch by its **time-locking event** (the event at latency 0).
2. EEGLAB files store neither a baseline nor filter settings, so captions must not invent them: for `.set` input the contract
   records `baseline = None` and `filter = None`, and every caption line that prints them says
   `baseline and filter not recorded (EEGLAB .set)`.
Output for `-epo.fif` / `-ave.fif` input stays byte-identical. Done when the Check ends with `OK` for all four test files.

## Risk
medium — shared loader code used by every module (reviewer sol); no analysis number changes for existing `.fif` input.

## Parameters
- Epochs file = name ends with `-epo.fif` OR suffix is `.set` (case-insensitive). `-ave.fif` stays evoked. `.set` is never an evoked and never part of the `<condition>/<group>/` split layout. Continuous (non-epoched) `.set` is not supported and stops with a message.
- Real fixtures (EEGLAB 2025.0.0 on MATLAB R2023a, from EEGLAB's own `sample_data/eeglab_data.set`; read-only): `brain-plot/test/data/eeglab/G1/sub01.set`, `G1/sub02.set` + `G1/sub02.fdt`, `G2/sub03.set`, `G2/sub04.set`, and `brain-plot/test/data/eeglab/counts.csv` (columns `subject,type_at_latency_0,n_epochs`, written by MATLAB, independent of Python). Each file: 20 epochs, 32 channels, 128 Hz, -0.203125 to 0.789062 s, event types `square` and `rt`; epochs were cut around both types, so some epochs contain both events. Counts per subject (`rt`/`square`): sub01 12/8, sub02 9/11, sub03 11/9, sub04 10/10.
- What MNE does on those files (probe 2026-10-12, `mne.read_epochs_eeglab`): `event_id` = `{'square/square': 1, 'square/rt': 2, 'rt': 3, 'square': 4}` (numbering differs between subjects; multi-event epochs get names joined with `/`); `epochs.baseline` is `None`; `epochs.metadata` is `None`; `highpass/lowpass` come back as 0.0 / 64.0 (invented defaults); positions are in the head frame and finite; channel types all `eeg`. In the `.set`, `EEG.epoch(i).eventtype` / `eventlatency` list every event of epoch i with its latency in ms; the time-locking event has latency 0.
- Locking-event rule (measured: the chosen event has |latency| = 0.0 ms in all 80 epochs): label of epoch i = the `eventtype` whose `eventlatency` is closest to 0; stop if that smallest |latency| exceeds 1.0 ms. Labels are `str(eventtype)`.
- Reading the `.set` struct: `pymatreader.read_mat(str(f))` (already installed; MNE uses it). The fields sit at the top level of the returned dict (EEGLAB saves with `-struct`), so use `m = read_mat(str(f)); eeg = m["EEG"] if "EEG" in m else m`. `eeg["epoch"]` is a dict of lists, one entry per epoch; an entry is a scalar/str for one event and a list for several. Missing `"epoch"` key (or empty) = continuous data → stop.
- Subject id of `sub01.set` stays `subject_id()` = `sub01`.
- Caption text for `.set` input: exactly `baseline and filter not recorded (EEGLAB .set)`. For `.fif` input the text is exactly what the code prints today: erp_plot `"Baseline {b} s; filter {lo:g}–{hi:g} Hz"` (capital B; `"Time-locked to: X; baseline {b} s; filter …"` when `time_locked_to` is set), microstate `"baseline {b} s, filter {lo:g}–{hi:g} Hz"`.
- Error text of `discover()` keeps the substring `no *-epo.fif or *-ave.fif` (a test asserts it); new full text: `no *-epo.fif or *-ave.fif (or EEGLAB *.set epochs) in {root}, its group sub-folders, or <condition>/<group>/ folders`.
- Synthetic data for the round-trip test: 2 groups x 2 subjects of the 16 channels `CH`, 10 epochs each (5 `A`, 5 `B`, one event per epoch), -0.2 to 1.0 s at 500 Hz, baseline (None, 0); the `.set` copies come from `epochs.export(path, fmt="eeglab")` (eeglabio is installed). Tolerances: evoked data `atol=1e-10` V (EEGLAB stores float32), loaded arrays in µV `atol=1e-4`.

## Files
may change: `brain-plot/erp_plot.py`, `brain-plot/tfr_plot.py`, `brain-plot/source_plot.py`, `brain-plot/microstate_plot.py`, `brain-plot/test/test_erp_plot.py`, `brain-plot/SKILL.md`
read-only: `brain-plot/test/data/`, `brain-plot/cluster_plot.py`, `brain-plot/besa_to_run.py`, `brain-plot/test/test_cluster.py`, `brain-plot/test/test_tfr.py`, `brain-plot/test/test_source.py`, `brain-plot/test/test_microstate.py`, `C:/Users/ASUS/Dropbox/metaphor_production/`, `docs/cluster-before-after/`, `docs/cluster-layout-compare.html`, `docs/cluster-layout-compare-real.html`, `docs/tfce-mne-vs-standard.html`, `AGENTS.md`, `AGENTS.md.bak-doctor-2026-10-09`

## Steps (N = 8)
1. `brain-plot/erp_plot.py`, just above `subject_id` (line 357, section `# ---------- data ----------`): add the helpers (add `from pymatreader import read_mat` to the imports only inside `eeglab_locking_types`, as a local import, so `.fif`-only users never import it).
   ```python
   def is_epochs(f):
       """An epochs file: MNE `*-epo.fif` or an epoched EEGLAB `.set`."""
       return f.name.endswith("-epo.fif") or f.suffix.lower() == ".set"


   def eeglab_locking_types(f):
       """Per epoch of an EEGLAB `.set`, the event type at latency 0 (EEGLAB's time-locking event). MNE names an epoch
       holding several events `a/b` and its '/' tag matching then makes conditions overlap, so MNE's names are not used."""
       from pymatreader import read_mat
       m = read_mat(str(f))
       eeg = m["EEG"] if "EEG" in m else m
       epoch = eeg.get("epoch")
       if not epoch:
           die(f"{f.name}: not an epoched EEGLAB file (no EEG.epoch); epoch the data in EEGLAB first")
       out = []
       for types, lats in zip(epoch["eventtype"], epoch["eventlatency"]):
           types = [types] if isinstance(types, (str, int, float)) else list(types)
           lats = np.atleast_1d(np.asarray(lats, dtype=float))
           i = int(np.argmin(np.abs(lats)))
           if abs(lats[i]) > 1.0:
               die(f"{f.name}: an epoch has no event at latency 0 (nearest {lats[i]:g} ms); the time-locking event is missing")
           out.append(str(types[i]))
       return out


   def read_epochs_any(f, **kw):
       """Epochs from `*-epo.fif` (kw go to mne.read_epochs) or an EEGLAB `.set` (read_epochs_eeglab takes no preload/proj);
       the `.set` conditions are the time-locking event types."""
       if f.suffix.lower() != ".set":
           return mne.read_epochs(f, **kw)
       epochs = mne.read_epochs_eeglab(f, verbose="error")
       labels = eeglab_locking_types(f)
       if len(labels) != len(epochs):
           die(f"{f.name}: {len(labels)} epochs in EEG.epoch but {len(epochs)} read by MNE")
       ids = {name: i + 1 for i, name in enumerate(sorted(set(labels)))}
       epochs.events[:, 2] = [ids[x] for x in labels]
       epochs.event_id = ids
       return epochs
   ```
   If `epochs.event_id = ids` raises an AttributeError in this MNE version, set it with `epochs.event_id.clear(); epochs.event_id.update(ids)` instead (probe 2026-10-12: plain assignment works). All call sites below pass the same keywords they pass today (`proj=False`, `preload=False`, `verbose="error"`).

2. `brain-plot/erp_plot.py`, replace every epochs-file test and read with the helpers. Exact sites (line numbers of the current file):
   - `find_groups` (364): `pat` becomes `sorted(list(d.glob("*-epo.fif")) + list(d.glob("*-ave.fif")) + list(d.glob("*.set")))`.
   - `groups_from_metadata` (406, 409): `if not is_epochs(f):`; `read_epochs_any(f, preload=False, verbose="error").metadata`. The message `group_by needs epochs files with metadata` stays; a `.set` has `metadata None` and is stopped by the existing `no metadata column` line.
   - `available_conditions` (457-458): `if is_epochs(unit):` and `list(read_epochs_any(unit, preload=False, proj=False, verbose="error").event_id)`.
   - `read_conditions` (510-511): `elif is_epochs(f):` and `query_epochs(read_epochs_any(f, proj=False, verbose="error"), f, conditions, query)`.
   - `discover` (654): the error text in Parameters.
   - `inspect` (666-667 and 674-675): `elif is_epochs(u):` / `read_epochs_any(u, preload=False, verbose="error")`; `if is_epochs(f0):` / `read_epochs_any(f0, preload=False, verbose="error")`.
   Do not touch `split_layout`, the `-ave.fif` globs, or `LOADER_VERSION` (the contract of `.fif` input is unchanged).

3. `brain-plot/erp_plot.py`, `contract(ev)` (529): new signature `contract(ev, eeglab=False)`. When `eeglab` is true, `baseline=None` and `filter=None` in the returned dict (all other keys unchanged). Add the caption helper right after `check_contract`:
   ```python
   def baseline_filter_text(k, sep):
       """Caption words for the baseline and the filter; EEGLAB .set files record neither (contract filter is None)."""
       if k["filter"] is None:
           return "baseline and filter not recorded (EEGLAB .set)"
       return f"baseline {k['baseline']} s{sep}filter {k['filter'][0]:g}–{k['filter'][1]:g} Hz"
   ```
   In `load` (589) call `contract(ev, eeglab=f.suffix.lower() == ".set")`. In the split layout `f` is the first file of the dict, a `-ave.fif`, so this is False there. `check_contract` needs no change (`None == None` across `.set` subjects; a `.fif` next to a `.set` differs in `baseline` and stops, which is wanted). Do not change `LOADER_VERSION`.

4. `brain-plot/erp_plot.py`, caption lines 1906-1908 become (for `.fif` the output is exactly today's):
   ```python
       bf = baseline_filter_text(k, "; ")
       lead = f"Time-locked to: {spec['time_locked_to']}; {bf}" if spec.get("time_locked_to") else bf[0].upper() + bf[1:]
       L.append("- " + lead + (f"; reference: {spec['reference']}" if spec.get("reference") else "")
                + " (identical in every panel, rule S1)")
   ```
   In `inspect` (after `out["filter_hz"] = ...`, 686): when `f0.suffix.lower() == ".set"` set `out["filter_hz"] = None`, `out["baseline"] = None` and add `out["note"] = "EEGLAB .set stores neither the baseline nor the filter settings; conditions are the time-locking event types"`. Update the module docstring line 8 to: `<data_dir> holds one *-epo.fif, *-ave.fif or epoched EEGLAB *.set per subject; …` (keep the rest of the sentence).

5. `brain-plot/microstate_plot.py` (509-511): the caption line uses the helper:
   ```python
       L.append(f"- Grand average: each subject's condition average, subjects weighted equally; {ep.baseline_filter_text(k, ', ')}"
                + (f", reference: {spec['reference']}" if spec.get("reference") else "") + " (identical in every panel, rule S1)")
   ```
   (`k` here is the loader's contract, as today; for `.fif` the line is unchanged.)

6. `brain-plot/tfr_plot.py` (102, 191, 196) and `brain-plot/source_plot.py` (111-112, 332, 337): `mne.read_epochs(<f>, ...)` → `ep.read_epochs_any(<f>, ...)` with the same keywords; `ep.contract(ep_sub)` → `ep.contract(ep_sub, eeglab=f.suffix.lower() == ".set")` (variable `f` is the file being read at that point; check it is a `Path`). In `source_plot.py` 111 the test becomes `if not ep.is_epochs(f):`.

7. `brain-plot/test/test_erp_plot.py`: add one block `# 10. EEGLAB .set input` before the final `OK` print (read the end of the file; follow the style of the other blocks: module-level asserts, temp roots via `tempfile.TemporaryDirectory()`). Two parts.
   Part A, synthetic round trip (single event per epoch): build the 2 x 2 synthetic epochs of Parameters (reuse the epochs construction of block 6, lines 396-408, with `event_id=dict(A=1, B=2)` and no metadata), save each subject twice: `rootF/<G>/<sub>-epo.fif` and `rootS/<G>/<sub>.set` (`epo.export(path, fmt="eeglab")`). Assert:
   a. `ep.discover(rootS)` has 2 groups of 2 units; `ep.available_conditions({"data": str(rootS)}, unit)` equals `["A", "B"]` for a `.set` unit (check the signature at line 452).
   b. `ep.read_conditions(f_set, ["A", "B"], None)` and the same call on the `.fif` twin return evokeds with `np.allclose(atol=1e-10)` data and equal `nave` lists.
   c. `ep.load(spec(rootS, conditions={"A": "A", "B": "B"}))` returns arrays `np.allclose(atol=1e-4)` to the `.fif` root's, and `meta["contract"]["filter"] is None and meta["contract"]["baseline"] is None` for `.set` while the `.fif` contract has a list for both (the function returns `data, times, info, meta`).
   d. A folder holding both `s1-epo.fif` and `s1.set` of one subject stops: `ep.select_files(spec(folder, ...))` raises `SystemExit` whose text contains `subject IDs appear more than once`.
   Part B, the real EEGLAB fixtures (`FIX = Path(__file__).resolve().parent / "data" / "eeglab"`; read `counts.csv` with the csv module). Assert:
   e. `ep.discover(FIX)` has groups `G1`, `G2` with 2 units each; for each of the 4 subjects `ep.available_conditions({"data": str(FIX)}, f)` equals `["rt", "square"]` (no name contains `/`).
   f. For each subject `ep.read_conditions(f, ["rt", "square"], None)[1]` (the nave list) equals `[n_rt, n_square]` from `counts.csv` — this is MATLAB's independent count of the epochs by the event at latency 0. Also `n_rt + n_square == 20`.
   g. `ep.load(spec(FIX, conditions={"rt": "RT", "square": "Square"}, components=[dict(name="P3", channels=<first two names of the real channel list that exist, read them with mne.read_epochs_eeglab on one fixture>, tmin_ms=250, tmax_ms=350, window_source="test")], reference="average"))` runs, returns 2 groups with 2 subjects each, `meta["contract"]["filter"] is None`.
   h. `ep.plot(<that spec>)` writes a `_caption.md` (find it like block 6 does with `latest(...)`) that contains `baseline and filter not recorded (EEGLAB .set)`, and `ep.baseline_filter_text` of a `.fif` contract starts with `baseline [`.
   i. `ep.inspect(FIX)` (capture stdout like the earlier inspect block) has `filter_hz` null and a `note`.
   j. A continuous `.set` stops: write one with `mne.io.RawArray(...)`/`raw.export(path, fmt="eeglab")` into a temp folder; `ep.read_epochs_any(path)` raises `SystemExit` with `not an epoched EEGLAB file` (MNE's reader may raise first: if `mne.read_epochs_eeglab` itself raises a `TypeError`/`ValueError` for continuous data, change `read_epochs_any` to call `eeglab_locking_types(f)` BEFORE `mne.read_epochs_eeglab`, so the clear message wins; do this reordering anyway, it costs nothing).

8. `brain-plot/SKILL.md` line 3 (frontmatter `description`): replace `per-subject MNE Epochs/Evoked .fif files` with `per-subject MNE Epochs/Evoked .fif files or epoched EEGLAB .set files`. Leave everything else in the file as is.

## Check
`C:/Users/ASUS/miniconda3/envs/mne/python.exe brain-plot/test/test_erp_plot.py && C:/Users/ASUS/miniconda3/envs/mne/python.exe brain-plot/test/test_tfr.py && C:/Users/ASUS/miniconda3/envs/mne/python.exe brain-plot/test/test_source.py && C:/Users/ASUS/miniconda3/envs/mne/python.exe brain-plot/test/test_microstate.py`

## Don't
- No commits.
- No rm, no git push, no git checkout . / restore . / reset --hard.
- Only the files in `## Files`. Leave every other uncommitted file alone, in particular `AGENTS.md`, `AGENTS.md.bak-doctor-2026-10-09`, `docs/cluster-before-after/`, `docs/cluster-layout-compare*.html`, `docs/tfce-mne-vs-standard.html`. Never write inside the Dropbox data folder; never write into `brain-plot/test/data/` (read-only fixtures; figures from tests go to temp folders — if a plot of the fixtures writes `brain_plot_eeglab/` next to the data, copy the fixtures to a temp folder first).
- No change to figure geometry or to any caption line other than the baseline/filter wording; output for `-epo.fif` / `-ave.fif` input must stay byte-identical (the existing tests must pass unchanged).
- No new dependency (`pymatreader` is already installed with MNE); no support for continuous `.set`; no `.set` in the `<condition>/<group>/` split layout.
- Run scripts in the foreground and wait; before replying, stop any background task still running.
- Reuse existing functions; don't copy existing logic. (`ep.is_epochs`, `ep.read_epochs_any`, `ep.baseline_filter_text` are the new shared helpers; every module calls them instead of repeating the test.)

## Acceptance (draft)
- verdict: TODO (accepted / review pending / rejected)
- files: brain-plot/SKILL.md, brain-plot/erp_plot.py, brain-plot/microstate_plot.py, brain-plot/source_plot.py, brain-plot/test/test_erp_plot.py, brain-plot/tfr_plot.py
- check: `C:/Users/ASUS/miniconda3/envs/mne/python.exe brain-plot/test/test_erp_plot.py && C:/Users/ASUS/miniconda3/envs/mne/python.exe brain-plot/test/test_tfr.py && C:/Users/ASUS/miniconda3/envs/mne/python.exe brain-plot/test/test_source.py && C:/Users/ASUS/miniconda3/envs/mne/python.exe brain-plot/test/test_microstate.py` → exit 1 (run by run-card)
- tokens:
  - round 1: exec deepseek-v4.1-flash: fresh 46k, cached 2787k, out 32k  (codex-eeglab-set-input.jsonl)
- review findings: TODO N real / M false positive / K missed (medium, no review)

## Acceptance
- verdict: accepted (wb executor, medium; sol review FAIL with 3 P1 + 1 P2, handled below)
- files: `brain-plot/erp_plot.py`, `tfr_plot.py`, `source_plot.py`, `microstate_plot.py`, `test/test_erp_plot.py`, `SKILL.md`; README (en/zh) and HANDOFF by Claude
- Check: all four module tests OK (erp, tfr, source, microstate) after the fixes; real EEGLAB fixtures: nave per condition equals MATLAB's independent counts; figure from the real `.set` files drawn and inspected (layout_issues empty)
- review findings: 1 real / 2 false positive (card contradictions, see below) / 3 K missed (sol, high-tier floor). Real: [P1] `file_stamp` ignored the sibling `.fdt` (cache reuse after an `.fdt` change) — fixed by Claude with a test. False positive: [P1] test dropped the first letter of the caption phrase (the card required lowercase "baseline" but step 4 prints "Baseline" at the line start; fixed to a case-insensitive assert); [P1] test used Cz/Pz instead of the first two channels (the first two of the sample data are FPz and EOG1; Cz/Pz is the sensible choice). [P2] reply.md in the task folder: runner convention.
- K missed (found by Claude on the first Check runs): the cache-hit path and 3 source_plot sites called `mne.io.read_info`, which only reads fiff headers → new `read_info_any`; the card did not list them.
- claude fix: `read_info_any` (4 sites), `file_stamp` follows the `.fdt`, test assertions.
- deferred: P3 `.set` baseline/filter could be recovered from `EEG.history`; EOG channels of the sample data are typed `eeg`.
