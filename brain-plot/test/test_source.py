"""Fast tests for source_plot.py on synthetic data (target < 3 min)."""
import json
import sys
import tempfile
from pathlib import Path

import mne
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import erp_plot as ep  # noqa: E402
import source_plot as sp  # noqa: E402

SUBJECTS_DIR = str(sp.default_subjects_dir())


def make_synthetic_dataset(data_dir, fwd, src, st_label, info, sfreq=100.0, tmax_s=1.0, peak_s=0.3, lowpass=None, name="sub01"):
    info = info.copy()
    with info._unlock():
        info["sfreq"] = sfreq
        info["lowpass"] = lowpass if lowpass is not None else sfreq / 2.0
    times = np.arange(int(round(-0.2 * sfreq)), int(round(tmax_s * sfreq)) + 1) / sfreq
    lh_v, rh_v = src[0]["vertno"], src[1]["vertno"]
    idx = np.where(np.isin(lh_v, st_label.vertices))[0][0]

    # Pulse at peak_s (250-350 ms) in left superior temporal gyrus
    pulse = np.exp(-((times - peak_s) / 0.05) ** 2)
    stc_data = np.zeros((len(lh_v) + len(rh_v), len(times)))
    stc_data[idx] = pulse * 1e-8
    stc = mne.SourceEstimate(stc_data, vertices=[lh_v, rh_v], tmin=times[0], tstep=1.0 / sfreq)

    ev = mne.simulation.simulate_evoked(fwd, stc, info, cov=None, nave=30, random_state=42)

    n_trials = 30
    rng = np.random.default_rng(42)
    trials = np.tile(ev.data[None, :, :], (n_trials, 1, 1))
    trials += rng.normal(0, 1e-7, trials.shape)  # baseline noise

    event_codes = np.tile([1, 2, 3], 10)
    events = np.column_stack([np.arange(n_trials) * 200, np.zeros(n_trials, int), event_codes])
    epochs = mne.EpochsArray(trials, info, events=events, event_id={"condA": 1, "condB": 2, "condC": 3}, tmin=times[0], baseline=None)

    sub_file = Path(data_dir) / f"{name}-epo.fif"
    epochs.save(sub_file, overwrite=True, verbose="error")
    return sub_file


def count_colored(img):
    """Count non-white, non-grey pixels."""
    non_white = ~np.all(img >= 254, axis=-1)
    non_grey = np.ptp(img, axis=-1) > 20
    return int(np.sum(non_white & non_grey))


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


def test_source_layout_selfcheck():
    fig = sp.plt.figure(figsize=(60 * sp.ep.MM, 60 * sp.ep.MM))
    valid = fig.add_axes([10 / 60, 10 / 60, 16 / 60, 8 / 60])
    assert sp.source_layout_issues(fig, [valid], 0.5) == []

    too_wide = fig.add_axes([30 / 60, 10 / 60, 21 / 60, 10.5 / 60])
    wrong_aspect = fig.add_axes([10 / 60, 30 / 60, 16 / 60, 9 / 60])
    fig.text(0.5, 0.9, "small", fontsize=6)
    issues = sp.source_layout_issues(fig, [valid, too_wide, wrong_aspect], 0.5)
    assert any("width outside 12–20 mm" in issue for issue in issues), issues
    assert any("aspect ratio changed" in issue for issue in issues), issues
    assert any("text below 7 pt" in issue for issue in issues), issues
    sp.plt.close(fig)
    print("assertion (layout) passed: brain size, aspect ratio, and minimum text size self-check")


