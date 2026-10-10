"""Cluster-permutation result module for brain-plot (agent guide references/cluster.md).

    python cluster_plot.py plot <spec.json>

Reads a saved MNE spatio-temporal cluster run and draws one figure per test: a channel × time raster of the test
statistic (only significant samples coloured by default) on the left, the µV-difference topomaps in a 2-column grid
on the right. Raster rows are grouped left / midline / right (or kept in file order). Draws only — it never computes a
test, threshold or p-value; the only computed number is the µV mean difference. Outputs go to
brain_plot_<data folder>/cluster/ next to the data folder, versioned (rules O1–O3).
"""
import csv
import hashlib
import json
import re
import sys
import textwrap
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mne
import numpy as np

import erp_plot as ep

REQUIRED = {"data", "tests"}
OPTIONAL = {"labels", "color", "display", "topo", "topo_bin_ms", "channel_order", "width_mm", "height_mm",
            "time_locked_to", "claim", "layout"}


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
    if spec.get("channel_order", "lmr") not in ("lmr", "file"):
        ep.die(f"channel_order must be 'lmr' or 'file' (got {spec['channel_order']!r}); 'lmr' orders the raster rows "
               "left / midline / right, 'file' keeps the result-file order")
    layout = spec.get("layout", "side")
    if layout not in ("side", "columns"):
        ep.die(f"layout must be 'side' or 'columns' (got {spec['layout']!r}); 'side' draws one figure per test, "
               "'columns' one figure with a column per test")
    if layout == "columns":
        if spec.get("channel_order", "lmr") != "lmr":
            ep.die('layout "columns" splits the raster by hemisphere; set channel_order to "lmr"')
        if len(tests) > 3:
            ep.die(f'layout "columns" draws one column per test; it holds at most 3 tests (got {len(tests)})')
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


def hemi_by_name(name):
    """Hemisphere group from the last character of a channel name, as MNE
    `make_1020_channel_selections(midline="12z")` reads it: ending in 1, 2 or z (lower-cased) is "Midline", another
    odd digit "Left", another even digit "Right"; None when the character is neither (the caller then uses the
    position rule)."""
    ch = name[-1].lower()
    if ch in "12z":
        return "Midline"
    if ch.isdigit():
        return "Left" if int(ch) % 2 else "Right"
    return None


def channel_rows(info, ch_names, mode, sphere):
    """Raster row order for one figure: `order` holds the channel indices (into `ch_names`) top to bottom; `rows` adds
    the tick label of every other channel, its channel index (None on a blank separator row) and the group name.
    mode "file" keeps the result-file order with no groups; "lmr" groups left / midline / right by the channel name
    (MNE `make_1020_channel_selections(midline="12z")`: names ending in 1, 2 or z are Midline, other odd digits Left,
    other even digits Right; a name ending in neither falls back to |x| ≤ 0.1 × max|x| as midline) and sorts each
    group anterior → posterior; a blank row separates the groups."""
    if mode == "file":
        rows = [(ch_names[i] if i % 2 == 0 else None, i, None) for i in range(len(ch_names))]
        return list(range(len(ch_names))), rows
    from mne.channels.layout import _find_topomap_coords
    pos = _find_topomap_coords(info, picks=np.arange(len(info.ch_names)), sphere=sphere)
    x, y = pos[:, 0], pos[:, 1]
    tol = 0.1 * float(np.abs(x).max())
    by_name = {"Left": [], "Midline": [], "Right": []}
    for i in range(len(ch_names)):
        g = hemi_by_name(ch_names[i])
        if g is None:
            g = "Left" if x[i] < -tol else ("Right" if x[i] > tol else "Midline")
        by_name[g].append(i)
    groups = [(name, by_name[name]) for name in ("Left", "Midline", "Right")]
    order, rows = [], []
    for name, idx in groups:
        if not idx:
            continue
        if order:
            rows.append((None, None, None))
        idx.sort(key=lambda i: -y[i])
        for k, i in enumerate(idx):
            order.append(i)
            rows.append((ch_names[i] if k % 2 == 0 else None, i, name))
    return order, rows


