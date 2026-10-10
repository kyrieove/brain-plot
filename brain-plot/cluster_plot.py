"""Cluster-permutation result module for brain-plot (agent guide references/cluster.md).

    python cluster_plot.py plot <spec.json>

Reads a saved MNE spatio-temporal cluster run and draws one figure: one column per test, a channel × time raster of
the test statistic (only significant samples coloured by default) with a row of µV-difference topomaps underneath.
Draws only — it never computes a test, threshold or p-value; the only computed number is the µV mean difference.
Outputs go to brain_plot_<data folder>/cluster/ next to the data folder, versioned (rules O1–O3).
"""
import csv
import hashlib
import json
import re
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mne
import numpy as np

import erp_plot as ep

REQUIRED = {"data", "tests"}
OPTIONAL = {"labels", "color", "display", "topo", "topo_bin_ms", "width_mm", "height_mm", "time_locked_to", "claim"}


def check_spec(spec):
    keys = set(spec)
    if REQUIRED - keys:
        ep.die(f"spec is missing required keys: {sorted(REQUIRED - keys)}")
    if keys - REQUIRED - OPTIONAL:
        ep.die(f"unsupported spec keys {sorted(keys - REQUIRED - OPTIONAL)} (see references/spec.md)")
    if not (isinstance(spec["data"], str) and spec["data"].strip()):
        ep.die("data must be the path of the cluster run folder (the one holding time_axis.csv); give it as a string")
    tests = spec["tests"]
    if not (isinstance(tests, list) and tests and all(isinstance(t, str) and t.strip() for t in tests)):
        ep.die("tests must be a non-empty list of test folder names; list at least one folder under the run folder")
    if len(set(tests)) != len(tests):
        ep.die(f"tests must not repeat (got {tests!r}); name each test folder once")
    if "labels" in spec:
        lab = spec["labels"]
        if not (isinstance(lab, dict) and all(isinstance(k, str) and isinstance(v, str) for k, v in lab.items())):
            ep.die("labels must be a {test folder name: column title} mapping of strings")
    if spec.get("color", "stat") not in ("stat", "uv"):
        ep.die(f"color must be 'stat' or 'uv' (got {spec['color']!r}); use 'stat' for the test statistic or 'uv' for the µV difference")
    if spec.get("display", "masked") not in ("masked", "contour"):
        ep.die(f"display must be 'masked' or 'contour' (got {spec['display']!r}); 'masked' colours only significant samples")
    if spec.get("topo", "bins") not in ("bins", "clusters"):
        ep.die(f"topo must be 'bins' or 'clusters' (got {spec['topo']!r}); 'bins' draws fixed time bins")
    if "topo_bin_ms" in spec and not (isinstance(spec["topo_bin_ms"], (int, float)) and spec["topo_bin_ms"] > 0):
        ep.die(f"topo_bin_ms must be a positive number of ms (got {spec['topo_bin_ms']!r})")
    for key in ("width_mm", "height_mm"):
        if key in spec and not (isinstance(spec[key], (int, float)) and spec[key] > 0):
            ep.die(f"{key} must be a positive number of mm (got {spec[key]!r})")
    for key in ("time_locked_to", "claim"):
        if key in spec and not ep.text(spec[key]):
            ep.die(f"{key} must be a non-empty string")


def read_csv(path):
    """Header and rows of a CSV file (a header-only file gives no rows but keeps its header)."""
    with open(path, newline="", encoding="utf8") as fh:
        reader = csv.DictReader(fh)
        return reader.fieldnames or [], list(reader)


def require_columns(path, cols, header):
    missing = [c for c in cols if c not in header]
    if missing:
        ep.die(f"{path.name} is missing the column(s) {missing}; it needs {list(cols)}")


def group_for(kind, slug, groups):
    """Subjects of a test per kind: pooled -> all, one group -> the group named as a _-token of the slug, else none."""
    if kind == "condition_pooled":
        return None, True
    if kind == "condition_group":
        tokens = set(slug.lower().split("_"))
        matches = [g for g in groups if isinstance(g, str) and g.lower() in tokens]
        if len(matches) != 1:
            ep.die(f"test {slug}: kind condition_group needs exactly one group from {groups} named as a '_'-separated "
                   f"token of the slug (found {matches}); rename the test or fix run_metadata groups")
        return matches[0], True
    return None, False