def main():
    test_source_layout_selfcheck()
    test_pure_helpers()
    print("Setting up coarse fsaverage source space (oct4)...")
    src = mne.setup_source_space("fsaverage", spacing="oct4", subjects_dir=SUBJECTS_DIR, add_dist=False, verbose="error")
    labels = mne.read_labels_from_annot("fsaverage", parc="aparc", hemi="lh", subjects_dir=SUBJECTS_DIR, verbose="error")
    st_label = [l for l in labels if l.name == "superiortemporal-lh"][0]

    ch_names = ["Fp1", "Fp2", "F7", "F3", "Fz", "F4", "F8", "FC5", "FC1", "FC2", "FC6", "T7", "C3", "Cz", "C4", "T8", "CP5", "CP1", "CP2", "CP6", "P7", "P3", "Pz", "P4", "P8", "O1", "Oz", "O2"]
    info = mne.create_info(ch_names, 100.0, "eeg")
    info.set_montage("standard_1020")

    bem = mne.read_bem_solution(Path(SUBJECTS_DIR) / "fsaverage" / "bem" / "fsaverage-5120-5120-5120-bem-sol.fif", verbose="error")
    fwd = mne.make_forward_solution(info, trans="fsaverage", src=src, bem=bem, eeg=True, meg=False, mindist=5.0, n_jobs=2, verbose="error")

    with tempfile.TemporaryDirectory() as tmp_dir:
        data_dir = Path(tmp_dir) / "data"
        data_dir.mkdir()
        make_synthetic_dataset(data_dir, fwd, src, st_label, info)

        base_spec = {
            "data": str(data_dir),
            "conditions": {"condA": "Condition A"},
            "noise_cov_ms": [-200, 0],
            "baseline_ms": [-200, 0],
            "method": "dSPM",
        }

        # (b) noise_cov_ms ending after 0 ms stops with a message
        try:
            s_bad_cov = dict(base_spec, noise_cov_ms=[-200, 50])
            sp.check_spec(s_bad_cov)
            raise AssertionError("accepted noise_cov_ms ending after 0 ms")
        except SystemExit as e:
            assert "0 ms" in str(e), e
        print("assertion (b) passed: noise_cov_ms ending after 0 ms stopped")

        # (c) a spec with an unknown key stops
        try:
            s_bad_key = dict(base_spec, unknown_key_xyz=123)
            sp.check_spec(s_bad_key)
            raise AssertionError("accepted unknown spec key")
        except SystemExit as e:
            assert "unsupported spec keys" in str(e), e
        print("assertion (c) passed: unknown spec key stopped")

        # (d) windows figure written with empty layout_issues
        spec_win = dict(base_spec, figure="windows", windows=[{"name": "N300", "tmin_ms": 250, "tmax_ms": 350}])
        out_win = sp.plot(spec_win, subjects_dir=SUBJECTS_DIR, src=src, bem=bem, fwd=fwd)[0]
        run_win = json.loads(Path(f"{out_win}_run.json").read_text(encoding="utf8"))
        assert run_win["layout_issues"] == [], f"layout issues in windows figure: {run_win['layout_issues']}"
        assert run_win["render_check"] == "ok", f"render_check failed: {run_win.get('render_check')}"
        assert "subject_p99" in run_win and "outlier_subjects" in run_win
        assert not Path(f"{out_win}_caption.md").exists(), "source figure must not produce _caption.md"
        assert Path(f"{out_win}.png").exists() and Path(f"{out_win}.svg").exists()
        print("assertion (d1) passed: windows figure written with empty layout_issues, outlier records, no caption")

        # (d) timeline figure written with empty layout_issues
        spec_time = dict(base_spec, figure="timeline", times_ms=[200, 300, 400], half_width_ms=50)
        out_time = sp.plot(spec_time, subjects_dir=SUBJECTS_DIR, src=src, bem=bem, fwd=fwd)[0]
        run_time = json.loads(Path(f"{out_time}_run.json").read_text(encoding="utf8"))
        assert run_time["layout_issues"] == [], f"layout issues in timeline figure: {run_time['layout_issues']}"
        assert run_time["render_check"] == "ok", f"render_check failed: {run_time.get('render_check')}"
        assert "subject_p99" in run_time and "outlier_subjects" in run_time
        assert not Path(f"{out_time}_caption.md").exists(), "source figure must not produce _caption.md"
        assert Path(f"{out_time}.png").exists() and Path(f"{out_time}.svg").exists()
        print("assertion (d2) passed: timeline figure written with empty layout_issues, outlier records, no caption")

        # (a) hemisphere check — count of coloured pixels larger on left than right
        # Render the map for 250-350 ms window
        grand_avg, times_s, _, _, _, _, _, _ = sp.load_and_compute(spec_win, subjects_dir=SUBJECTS_DIR, src=src, bem=bem, fwd=fwd)
        times_ms = times_s * 1000.0
        t_mask = (times_ms >= 250) & (times_ms <= 350)
        val = grand_avg[0][:, t_mask].mean(axis=-1)
        fmin = float(np.percentile(val, 90.0))
        fmax = float(np.percentile(val, 99.5))
        fmid = (fmin + fmax) / 2.0

        renderer = sp.BrainRenderer(SUBJECTS_DIR, src)
        lh_v = src[0]["vertno"]
        img_lh = renderer.render("lh", val[:len(lh_v)], fmin, fmid, fmax)
        img_rh = renderer.render("rh", val[len(lh_v):], fmin, fmid, fmax)
        c_lh = count_colored(img_lh)
        c_rh = count_colored(img_rh)
        assert c_lh > c_rh, f"hemisphere check failed: lh={c_lh}, rh={c_rh}"
        print(f"assertion (a) passed: hemisphere check (lh={c_lh} > rh={c_rh})")

        # (e) rank-deficient subject must not get dSPM max > 3x full rank
        max_full = float(grand_avg.max())
        data_dir_def = Path(tmp_dir) / "data_def"
        data_dir_def.mkdir()
        ep_orig = mne.read_epochs(Path(data_dir) / "sub01-epo.fif", proj=False, verbose="error")
        def_data = ep_orig.get_data().copy()
        ch_fz = ep_orig.ch_names.index("Fz")
        ch_f3 = ep_orig.ch_names.index("F3")
        ch_f4 = ep_orig.ch_names.index("F4")
        def_data[:, ch_fz, :] = (def_data[:, ch_f3, :] + def_data[:, ch_f4, :]) / 2.0
        ep_def = mne.EpochsArray(def_data, ep_orig.info, events=ep_orig.events, event_id=ep_orig.event_id, tmin=ep_orig.times[0], baseline=None)
        ep_def.save(data_dir_def / "sub01-epo.fif", overwrite=True, verbose="error")

        spec_def = dict(spec_win, data=str(data_dir_def))
        grand_avg_def, _, _, _, _, _, _, params_def = sp.load_and_compute(spec_def, subjects_dir=SUBJECTS_DIR, src=src, bem=bem, fwd=fwd)
        max_def = float(grand_avg_def.max())
        assert params_def["rank"]["sub01"] == 26, f"expected rank 26, got {params_def['rank']['sub01']}"
        assert max_def <= 3.0 * max_full, f"rank-deficient dSPM inflated: max_def={max_def} vs max_full={max_full}"
        print(f"assertion (e) passed: rank-deficient dSPM not inflated (max_def={max_def:.2f} <= 3x max_full={max_full:.2f}, rank={params_def['rank']['sub01']})")

        # (f) >= 3 rows x >= 2 columns figure passes render_check; monkeypatched blank stops
        spec_3x2 = dict(
            base_spec,
            conditions={"condA": "Condition A", "condB": "Condition B", "condC": "Condition C"},
            figure="windows",
            windows=[
                {"name": "W1", "tmin_ms": 250, "tmax_ms": 350},
                {"name": "W2", "tmin_ms": 350, "tmax_ms": 450},
            ],
        )

        orig_screenshot = mne.viz.Brain.screenshot
        call_count = [0]

        def bad_screenshot(self, *args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 2:
                return np.full((800, 800, 3), 255, dtype=np.uint8)
            return orig_screenshot(self, *args, **kwargs)

        mne.viz.Brain.screenshot = bad_screenshot
        try:
            sp.plot(spec_3x2, subjects_dir=SUBJECTS_DIR, src=src, bem=bem, fwd=fwd)
            raise AssertionError("blank screenshot was not caught by render_check")
        except SystemExit as e:
            assert "blank brain image" in str(e), f"unexpected exit message: {e}"
            print("assertion (f1) passed: monkeypatched white screenshot caught by render_check")
        finally:
            mne.viz.Brain.screenshot = orig_screenshot

        out_3x2 = sp.plot(spec_3x2, subjects_dir=SUBJECTS_DIR, src=src, bem=bem, fwd=fwd)[0]
        run_3x2 = json.loads(Path(f"{out_3x2}_run.json").read_text(encoding="utf8"))
        assert run_3x2["render_check"] == "ok"
        assert run_3x2["layout_issues"] == []
        assert Path(f"{out_3x2}.png").exists()
        print("assertion (f2) passed: 3 rows x 2 cols figure passed render_check: ok")

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

        # (j) subjects with different time grids stop instead of being averaged
        data_dir_mix = Path(tmp_dir) / "data_mix"
        data_dir_mix.mkdir()
        make_synthetic_dataset(data_dir_mix, fwd, src, st_label, info, name="sub01")
        make_synthetic_dataset(data_dir_mix, fwd, src, st_label, info, sfreq=250.0, lowpass=40.0, name="sub02")
        try:
            sp.load_and_compute(dict(spec_win, data=str(data_dir_mix)), subjects_dir=SUBJECTS_DIR, src=src, bem=bem, fwd=fwd)
            raise AssertionError("averaged subjects with different time grids")
        except SystemExit as e:
            assert "differs from" in str(e) or "time axis differs" in str(e), e
        print("assertion (j) passed: different time grids stopped")

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

        # (o) run record carries method facts and provenance
        out_o = sp.plot(spec_win, subjects_dir=SUBJECTS_DIR, src=src, bem=bem, fwd=fwd)[0]
        run_o = json.loads(Path(f"{out_o}_run.json").read_text(encoding="utf8"))
        assert {"estimate", "orientation", "aggregation", "trial_counts", "colour_scale", "noise_cov"} <= set(run_o["method_facts"]), run_o.keys()
        assert run_o["inputs"] and run_o["code_md5"] and run_o["versions"]["mne"], run_o.keys()
        assert len(list((ep.out_root(spec_win) / ".cache" / "source").iterdir())) <= ep.CACHE_KEEP
        print("assertion (o) passed: method facts, provenance, source cache pruned")

    print("OK")


if __name__ == "__main__":
    main()
