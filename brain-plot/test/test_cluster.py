"""Test for the cluster-permutation result module: python test/test_cluster.py (prints OK on success)."""
import csv
import json
import sys
import tempfile
from pathlib import Path

import mne

MONTAGE = "colin27_1020" if "colin27_1020" in mne.channels.get_builtin_montages() else "standard_1020"  # MNE ≥ 1.14 drops the old name
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import cluster_plot  # noqa: E402

mne.set_log_level("error")

CH = ["Fz", "Cz", "Pz", "Oz", "C3", "C4"]
TIMES_MS = np.arange(2, 801, 2, dtype=float)
T01 = "01_condition_main_effect_all"
T02 = "02_condition_by_group_interaction"
T03 = "03_within_td_condition_effect"


def write_csv(path, header, rows):
    with open(path, "w", newline="", encoding="utf8") as fh:
        writer = csv.writer(fh)
        writer.writerow(header)
        writer.writerows(rows)


def make_synthetic_run(root):
    sfreq = 500.0
    t = np.arange(-0.2, 1.0, 1 / sfreq)
    info = mne.create_info(CH, sfreq, "eeg")
    info.set_montage(mne.channels.make_standard_montage(MONTAGE))
    signal = np.zeros((len(CH), len(t)))
    win = (t >= 0.3) & (t <= 0.5)
    signal[CH.index("Cz"), win] = 2e-6
    signal[CH.index("Pz"), win] = 2e-6
    rng = np.random.default_rng(0)
    manifest = []
    for group in ("TD", "MD"):
        for i in range(1, 4):
            pid = f"{group.lower()}{i:02d}"
            go = rng.normal(0, 0.05e-6, signal.shape)
            nogo = go + signal + rng.normal(0, 0.05e-6, signal.shape)
            for cond, data in (("GO", go), ("NoGO", nogo)):
                d = root / "ev" / cond / group
                d.mkdir(parents=True, exist_ok=True)
                mne.EvokedArray(data, info, tmin=-0.2, comment=cond).save(d / f"{pid}_{cond}-ave.fif",
                                                                        overwrite=True)
                manifest.append([group, cond, pid, f"ev/{cond}/{group}/{pid}_{cond}-ave.fif", 30])

    run = root / "stats" / "run1"
    run.mkdir(parents=True)
    (run / "run_metadata.json").write_text(json.dumps(
        {"groups": ["TD", "MD"], "conditions": ["GO", "NoGO"],
         "difference_definition": "NoGO minus GO within each participant"}), encoding="utf8")
    write_csv(run / "time_axis.csv", ["time_index", "time_ms"], [[i, float(t_ms)] for i, t_ms in enumerate(TIMES_MS)])
    write_csv(run / "channel_order.csv", ["channel_index", "channel"], [[i, c] for i, c in enumerate(CH)])
    write_csv(run / "input_manifest.csv", ["group", "condition", "participant_id", "file", "nave"], manifest)

    stat = np.full((len(TIMES_MS), len(CH)), 0.5)
    mask = np.zeros((len(TIMES_MS), len(CH)), dtype=bool)
    sig_rows = (TIMES_MS >= 300) & (TIMES_MS <= 500)
    cols = [CH.index("Cz"), CH.index("Pz")]
    stat[np.ix_(sig_rows, cols)] = 5.0
    mask[np.ix_(sig_rows, cols)] = True
    cluster = [[1, 0.001, 300, 500, "Cz;Pz"]]

    def write_test(slug, meta, s, m, clusters):
        d = run / slug
        d.mkdir()
        np.save(d / "observed_statistic.npy", s.astype(np.float32))
        np.save(d / "significant_cluster_union_mask.npy", m)
        (d / "test_metadata.json").write_text(json.dumps(meta), encoding="utf8")
        write_csv(d / "cluster_summary_significant.csv",
                  ["cluster_id", "p_cluster", "time_start_ms", "time_end_ms", "channels"], clusters)

    write_test(T01, {"name": "Condition main effect (all)", "kind": "condition_pooled", "statistic": "t",
                     "tail": "two-tailed", "cluster_forming_threshold": 2.0, "cluster_level_alpha": 0.05,
                     "n_permutations": 1000, "df1": 5, "df2": None, "n_significant_clusters": 1},
               stat, mask, cluster)
    write_test(T02, {"name": "Condition by group interaction", "kind": "interaction", "statistic": "F",
                     "tail": "two-tailed", "cluster_forming_threshold": 3.0, "cluster_level_alpha": 0.05,
                     "n_permutations": 1000, "df1": 2, "df2": 18, "n_significant_clusters": 0},
               np.full((len(TIMES_MS), len(CH)), 0.5), np.zeros((len(TIMES_MS), len(CH)), dtype=bool), [])
    write_test(T03, {"name": "Within-TD condition effect", "kind": "condition_group", "statistic": "t",
                     "tail": "two-tailed", "cluster_forming_threshold": 2.0, "cluster_level_alpha": 0.05,
                     "n_permutations": 1000, "df1": 2, "df2": None, "n_significant_clusters": 1},
               stat, mask, cluster)
    return run


