"""Convert a BESA Statistics paired-t cluster project into the run folder cluster_plot.py reads.

    python besa_to_run.py convert --results R --summary S --avr-dir A --elp E --cond-a NoGO --cond-b GO --out O

Reads one BESA Statistics project — the `*_Results.dat` of its `IntermediateFiles`, the exported "Summary of Cluster
Statistics" csv, the per-subject .avr files and `channels.elp` — and writes a NEW run folder that `cluster_plot.py`
reads unchanged: `time_axis.csv`, `channel_order.csv`, `run_metadata.json`, `input_manifest.csv`,
`evoked/<cond>/<id>_<cond>-ave.fif` and one test folder `<slug>/` with `observed_statistic.npy`,
`significant_cluster_union_mask.npy`, `test_metadata.json` and `cluster_summary_significant.csv`. The module never
computes a statistic: it copies BESA's t map, cluster ids and p-values as BESA wrote them and only converts units and
shapes. It stops (`ep.die`) when BESA's own files disagree with each other. Developer reference: `docs/rules.md`.
"""
import argparse
import csv
import json
import re
from pathlib import Path

import mne
import numpy as np
from scipy import stats

import erp_plot as ep

M_TO_MM = 1000.0
SPHERE_RADIUS_M = 0.095  # channels.elp positions scaled to the 9.5 cm head of the MNE head frame
TOL = 1e-6


def block(txt, tag):
    """Matrix or Array named <tag> of the BESA results file, reshaped when it carries DimsSizes."""
    m = re.search(rf"<{tag}>\s*<(Matrix|Array)([^>]*)>(.*?)</\1>", txt, re.S)
    if not m:
        ep.die(f"{tag} not found in the BESA results file")
    dims = re.search(r'DimsSizes="([\d;]+)"', m.group(2))
    vals = np.array([float(v) for v in m.group(3).replace("\n", ";").split(";") if v.strip()])
    return vals.reshape([int(d) for d in dims.group(1).split(";")]) if dims else vals


def read_results(path):
    """t map, cluster ids, cluster p-values and cluster values of the BESA results file."""
    txt = Path(path).read_text(encoding="utf8", errors="replace")
    t, ids = block(txt, "TValues"), block(txt, "ClusterIDs").astype(int)
    cluster_p, cluster_value = block(txt, "ClusterProbabilities"), block(txt, "ClusterValues")
    if t.shape != ids.shape:
        ep.die(f"{path}: TValues {t.shape} and ClusterIDs {ids.shape} must have the same shape")
    if len(cluster_p) != ids.max() + 1:
        ep.die(f"{path}: ClusterProbabilities holds {len(cluster_p)} values but ClusterIDs name "
               f"{ids.max() + 1} clusters")
    return dict(t=t, ids=ids, cluster_p=cluster_p, cluster_value=cluster_value)


def read_summary(path, cond_a, cond_b):
    """Settings, one parsed row per cluster and the channels per cluster of the BESA cluster summary csv."""
    lines = Path(path).read_text(encoding="utf8", errors="replace").splitlines()
    start = next((i for i, line in enumerate(lines) if line.split(";")[0].strip() == "Cluster ID"), None)
    if start is None:
        ep.die(f"{path}: no cluster table (a line whose first field is 'Cluster ID') was found")
    settings = {}
    for line in lines[:start]:
        key, sep, value = line.partition(" = ")
        if sep:
            settings[key.strip()] = value.strip()
    header = lines[start].split(";")
    for key in (f"Mean for {cond_a}", f"Mean for {cond_b}"):
        if key not in header:
            ep.die(f"{path}: the cluster table has no {key!r} column (found {header})")
    rows, i = [], start + 1
    while i < len(lines) and lines[i].strip():
        fields = lines[i].split(";")
        if len(fields) != len(header):
            ep.die(f"{path}: cluster row {i + 1} has {len(fields)} fields, the header has {len(header)}")
        row = dict(zip(header, (f.strip() for f in fields)))
        number = re.fullmatch(r"Cluster (\d+)", row["Cluster ID"])
        if not number:
            ep.die(f"{path}: cluster row {i + 1} starts with {row['Cluster ID']!r}, expected 'Cluster <k>'")
        rows.append(dict(number=int(number.group(1)), p_value=float(row["p-value"]),
                         cluster_value=float(row["Cluster value"]), mean_a=float(row[f"Mean for {cond_a}"]),
                         mean_b=float(row[f"Mean for {cond_b}"]), start=float(row["Start Time"]),
                         end=float(row["End Time"]), max_t=float(row["maximum t-value"]),
                         max_latency=float(row["latency at maximum"]), max_channel=row["channel at maximum"]))
        i += 1
    if [r["number"] for r in rows] != list(range(1, len(rows) + 1)):
        ep.die(f"{path}: the cluster table numbers {[r['number'] for r in rows]} are not 1..K in order")
    channels = {}
    for line in lines[i:]:
        if not line.strip():
            continue
        fields = [f.strip() for f in line.split(";")]
        number = re.fullmatch(r"Cluster (\d+)", fields[0])
        if not number:
            ep.die(f"{path}: the channel list {fields[0]!r} does not start with 'Cluster <k>'")
        channels[int(number.group(1))] = [f for f in fields[1:] if f]
    if sorted(channels) != [r["number"] for r in rows]:
        ep.die(f"{path}: the cluster table names clusters {[r['number'] for r in rows]} but the channel lists "
               f"name {sorted(channels)}")
    return dict(settings=settings, rows=rows, channels=channels)


