"""Test for time-frequency module: python test/test_tfr.py (prints OK on success)."""
import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import mne
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import erp_plot as ep  # noqa: E402
import tfr_plot  # noqa: E402

mne.set_log_level("error")


def make_synthetic_dataset(root):
    montage = mne.channels.make_standard_montage("standard_1020")
    ch_names = ["Fz", "FCz", "Cz", "Pz", "Oz"]
    sfreq = 250.0
    info = mne.create_info(ch_names, sfreq, "eeg")
    info.set_montage(montage)

    times = np.arange(-1.0, 2.0 + 1 / sfreq, 1 / sfreq)
    n_trials = 40
    rng = np.random.default_rng(42)

    # Time envelope for 300-600 ms (centre 450 ms, width ~100 ms)
    env = np.exp(-((times - 0.45) / 0.08) ** 2)

    for g in ["G1", "G2"]:
        g_dir = root / g
        g_dir.mkdir(parents=True, exist_ok=True)
        for s in range(4):
            data_trials = []
            events = []
            event_id = {"burst": 1, "phase": 2, "noise": 3}

            trial_idx = 0
            for cond_name, event_code in event_id.items():
                for _ in range(n_trials):
                    noise = rng.normal(0, 1.0, (len(ch_names), len(times))) * 1e-6
                    sig = np.zeros((len(ch_names), len(times)))

                    if cond_name == "burst":
                        # 10 Hz burst, random phase per trial
                        phi = rng.uniform(0, 2 * np.pi)
                        osc = 10.0 * 1e-6 * env * np.sin(2 * np.pi * 10.0 * times + phi)
                        sig += osc
                    elif cond_name == "phase":
                        # 5 Hz phase-locked response, constant phase across trials
                        osc = 10.0 * 1e-6 * env * np.sin(2 * np.pi * 5.0 * times)
                        sig += osc

                    data_trials.append(sig + noise)
                    events.append([trial_idx * int(sfreq), 0, event_code])
                    trial_idx += 1

            epochs_data = np.array(data_trials)
            epochs = mne.EpochsArray(epochs_data, info, events=np.array(events), event_id=event_id, tmin=-1.0, verbose=False)
            fpath = g_dir / f"sub-{g}s{s + 1:02d}-epo.fif"
            epochs.save(fpath, overwrite=True)