def read_run(spec):
    """Read the run folder and every named test folder into one internal form."""
    run_dir = Path(spec["data"])
    if not run_dir.is_dir():
        ep.die(f"run folder {run_dir} does not exist; set data to the folder holding time_axis.csv, channel_order.csv "
               "and run_metadata.json")
    ta_path, ch_path = run_dir / "time_axis.csv", run_dir / "channel_order.csv"
    for p in (ta_path, ch_path, run_dir / "run_metadata.json"):
        if not p.exists():
            ep.die(f"{p} is missing; the run folder needs time_axis.csv, channel_order.csv, run_metadata.json and "
                   "input_manifest.csv")
    header, rows = read_csv(ta_path)
    require_columns(ta_path, ("time_index", "time_ms"), header)
    times_ms = np.array([float(r["time_ms"]) for r in rows], dtype=float)
    header, rows = read_csv(ch_path)
    require_columns(ch_path, ("channel_index", "channel"), header)
    ch_names = [r["channel"] for r in rows]
    meta = json.loads((run_dir / "run_metadata.json").read_text(encoding="utf8"))
    for key in ("groups", "conditions", "difference_definition"):
        if key not in meta:
            ep.die(f"run_metadata.json is missing the key {key!r}; it needs groups, conditions and difference_definition")
    n_t, n_ch = len(times_ms), len(ch_names)
    labels = spec.get("labels", {})
    tests = []
    for slug in spec["tests"]:
        folder = run_dir / slug
        if not folder.is_dir():
            avail = sorted(p.name for p in run_dir.iterdir() if p.is_dir())
            ep.die(f"test folder {slug} not found under {run_dir}; available test folders: {avail}")
        for name in ("observed_statistic.npy", "significant_cluster_union_mask.npy", "test_metadata.json",
                     "cluster_summary_significant.csv"):
            if not (folder / name).exists():
                ep.die(f"test {slug}: {name} is missing from {folder}")
        tmeta = json.loads((folder / "test_metadata.json").read_text(encoding="utf8"))
        if tmeta.get("statistic") not in ("t", "F"):
            ep.die(f"test {slug}: test_metadata statistic must be 't' or 'F' (got {tmeta.get('statistic')!r})")
        stat = np.load(folder / "observed_statistic.npy")
        mask = np.load(folder / "significant_cluster_union_mask.npy").astype(bool)
        if stat.shape != (n_t, n_ch) or mask.shape != (n_t, n_ch):
            ep.die(f"test {slug}: observed_statistic {stat.shape} and mask {mask.shape} must both be "
                   f"(len(time_axis), len(channel_order)) = {(n_t, n_ch)}")
        header, rows = read_csv(folder / "cluster_summary_significant.csv")
        require_columns(folder / "cluster_summary_significant.csv",
                        ("cluster_id", "p_cluster", "time_start_ms", "time_end_ms", "channels"), header)
        clusters = [dict(cluster_id=int(r["cluster_id"]), p_cluster=float(r["p_cluster"]),
                         time_start_ms=float(r["time_start_ms"]), time_end_ms=float(r["time_end_ms"]),
                         channels=[c.strip() for c in r["channels"].split(";") if c.strip()]) for r in rows]
        group, has_diff = group_for(tmeta.get("kind"), slug, meta["groups"])
        tests.append(dict(slug=slug, label=labels.get(slug, tmeta.get("name", slug)), meta=tmeta, stat=stat,
                          mask=mask, clusters=clusters, group=group, has_diff=has_diff))
    if spec.get("color", "stat") == "uv":
        for t in tests:
            if not t["has_diff"]:
                kind = t["meta"].get("kind")
                ep.die(f'test {t["slug"]} (kind {kind}) has no single difference wave; use color "stat"')
    return dict(times_ms=times_ms, ch_names=ch_names, meta=meta, tests=tests)


