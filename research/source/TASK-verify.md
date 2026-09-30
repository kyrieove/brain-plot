# Task: independent check of the source module's dSPM numbers + outlier subjects

Do NOT edit any file in the repo. Write only `C:\dev\brain-plot\research\source\verify.md` (and scratch scripts under
`C:\dev\brain-plot\research\source\verify_scratch\`). Python: `C:\Users\ASUS\miniconda3\envs\mnedev\python.exe`.
Data (read-only): `D:\1-python_datasets\metaphor production\derivatives\preprocessed_epochs_verb\sub*-epo.fif`.
fsaverage: subjects_dir `C:\Users\ASUS\mne_data\MNE-fsaverage-data`. Module under test:
`C:\dev\brain-plot\brain-plot\source_plot.py` (read it; its forward is cached at
`D:\1-python_datasets\metaphor production\derivatives\brain_plot_preprocessed_epochs_verb\.cache\source\*\fsaverage-fwd.fif`).
Run long scripts in the foreground; `n_jobs` ≤ 2.

## 1. Independent recompute (plain MNE, do not import source_plot for this part)
For `sub1`, condition `Hmet`, trials `acc == 1` (metadata column; the condition is the event key `Hmet`):
average reference projection, baseline −200…0 ms, noise covariance −200…0 ms (`method="shrunk"`), evoked cropped to
−200…1000 ms and decimated to 100 Hz, fsaverage forward (you may reuse the cached `-fwd.fif`), `loose=0.2`,
`depth=0.8`, dSPM, `lambda2=1/9`, `pick_ori=None`. Report the mean dSPM over 300–500 ms in the aparc label
`superiortemporal-lh` and in `lateraloccipital-lh`, and over 100–200 ms in `lateraloccipital-lh`.
Then get the module's value for the same numbers: call `source_plot.load_and_compute(spec)` with a spec that restricts
subjects to `sub1` (key `subjects`; copy the other keys from
`…\brain_plot_preprocessed_epochs_verb\specs\source_timeline.json`), and index its grand average the same way.
Relative difference must be < 1 %; if not, find out why (name the line in source_plot.py).

## 2. Why is "Literal (low)" (`Llit`) so much larger?
In the module's all-subject grand average, `Llit` is far stronger at 600–800 ms than every other condition. Compute,
per subject and condition, the mean dSPM over all vertices in 600–800 ms and the 99th percentile over vertices
(plain MNE as in part 1, all 59 subjects except sub27; per subject compute the inverse once and apply it to the six
condition evokeds). Report: the table's summary (median and max per condition), subjects whose `Llit` value is > 3×
the median of `Llit`, their trial counts per condition, and for each such subject what is odd in its `Llit` evoked
(e.g. max |µV| per channel in 600–800 ms vs the other conditions, a single channel dominating).

## Final message (≤ 8 lines)
The three recomputed numbers vs the module (and % difference); the outlier subjects (if any) and the likely cause;
path of `verify.md`.