def run_tests():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        data_dir = root / "data"
        make_synthetic_dataset(data_dir)

        base_spec = {
            "data": str(data_dir),
            "conditions": {"burst": "10 Hz Burst", "phase": "5 Hz Phase", "noise": "Noise Only"},
            "channels": ["Fz", "Cz"],
            "measure": "power",
            "xlim_ms": [-500, 1500],
            "baseline_ms": [-500, -200],
            "windows": [{"name": "alpha", "fmin": 8, "fmax": 12, "tmin_ms": 300, "tmax_ms": 600}],
        }

        # 1. Run power spec
        out_paths = tfr_plot.plot(base_spec)
        assert len(out_paths) == 2, f"expected 2 figures for 2 groups, got {len(out_paths)}"

        for out in out_paths:
            run_json = json.loads(Path(f"{out}_run.json").read_text(encoding="utf8"))
            assert run_json["layout_issues"] == [], f"layout issues found: {run_json['layout_issues']}"

        grand_avg, times, freqs, info, valid_ids, trial_counts, tf_params = tfr_plot.load_and_compute(base_spec)
        roi_idx = [info.ch_names.index(ch) for ch in base_spec["channels"]]

        t_mask = (times >= 300) & (times <= 600)
        f_mask = (freqs >= 8) & (freqs <= 12)

        g = "G1"
        burst_power = grand_avg[g, "burst"][roi_idx].mean(0)
        phase_power = grand_avg[g, "phase"][roi_idx].mean(0)
        noise_power = grand_avg[g, "noise"][roi_idx].mean(0)

        # Power peak of burst condition lies at 8-12 Hz / 300-600 ms
        f_idx, t_idx = np.unravel_index(np.argmax(burst_power), burst_power.shape)
        peak_f, peak_t = freqs[f_idx], times[t_idx]
        assert 8.0 <= peak_f <= 12.0, f"peak freq for burst condition was {peak_f} Hz, expected 8-12 Hz"
        assert 300.0 <= peak_t <= 600.0, f"peak time for burst condition was {peak_t} ms, expected 300-600 ms"

        burst_win_mean = burst_power[f_mask, :][:, t_mask].mean()
        phase_win_mean = phase_power[f_mask, :][:, t_mask].mean()
        noise_win_mean = noise_power[f_mask, :][:, t_mask].mean()
        assert burst_win_mean > phase_win_mean + 1.0, "burst condition should have significantly higher power in 8-12 Hz / 300-600 ms"
        assert burst_win_mean > noise_win_mean + 1.0, "burst condition should have significantly higher power than noise"

        # 2. Test cache hit on second run
        with patch.object(mne.Epochs, "compute_tfr") as mock_compute:
            tfr_plot.plot(base_spec)
            assert mock_compute.call_count == 0, "compute_tfr was called on cached run!"

        # 3. Run ITC spec
        itc_spec = base_spec.copy()
        itc_spec["measure"] = "itc"
        del itc_spec["windows"]
        out_itc = tfr_plot.plot(itc_spec)
        assert len(out_itc) == 2

        grand_avg_itc, times_itc, freqs_itc, _, _, _, _ = tfr_plot.load_and_compute(itc_spec)
        phase_itc = grand_avg_itc[g, "phase"][roi_idx].mean(0)
        t_mask_itc = (times_itc >= 300) & (times_itc <= 600)

        # In phase condition, ITC should peak near 5 Hz
        itc_freq_profile = phase_itc[:, t_mask_itc].mean(axis=1)
        itc_peak_freq = freqs_itc[np.argmax(itc_freq_profile)]
        assert 4.0 <= itc_peak_freq <= 6.0, f"ITC peak frequency was {itc_peak_freq}, expected ~5 Hz"

        burst_itc = grand_avg_itc[g, "burst"][roi_idx].mean(0)
        burst_itc_mean = burst_itc[:, t_mask_itc].mean()
        phase_itc_mean = phase_itc[:, t_mask_itc].mean()
        assert phase_itc_mean > burst_itc_mean, "phase-locked condition should have higher ITC than burst condition"

        # 4. Stop cases
        def assert_stops(spec_mod, match_str):
            try:
                tfr_plot.plot(spec_mod)
                assert False, f"Expected stop with message containing {match_str!r}, but succeeded"
            except SystemExit as e:
                assert match_str in str(e), f"Expected {match_str!r} in error message, got: {e}"

        # Stop case 1: measure not power/itc
        s1 = base_spec.copy()
        s1["measure"] = "entropy"
        assert_stops(s1, "measure must be 'power' or 'itc'")

        # Stop case 2: channel missing
        s2 = base_spec.copy()
        s2["channels"] = ["NonExistentChannel"]
        assert_stops(s2, "not in data channels")

        # Stop case 3: xlim_ms or baseline_ms reaching into edge zone
        s3 = base_spec.copy()
        s3["xlim_ms"] = [-1000, 1500]
        assert_stops(s3, "reaches into the edge zone")

        s3b = base_spec.copy()
        s3b["xlim_ms"] = [-500, 2000]
        assert_stops(s3b, "reaches into the edge zone")

        s3c = base_spec.copy()
        s3c["baseline_ms"] = [-1000, -800]
        assert_stops(s3c, "reaches into the edge zone")

        # Stop case 4: window outside freqs/xlim_ms
        s4 = base_spec.copy()
        s4["windows"] = [{"name": "out", "fmin": 1, "fmax": 2, "tmin_ms": 300, "tmax_ms": 500}]
        assert_stops(s4, "outside freqs")

        s4b = base_spec.copy()
        s4b["windows"] = [{"name": "out", "fmin": 8, "fmax": 12, "tmin_ms": -800, "tmax_ms": -600}]
        assert_stops(s4b, "outside freqs")

        # Stop case 5: grid key not in conditions
        s5 = base_spec.copy()
        s5["grid"] = [["burst", "bad_cond"]]
        assert_stops(s5, "not found in conditions")
        assert_stops({**base_spec, "query": "acc == 99"}, "leaves no trials")

    print("OK")


if __name__ == "__main__":
    run_tests()