def read_manifest(run_dir):
    """Rows of input_manifest.csv and the ancestor folder the file column is relative to."""
    path = run_dir / "input_manifest.csv"
    if not path.exists():
        ep.die(f"{path} is missing; the run folder needs input_manifest.csv")
    header, rows = read_csv(path)
    require_columns(path, ("group", "condition", "participant_id", "file", "nave"), header)
    if not rows:
        ep.die("input_manifest.csv has no rows; it lists the per-subject files the run used")
    first = rows[0]["file"]
    root = next((r for r in [run_dir] + list(run_dir.parents) if (r / first).exists()), None)
    if root is None:
        ep.die(f"cannot find the manifest root: no folder from {run_dir} up to its parents holds {first!r}; the file "
               "column must be relative to an ancestor folder of the run folder")
    return rows, root


def picked_info(info, ch_names, source):
    """Channel order of the result files; a missing channel stops."""
    missing = [c for c in ch_names if c not in info.ch_names]
    if missing:
        ep.die(f"{source}: evoked file is missing channel(s) {missing}; the run's channel_order.csv names channels the "
               "file does not have")
    return mne.pick_info(info, [info.ch_names.index(c) for c in ch_names])


def diff_uv(run, test, run_dir):
    """Grand-average A − B µV difference (n_times, n_ch) for one test, the number of subjects and the topomap info."""
    meta = run["meta"]
    conds = meta["conditions"]
    m = re.match(r"^\s*(\S+)\s+minus\s+(\S+)", meta.get("difference_definition") or "")
    if not m:
        ep.die(f"cannot read run_metadata difference_definition {meta.get('difference_definition')!r}; it must read "
               "like 'NoGO minus GO'")
    a, b = m.group(1), m.group(2)
    for c in (a, b):
        if c not in conds:
            ep.die(f"condition {c!r} from difference_definition is not one of run_metadata conditions {conds}")
    rows, root = read_manifest(run_dir)
    kind = test["meta"].get("kind")
    if kind == "condition_pooled":
        sel = rows
    elif kind == "condition_group":
        sel = [r for r in rows if r["group"] == test["group"]]
    else:
        ep.die(f'test {test["slug"]} (kind {kind}) has no single difference wave; use color "stat"')
    by_id = {}
    for r in sel:
        by_id.setdefault(r["participant_id"], {})[r["condition"]] = r
    ids = sorted(by_id)
    for pid in ids:
        if a not in by_id[pid] or b not in by_id[pid]:
            ep.die(f"participant {pid} is missing a {a!r} or {b!r} file in input_manifest.csv; both are needed for "
                   f"{a} minus {b}")
    ch_names, times_ms = run["ch_names"], run["times_ms"]

    def sampled(ev, fname):
        """(n_ch, n_times) µV of `ev` at the run's channels and result times; stops on a mismatch."""
        missing = [c for c in ch_names if c not in ev.ch_names]
        if missing:
            ep.die(f"{fname}: evoked file is missing channel(s) {missing}; the run's channel_order.csv names channels "
                   "the file does not have")
        idx = [ev.ch_names.index(c) for c in ch_names]
        d = np.abs(ev.times[None, :] * 1000.0 - times_ms[:, None])
        worst, half = float(d.min(1).max()), 0.5 / ev.info["sfreq"] * 1000.0
        if worst > half:
            ep.die(f"{fname}: result times lie up to {worst:.3f} ms off the evoked samples (half a sample is "
                   f"{half:.3f} ms at {ev.info['sfreq']:g} Hz); the result and the evoked files do not share a time "
                   "base")
        return ev.data[idx][:, d.argmin(1)] * 1e6

    total, n_subj, info = None, 0, None
    for pid in ids:
        file_a, file_b = by_id[pid][a]["file"], by_id[pid][b]["file"]
        ev_a = mne.read_evokeds(root / file_a, verbose="error")[0]
        ev_b = mne.read_evokeds(root / file_b, verbose="error")[0]
        if info is None:
            info = picked_info(ev_a.info, ch_names, file_a)
        diff = sampled(ev_a, file_a) - sampled(ev_b, file_b)  # µV
        total = diff if total is None else total + diff
        n_subj += 1
    return (total / n_subj).T, n_subj, info