def write_run_json(out, spec, tests, layout_issues, size_mm, layout=None):
    data = dict(
        spec=spec,
        tests=tests,
        layout_issues=layout_issues,
        code_md5=hashlib.md5(Path(__file__).read_bytes()).hexdigest(),
        versions=dict(mne=mne.__version__, matplotlib=matplotlib.__version__, numpy=np.__version__),
        size_mm=size_mm,
        qa="PENDING: the agent records the visual QA result here after checking the PNG",
    )
    if layout is not None:
        data["layout"] = layout
    Path(f"{out}_run.json").write_text(json.dumps(data, indent=1, ensure_ascii=False, allow_nan=False), encoding="utf8")


def write_caption(out, spec, run, tests):
    """Caption facts for one figure: the figure-level lines once, then the statistic (and µV-map) line of every test in
    order (the `side` layout passes a single test)."""
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
    for test in tests:
        m = test["meta"]
        if test["clusters"]:
            cl = "; ".join(f"{c['cluster_id']} (p={c['p_cluster']:g}, {c['time_start_ms']:g}–{c['time_end_ms']:g} ms)"
                           for c in test["clusters"])
        else:
            cl = "no significant cluster"
        lines.append(f"- **{test['label']}**: statistic {m['statistic']} ({m['tail']}), cluster-forming threshold "
                     f"{m['cluster_forming_threshold']:g}, {m['n_permutations']} permutations, cluster-level alpha "
                     f"{m['cluster_level_alpha']:g}; significant clusters: {cl}")
        if test["has_diff"]:
            lines.append(f"- **µV maps — {test['label']}**: {run['meta']['difference_definition']} "
                         f"(N = {test['n_subj']})")
    if spec.get("claim"):
        lines.append(f"- **Claim**: {spec['claim']}")
    lines.append("")
    Path(f"{out}_caption.md").write_text("\n".join(lines), encoding="utf8")


def bins_of_times(times, step):
    """Half-open sample masks [a, a + step) of the result time axis (the last bin closed at the last sample)."""
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


def maps_of(t, times, ch_names, topo_mode, bins, uv):
    """(vector, marked channels, time label) per topomap of one test: mean over each time bin, or over each significant
    cluster window. `uv` picks the µV difference where it exists, else the statistic."""
    q = t["uv"] if uv else t["stat"]
    out = []
    if topo_mode == "bins":
        for m in bins:
            out.append((q[m].mean(0), t["mask"][m].any(0), f"{times[m][0]:.0f}–{times[m][-1]:.0f} ms"))
    else:
        for c in t["clusters"]:
            m = ep.sample_mask(times, c["time_start_ms"], c["time_end_ms"])
            out.append((q[m].mean(0), np.array([ch in c["channels"] for ch in ch_names]),
                        f"{c['time_start_ms']:g}–{c['time_end_ms']:g} ms"))
    return out


def raster_limits(t, color, display):
    """(v, vmin, vmax, cmap name) of one test's raster: v is the colour half-range from the shown values, the colormap
    and limits follow the colour / the statistic (Reds for F, RdBu_r otherwise)."""
    values = t["uv"] if color == "uv" else t["stat"]
    sel = values[t["mask"]] if display == "masked" else values
    peak = float(np.abs(sel).max()) if sel.size else 0.0
    v = float(np.ceil(peak * 10) / 10) or 1.0
    if color == "stat" and t["meta"]["statistic"] == "F":
        return v, 0.0, v, "Reds"
    return v, -v, v, "RdBu_r"


def raster_array(t, rows, values):
    """(masked (n_rows, n_times) array, significance mask) of `values` for `rows` (label, channel index, group); blank
    separator rows stay NaN. `rows` is the whole raster for `side`, one hemisphere group for `columns`."""
    arr = np.full((len(rows), values.shape[0]), np.nan)
    sig = np.zeros((len(rows), values.shape[0]), dtype=bool)
    for k, (_, i, _) in enumerate(rows):
        if i is not None:
            arr[k], sig[k] = values[:, i], t["mask"][:, i]
    return np.ma.masked_invalid(arr), sig