def read_avr(path):
    """Values in µV (n_t, n_ch; the file stores channels as rows), channel names, TSB ms and DI ms of one BESA .avr file."""
    text = Path(path).read_text(encoding="utf8", errors="replace").splitlines()
    head = re.search(r"Npts=\s*(\d+)\s+TSB=\s*([\d.\-]+)\s+DI=\s*([\d.\-]+)", text[0])
    nchan = re.search(r"Nchan=\s*(\d+)", text[0])
    if not (head and nchan):
        ep.die(f"{path}: the first line is not a BESA .avr header (Npts/TSB/DI/Nchan)")
    npts, tsb, di = int(head.group(1)), float(head.group(2)), float(head.group(3))
    data = np.loadtxt(path, skiprows=2)  # BESA .avr: one row per channel, one column per time sample
    if data.shape != (int(nchan.group(1)), npts):
        ep.die(f"{path}: holds {data.shape} values but its header names {int(nchan.group(1))} channels of "
               f"{npts} samples")
    return data.T, text[1].split(), tsb, di


def read_elp(path):
    """Ordered mapping channel name -> (theta, phi) in degrees from a BESA channels.elp file."""
    elp = {}
    for line in Path(path).read_text(encoding="utf8", errors="replace").splitlines():
        fields = line.split()
        if len(fields) == 4 and fields[0] == "EEG":
            elp[fields[1]] = (float(fields[2]), float(fields[3]))
    if not elp:
        ep.die(f"{path}: holds no 'EEG <name> <theta> <phi>' line")
    return elp


def positions(elp):
    """MNE head-frame positions of the .elp angles: x right, y front, z up, 9.5 cm radius."""
    ch_pos = {}
    for name, (theta, phi) in elp.items():
        if theta < 0:
            theta, phi = -theta, phi + 180
        t, p = np.deg2rad(theta), np.deg2rad(phi)
        ch_pos[name] = SPHERE_RADIUS_M * np.array([np.sin(t) * np.cos(p), np.sin(t) * np.sin(p), np.cos(t)])
    return ch_pos


def write_csv(path, header, rows):
    with open(path, "w", newline="", encoding="utf8") as fh:
        writer = csv.writer(fh)
        writer.writerow(header)
        writer.writerows(rows)


def setting(settings, key, path):
    if key not in settings:
        ep.die(f"{path}: the settings line {key!r} is missing from the cluster summary")
    return settings[key]