def first_info(run, run_dir):
    """Topomap info from the first manifest file (a run whose tests have no µV difference at all)."""
    rows, root = read_manifest(run_dir)
    ev = mne.read_evokeds(root / rows[0]["file"], verbose="error")[0]
    return picked_info(ev.info, run["ch_names"], rows[0]["file"])


def write_run_json(out, spec, records, layout_issues, size_mm):
    data = dict(
        spec=spec,
        tests=records,
        layout_issues=layout_issues,
        code_md5=hashlib.md5(Path(__file__).read_bytes()).hexdigest(),
        versions=dict(mne=mne.__version__, matplotlib=matplotlib.__version__, numpy=np.__version__),
        size_mm=size_mm,
        qa="PENDING: the agent records the visual QA result here after checking the PNG",
    )
    Path(f"{out}_run.json").write_text(json.dumps(data, indent=1, ensure_ascii=False, allow_nan=False), encoding="utf8")


def write_caption(out, spec, run, tests):
    display = spec.get("display", "masked")
    mode = ("only samples in significant clusters are coloured" if display == "masked"
            else "full map, significant samples outlined")
    topo_mode = spec.get("topo", "bins")
    topo_txt = (f"{spec.get('topo_bin_ms', 100):g} ms bins" if topo_mode == "bins"
                else "one map per significant cluster window")
    lines = [
        f"# Caption for {out.name}",
        "",
        f"- **Display**: {mode}",
        f"- **Topomaps**: {topo_txt}",
        "- **Channel marker**: white dots: channels in a significant cluster within the map's time range",
    ]
    for t in tests:
        m = t["meta"]
        if t["clusters"]:
            cl = "; ".join(f"{c['cluster_id']} (p={c['p_cluster']:g}, {c['time_start_ms']:g}–{c['time_end_ms']:g} ms)"
                           for c in t["clusters"])
        else:
            cl = "no significant cluster"
        lines.append(f"- **{t['label']}**: statistic {m['statistic']} ({m['tail']}), cluster-forming threshold "
                     f"{m['cluster_forming_threshold']:g}, {m['n_permutations']} permutations, cluster-level alpha "
                     f"{m['cluster_level_alpha']:g}; significant clusters: {cl}")
        if t["has_diff"]:
            lines.append(f"- **µV maps — {t['label']}**: {run['meta']['difference_definition']} (N = {t['n_subj']})")
    if spec.get("claim"):
        lines.append(f"- **Claim**: {spec['claim']}")
    lines.append("")
    Path(f"{out}_caption.md").write_text("\n".join(lines), encoding="utf8")