def draw_raster(ax, arr, sig, display, times, cmap, vmin, vmax):
    """Raster image of one block on ax (masked colours significant samples only, contour outlines them on the full map);
    returns the image."""
    n_rows = arr.shape[0]
    dt = float(times[1] - times[0]) if len(times) > 1 else 1.0
    extent = [times[0] - dt / 2, times[-1] + dt / 2, n_rows - 0.5, -0.5]
    if display == "masked":
        im = ax.imshow(np.ma.masked_where(~sig, arr), aspect="auto", origin="upper", extent=extent,
                       interpolation="nearest", cmap=cmap, vmin=vmin, vmax=vmax, rasterized=True)
    else:
        im = ax.imshow(arr, aspect="auto", origin="upper", extent=extent, interpolation="nearest",
                       cmap=cmap, vmin=vmin, vmax=vmax, rasterized=True)
        ax.contour(times, np.arange(n_rows), sig.astype(float), levels=[0.5], colors="black", linewidths=0.4)
    return im


def colorbar(fig, rect_mm, im, ticks, title, W, H):
    """Colour bar for `im` in the [x, y, width, height] mm rectangle `rect_mm`; `ticks` are labelled, `title` sits above
    the bar."""
    cax = fig.add_axes([rect_mm[0] / W, rect_mm[1] / H, rect_mm[2] / W, rect_mm[3] / H])
    cb = fig.colorbar(im, cax=cax)
    cb.set_ticks(ticks)
    cb.set_ticklabels([f"{x:g}".replace("-", "−") for x in ticks])
    cb.ax.tick_params(labelsize=5, width=0.4, length=2)
    cb.ax.set_title(title, fontsize=6, pad=2)
    cb.outline.set_linewidth(0.4)
    return cb


def topo_limits(maps, has_uv, info, sphere):
    """Shared topomap colour scale over `maps` (list of (vector, marked, label)): (vt, vmin, vmax, cmap, sensor peak,
    interpolated peak), µV (RdBu_r) when `has_uv` else the statistic (Reds)."""
    sensor = max(float(np.abs(vec).max()) for vec, _, _ in maps)
    interp = max(ep.interp_peak(vec, info, sphere) for vec, _, _ in maps)
    vt = float(np.ceil(max(sensor, interp) * 10) / 10) or 1.0
    cmap, lo, hi = ("RdBu_r", -vt, vt) if has_uv else ("Reds", 0.0, vt)
    return vt, lo, hi, cmap, sensor, interp


def draw_map(fig, rect_mm, vec, marked, lab, cmap, lo, hi, info, sphere, W, H):
    """One topomap in the [x, y, width, height] mm rectangle `rect_mm` with its time label under it; returns the
    image."""
    tax = fig.add_axes([rect_mm[0] / W, rect_mm[1] / H, rect_mm[2] / W, rect_mm[3] / H])
    im, _ = mne.viz.plot_topomap(
        vec, info, axes=tax, show=False, cmap=cmap, vlim=(lo, hi),
        contours=np.linspace(lo, hi, ep.TOPO["contours"] + 1), sensors=False,
        extrapolate=ep.TOPO["extrapolate"], image_interp=ep.TOPO["image_interp"], sphere=sphere,
        mask=marked, mask_params=dict(marker="o", markerfacecolor="white", markeredgecolor="black",
                                      markeredgewidth=0.25, markersize=1.2))
    tax.text(0.5, -0.05, lab, transform=tax.transAxes, ha="center", va="top", fontsize=5)
    return im


def row_label(label):
    """Topomap row label of the columns layout: drops "(N = …)" and wraps the ": "-split parts at 12 characters (N is
    in the raster column title)."""
    label = re.sub(r"\s*\(N\s*=\s*\d+\)", "", label)
    return "\n".join(line for part in label.split(": ", 1) for line in textwrap.wrap(part, 12))


def group_rows(rows):
    """The raster rows split into [(group name, rows)] at the blank separator rows (left / midline / right)."""
    groups = []
    for row in rows:
        if row[1] is None:
            continue
        if not groups or groups[-1][0] != row[2]:
            groups.append((row[2], []))
        groups[-1][1].append(row)
    return groups


