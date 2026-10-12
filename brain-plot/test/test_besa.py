"""Test for the BESA-to-run converter: python test/test_besa.py (prints OK on success)."""
import csv
import json
import sys
import tempfile
from pathlib import Path

import mne
import numpy as np
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import besa_to_run  # noqa: E402
import cluster_plot  # noqa: E402

mne.set_log_level("error")

BESA = Path("C:/Users/ASUS/Dropbox/metaphor_production/gn_manuscript/10-ERP_stats/02_v2_cluster_three-groups/"
            "besa_check")
CH = ["Fz", "Cz", "Pz", "Oz"]
ELP = ["EEG Fz 45.000 90.000", "EEG Cz 0.000 0.000", "EEG Pz 45.000 -90.000", "EEG Oz 90.000 -90.000"]
SUBJECTS = ["0001", "0002", "0003"]
N_T = 6
TIMES = np.linspace(0, 10, N_T)
AVR_HEAD = "Npts= 6   TSB= 0.000 DI= 2.000000 SB= 1.000 SC= 200.0 Nchan= 4"
SLUG = "01_cond_all"


def rows_of(path):
    with open(path, newline="", encoding="utf8") as fh:
        return list(csv.DictReader(fh))


def matrix(values, fmt, dims, dtype):
    body = "\n".join(";".join(fmt % v for v in row) for row in values)
    return f'<Matrix DataType="{dtype}" DimsSizes="{dims}" NumDims="2">{body}</Matrix>'


def array(values, fmt):
    return f'<Array DataType="float" ValidSize="{len(values)}">' + ";".join(fmt % v for v in values) + "</Array>"


def avr_text(values):
    return AVR_HEAD + "\n" + " ".join(CH) + "\n" + "\n".join(" ".join(f"{v:8.4f}" for v in row) for row in values.T) + "\n"  # BESA .avr: one row per channel


def build_project(root):
    """The mini BESA project: 3 participants x (NoGO, GO), 2 clusters, one of them significant."""
    rng = np.random.default_rng(0)
    go = rng.normal(0, 0.5, (len(SUBJECTS), N_T, len(CH)))
    nogo = go + rng.normal(0, 0.02, go.shape)  # small per-subject noise, so every paired t stays finite
    for i in range(len(SUBJECTS)):
        for name in ("Cz", "Pz"):
            nogo[i, 2:5, CH.index(name)] += 2.0
        nogo[i, 1, CH.index("Fz")] += 1.0
    (root / "avr").mkdir(parents=True)
    (root / "avr" / "channels.elp").write_text("\n".join(ELP) + "\n", encoding="utf8")
    for i, pid in enumerate(SUBJECTS):
        group = "A" if pid in ("0001", "0002") else "B"
        for cond, values in (("NoGO", nogo[i]), ("GO", go[i])):
            for folder in (root / "avr" / "paired_all" / cond, root / "avr" / cond / group):
                folder.mkdir(parents=True, exist_ok=True)
                (folder / f"{pid}_{cond}.avr").write_text(avr_text(values), encoding="utf8")

    t_stat = np.array([[stats.ttest_rel(nogo[:, ti, ci], go[:, ti, ci]).statistic for ti in range(N_T)]
                       for ci in range(len(CH))])
    ids = np.full((len(CH), N_T), -1, dtype=int)
    ids[CH.index("Cz"), 2:5] = 0
    ids[CH.index("Pz"), 2:5] = 0
    ids[CH.index("Fz"), 1] = 1
    values = [float(t_stat[ids == k].sum()) for k in (0, 1)]
    (root / "Results.dat").write_text(
        "<StatResults>\n<WS_SetParams>\n<TValues>\n" + matrix(t_stat, "%g", f"{len(CH)};{N_T}", "float") +
        "\n</TValues>\n<WS_RunStatistics>\n<ClusterValues>\n" + array(values, "%g") + "\n</ClusterValues>\n"
        "<ClusterIDs>\n" + matrix(ids, "%d", f"{len(CH)};{N_T}", "int") + "\n</ClusterIDs>\n<ClusterProbabilities>\n"
        + array([0.01, 0.5], "%g") + "\n</ClusterProbabilities>\n</StatResults>\n", encoding="utf8")

    table = ["sep=;", "BESA Statistics cluster summary report", "", "Project settings:", "Start time = 0",
             "End time = 10", "Neighbor Distance = 4.6", "Cluster Alpha = 0.05", "Number of Permutations = 100",
             "Right-tail cluster threshold value = 1", "Left-tail cluster threshold value = -1",
             "Average over Time = False", "Average over Channels = False", "",
             "Permutation Test Results Main Effect",
             "Cluster ID;p-value;Cluster value;Mean for NoGO;Mean for GO;Start Time;End Time;maximum t-value;"
             "latency at maximum;channel at maximum"]
    channels = []
    for k, p in ((1, 0.01), (2, 0.5)):
        m = ids == k - 1
        flat, where = t_stat[m], np.argwhere(m)
        peak = int(np.argmax(flat) if values[k - 1] > 0 else np.argmin(flat))
        span = TIMES[m.any(0)]
        table.append(";".join([f"Cluster {k}", f"{p:g}", f"{values[k - 1]:g}", f"{nogo[:, m.T].mean():g}",
                               f"{go[:, m.T].mean():g}", f"{span.min():g}", f"{span.max():g}", f"{flat[peak]:g}",
                               f"{TIMES[where[peak][1]]:g}", CH[where[peak][0]]]))
        channels.append("Cluster %d;%s" % (k, ";".join(c for c in CH if c in set(np.array(CH)[m.any(1)]))))
    (root / "cluster_summary.csv").write_text("\n".join(table) + "\n\n" + "\n".join(channels) + "\n", encoding="utf8")