def run_tests():
    with tempfile.TemporaryDirectory() as td:
        run = make_synthetic_run(Path(td))
        spec = {"data": str(run), "tests": [T01, T03]}

        # (a) the µV difference and the subject counts
        read = cluster_plot.read_run(spec)
        by_slug = {t["slug"]: t for t in read["tests"]}
        uv, n01, info = cluster_plot.diff_uv(read, by_slug[T01], run)
        i400 = int(np.argmin(np.abs(read["times_ms"] - 400)))
        assert abs(uv[i400, read["ch_names"].index("Cz")] - 2.0) < 0.1, "Cz difference at 400 ms was not ~2 µV"
        assert abs(uv[i400, read["ch_names"].index("Oz")]) < 0.2, "Oz should carry no difference"
        _, n03, _ = cluster_plot.diff_uv(read, by_slug[T03], run)
        assert (n01, n03) == (6, 3), f"subject counts were {(n01, n03)}"
        print("cluster µV difference: 2 µV at Cz, 6/3 subjects")

        # (f) a B (GO) file whose channel order differs from channel_order.csv still lines up
        go_file = Path(td) / "ev" / "GO" / "TD" / "td01_GO-ave.fif"
        ev_go = mne.read_evokeds(go_file, verbose="error")[0]
        ev_go.reorder_channels(list(reversed(ev_go.ch_names)))
        ev_go.save(go_file, overwrite=True)
        read_f = cluster_plot.read_run(spec)
        uv_f, _, _ = cluster_plot.diff_uv(read_f, {t["slug"]: t for t in read_f["tests"]}[T01], run)
        assert abs(uv_f[i400, read_f["ch_names"].index("Cz")] - 2.0) < 0.1, "reversed B channels broke the Cz difference"
        print("cluster reversed-GO-channel difference still 2 µV at Cz")

        # (b) default spec writes one figure per test and a clean layout
        outs = cluster_plot.plot(spec)
        assert len(outs) == 2, f"expected one figure per test, got {outs}"
        o01 = next(o for o in outs if "_t01_" in o.name)
        o03 = next(o for o in outs if "_t03_" in o.name)
        for out in (o01, o03):
            for ext in (".png", ".svg", "_run.json", "_caption.md"):
                assert Path(f"{out}{ext}").exists(), f"missing {out}{ext}"
            rec = json.loads(Path(f"{out}_run.json").read_text(encoding="utf8"))
            assert rec["layout_issues"] == [], f"layout issues in {out.name}: {rec['layout_issues']}"
        assert json.loads(Path(f"{o01}_run.json").read_text(encoding="utf8"))["tests"][T01]["n_subjects"] == 6
        assert json.loads(Path(f"{o03}_run.json").read_text(encoding="utf8"))["tests"][T03]["n_subjects"] == 3
        assert "_topo-bins100ms" in o01.name and "_topo-bins100ms" in o03.name, (o01.name, o03.name)
        print("cluster default render: one figure per test, png/svg/_run.json/_caption.md, clean layout")

        # (h) the default render's topomap bins are half-open with honest labels
        svg = Path(f"{o01}.svg").read_text(encoding="utf8")
        assert "2–100 ms" in svg and "2–102 ms" not in svg, "topomap bins are not the half-open 2–100 ms"
        print("cluster bins: half-open 2–100 ms label, no overlapping 2–102 ms")

        # (i) channel_rows groups the synthetic montage left / midline / right, anterior first
        rows = cluster_plot.channel_rows(info, CH, "lmr", cluster_plot.ep.common_sphere(info))
        grouped = {}
        for lab, i, g in rows:
            if i is not None:
                grouped.setdefault(g, []).append(CH[i])
        assert grouped == {"Left": ["C3"], "Midline": ["Fz", "Cz", "Pz", "Oz"], "Right": ["C4"]}, grouped
        assert [i for _, i, _ in rows if i is not None] == [4, 0, 1, 2, 3, 5]
        assert [lab for lab, i, _ in rows if i is not None] == ["C3", "Fz", None, "Pz", None, "C4"], "every other label"
        print("cluster channel rows: Left [C3], Midline [Fz, Cz, Pz, Oz], Right [C4]")

        # (i) the name rule itself, as MNE make_1020_channel_selections(midline="12z") reads it
        assert [cluster_plot.hemi_by_name(n) for n in ("FC1", "C2", "Fz")] == ["Midline"] * 3
        assert [cluster_plot.hemi_by_name(n) for n in ("C3", "TP9")] == ["Left"] * 2
        assert [cluster_plot.hemi_by_name(n) for n in ("C4", "TP10")] == ["Right"] * 2
        print("cluster channel rows: name rule Midline 1/2/z, Left odd digit, Right even digit")

        # (ii) channel_order "file" renders in file order with no groups
        cluster_plot.plot({**spec, "channel_order": "file"})
        print("cluster channel_order file renders")

        # (c) contour and cluster-window topomaps render
        for extra in ({"display": "contour"}, {"topo": "clusters"}):
            cluster_plot.plot({**spec, **extra})
        print("cluster display contour and topo clusters render")

        # (d) an F test with no µV difference renders (default colour)
        cluster_plot.plot({**spec, "tests": [T02]})
        print("cluster F test topomaps render")

        def assert_stops(s, match):
            try:
                cluster_plot.plot(s)
                assert False, f"expected stop with {match!r}"
            except SystemExit as e:
                assert match in str(e), f"expected {match!r} in {e}"

        # (j) layout columns writes ONE figure for all tests, cleanly, with both tests recorded
        outs_c = cluster_plot.plot({**spec, "layout": "columns"})
        assert len(outs_c) == 1, f"columns layout writes one figure, got {outs_c}"
        oc = outs_c[0]
        assert "_columns_t01-t03_" in oc.name, oc.name
        rec_c = json.loads(Path(f"{oc}_run.json").read_text(encoding="utf8"))
        assert rec_c["layout_issues"] == [], f"columns layout issues: {rec_c['layout_issues']}"
        assert set(rec_c["tests"]) == {T01, T03}, sorted(rec_c["tests"])
        assert rec_c.get("layout") == "columns", rec_c.get("layout")
        cap_c = Path(f"{oc}_caption.md").read_text(encoding="utf8")
        assert "Condition main effect (all)" in cap_c and "Within-TD condition effect" in cap_c, "columns caption misses a test"
        print("cluster columns render: one figure, t01-t03, clean layout, both tests recorded")

        # (k) layout columns with a t and an F test under colour stat stops: one shared colour scale
        assert_stops({**spec, "tests": [T01, T02], "layout": "columns"}, "mix t and F")

        # (l) layout columns needs the hemisphere row order
        assert_stops({**spec, "layout": "columns", "channel_order": "file"}, "channel_order to")

        # (m) the side layout is unchanged: one figure per test, no columns part in the name or the record
        outs_s = cluster_plot.plot(spec)
        assert len(outs_s) == 2 and all("_columns" not in o.name for o in outs_s), outs_s
        assert "layout" not in json.loads(Path(f"{outs_s[0]}_run.json").read_text(encoding="utf8"))
        print("cluster side layout unchanged: one figure per test, no columns part")

        # (n) layout waves writes one figure per drawable test, skips the interaction, clean layout
        wave_ch = {f"{T01}/1": ["Cz", "Pz"], f"{T03}/1": ["Cz", "Pz"]}
        outs_w = cluster_plot.plot({**spec, "tests": [T01, T02, T03], "layout": "waves",
                                    "waves_channels": wave_ch})
        assert len(outs_w) == 2, f"waves layout writes one figure per drawable test, got {outs_w}"
        for out in outs_w:
            for ext in (".png", ".svg", "_run.json", "_caption.md"):
                assert Path(f"{out}{ext}").exists(), f"missing {out}{ext}"
            rec_w = json.loads(Path(f"{out}_run.json").read_text(encoding="utf8"))
            assert rec_w["layout_issues"] == [], f"waves layout issues in {out.name}: {rec_w['layout_issues']}"
            assert rec_w.get("layout") == "waves", rec_w.get("layout")
            assert any(s["test"] == T02 and "interaction" in s["reason"] for s in rec_w["waves_skipped"]), \
                rec_w["waves_skipped"]
        ow = next(o for o in outs_w if "_t01_" in o.name)
        assert "cluster_waves_t01_" in ow.name, ow.name
        print("cluster waves: one figure per drawable test, T02 skipped, clean layout")

        # (o) cluster_waves mean_a equals a plain-numpy mean over the chosen channels and subjects
        read_w = cluster_plot.read_run(spec)
        tw = {t["slug"]: t for t in read_w["tests"]}[T01]
        c0 = tw["clusters"][0]
        sel = ["Cz", "Pz"]
        tt, waves, _ = cluster_plot.cluster_waves(read_w, tw, run, {c0["cluster_id"]: sel})
        man, root = cluster_plot.read_manifest(run)
        by_cond = {}
        for r in man:
            by_cond.setdefault(r["participant_id"], {})[r["condition"]] = r["file"]
        subj = []
        for pid in sorted(by_cond):
            ev = mne.read_evokeds(root / by_cond[pid]["NoGO"], verbose="error")[0]
            ci_ = [ev.ch_names.index(ch) for ch in sel]
            subj.append(ev.data[ci_].mean(0) * 1e6)
        expect = np.array(subj).mean(0)
        assert len(tt) == expect.shape[0], "cluster_waves time axis length"
        assert np.max(np.abs(waves[c0["cluster_id"]][0] - expect)) < 1e-9, "cluster_waves mean_a differs from numpy"
        print("cluster waves: mean_a matches a plain-numpy mean over the chosen channels and subjects")

        # (p) waves stops: only an interaction, no waves_channels (with a recommendation), an unknown channel
        assert_stops({**spec, "tests": [T02], "layout": "waves"}, "no test left to draw")
        assert_stops({**spec, "layout": "waves"}, "needs waves_channels")
        assert_stops({**spec, "layout": "waves"}, "recommended:")
        assert_stops({**spec, "layout": "waves", "waves_channels": ["Cz", "Nope"]}, "unknown channel(s)")
        print("cluster waves stops: interaction only, missing/unknown waves_channels")

        # (p) cluster_peak, recommend_channels and waves_parts agree with the spec
        peak_ms, lo_ms, hi_ms = cluster_plot.cluster_peak(tw, c0, read_w["times_ms"], read_w["ch_names"])
        assert c0["time_start_ms"] <= peak_ms <= c0["time_end_ms"], (peak_ms, c0)
        assert 0 < hi_ms - lo_ms <= 50.0 + 1e-6, (lo_ms, hi_ms)
        rec_ch = cluster_plot.recommend_channels(tw, c0, read_w["times_ms"], read_w["ch_names"])
        assert 0 < len(rec_ch) <= 6 and all(n in c0["channels"] for n in rec_ch), rec_ch
        assert cluster_plot.waves_parts(1) == [(1, 1)]
        assert cluster_plot.waves_parts(2) == [(2, 2)]
        assert cluster_plot.waves_parts(3) == [(3, 2)]
        assert cluster_plot.waves_parts(4) == [(4, 2)]
        assert cluster_plot.waves_parts(6) == [(6, 2)]
        assert cluster_plot.waves_parts(7) == [(6, 2), (1, 1)]
        assert cluster_plot.waves_parts(13) == [(6, 2), (6, 2), (1, 1)]
        print("cluster waves: peak window <= 50 ms, recommendation inside the cluster, waves_parts split")

        # (e) stops
        assert_stops({**spec, "tests": [T02], "color": "uv"}, "no single difference wave")
        assert_stops({**spec, "bogus": 1}, "unsupported spec keys")
        assert_stops({**spec, "channel_order": "bogus"}, "channel_order")
        assert_stops({**spec, "tests": ["99_missing"]}, "not found")
        np.save(run / T01 / "significant_cluster_union_mask.npy", np.zeros((10, len(CH)), dtype=bool))
        assert_stops(spec, "must both be")
        print("cluster stops: uv on interaction, unknown key/folder, bad channel_order, wrong mask shape")

        # (g) a time_axis.csv without time_index stops
        ta = run / "time_axis.csv"
        _, ta_rows = cluster_plot.read_csv(ta)
        write_csv(ta, ["time_ms"], [[r["time_ms"]] for r in ta_rows])
        assert_stops({**spec, "tests": [T01]}, "missing the column")
        print("cluster stops: time_axis.csv without time_index")

        # (q) the bins marker needs a channel significant in at least half of the bin's samples
        times5 = np.arange(5.0)
        m5 = np.zeros((5, 2), dtype=bool)
        m5[:3, 0] = True   # channel A significant in 3 of the 5 samples
        m5[:1, 1] = True   # channel B significant in 1 of the 5 samples
        maps5 = cluster_plot.maps_of({"stat": np.zeros((5, 2)), "uv": None, "mask": m5, "clusters": []}, times5,
                                     ["A", "B"], "bins", cluster_plot.bins_of_times(times5, 5.0), False)
        assert maps5[0][1].tolist() == [True, False], maps5[0][1]
        print("cluster bins marker: a channel significant in 3/5 samples is marked, 1/5 is not")

        # (s) the short-name rule: leading digits per test, falling back to the full slug on a clash or a missing id
        assert cluster_plot.stem_ids(["01_condition_main_effect_all",
                                      "03_within_td_condition_effect"]) == ["01", "03"]
        assert cluster_plot.stem_ids(["01_a", "01_b"]) == ["01_a", "01_b"]
        assert cluster_plot.stem_ids(["alpha", "02_b"]) == ["alpha", "02_b"]
        print("cluster stem ids: leading digits, full-slug fallback on a clash or a missing id")

    print("OK")


if __name__ == "__main__":
    run_tests()