def plot(spec):
    check_spec(spec)
    plt.rcParams.update(ep.STYLE)
    run = read_run(spec)
    times, ch_names, tests = run["times_ms"], run["ch_names"], run["tests"]
    run_dir = Path(spec["data"])
    color, display, topo_mode = spec.get("color", "stat"), spec.get("display", "masked"), spec.get("topo", "bins")
    step = float(spec.get("topo_bin_ms", 100))
    mode = spec.get("channel_order", "lmr")
    layout = spec.get("layout", "side")

    if layout == "columns" and color == "stat" and len({t["meta"]["statistic"] for t in tests}) > 1:
        ep.die('layout "columns" shares one colour scale; tests mix t and F')

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
    order, rows = channel_rows(info, ch_names, mode, sphere)

    bins = bins_of_times(times, step)
    has_uv_all = all(t["uv"] is not None for t in tests)
    for t in tests:
        use_uv = has_uv_all if layout == "columns" else t["uv"] is not None
        t["maps"] = maps_of(t, times, ch_names, topo_mode, bins, use_uv)

    topo_part = f"bins{step:g}ms" if topo_mode == "bins" else "clusters"
    if layout == "columns":
        return [plot_columns(spec, run, tests, rows, info, sphere, color, display, topo_part)]
    return plot_side(spec, run, tests, rows, info, sphere, color, display, topo_part)


