"""Test for the cluster-permutation result module: python test/test_cluster.py (prints OK on success)."""
import csv
import json
import sys
import tempfile
from pathlib import Path

import mne
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
    info.set_montage(mne.channels.make_standard_montage("standard_1020"))
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
        order, rows = cluster_plot.channel_rows(info, CH, "lmr", cluster_plot.ep.common_sphere(info))
        grouped = {}
        for lab, i, g in rows:
            if i is not None:
                grouped.setdefault(g, []).append(CH[i])
        assert grouped == {"Left": ["C3"], "Midline": ["Fz", "Cz", "Pz", "Oz"], "Right": ["C4"]}, grouped
        assert order == [4, 0, 1, 2, 3, 5], order
        assert [lab for lab, i, _ in rows if i is not None] == ["C3", "Fz", None, "Pz", None, "C4"], "every other label"
        print("cluster channel rows: Left [C3], Midline [Fz, Cz, Pz, Oz], Right [C4]")

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

        # (e) stops
        def assert_stops(s, match):
            try:
                cluster_plot.plot(s)
                assert False, f"expected stop with {match!r}"
            except SystemExit as e:
                assert match in str(e), f"expected {match!r} in {e}"

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

    print("OK")


if __name__ == "__main__":
    run_tests()