def plot(spec):
    check_spec(spec)
    plt.rcParams.update(ep.STYLE)
    run = read_run(spec)
    times, ch_names, tests = run["times_ms"], run["ch_names"], run["tests"]
    run_dir = Path(spec["data"])
    color, display, topo_mode = spec.get("color", "stat"), spec.get("display", "masked"), spec.get("topo", "bins")
    step = float(spec.get("topo_bin_ms", 100))
    n_ch = len(ch_names)

    info = None
    for t in tests:
        if t["has_diff"]:
            uv, n_subj, test_info = diff_uv(run, t, run_dir)
            t["uv"], t["n_subj"] = uv, n_subj
            if info is None:
                info = test_info
        else:
            t["uv"], t["n_subj"] = None, None
    if info is None:
        info = first_info(run, run_dir)
    sphere = ep.common_sphere(info)

    W = float(spec.get("width_mm", 180))
    left, right, gap = 14.0, 14.0, 16.0
    n_col = len(tests)
    cw = (W - left - right - (n_col - 1) * gap) / n_col
    raster_h = max(60.0, 1.5 * n_ch)
    n_row = max(1, int((cw + 2) // (11 + 2)))  # ≥ 11 mm maps with 2 mm gaps fill the column
    map_mm = (cw - (n_row - 1) * 2.0) / n_row
    step_h = map_mm + 7.0

    def bins_of_times():
        nbins = int(np.ceil((times[-1] - times[0]) / step))
        edges = times[0] + step * np.arange(nbins + 1)
        masks = []
        for i in range(nbins):
            m = (times >= edges[i] - 1e-3) & (times < edges[i + 1] - 1e-3)
            if i == nbins - 1:
                m |= times >= times[-1] - 1e-3
            if m.any():
                masks.append(m)
        return masks

    def maps_of(t):
        q = t["uv"] if t["uv"] is not None else t["stat"]
        out = []
        if topo_mode == "bins":
            for m in bins_of_times():
                out.append((q[m].mean(0), t["mask"][m].any(0), f"{times[m][0]:.0f}–{times[m][-1]:.0f} ms"))
        else:
            for c in t["clusters"]:
                m = ep.sample_mask(times, c["time_start_ms"], c["time_end_ms"])
                out.append((q[m].mean(0), np.array([ch in c["channels"] for ch in ch_names]),
                            f"{c['time_start_ms']:g}–{c['time_end_ms']:g} ms"))
        return out

    all_maps = {t["slug"]: maps_of(t) for t in tests}
    n_map_rows = max(1, max(int(np.ceil(max(1, len(all_maps[t["slug"]])) / n_row)) for t in tests))
    H = float(spec.get("height_mm") or (12 + raster_h + 14 + n_map_rows * step_h + 4))

    raster_top, raster_bottom = H - 12.0, H - 12.0 - raster_h
    maps_top = raster_bottom - 14.0
    fig = plt.figure(figsize=(W * ep.MM, H * ep.MM))

    records = {}
    for i, t in enumerate(tests):
        x_left = left + i * (cw + gap)
        stat_name = t["meta"]["statistic"]
        values = t["uv"] if color == "uv" else t["stat"]
        mask = t["mask"]
        sel = values[mask] if display == "masked" else values
        peak = float(np.abs(sel).max()) if sel.size else 0.0
        v = float(np.ceil(peak * 10) / 10) or 1.0
        if color == "stat" and stat_name == "F":
            cmap, vmin, vmax = "Reds", 0.0, v
        else:
            cmap, vmin, vmax = "RdBu_r", -v, v

        ax = fig.add_axes([x_left / W, raster_bottom / H, cw / W, raster_h / H])
        dt = float(times[1] - times[0]) if len(times) > 1 else 1.0
        extent = [times[0] - dt / 2, times[-1] + dt / 2, n_ch - 0.5, -0.5]
        if display == "masked":
            cmap_obj = plt.get_cmap(cmap).copy()
            cmap_obj.set_bad("white")
            im = ax.imshow(np.ma.masked_where(~mask.T, values.T), aspect="auto", origin="upper", extent=extent,
                           interpolation="nearest", cmap=cmap_obj, vmin=vmin, vmax=vmax, rasterized=True)
        else:
            im = ax.imshow(values.T, aspect="auto", origin="upper", extent=extent, interpolation="nearest",
                           cmap=cmap, vmin=vmin, vmax=vmax, rasterized=True)
            ax.contour(times, np.arange(n_ch), mask.T.astype(float), levels=[0.5], colors="black", linewidths=0.4)
        ax.set_yticks(np.arange(n_ch))
        ax.set_yticklabels(ch_names, fontsize=4)
        if i == 0:
            ax.set_ylabel("Channel")
        xt, labs, _ = ep.x_ticks(ax, fig, times[0], times[-1], zero=True)
        ax.set_xticks(xt)
        ax.set_xticklabels(labs)
        ax.set_xlabel("Time (ms)")
        ax.set_title(t["label"], fontsize=7)
        ep.letter(ax, i)

        cax = fig.add_axes([(x_left + cw + 3.0) / W, raster_bottom / H, 2.0 / W, raster_h / H])
        cb = fig.colorbar(im, cax=cax)
        ticks = [0.0, v] if (color == "stat" and stat_name == "F") else [-v, 0.0, v]
        cb.set_ticks(ticks)
        cb.set_ticklabels([f"{x:g}".replace("-", "−") for x in ticks])
        cb.ax.tick_params(labelsize=5, width=0.4, length=2)
        cb.ax.set_title("µV" if color == "uv" else stat_name, fontsize=6, pad=2)
        cb.outline.set_linewidth(0.4)

        maps = all_maps[t["slug"]]
        has_uv = t["uv"] is not None
        if maps:
            sensor = max(float(np.abs(vec).max()) for vec, _, _ in maps)
            interp = max(ep.interp_peak(vec, info, sphere) for vec, _, _ in maps)
            vt = float(np.ceil(max(sensor, interp) * 10) / 10) or 1.0
            tcmap, tlo, thi = ("RdBu_r", -vt, vt) if has_uv else ("Reds", 0.0, vt)
            last_im = None
            for k, (vec, marked, lab) in enumerate(maps):
                r, c = divmod(k, n_row)
                row_top = maps_top - r * step_h
                map_x = x_left + c * (map_mm + 2.0)
                tax = fig.add_axes([map_x / W, (row_top - map_mm) / H, map_mm / W, map_mm / H])
                last_im, _ = mne.viz.plot_topomap(
                    vec, info, axes=tax, show=False, cmap=tcmap, vlim=(tlo, thi),
                    contours=np.linspace(tlo, thi, ep.TOPO["contours"] + 1), sensors=False,
                    extrapolate=ep.TOPO["extrapolate"], image_interp=ep.TOPO["image_interp"], sphere=sphere,
                    mask=marked, mask_params=dict(marker="o", markerfacecolor="white", markeredgecolor="black",
                                                  markeredgewidth=0.25, markersize=1.2))
                tax.text(0.5, -0.05, lab, transform=tax.transAxes, ha="center", va="top", fontsize=5)
            block_bottom = maps_top - n_map_rows * step_h
            cax_t = fig.add_axes([(x_left + cw + 3.0) / W, block_bottom / H, 2.0 / W, (maps_top - block_bottom) / H])
            cb_t = fig.colorbar(last_im, cax=cax_t)
            tticks = [-vt, 0.0, vt] if has_uv else [0.0, vt]
            cb_t.set_ticks(tticks)
            cb_t.set_ticklabels([f"{x:g}".replace("-", "−") for x in tticks])
            cb_t.ax.tick_params(labelsize=5, width=0.4, length=2)
            cb_t.ax.set_title("µV" if has_uv else stat_name, fontsize=6, pad=2)
            cb_t.outline.set_linewidth(0.4)
            topo_limits = dict(v=vt, vmin=tlo, vmax=thi, cmap=tcmap, sensor_max=sensor, interp_max=interp)
        else:
            topo_limits = None
            fig.text((x_left + map_mm / 2) / W, (maps_top - map_mm / 2) / H, "no significant cluster",
                     ha="center", va="center", fontsize=5)
        records[t["slug"]] = dict(metadata=t["meta"], n_subjects=t["n_subj"],
                                  color_limits=dict(raster=dict(v=v, vmin=vmin, vmax=vmax, cmap=cmap), topo=topo_limits))

    nums = [re.match(r"\d+", s).group(0) if re.match(r"\d+", s) else s for s in spec["tests"]]
    topo_part = f"bins{step:g}ms" if topo_mode == "bins" else "clusters"
    stem = f"cluster_{color}-{display}_{'-'.join('t' + n for n in nums)}_topo-{topo_part}"
    if spec.get("time_locked_to"):
        stem += f"_lock-{ep.safe(spec['time_locked_to'])}"
    out = ep.versioned(ep.out_root(spec) / "cluster", stem)
    issues = ep.report_layout(fig, out.name)
    fig.savefig(f"{out}.png", dpi=600)
    fig.savefig(f"{out}.svg")
    plt.close(fig)
    write_run_json(out, spec, records, issues, [W, H])
    write_caption(out, spec, run, tests)
    ep.archive(out)
    print("wrote", f"{out}.png/.svg")
    return out


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) < 3 or sys.argv[1] != "plot":
        ep.die("usage: python cluster_plot.py plot <spec.json>")
    plot(ep.read_spec(sys.argv[2]))