def plot_side(spec, run, tests, rows, info, sphere, color, display, topo_part):
    """Today's layout, byte-for-byte unchanged: one figure per test (raster left, 2-column map grid right)."""
    times, ch_names = run["times_ms"], run["ch_names"]
    W = float(spec.get("width_mm", 180))
    raster_h, top_m, bottom_m = 100.0, 12.0, 14.0
    n_rows = len(rows)
    outs = []
    for t in tests:
        maps = t["maps"]
        has_uv = t["uv"] is not None
        if maps:
            n_cols = 1 if len(maps) == 1 else 2
            n_grid_rows = -(-len(maps) // n_cols)
            map_mm = min(24.0, (raster_h - n_grid_rows * 6.0) / n_grid_rows)
            maps_w = n_cols * map_mm + (n_cols - 1) * 3.0
        else:
            n_cols, n_grid_rows, map_mm, maps_w = 1, 0, 0.0, 0.0
        grid_h = n_grid_rows * (map_mm + 6.0)
        H = float(spec["height_mm"]) if spec.get("height_mm") else top_m + max(raster_h, grid_h) + bottom_m
        rw = W - 22.0 - 16.0 - maps_w - 14.0
        raster_bottom, maps_top = H - top_m - raster_h, H - top_m
        maps_left = W - maps_w - 14.0
        fig = plt.figure(figsize=(W * ep.MM, H * ep.MM))

        stat_name = t["meta"]["statistic"]
        v, vmin, vmax, cmap = raster_limits(t, color, display)
        arr, sig = raster_array(t, rows, t["uv"] if color == "uv" else t["stat"])
        cmap_obj = plt.get_cmap(cmap).copy()
        cmap_obj.set_bad("white")

        ax = fig.add_axes([22.0 / W, raster_bottom / H, rw / W, raster_h / H])
        im = draw_raster(ax, arr, sig, display, times, cmap_obj, vmin, vmax)
        ax.set_yticks(np.arange(n_rows))
        ax.set_yticklabels([lab or "" for lab, _, _ in rows], fontsize=5)
        xt, labs, _ = ep.x_ticks(ax, fig, times[0], times[-1], zero=True)
        ax.set_xticks(xt)
        ax.set_xticklabels(labs)
        ax.set_xlabel("Time (ms)")
        ax.set_title(t["label"], fontsize=7)
        ep.letter(ax, 0)
        ylo, yhi = ax.get_ylim()
        groups = {}
        for k, (_, i, g) in enumerate(rows):
            if i is not None:
                groups.setdefault(g, []).append(k)
        for g, ks in groups.items():
            ax.text(-15.0 / rw, (float(np.mean(ks)) - ylo) / (yhi - ylo), g, transform=ax.transAxes,
                    rotation=90, ha="center", va="center", fontsize=6)

        ticks = [0.0, v] if (color == "stat" and stat_name == "F") else [-v, 0.0, v]
        colorbar(fig, [22.0 + rw + 3.0, raster_bottom, 2.0, raster_h], im, ticks,
                 "µV" if color == "uv" else stat_name, W, H)

        if maps:
            vt, tlo, thi, tcmap, sensor, interp = topo_limits(maps, has_uv, info, sphere)
            last_im = None
            for k, (vec, marked, lab) in enumerate(maps):
                r, c = divmod(k, n_cols)
                row_top = maps_top - r * (map_mm + 6.0)
                map_x = maps_left + c * (map_mm + 3.0)
                last_im = draw_map(fig, [map_x, row_top - map_mm, map_mm, map_mm], vec, marked, lab,
                                   tcmap, tlo, thi, info, sphere, W, H)
                if k == 0:
                    ep.letter(last_im.axes, 1)
            tticks = [-vt, 0.0, vt] if has_uv else [0.0, vt]
            colorbar(fig, [maps_left + maps_w + 3.0, maps_top - grid_h, 2.0, grid_h], last_im, tticks,
                     "µV" if has_uv else stat_name, W, H)
            topo_rec = dict(v=vt, vmin=tlo, vmax=thi, cmap=tcmap, sensor_max=sensor, interp_max=interp)
        else:
            topo_rec = None
            fig.text(maps_left / W, (maps_top - map_mm / 2) / H, "no significant cluster",
                     ha="left", va="center", fontsize=5)
        record = dict(metadata=t["meta"], n_subjects=t["n_subj"],
                      color_limits=dict(raster=dict(v=v, vmin=vmin, vmax=vmax, cmap=cmap), topo=topo_rec))

        m = re.match(r"\d+", t["slug"])
        stem = f"cluster_{color}-{display}_t{m.group(0) if m else t['slug']}_topo-{topo_part}"
        if spec.get("time_locked_to"):
            stem += f"_lock-{ep.safe(spec['time_locked_to'])}"
        out = ep.versioned(ep.out_root(spec) / "cluster", stem)
        issues = ep.report_layout(fig, out.name)
        fig.savefig(f"{out}.png", dpi=600)
        fig.savefig(f"{out}.svg")
        plt.close(fig)
        write_run_json(out, spec, {t["slug"]: record}, issues, [W, H])
        write_caption(out, spec, run, [t])
        ep.archive(out)
        print("wrote", f"{out}.png/.svg")
        outs.append(out)
    return outs


def plot_columns(spec, run, tests, rows, info, sphere, color, display, topo_part):
    """The columns layout (card 2026-10-11): ONE figure, one column per test (three stacked hemisphere raster
    sub-panels, Left / Midline / Right) with a shared raster colour bar, then one row of topomaps per test with a shared
    map colour bar."""
    times = run["times_ms"]
    W = float(spec.get("width_mm", 180))
    n = len(tests)
    left_m, right_m, top_m = 20.0, 14.0, 12.0
    cw = (W - left_m - right_m - (n - 1) * 8.0) / n
    groups = group_rows(rows)
    h = 1.2 * max(len(gr) for _, gr in groups)
    sub_h = [h] * len(groups)
    raster_block = sum(sub_h) + 2.5 * (len(groups) - 1)

    rlims = [raster_limits(t, color, display) for t in tests]
    rv = max(lim[0] for lim in rlims)
    rcmap = rlims[0][3]
    rvmin, rvmax = (0.0, rv) if rcmap == "Reds" else (-rv, rv)
    stat_name = tests[0]["meta"]["statistic"] if color == "stat" else "µV"

    all_maps = [mp for t in tests for mp in t["maps"]]
    has_uv = all(t["uv"] is not None for t in tests)
    tlims = topo_limits(all_maps, has_uv, info, sphere) if all_maps else None
    n_maps = max((len(t["maps"]) for t in tests), default=0)
    map_mm = min(20.0, (W - left_m - right_m - (n_maps - 1) * 2.0) / n_maps) if n_maps else 0.0

    H = (float(spec["height_mm"]) if spec.get("height_mm")
         else top_m + raster_block + 10.0 + 6.0 + n * (map_mm + 11.0) + 4.0)
    fig = plt.figure(figsize=(W * ep.MM, H * ep.MM))

    def rect(x, y_top, w, h):  # [x, y_top, w, h] mm from the top -> figure fractions (bottom origin)
        return [x / W, (H - y_top - h) / H, w / W, h / H]

    gtop, y = [], top_m
    for h in sub_h:
        gtop.append(y)
        y += h + 2.5

    axs = [[fig.add_axes(rect(left_m + c * (cw + 8.0), gtop[gi], cw, sub_h[gi])) for gi in range(len(groups))]
           for c in range(n)]
    xt, labs, _ = ep.x_ticks(axs[0][-1], fig, times[0], times[-1], zero=True)

    cmap_obj = plt.get_cmap(rcmap).copy()
    cmap_obj.set_bad("white")
    raster_im = None
    for c, t in enumerate(tests):
        values = t["uv"] if color == "uv" else t["stat"]
        for gi, (gname, grows) in enumerate(groups):
            ax = axs[c][gi]
            arr, sig = raster_array(t, grows, values)
            raster_im = draw_raster(ax, arr, sig, display, times, cmap_obj, rvmin, rvmax)
            ax.set_yticks(np.arange(len(grows)))
            ax.set_yticklabels([lab or "" for lab, _, _ in grows], fontsize=5)
            ax.set_xticks(xt)
            ax.set_xticklabels(labs if gi == len(groups) - 1 else [])
            if gi == len(groups) - 1:
                ax.set_xlabel("Time (ms)")
            if gi == 0:
                ax.set_title(t["label"], fontsize=7)
                ep.letter(ax, c)
            if c == 0:
                yc = gtop[gi] + sub_h[gi] / 2.0
                fig.text((left_m - 12.0) / W, (H - yc) / H, gname, rotation=90, ha="center", va="center", fontsize=6)

    colorbar(fig, [W - right_m + 3.0, H - top_m - raster_block, 2.0, raster_block], raster_im,
             [0.0, rv] if rcmap == "Reds" else [-rv, 0.0, rv], stat_name, W, H)

    topo_top = top_m + raster_block + 10.0 + 6.0
    map_bar_im = None
    for r, t in enumerate(tests):
        y_top = topo_top + r * (map_mm + 11.0)
        if not t["maps"]:
            fig.text(left_m / W, (H - (y_top + map_mm / 2.0)) / H, "no significant cluster",
                     ha="left", va="center", fontsize=5)
            continue
        vt, tlo, thi, tcmap = tlims[0], tlims[1], tlims[2], tlims[3]
        fig.text((left_m - 2.0) / 2.0 / W, (H - (y_top + map_mm / 2.0)) / H, row_label(t["label"]),
                 ha="center", va="center", multialignment="center", fontsize=6)
        for k, (vec, marked, lab) in enumerate(t["maps"]):
            im = draw_map(fig, [left_m + k * (map_mm + 2.0), H - y_top - map_mm, map_mm, map_mm], vec, marked, lab,
                          tcmap, tlo, thi, info, sphere, W, H)
            map_bar_im = im
            if k == 0:
                ep.letter(im.axes, n + r)
    if tlims:
        map_bar_h = (n - 1) * (map_mm + 11.0) + map_mm
        colorbar(fig, [W - right_m + 3.0, H - topo_top - map_bar_h, 2.0, map_bar_h], map_bar_im,
                 [-tlims[0], 0.0, tlims[0]] if has_uv else [0.0, tlims[0]],
                 "µV" if has_uv else stat_name, W, H)

    topo_rec = (dict(v=tlims[0], vmin=tlims[1], vmax=tlims[2], cmap=tlims[3], sensor_max=tlims[4],
                     interp_max=tlims[5]) if tlims else None)
    records = {t["slug"]: dict(metadata=t["meta"], n_subjects=t["n_subj"],
                               color_limits=dict(raster=dict(v=rv, vmin=rvmin, vmax=rvmax, cmap=rcmap),
                                                 topo=topo_rec)) for t in tests}
    nums = [m.group(0) if (m := re.match(r"\d+", t["slug"])) else t["slug"] for t in tests]
    stem = f"cluster_{color}-{display}_columns_t{'-t'.join(nums)}_topo-{topo_part}"
    if spec.get("time_locked_to"):
        stem += f"_lock-{ep.safe(spec['time_locked_to'])}"
    out = ep.versioned(ep.out_root(spec) / "cluster", stem)
    issues = ep.report_layout(fig, out.name)
    fig.savefig(f"{out}.png", dpi=600)
    fig.savefig(f"{out}.svg")
    plt.close(fig)
    write_run_json(out, spec, records, issues, [W, H], layout="columns")
    write_caption(out, spec, run, tests)
    ep.archive(out)
    print("wrote", f"{out}.png/.svg")
    return out


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) < 3 or sys.argv[1] != "plot":
        ep.die("usage: python cluster_plot.py plot <spec.json>")
    plot(ep.read_spec(sys.argv[2]))