def convert(args):
    """Turn the BESA project into the run folder `args.out` (it must not exist yet)."""
    out = Path(args.out)
    res, summ, elp = read_results(args.results), read_summary(args.summary, args.cond_a, args.cond_b), read_elp(args.elp)
    settings, rows, cluster_channels = summ["settings"], summ["rows"], summ["channels"]
    cluster_alpha = float(setting(settings, "Cluster Alpha", args.summary))
    n_permutations = int(setting(settings, "Number of Permutations", args.summary))
    neighbor_cm = float(setting(settings, "Neighbor Distance", args.summary))
    start_ms, end_ms = float(setting(settings, "Start time", args.summary)), float(setting(settings, "End time", args.summary))
    for tail in ("Right-tail", "Left-tail"):
        if not any(key.startswith(tail) for key in settings):
            ep.die(f"{args.summary}: no {tail} cluster threshold line; a two-sided test cannot be read off it")
    names, t, ids = list(elp), res["t"], res["ids"]
    n_ch, n_t = t.shape
    if len(names) != n_ch:
        ep.die(f"{args.elp} names {len(names)} channels but the results file holds {n_ch}")
    times = np.linspace(start_ms, end_ms, n_t)

    files = {}
    for cond in (args.cond_a, args.cond_b):
        found = sorted((Path(args.avr_dir) / cond).glob(f"*_{cond}.avr"))
        files[cond] = {p.name.split("_")[0]: p for p in found}
    if not files[args.cond_a] or list(files[args.cond_a]) != list(files[args.cond_b]):
        ep.die(f"{args.avr_dir}: {args.cond_a} holds {len(files[args.cond_a])} and {args.cond_b} "
               f"{len(files[args.cond_b])} files with different participant ids; the project must be paired")
    pids = list(files[args.cond_a])
    n = len(pids)
    if args.group_dir:
        base = Path(args.group_dir) / args.cond_a
        group_of = {}
        for folder in sorted(p for p in base.iterdir() if p.is_dir()):
            for f in folder.glob(f"*_{args.cond_a}.avr"):
                pid = f.name.split("_")[0]
                if group_of.setdefault(pid, folder.name) != folder.name:
                    ep.die(f"{base}: participant {pid} appears in more than one group folder")
        missing = [i for i in pids if i not in group_of]
        if missing:
            ep.die(f"{base}: no group folder holds {missing}; every participant needs exactly one")
        groups = sorted(set(group_of.values()))
    else:
        group_of = dict.fromkeys(pids, "all")
        groups = ["all"]

    if out.exists():
        ep.die(f"{args.out} already exists; give a new output folder (this script never writes into an existing one)")
    out.mkdir(parents=True)

    data = {}
    info = None
    for pid in pids:
        for cond in (args.cond_a, args.cond_b):
            src = files[cond][pid]
            values, chans, tsb, di = read_avr(src)
            if chans != names:
                ep.die(f"{src}: channel names differ from {args.elp}")
            if values.shape[0] != n_t:
                ep.die(f"{src}: holds {values.shape[0]} time samples, the results file holds {n_t}")
            if abs(tsb - times[0]) > TOL or abs(di - (times[1] - times[0])) > TOL:
                ep.die(f"{src}: starts at {tsb} ms with a {di} ms step, the results time axis starts at "
                       f"{times[0]} ms with a {times[1] - times[0]} ms step")
            data.setdefault(cond, {})[pid] = values
            if info is None:
                info = mne.create_info(names, M_TO_MM / di, "eeg")
                info.set_montage(mne.channels.make_dig_montage(ch_pos=positions(elp), coord_frame="head"))
            target = out / "evoked" / cond
            target.mkdir(parents=True, exist_ok=True)
            mne.EvokedArray(values.T * 1e-6, info, tmin=tsb / M_TO_MM, nave=1, comment=cond).save(
                target / f"{pid}_{cond}-ave.fif")

    write_csv(out / "time_axis.csv", ["time_index", "time_ms"], [[i, float(v)] for i, v in enumerate(times)])
    write_csv(out / "channel_order.csv", ["channel_index", "channel"], list(enumerate(names)))
    write_csv(out / "input_manifest.csv", ["group", "condition", "participant_id", "file", "nave"],
              [[group_of[pid], cond, pid, f"evoked/{cond}/{pid}_{cond}-ave.fif", ""]
               for pid in pids for cond in (args.cond_a, args.cond_b)])
    (out / "run_metadata.json").write_text(json.dumps(dict(
        analysis="BESA Statistics 2.1 cluster-based permutation test (converted by besa_to_run.py)",
        time_window_ms=[start_ms, end_ms], n_time_samples=n_t, sampling_frequency_hz=M_TO_MM / di, n_channels=n_ch,
        groups=groups, conditions=sorted([args.cond_a, args.cond_b]),
        sample_sizes={g: sum(1 for pid in pids if group_of[pid] == g) for g in groups},
        difference_definition=f"{args.cond_a} minus {args.cond_b} within each participant",
        cluster_forming_alpha=cluster_alpha, cluster_level_alpha=args.alpha, n_permutations=n_permutations,
        neighbor_distance_cm=neighbor_cm, all_participants_used=True, exclusions=[]), indent=2), encoding="utf8")

    significant = [r["number"] for r in rows if r["p_value"] < args.alpha]
    threshold = stats.t.ppf(1 - cluster_alpha / 2, n - 1)
    test = out / args.slug
    test.mkdir()
    np.save(test / "observed_statistic.npy", t.T.astype(np.float32))
    np.save(test / "significant_cluster_union_mask.npy", np.isin(ids, [k - 1 for k in significant]).T)
    sig_rows = []
    for r in rows:
        if r["p_value"] >= args.alpha:
            continue
        sign = ">" if r["cluster_value"] > 0 else "<"
        sig_rows.append([r["number"], r["p_value"], r["start"], r["end"], len(cluster_channels[r["number"]]),
                         ";".join(cluster_channels[r["number"]]), r["cluster_value"], r["max_t"], r["max_latency"],
                         r["max_channel"], f"{args.cond_a} {sign} {args.cond_b}"])
    write_csv(test / "cluster_summary_significant.csv",
              ["cluster_id", "p_cluster", "time_start_ms", "time_end_ms", "n_channels", "channels", "cluster_mass",
               "peak_stat", "peak_time_ms", "peak_channel", "direction"], sig_rows)
    (test / "test_metadata.json").write_text(json.dumps(dict(
        name=f"{args.cond_a} \u2212 {args.cond_b}, all participants (N = {n})", slug=args.slug, kind="condition_pooled",
        statistic="t", tail="two-sided", cluster_forming_alpha=cluster_alpha, cluster_forming_threshold=threshold,
        cluster_level_alpha=args.alpha, n_permutations=n_permutations, df1=n - 1, df2=None, n_clusters=len(rows),
        n_significant_clusters=len(significant), minimum_cluster_p=float(np.min(res["cluster_p"])),
        source="BESA Statistics 2.1, converted by besa_to_run.py"), indent=2), encoding="utf8")

    verify(res, summ, names, times, {c: np.stack([data[c][pid] for pid in pids]) for c in (args.cond_a, args.cond_b)},
           args.cond_a, args.cond_b, threshold)
    print(f"OK: {len(rows)} clusters, {len(significant)} significant, N = {n}, out = {out}")


