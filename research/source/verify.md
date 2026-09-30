# Independent verification: source dSPM values and `Llit` outlier

## Scope and method

I independently recomputed the source estimates with MNE 1.13.0.dev208; `source_plot` was not used for this calculation. For each epoch file, I selected `acc == 1`, added an average EEG reference projection, applied the −200 to 0 ms baseline, estimated a shrunk covariance over −200 to 0 ms, averaged each event condition, cropped to −200 to 1000 ms, and decimated by 5 to 100 Hz. I used the cached fsaverage forward, `loose=0.2`, `depth=0.8`, dSPM, `lambda2=1/9`, and `pick_ori=None`. The query was applied before averaging and covariance estimation, matching the module. Source estimates were summarized using inclusive time masks and aparc vertex membership.

For the group summary, I processed all 59 subjects except `sub27`. Each subject had one inverse operator applied to its six condition evokeds. “Mean” is the mean across all vertices of each subject’s time-averaged 600–800 ms source map; “P99” is its 99th percentile across vertices. The table reports the across-subject median and maximum of each measure.

## Sub1, Hmet: independent estimate vs module

`sub1` had 23 valid `Hmet` trials. Entries below are the mean dSPM over the stated label vertices and inclusive time interval.

| Label and interval | Plain MNE | Module | Relative difference |
|---|---:|---:|---:|
| `superiortemporal-lh`, 300–500 ms | 4.183636298 | 4.183636189 | 0.00000261% |
| `lateraloccipital-lh`, 300–500 ms | 2.582266401 | 2.582266331 | 0.00000274% |
| `lateraloccipital-lh`, 100–200 ms | 2.573871675 | 2.573871613 | 0.00000243% |

All differences are far below 1%. To call `source_plot.load_and_compute(spec)` while keeping its external cache read-only, the verification script disabled `np.savez` for that call and supplied a NumPy-scalar JSON converter. The module’s existing subject cache contains NumPy `int64` trial counts; a direct call otherwise fails at [source_plot.py:359](../../brain-plot/source_plot.py#L359), where `json.dumps(trial_counts)` cannot serialize them. No project source was changed.

## Per-condition 600–800 ms summary

Values are dSPM. Each cell is `median / maximum` across the 59 subject-level maps.

| Condition | Mean across vertices | P99 across vertices |
|---|---:|---:|
| Hmet | 3.5284 / 21.5960 | 10.5853 / 71.6215 |
| Hlit | 3.4417 / 17.3625 | 9.9083 / 58.0657 |
| Hrep | 3.1887 / 22.8244 | 9.4731 / 77.6738 |
| Lmet | 3.5143 / 36.0410 | 10.2922 / 123.0883 |
| Llit | 3.5588 / 73.1219 | 10.6885 / 247.3543 |
| Lrep | 3.0166 / 16.0814 | 8.9229 / 63.9304 |

Only `sub33` exceeds 3× the `Llit` mean median: threshold 10.6764; `sub33` is 73.1219 (20.55× the median). Its `Llit` P99 is 247.3543, versus the `Llit` P99 median of 10.6885. The other condition medians are similar to `Llit`; the standout is the subject-level maximum, which points to one influential subject rather than a generally elevated `Llit` response across the sample.

### `sub33` inspection

| Condition | Valid trials | Maximum channel amplitude, 600–800 ms |
|---|---:|---:|
| Hmet | 8 | 7.86 µV at Fp1 |
| Hlit | 13 | 7.29 µV at FT8 |
| Hrep | 6 | 12.81 µV at F8 |
| Lmet | 6 | 12.80 µV at F6 |
| Llit | 10 | 10.72 µV at Fz |
| Lrep | 9 | 13.73 µV at T8 |

The `Llit` peak is not an extreme sensor voltage and is not a lone-channel spike: F4 reaches 10.68 µV and several other frontal channels are close (Fp2 10.26 µV, FC4 9.57 µV). Its mean of per-channel peak amplitudes is 6.08 µV, comparable to Hrep (6.09 µV) and Lmet (5.80 µV). The cached baseline covariance has a 62-eigenvalue condition number of about 333,098 for `sub33`, versus a subject median of about 28,001; its median channel noise SD is 3.59 µV versus 3.90 µV across subjects. This unusually ill-conditioned covariance is a plausible dSPM whitening amplifier for a broad frontal `Llit` response, but the summaries alone do not prove causality. It is the leading explanation for the outsized subject-level source map; inspect/review `sub33` and its covariance before interpreting the group `Llit` map.

## Reproduction files

- `verify_scratch/recompute.py`: independent MNE calculations and module comparison.
- `verify_scratch/inspect_outlier.py`: channel-amplitude and covariance diagnostics for `sub33`.
- `verify_scratch/inspect_cov.py`: covariance eigenvalue condition-number comparison.