def convert_args(root, out, **extra):
    args = ["convert", "--results", str(root / "Results.dat"), "--summary", str(root / "cluster_summary.csv"),
            "--avr-dir", str(root / "avr" / "paired_all"), "--elp", str(root / "avr" / "channels.elp"),
            "--cond-a", "NoGO", "--cond-b", "GO", "--out", str(out), "--slug", SLUG]
    for key, value in extra.items():
        args += [f"--{key.replace('_', '-')}", str(value)]
    return args


def part_synthetic():
    with tempfile.TemporaryDirectory() as tmp:
        root, out = Path(tmp) / "project", Path(tmp) / "run"
        build_project(root)
        besa_to_run.main(convert_args(root, out, group_dir=root / "avr"))
        for name in ("time_axis.csv", "channel_order.csv", "run_metadata.json", "input_manifest.csv"):
            assert (out / name).is_file(), name
        for name in ("observed_statistic.npy", "significant_cluster_union_mask.npy", "test_metadata.json",
                     "cluster_summary_significant.csv"):
            assert (out / SLUG / name).is_file(), name

        stat = np.load(out / SLUG / "observed_statistic.npy")
        assert stat.shape == (N_T, len(CH)), stat.shape
        mask = np.load(out / SLUG / "significant_cluster_union_mask.npy")
        want = np.zeros((N_T, len(CH)), bool)
        want[2:5, [CH.index("Cz"), CH.index("Pz")]] = True
        assert np.array_equal(mask, want), mask.astype(int)

        significant = rows_of(out / SLUG / "cluster_summary_significant.csv")
        assert [r["cluster_id"] for r in significant] == ["1"], significant
        assert significant[0]["channels"] == "Cz;Pz" and float(significant[0]["p_cluster"]) == 0.01, significant

        manifest = rows_of(out / "input_manifest.csv")
        assert len(manifest) == 2 * len(SUBJECTS), len(manifest)
        assert {r["group"] for r in manifest} == {"A", "B"}, manifest
        assert all(r["nave"] == "" for r in manifest)
        first = manifest[0]
        ev = mne.read_evokeds(out / first["file"])[0]
        assert ev.comment == first["condition"]
        i, cond = SUBJECTS.index(first["participant_id"]), first["condition"]
        avr = np.loadtxt(root / "avr" / "paired_all" / cond / f"{first['participant_id']}_{cond}.avr", skiprows=2)
        assert ev.data.shape == avr.shape and np.allclose(ev.data, avr * 1e-6, atol=1e-12), first  # both (n_ch, n_t)

        meta = json.loads((out / SLUG / "test_metadata.json").read_text(encoding="utf8"))
        assert meta["name"] == "NoGO \u2212 GO, all participants (N = 3)", meta["name"]
        assert abs(meta["cluster_forming_threshold"] - stats.t.ppf(0.975, len(SUBJECTS) - 1)) < 1e-9
        assert meta["n_significant_clusters"] == 1 and meta["n_clusters"] == 2

        try:
            besa_to_run.main(convert_args(root, out, group_dir=root / "avr"))
        except SystemExit:
            pass
        else:
            raise AssertionError("a second convert into the same --out did not stop")
        assert np.array_equal(np.load(out / SLUG / "significant_cluster_union_mask.npy"), mask)


def part_real():
    if not BESA.is_dir():
        print(f"skipped real-data part: {BESA} not found")
        return
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "run"
        besa_to_run.main(["convert",
                          "--results", str(BESA / "besa_data_folder/StatGroup_All/StatFiles/IntermediateFiles/"
                                                 "Stat_gn_T01_NoGO-GO_Results.dat"),
                          "--summary", str(BESA / "besa_out/T01/T01_cluster_summary.csv"),
                          "--avr-dir", str(BESA / "avr/paired_all"), "--elp", str(BESA / "avr/channels.elp"),
                          "--group-dir", str(BESA / "avr"), "--cond-a", "NoGO", "--cond-b", "GO",
                          "--out", str(out)])
        assert np.load(out / SLUG / "significant_cluster_union_mask.npy").shape == (501, 64)
        assert np.load(out / SLUG / "observed_statistic.npy").shape == (501, 64)
        significant = rows_of(out / SLUG / "cluster_summary_significant.csv")
        assert [r["cluster_id"] for r in significant] == ["1", "2", "3"], significant
        assert [r["n_channels"] for r in significant] == ["47", "64", "26"], significant
        assert len(rows_of(out / "input_manifest.csv")) == 260
        meta = json.loads((out / SLUG / "test_metadata.json").read_text(encoding="utf8"))
        assert meta["n_permutations"] == 5000, meta
        assert abs(meta["cluster_forming_threshold"] - 1.97852) < 1e-4, meta
        run = cluster_plot.read_run({"data": str(out), "tests": [SLUG]})
        assert len(run["tests"]) == 1 and len(run["tests"][0]["clusters"]) == 3, run["tests"]


part_synthetic()
part_real()
print("OK")