def verify(res, summ, names, times, data, cond_a, cond_b, threshold):
    """Check BESA's t map, cluster masks, time spans and means against each other; die on the first mismatch."""
    t, ids, per_cluster = res["t"], res["ids"], summ["channels"]
    label = np.array(names)
    for row in summ["rows"]:
        k = row["number"]
        m = ids == k - 1
        if abs(res["cluster_p"][k - 1] - row["p_value"]) > 1e-6 or \
                not np.isclose(res["cluster_value"][k - 1], row["cluster_value"], rtol=1e-4):
            ep.die(f"cluster {k}: the results file gives p = {res['cluster_p'][k - 1]:g}, cluster value "
                   f"{res['cluster_value'][k - 1]:g}; the summary table gives p = {row['p_value']:g}, cluster value "
                   f"{row['cluster_value']:g}")
        found = set(label[m.any(1)])
        if found != set(per_cluster[k]):
            ep.die(f"cluster {k}: the channel lists disagree (t map {sorted(found)}, summary {sorted(per_cluster[k])})")
        span = times[m.any(0)]
        if span.min() != row["start"] or span.max() != row["end"]:
            ep.die(f"cluster {k}: the t map spans {span.min()}–{span.max()} ms, the summary {row['start']}–{row['end']}")
        signs = np.sign(t[m])
        if not (signs == signs[0]).all() or signs[0] != np.sign(row["cluster_value"]):
            ep.die(f"cluster {k}: its t values do not share one sign matching the cluster value {row['cluster_value']}")
        if np.abs(t[m]).min() < threshold - 1e-3:
            ep.die(f"cluster {k}: holds a sample below the cluster-forming threshold {threshold:.5f} "
                   f"(smallest |t| {np.abs(t[m]).min():.5f})")
        diff = data[cond_a][:, m.T].mean() - data[cond_b][:, m.T].mean()  # data: (subjects, n_t, n_ch), m: (n_ch, n_t)
        if abs(diff - (row["mean_a"] - row["mean_b"])) > 1e-3:
            ep.die(f"cluster {k}: the .avr files give a mean {cond_a} − {cond_b} of {diff} µV, the summary "
                   f"{row['mean_a'] - row['mean_b']} µV")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Convert a BESA Statistics cluster project into a run folder.")
    sub = parser.add_subparsers(dest="command", required=True)
    conv = sub.add_parser("convert", help="write the run folder cluster_plot.py reads")
    conv.add_argument("--results", required=True, help="the *_Results.dat of the project's IntermediateFiles")
    conv.add_argument("--summary", required=True, help="the exported cluster summary csv")
    conv.add_argument("--avr-dir", required=True, help="folder holding <cond>/<id>_<cond>.avr")
    conv.add_argument("--elp", required=True, help="the channels.elp of the project")
    conv.add_argument("--cond-a", required=True, help="the condition the t values subtract the other from")
    conv.add_argument("--cond-b", required=True, help="the subtracted condition")
    conv.add_argument("--out", required=True, help="the new run folder (must not exist)")
    conv.add_argument("--group-dir", help="optional folder holding <cond>/<group>/<id>_<cond>.avr")
    conv.add_argument("--slug", default="01_cond_all")
    conv.add_argument("--alpha", type=float, default=0.05, help="cluster-level significance level")
    args = parser.parse_args(argv)
    if args.command == "convert":
        convert(args)


if __name__ == "__main__":
    main()
