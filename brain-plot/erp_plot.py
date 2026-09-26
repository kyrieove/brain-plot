"""Publication ERP figures (waveforms + scalp topographies) from per-subject MNE files.

    python erp_plot.py inspect <data_dir>      # facts the agent needs before the interview
    python erp_plot.py windows <spec.json>     # candidate windows from the waveform collapsed over groups and conditions
    python erp_plot.py plot    <spec.json>     # one figure per component: .png/.svg + _caption.md + _run.json
    python erp_plot.py explore <spec.json>     # overview before windows are known

<data_dir> holds one *-epo.fif or *-ave.fif per subject; sub-folders are groups. The subject ID is the file
name up to the first "_" or "-". Input must be preprocessed EEG potentials (no bad channels left, one common
channel set, time grid, baseline, filter and reference); the loader stops on any mismatch. The spec format and
the rules this script enforces are in references/spec.md and references/rules.md. Outputs go to brain-plot/ next to
the data folder (rules O1–O3).
"""
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
from matplotlib.gridspec import GridSpec
from matplotlib.ticker import MaxNLocator
from scipy.signal import find_peaks, peak_widths

LOADER_VERSION = 3
MM = 1 / 25.4
TWO_COLORS = ["#1b7f79", "#e0533d"]
OKABE_ITO = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#56B4E9"]
GROUP_COLORS = ["#000000"] + OKABE_ITO  # first group in spec["groups"] (the reference group) is black
STYLE = {
    "font.family": "sans-serif", "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 7, "axes.titlesize": 7, "axes.labelsize": 7, "xtick.labelsize": 6, "ytick.labelsize": 6,
    "legend.fontsize": 6, "legend.frameon": False, "axes.linewidth": 0.6, "xtick.major.width": 0.6,
    "ytick.major.width": 0.6, "xtick.major.size": 2.5, "ytick.major.size": 2.5, "lines.linewidth": 1.0,
    "axes.spines.top": False, "axes.spines.right": False, "pdf.fonttype": 42, "svg.fonttype": "none",
}
REQUIRED = {"data", "conditions", "claim", "key_comparison", "time_locked_to", "reference"}
OPTIONAL = {"kind", "groups", "exclude", "query", "overlay", "ordered", "colors", "xlim_ms", "polarity", "width_mm",
            "height_mm", "cmap", "stats_note", "group_by", "linestyles", "error", "components", "channels", "layout"}
COMPONENT_KEYS = {"name", "channels", "tmin_ms", "tmax_ms", "window_source"}
TOPO = dict(contours=8, extrapolate="head", image_interp="cubic")  # recorded in every caption; sphere: common_sphere()


def die(msg):
    sys.exit(f"ERROR: {msg}")


# ---------- spec ----------
def check_spec(spec):
    keys = set(spec)
    if REQUIRED - keys:
        die(f"spec is missing {sorted(REQUIRED - keys)}")
    if keys - REQUIRED - OPTIONAL:
        die(f"unsupported spec keys {sorted(keys - REQUIRED - OPTIONAL)} (see references/spec.md)")
    if spec.get("overlay", "groups") not in ("groups", "conditions"):
        die("overlay must be 'groups' or 'conditions'")
    if "group_by" in spec and not text(spec["group_by"]):
        die("group_by must be a metadata column name")
    if spec.get("kind", "combo") not in ("combo", "erp", "topo"):
        die("kind must be 'combo', 'erp' or 'topo'")
    if spec.get("error", "none") not in ("none", "sem"):
        die("error must be 'none' or 'sem'")
    if spec.get("polarity", "positive_up") not in ("positive_up", "negative_up"):
        die("polarity must be 'positive_up' or 'negative_up'")
    if not isinstance(spec["conditions"], dict) or not spec["conditions"]:
        die("conditions must be a non-empty {file_key: label} mapping")
    if not isinstance(spec.get("exclude", {}), dict) or not all(text(r) for r in spec.get("exclude", {}).values()):
        die("exclude must be {subject_id: non-empty reason}")
    for k in ("claim", "key_comparison", "time_locked_to", "reference"):
        if not text(spec.get(k)):
            die(f"'{k}' must be a non-empty string")
    erp = spec.get("kind", "combo") == "erp"
    if erp:  # kind "erp" draws by channel; components are optional gray bands (rule K1)
        if spec.get("layout", "roi") not in ("single", "grid", "roi"):
            die("layout must be 'single', 'grid' or 'roi'")
        ch = spec.get("channels")
        rows = ch if spec.get("layout", "roi") == "grid" else [ch]
        if not (ch == "all" and spec.get("layout") == "single") and not (
                isinstance(ch, list) and ch and all(isinstance(r, list) and r and all(text(x) for x in r) for r in rows)
                and len(sum(rows, [])) == len(set(sum(rows, [])))):
            die("kind 'erp' needs channels: a list of names (single/roi), rows of names (grid), or 'all' (single); "
                "no repeats")
        if spec.get("layout") == "grid" and spec.get("error", "none") == "sem":
            die("layout 'grid' draws no SEM band; use 'roi' or 'single' for error: 'sem'")
    elif "channels" in spec or "layout" in spec:
        die("'channels' and 'layout' belong to kind 'erp'; combo/topo take channels per component")
    elif not spec.get("components"):
        die("components is empty")
    lo, hi = spec.get("xlim_ms", [-np.inf, np.inf])
    names = [c.get("name") for c in spec.get("components", [])]
    if not all(isinstance(x, str) for x in names) or len({x.casefold() for x in names}) != len(names):
        die(f"component names must be strings, unique ignoring case (they become file names): {names}")
    for c in spec.get("components", []):
        need = COMPONENT_KEYS - {"channels"} if erp else COMPONENT_KEYS  # an erp band has no channels of its own
        if set(c) != need:
            die(f"component {c.get('name')} needs exactly {sorted(need)}")
        if not re.fullmatch(r"[A-Za-z0-9_\-]+", str(c["name"])):
            die(f"component name {c['name']!r}: use letters, digits, '_' or '-' (it becomes a file name)")
        ch = c.get("channels", ["-"])
        if not isinstance(ch, list) or not ch or len(set(ch)) != len(ch):
            die(f"component {c['name']}: channels must be a non-empty list without repeats (repeats re-weight the ROI)")
        if not all(isinstance(x, (int, float)) and np.isfinite(x) for x in (c["tmin_ms"], c["tmax_ms"])) \
                or not c["tmin_ms"] < c["tmax_ms"]:
            die(f"component {c['name']}: tmin_ms < tmax_ms, both finite numbers")
        if not lo <= c["tmin_ms"] or not c["tmax_ms"] <= hi:
            die(f"component {c['name']}: window must lie inside xlim_ms {lo, hi}")
        if not text(c["window_source"]):
            die(f"component {c['name']}: window_source must say where the window comes from")


def text(x):
    return isinstance(x, str) and bool(x.strip())


# ---------- output layout (plan 2026-09-26) ----------
KIND_DIR = {"erp": "ERP", "topo": "topo", "combo": "ERP_topo"}


def out_root(spec):
    """Rule O1: every output goes to brain-plot/ next to the data folder."""
    return Path(spec["data"]).resolve().parent / "brain-plot"


def comparison(spec):
    """File-name part: what the lines are, then what the panels are."""
    return "conditions-by-group" if spec.get("overlay", "groups") == "conditions" else "groups-by-condition"


def safe(x):
    return re.sub(r'[\\/:*?"<>|\s]+', "", str(x))


def versioned(folder, stem):
    """Rule O2: path prefix of the next version of `stem` (…_v01, _v02, …). Files of the previous versions move to
    folder/_history/; nothing is overwritten. Call only once the figure has passed its checks."""
    hist = folder / "_history"
    pat = re.compile(re.escape(stem) + r"_v(\d+)(?![\d])")
    old = [f for d in (folder, hist) if d.exists() for f in d.iterdir() if pat.match(f.name)]
    n = max((int(pat.match(f.name).group(1)) for f in old), default=0) + 1
    for f in old:
        if f.parent == folder:
            hist.mkdir(parents=True, exist_ok=True)
            f.rename(hist / f.name)
    folder.mkdir(parents=True, exist_ok=True)
    return folder / f"{stem}_v{n:02d}"


# ---------- data ----------
def subject_id(f):
    return re.match(r"[^_\-.]+", f.name).group(0)


def find_groups(data_dir):
    root = Path(data_dir)
    pat = lambda d: sorted(list(d.glob("*-epo.fif")) + list(d.glob("*-ave.fif")))
    groups = {d.name: pat(d) for d in sorted(root.iterdir()) if d.is_dir() and pat(d)}
    if groups and pat(root):
        die(f"{root} has both group sub-folders and subject files at the top level")
    return groups or {"all": pat(root)}


def groups_from_metadata(found, col):
    """Split a flat folder of epochs files into groups by a between-subject metadata column (constant per file)."""
    if list(found) != ["all"]:
        die("group_by needs one flat folder of subject files, not group sub-folders")
    by = {}
    for f in found["all"]:
        if not f.name.endswith("-epo.fif"):
            die(f"{f.name}: group_by needs epochs files with metadata")
        md = mne.read_epochs(f, preload=False, verbose="error").metadata
        if md is None or col not in md:
            die(f"{f.name}: no metadata column {col!r}")
        vals = md[col].dropna().unique()
        if len(vals) != 1:
            die(f"{f.name}: {col!r} is not constant within the subject ({list(vals)}); it is not a group variable")
        by.setdefault(str(vals[0]), []).append(f)
    return dict(sorted(by.items()))  # alphabetical unless spec["groups"] gives the order


def select_files(spec):
    found = find_groups(spec["data"])
    if spec.get("group_by"):
        found = groups_from_metadata(found, spec["group_by"])
    order = spec.get("groups") or list(found)
    if [g for g in order if g not in found]:
        die(f"groups not found in {spec['data']}: {[g for g in order if g not in found]}")
    excl = spec.get("exclude", {})
    all_ids = [subject_id(f) for g in order for f in found[g]]
    dup = sorted({i for i in all_ids if all_ids.count(i) > 1})
    if dup:
        die(f"subject IDs appear more than once: {dup}")
    if [i for i in excl if i not in all_ids]:
        die(f"excluded IDs not found: {[i for i in excl if i not in all_ids]}")
    groups = {g: [f for f in found[g] if subject_id(f) not in excl] for g in order}
    if [g for g, fs in groups.items() if not fs]:
        die(f"groups left empty: {[g for g, fs in groups.items() if not fs]}")
    return groups


def read_conditions(f, conditions, query):
    """Evoked per condition and trial counts for one subject file."""
    if f.name.endswith("-epo.fif"):
        ep = mne.read_epochs(f, proj=False, verbose="error")
        if query:
            ep = ep[query]
        evs = []
        for c in conditions:
            if len(ep[c]) == 0:
                die(f"{f.name}: no trials left for '{c}' (query={query!r})")
            evs.append(ep[c].average())
    else:
        if query:
            die(f"{f.name}: 'query' cannot be applied to averaged (-ave.fif) files")
        evs_all = mne.read_evokeds(f, proj=False, verbose="error")
        comments = [e.comment for e in evs_all]
        if len(set(comments)) != len(comments):
            die(f"{f.name}: several Evoked objects share a comment {comments}; the condition is ambiguous")
        by = {e.comment: e for e in evs_all}
        if [c for c in conditions if c in by and by[c].kind != "average"]:
            die(f"{f.name}: only kind='average' Evoked objects are supported")
        if [c for c in conditions if c not in by]:
            die(f"{f.name}: conditions {[c for c in conditions if c not in by]} not in file ({list(by)})")
        evs = [by[c] for c in conditions]
    return evs, [e.nave for e in evs]


def contract(ev):
    """Everything that must be identical across subjects and conditions for averaging to be valid."""
    info = ev.info
    locs = np.round(np.array([ch["loc"][:3] for ch in info["chs"]]), 5)
    dig = np.round(np.array([d["r"] for d in info["dig"] or []]).reshape(-1, 3), 5)
    return dict(ch_names=list(info.ch_names), types=sorted(set(ev.get_channel_types())), sfreq=info["sfreq"],
                units=sorted({int(ch["unit"]) for ch in info["chs"]}), coord_frames=sorted({int(ch["coord_frame"]) for ch in info["chs"]}),
                baseline=None if ev.baseline is None else [round(b, 4) for b in ev.baseline],
                filter=[info["highpass"], info["lowpass"]], custom_ref=bool(info["custom_ref_applied"]),
                projs_unapplied=[p["desc"] for p in info["projs"] if not p["active"]],
                n_times=len(ev.times), t0=round(float(ev.times[0]), 6),
                locs=hashlib.md5(locs.tobytes()).hexdigest(), locs_finite=bool(np.isfinite(locs).all() and locs.any()),
                dig=hashlib.md5(dig.tobytes()).hexdigest())


def load(spec):
    """Validated arrays per group: (n_subj, n_cond, n_ch, n_t) in µV; cache keyed on the exact input files."""
    groups = select_files(spec)
    conds = list(spec["conditions"])
    files = [f for fs in groups.values() for f in fs]
    stamp = [[str(f), f.stat().st_size, f.stat().st_mtime_ns] for f in files]
    key = json.dumps([LOADER_VERSION, list(groups), stamp, conds, spec.get("query")])
    cache = out_root(spec) / ".cache" / (hashlib.md5(key.encode()).hexdigest() + ".npz")
    if cache.exists():
        z = np.load(cache, allow_pickle=True)
        meta = json.loads(str(z["meta"]))
        info = mne.io.read_info(files[0], verbose="error")
        if list(info.ch_names) == meta["contract"]["ch_names"]:
            return {g: z[g] for g in groups}, z["times"], info, meta
    data, nave, ids, ref = {}, {}, {}, None
    for g, fs in groups.items():
        arrs, counts = [], []
        for f in fs:
            evs, n = read_conditions(f, conds, spec.get("query"))
            for c, ev in zip(conds, evs):
                if ev.info["bads"]:
                    die(f"{f.name} [{c}]: bad channels {ev.info['bads']} are still marked; resolve them before plotting")
                k = contract(ev)
                if k["types"] != ["eeg"] or k["units"] != [int(mne.io.constants.FIFF.FIFF_UNIT_V)]:
                    die(f"{f.name}: only EEG potentials in volts are supported (types {k['types']}, units {k['units']})")
                if k["projs_unapplied"]:
                    die(f"{f.name}: unapplied projectors {k['projs_unapplied']}; apply or remove them upstream")
                if not k["locs_finite"] or k["coord_frames"] != [int(mne.io.constants.FIFF.FIFFV_COORD_HEAD)]:
                    die(f"{f.name}: channel positions missing or not in head coordinates; set the montage upstream")
                if ref is None:
                    ref, ref_file, times, info = k, f.name, ev.times, ev.info
                diff = [x for x in k if k[x] != ref[x]]
                if diff:
                    die(f"{f.name} [{c}] differs from {ref_file} in {diff}; the loader does not re-reference, "
                        "resample or interpolate")
            x = np.array([ev.data for ev in evs]) * 1e6
            if not np.isfinite(x).all():
                die(f"{f.name}: non-finite values in the data")
            arrs.append(x)
            counts.append(n)
        data[g], nave[g], ids[g] = np.array(arrs), [list(map(int, c)) for c in counts], [subject_id(f) for f in fs]
        print(f"loaded {g}: {len(fs)} subjects")
    meta = dict(contract=ref, nave=nave, ids=ids, inputs=stamp, loader_version=LOADER_VERSION)
    cache.parent.mkdir(parents=True, exist_ok=True)
    np.savez(cache, times=times, meta=json.dumps(meta), **data)
    return data, times, info, meta


# ---------- inspect / windows ----------
def inspect(data_dir):
    groups = find_groups(data_dir)
    out = {"groups": {g: len(f) for g, f in groups.items()}}
    trials = {}
    for files in groups.values():
        for f in files:
            if f.name.endswith("-epo.fif"):
                ep = mne.read_epochs(f, preload=False, verbose="error")
                for c in ep.event_id:
                    trials.setdefault(c, []).append(len(ep[c]))
    f0 = next(iter(groups.values()))[0]
    if f0.name.endswith("-epo.fif"):
        ep = mne.read_epochs(f0, preload=False, verbose="error")
        info, times, baseline, md = ep.info, ep.times, ep.baseline, ep.metadata
    else:
        ev = mne.read_evokeds(f0, verbose="error")
        info, times, baseline, md = ev[0].info, ev[0].times, ev[0].baseline, None
        trials = {e.comment: [e.nave] for e in ev}
    out["conditions_trials_min_median_max"] = {c: [min(v), int(np.median(v)), max(v)] for c, v in trials.items()}
    out["n_channels"], out["ch_names"] = len(info.ch_names), info.ch_names
    out["has_montage"] = info.get_montage() is not None
    out["time_range_ms"] = [round(times[0] * 1000), round(times[-1] * 1000)]
    out["sfreq"], out["baseline"] = info["sfreq"], baseline
    out["filter_hz"] = [info["highpass"], info["lowpass"]]
    out["custom_reference_applied"] = bool(info["custom_ref_applied"])
    out["bads"] = info["bads"]
    if md is not None:
        out["metadata"] = {c: (sorted(md[c].dropna().unique().tolist()) if md[c].nunique() <= 6 else "continuous")
                           for c in md.columns}
    print(json.dumps(out, indent=1, ensure_ascii=False, default=str))


def windows(spec):
    """Heuristic candidates only: peaks of the ROI waveform averaged over all subjects (equal weight) and all
    conditions, searched in each component's [tmin_ms, tmax_ms] (use a generous search range here). The reported
    interval is the full width at half prominence, not a rule; the user decides names and final windows."""
    check_spec(spec)
    data, times, info, _ = load(spec)
    allsub = np.concatenate([d.mean(1) for d in data.values()]).mean(0)  # (ch, t)
    ms = times * 1000
    for c in spec["components"]:
        sel = (ms >= c["tmin_ms"]) & (ms <= c["tmax_ms"])
        y, t = allsub[[info.ch_names.index(ch) for ch in c["channels"]]].mean(0)[sel], ms[sel]
        print(f"\n{c['name']} · {', '.join(c['channels'])} · search {c['tmin_ms']}–{c['tmax_ms']} ms "
              f"(all {sum(len(d) for d in data.values())} subjects, all conditions, equal weights)")
        for sign, lab in ((1, "positive"), (-1, "negative")):
            pk, _ = find_peaks(sign * y, prominence=0.1 * np.ptp(y))
            if len(pk):
                _, _, a, b = peak_widths(sign * y, pk, rel_height=0.5)
                for p, lo, hi in zip(pk, a, b):
                    print(f"  {lab:8s} peak {t[p]:5.0f} ms {y[p]:7.2f} µV   FWHP {t[int(lo)]:.0f}–{t[int(np.ceil(hi))]:.0f} ms")


# ---------- plot ----------
MAX_LINES = 7


def colors_for(n, ordered):
    if ordered:
        return [plt.cm.viridis(x) for x in np.linspace(0, 0.9, n)]
    return TWO_COLORS if n == 2 else OKABE_ITO + ["#000000"]


def letter(ax, i, x=-0.02, y=None):
    """Panel letter; y=None: a fixed 15 pt above the axes (waveform panels, whose height varies with the count)."""
    ax.annotate("abcdefghijklmnopqrstuvwxyz"[i % 26], (x, 1.0 if y is None else y), xycoords="axes fraction",
                xytext=(0, 15 if y is None else 0), textcoords="offset points",
                fontsize=8, fontweight="bold", va="bottom", ha="right")


def nice_ticks(ylim):
    """Rule T1: y ticks (0 excluded) with at least one tick on every side of 0 that the axis extends to by more
    than 15 % of its range; tries finer steps (up to 10 bins) first. Returns (ticks, needs_extension)."""
    span = ylim[1] - ylim[0]
    need_neg, need_pos = ylim[0] < -0.15 * span, ylim[1] > 0.15 * span
    for nbins in range(5, 11):
        yt = [v for v in MaxNLocator(nbins=nbins, steps=[1, 2, 5, 10]).tick_values(*ylim)
              if v != 0 and ylim[0] <= v <= ylim[1]]
        if (not need_neg or min(yt, default=0) < 0) and (not need_pos or max(yt, default=0) > 0):
            return yt, False
    return yt, True


def set_yticks(ax, ylim):
    yt, _ = nice_ticks(ylim)
    ax.set_yticks(yt, [f"{v:g}".replace("-", "−") for v in yt])


def sample_mask(ms, lo, hi):
    """Samples with lo <= t <= hi. FIF stores times as float32 (e.g. 306 ms reads as 305.99999), so bounds get a
    1 µs tolerance only; a window never widens to a neighbouring sample."""
    return (ms >= lo - 1e-3) & (ms <= hi + 1e-3)


def line_stats(x, idx, t, w):
    """x: (n_subj, n_ch, n_t) µV. ROI mean per subject, then mean and between-subject SEM over time (None if n < 2);
    topography = subject mean over the window at every channel."""
    roi = x[:, idx].mean(1)[:, t]
    sem = roi.std(0, ddof=1) / np.sqrt(len(roi)) if len(roi) > 1 else None
    return roi.mean(0), sem, x[:, :, w].mean(axis=(0, 2))


def cross_axes(ax, fig, lo, hi, ylim, negative_up, x, low_env, high_env):
    """Spines through the origin (x-axis at 0 µV, y-axis at 0 ms). Each x tick label is measured and placed on the
    side of the axis where the visible lines (low_env/high_env) leave the most room over the label's own width; if
    they reach into the label on that side too, the label moves just past them."""
    ax.set_xlim(lo, hi)
    ax.set_ylim(*(ylim[::-1] if negative_up else ylim))
    ax.spines["left"].set_position(("data", 0))
    ax.spines["bottom"].set_position(("data", 0))
    set_yticks(ax, ylim)
    ax.text(0, 1.0, "  µV", transform=ax.get_xaxis_transform(), fontsize=6, va="top", ha="left")
    ax.tick_params(direction="inout", length=3, pad=1.5)
    span = hi - lo
    step = 200 if span >= 600 else 100 if span >= 300 else 50
    fig.canvas.draw()
    inv = ax.transData.inverted()
    pt = fig.dpi / 72  # display pixels per point
    renderer = fig.canvas.get_renderer()
    while True:  # widen the tick step until neighbouring labels keep a 3-pt gap
        xt = [v for v in np.arange(np.ceil(lo / step) * step, hi + 1e-9, step) if v != 0]
        labs = [f"{v:g}".replace("-", "−") for v in xt]
        boxes = []
        for v, lab in zip(xt, labs):
            probe = ax.annotate(lab, (v, 0), fontsize=6, ha="center")
            boxes.append(probe.get_window_extent(renderer))
            probe.remove()
        if all(b1.x0 - b0.x1 >= 3 * pt for b0, b1 in zip(boxes, boxes[1:])) or len(xt) <= 1:
            break
        step *= 2
    ax.set_xticks(xt, [])
    ax.annotate("ms", (hi, 0), xytext=(3, 0), textcoords="offset points", fontsize=6, ha="left", va="center",
                annotation_clip=False)  # unit at the end of the x-axis, like µV at the top of the y-axis
    for v, lab, bb in zip(xt, labs, boxes):
        (x0, _), (x1, _) = inv.transform([(bb.x0, 0), (bb.x1, 0)])
        s = (x >= min(x0, x1) - 2) & (x <= max(x0, x1) + 2)
        y0 = ax.transData.transform((0, 0))[1]
        to_pt = lambda y: (ax.transData.transform(np.c_[x[s], y])[:, 1] - y0) / pt  # display offset from the axis
        a, b = np.minimum(to_pt(low_env[s]), to_pt(high_env[s])), np.maximum(to_pt(low_env[s]), to_pt(high_env[s]))
        text_h = bb.height / pt

        def offset(near, far):  # 3 pt from the axis if the lines stay clear of the label there, else just past them
            return 3.0 if far <= 0 or near > 3.0 + text_h + 1.0 else far + 1.5
        up, dn = b > 0, a < 0
        off_up = offset(np.maximum(a[up], 0).min() if up.any() else np.inf, b[up].max() if up.any() else 0)
        off_dn = offset(np.maximum(-b[dn], 0).min() if dn.any() else np.inf, (-a[dn]).max() if dn.any() else 0)
        go_up = off_up <= off_dn
        off = off_up if go_up else -off_dn
        ax.annotate(lab, (v, 0), xytext=(0, off), textcoords="offset points", fontsize=6,
                    ha="center", va="bottom" if go_up else "top")


def canvas_size(spec):
    """Rule T6: the canvas is fixed by the spec (default 180 × 120 mm), never derived from the content."""
    return spec.get("width_mm", 180), spec.get("height_mm", 120)


LEGEND_KW = dict(handlelength=1.2, labelspacing=0.3, borderaxespad=0.3)
GAP_MM, CBAR_MM, CBAR_PAD_MM = 8.0, 4.0, 4.0  # rule L4: waveform-map gap, colour bar width and its spacer


def data_ylim(stats):
    """Shared y-range of a figure from every visible line (mean, plus SEM only if drawn), 8 % padding, 0 inside."""
    env = [(m, np.zeros_like(m) if e is None else e) for m, e in stats.values()]
    ymin, ymax = min((m - e).min() for m, e in env), max((m + e).max() for m, e in env)
    pad = 0.08 * max(ymax - ymin, 1e-6)
    ylim = [min(ymin - pad, -pad), max(ymax + pad, pad)]
    yt, short = nice_ticks(ylim)
    if short:  # even 10 bins leave a side unlabelled: extend that side to its next tick
        step = np.diff(MaxNLocator(nbins=5, steps=[1, 2, 5, 10]).tick_values(*ylim))[0]
        span = ylim[1] - ylim[0]
        if ylim[0] < -0.15 * span and not any(v < 0 for v in yt):
            ylim[0] = -step
        if ylim[1] > 0.15 * span and not any(v > 0 for v in yt):
            ylim[1] = step
    return ylim


def legend_room(series, x, lo, hi, ylim, width, windows, axis_frac):
    """Single-panel legend (upper/lower right): free fraction of the axes above and below the visible lines inside
    the right strip the legend covers; the x-axis and one tick-label line on each side count as occupied. A gray
    window band reaching into the strip blocks both corners: (-inf, -inf)."""
    edge = (hi - lo) * (width + 0.02)
    if any(comp_overlaps(w, (hi - edge, hi)) for w in windows):
        return -np.inf, -np.inf
    strip = x >= hi - edge
    span = ylim[1] - ylim[0]
    top = max(max((m + (0 if e is None else e))[strip].max() for m, e in series), axis_frac * span)
    bottom = min(min((m - (0 if e is None else e))[strip].min() for m, e in series), -axis_frac * span)
    return (ylim[1] - top) / span, (bottom - ylim[0]) / span


def comp_overlaps(a, b):
    return a[0] < b[1] and a[1] > b[0]


def line_styles(spec, n):
    """Solid unless the spec gives one style per line (e.g. a second factor: '-' high, '--' low)."""
    styles = spec.get("linestyles") or ["-"] * n
    if len(styles) != n or any(x not in ("-", "--", ":", "-.") for x in styles):
        die(f"linestyles needs one of '-', '--', ':', '-.' per line ({n} lines)")
    return styles


def legend_size(spec, n, labels, colors):
    """One-column legend measured once on an empty figure of the final size: width and height as fractions of a
    waveform panel, the tick-label band as a fraction of panel height, and the width in mm."""
    fig, gs = canvas(spec, n, len(labels), maps=spec.get("kind", "combo") == "combo")
    ax = fig.add_subplot(gs[0, 0])
    for lab, col, ls in zip(labels, colors, line_styles(spec, len(labels))):
        ax.plot([], [], color=col, ls=ls, lw=0.9, label=lab)
    leg = ax.legend(**LEGEND_KW)
    fig.canvas.draw()
    win = leg.get_window_extent()
    bb = win.transformed(ax.transAxes.inverted())
    axis_frac = 10 / (ax.get_window_extent().height * 72 / fig.dpi)  # 6-pt tick label + 3-pt offset + 1 pt
    plt.close(fig)
    return bb.width, bb.height, axis_frac, win.width / fig.dpi * 25.4


def topo_grid(n_lines):
    ncol = int(np.ceil(np.sqrt(n_lines)))
    return int(np.ceil(n_lines / ncol)), ncol


def canvas(spec, n, n_lines, gap=GAP_MM, maps=True):
    """Fixed physical canvas, all widths in mm (wspace 0): waveforms | gap (8 mm, widened for the legend by rule L7)
    | topomaps (~19 mm per head column, at most 55 % of what is left) | spacer | colour bar."""
    W, H = canvas_size(spec)
    fig = plt.figure(figsize=(W * MM, H * MM))
    tiny = 1e-3  # kind "erp": the map and colour-bar columns collapse to nothing
    pad, bar = (CBAR_PAD_MM, CBAR_MM) if maps else (tiny, tiny)
    usable = W - 24 - gap - pad - bar  # 12-mm side margins
    topo_mm = min(19 * topo_grid(n_lines)[1], 0.55 * usable) if maps else tiny
    avail, need = H - 18, 13.0  # 9-mm top/bottom margins; facet label + ROI title + letter need 13 mm between panels
    hspace = 0.55 if n < 2 or 0.55 * avail / (n + 0.55 * (n - 1)) >= need else need / ((avail - (n - 1) * need) / n)
    gs = GridSpec(n, 5, figure=fig, width_ratios=[usable - topo_mm, gap, topo_mm, pad, bar],
                  hspace=hspace, wspace=0, left=12 / W, right=1 - 12 / W, top=1 - 9 / H, bottom=9 / H)
    return fig, gs


def single_panel_corner(firsts, ylims, windows, x, lo, hi, size):
    """Rule L7 with one waveform panel (no gap between panels): upper or lower right inside the panel, the side
    with the most room in the worst figure of the set; stop if a gray band reaches into the legend's strip."""
    rooms = [legend_room(f, x, lo, hi, y, size[0], w, size[2]) for f, y, w in zip(firsts, ylims, windows)]
    high, low = min(r[0] for r in rooms), min(r[1] for r in rooms)
    if max(high, low) == -np.inf:
        die("one waveform panel: a gray band reaches into the legend's strip at the right; add a panel or change xlim_ms")
    return "high" if high >= low else "low"


def common_sphere(info):
    """One explicit head sphere (x, y, z, r in m) for every map: MNE's default origin, radius = 1.01 × the outermost
    projected electrode (MNE clips the image at that radius), so the coloured disc never extends beyond the drawn
    head. (A sphere fitted to the electrodes moved the origin up ~4 cm and pushed electrodes outside the outline.)"""
    from mne.channels.layout import _find_topomap_coords
    pos = _find_topomap_coords(info, picks=np.arange(len(info.ch_names)), sphere=np.array([0, 0, 0, 0.095]))
    return [0.0, 0.0, 0.0, max(0.095, float(np.linalg.norm(pos, axis=1).max()) * 1.01)]


def obstacles_of(fig):
    """Window extents of every text and every axes (waveform areas, topomap heads) in the figure."""
    R = fig.canvas.get_renderer()
    boxes = [t.get_window_extent(R) for t in fig.texts if t.get_text()]
    for a in fig.axes:
        boxes.append(a.get_window_extent(R))
        boxes += [t.get_window_extent(R) for t in a.texts + [a.title] if t.get_visible() and t.get_text()]
    return boxes


def draw(spec, comp, panels, lines, colors, stats, topo, v, info, ms, t, lo, hi, negative_up, sphere, leg_size,
         corner, gap_mm):
    """Render one component figure with colour limit v. Returns the figure, the largest |value| of the interpolated
    maps, line/map counts, the size and where the legend went ('between panels', 'widened gap', 'inside panel' or
    None when it collided between the panels)."""
    n = len(panels)
    maps = spec.get("kind", "combo") == "combo"
    fig, gs = canvas(spec, n, len(lines), gap_mm, maps)
    ylim = data_ylim(stats)
    levels = np.linspace(-v, v, TOPO["contours"] + 1)  # one set of contour levels for every map
    styles = line_styles(spec, len(lines))
    n_lines = n_maps = 0
    peak = 0.0
    axes = []
    for r_i, (p, plabel) in enumerate(panels):
        ax = fig.add_subplot(gs[r_i, 0]); letter(ax, 2 * r_i if maps else r_i)
        axes.append((ax, p))
        for b in comp["bands"]:
            ax.axvspan(b["tmin_ms"], b["tmax_ms"], color="0.88", lw=0, zorder=0)  # full-height window band
            ax.text((b["tmin_ms"] + b["tmax_ms"]) / 2, 1.0, b["name"], transform=ax.get_xaxis_transform(),
                    ha="center", va="bottom", fontsize=6.5, fontweight="bold")
        for (l, lab), col, ls in zip(lines, colors, styles):
            m, e = stats[p, l]
            if e is not None:
                ax.fill_between(ms[t], m - e, m + e, color=col, alpha=0.15, lw=0)
            ax.plot(ms[t], m, color=col, ls=ls, lw=0.9, label=lab)
            n_lines += 1
        ax.set_title(", ".join(comp["channels"]), pad=11, fontsize=7)  # rule L5: electrodes above the panel
        ax.text(0.5, -0.06, plabel, transform=ax.transAxes, ha="center", va="top", fontsize=7.5,
                fontweight="bold")  # rule L6: facet name below its panel
        ax.set_xlim(lo, hi)
        if corner in ("high", "low"):  # single panel: inside, upper/lower right; grow the y-range on that side
            high = corner == "high"
            need = leg_size[1] + 0.03
            for _ in range(10):  # the axis band is fixed in points, so re-measure after each extension
                room = legend_room([stats[p, l] for l, _ in lines], ms[t], lo, hi, ylim, leg_size[0],
                                   [(b["tmin_ms"], b["tmax_ms"]) for b in comp["bands"]], leg_size[2])
                free, span = room[0 if high else 1], ylim[1] - ylim[0]
                if free >= need - 1e-3:
                    break
                d = (need - free) * span / (1 - need)
                ylim[1 if high else 0] += d if high else -d
            ax.legend(loc=("upper" if high != negative_up else "lower") + " right", **LEGEND_KW)
        if not maps:
            continue
        # rule L4: topomaps to the right, one per line, near-square grid, black labels
        nrow_t, ncol_t = topo_grid(len(lines))
        sub = gs[r_i, 2].subgridspec(nrow_t, ncol_t, wspace=0.02, hspace=0.25)
        for j, (l, lab) in enumerate(lines):
            tax = fig.add_subplot(sub[j // ncol_t, j % ncol_t])
            if j == 0:
                letter(tax, 2 * r_i + 1, x=0.0, y=0.95)
            im, _ = mne.viz.plot_topomap(topo[p, l], info, axes=tax, show=False, cmap=spec.get("cmap", "RdBu_r"),
                                         vlim=(-v, v), contours=levels, sensors=False, extrapolate=TOPO["extrapolate"],
                                         image_interp=TOPO["image_interp"], sphere=sphere,
                                         mask_params=dict(markeredgewidth=0.3))  # rule L11: no marks; MNE takes the
                                         # contour width (0.15 pt) from this parameter even without a mask
            a = im.get_array()
            if np.ma.count(a):
                peak = max(peak, float(np.ma.abs(a).max()))
            tax.text(0.5, -0.04, lab, transform=tax.transAxes, ha="center", va="top", fontsize=6)
            n_maps += 1
        pos = gs[r_i, 2].get_position(fig)
        fig.text((pos.x0 + pos.x1) / 2, pos.y1 + 0.01, f"{comp['name']}  {comp['tmin_ms']:g}–{comp['tmax_ms']:g} ms",
                 ha="center", va="bottom", fontsize=6.5)  # rule S4: window stated in the figure
    for ax, p in axes:  # ticks last: a single-panel legend may have grown the shared y-range
        env = [(m, np.zeros_like(m) if e is None else e) for (pp, _), (m, e) in stats.items() if pp == p]
        cross_axes(ax, fig, lo, hi, ylim, negative_up, ms[t],
                   np.min([m - e for m, e in env], axis=0), np.max([m + e for m, e in env], axis=0))
    placed = "inside panel"
    if corner == "between":  # rule L7
        g = len(axes) // 2 - 1
        above, below = axes[g][0].get_position(), axes[g + 1][0].get_position()
        y = (above.y0 + below.y1) / 2
        widened = gap_mm > GAP_MM
        gx = gs[g, 1].get_position(fig)
        loc, anchor = ("center", ((gx.x0 + gx.x1) / 2, y)) if widened else ("center right", (above.x1, y))
        h, lab = axes[0][0].get_legend_handles_labels()
        fig.canvas.draw()
        boxes = obstacles_of(fig)
        for ncol in [1] if widened else range(1, len(lab) + 1):  # fewest columns whose height fits the gap
            leg = fig.legend(h, lab, loc=loc, bbox_to_anchor=anchor, ncol=ncol, columnspacing=1.0,
                             borderaxespad=0, handlelength=1.2, labelspacing=0.3)
            fig.canvas.draw()
            bb = leg.get_window_extent(fig.canvas.get_renderer())
            if widened or bb.height <= 0.8 * (above.y0 - below.y1) * fig.bbox.height:
                break
            leg.remove()
        pad = 2 * fig.dpi / 72
        clash = any(bb.x0 - pad < o.x1 and o.x0 < bb.x1 + pad and bb.y0 - pad < o.y1 and o.y0 < bb.y1 + pad
                    for o in boxes)
        placed = None if clash else ("widened gap" if widened else "between panels")
    if not maps:
        return fig, peak, n_lines, n_maps, list(canvas_size(spec)), placed
    cax = fig.add_subplot(gs[:, 4])
    cp = cax.get_position()
    cax.set_position([cp.x0, 0.5 - 0.15, cp.width, 0.3])
    cb = fig.colorbar(im, cax=cax, ticks=[-v, 0, v])
    cb.ax.set_yticklabels([f"{-v:.1f}".replace("-", "−"), "0", f"{v:.1f}"])
    cb.set_label("µV", fontsize=6, labelpad=1)
    cb.outline.set_linewidth(0.4)
    cb.ax.tick_params(labelsize=6, width=0.4, length=2)
    return fig, peak, n_lines, n_maps, list(canvas_size(spec)), placed


def topo_block(m, n, W, H):
    """kind "topo": rows × columns of maps in each of n stacked panels, adapted to the line count and the fixed canvas
    (rule T6). Map size of each shape follows the GridSpec geometry in draw_topo; take the largest maps, but among
    shapes within 10 % of that size the one with more rows, so the canvas is filled rather than left half empty."""
    block = (H - 18) / (n + 0.25 * (n - 1))  # hspace 0.25 between panels
    size = {}
    for r in range(1, m + 1):
        c = -(-m // r)
        if -(-m // c) == r:  # no empty row
            size[r] = min(block / (r + 0.3 * (r - 1)), (W - 44) / (c + 0.05 * (c - 1)))
    r = max(k for k, v in size.items() if v >= 0.9 * max(size.values()))
    return r, -(-m // r)


def draw_topo(spec, comp, panels, lines, topo, v, info, sphere):
    """kind "topo": topomaps only, one per (panel, line), over the component window. Each panel is a row block of
    maps whose rows × columns topo_block() adapts to the line and panel count on the fixed canvas (rule T6)."""
    n, m = len(panels), len(lines)
    label_mm, top_mm = 10.0, 12.0
    W, H = canvas_size(spec)  # rule T6: fixed canvas; the maps shrink or grow to fit it
    nrow_t, ncol_t = topo_block(m, n, W, H)
    fig = plt.figure(figsize=(W * MM, H * MM))
    gs = GridSpec(n, 4, figure=fig, width_ratios=[label_mm, W - 26 - label_mm - CBAR_PAD_MM - CBAR_MM, CBAR_PAD_MM, CBAR_MM],
                  hspace=0.25,
                  wspace=0, left=12 / W, right=1 - 14 / W, top=1 - top_mm / H, bottom=6 / H)
    levels = np.linspace(-v, v, TOPO["contours"] + 1)
    peak, n_maps = 0.0, 0
    for r_i, (p, plabel) in enumerate(panels):
        sub = gs[r_i, 1].subgridspec(nrow_t, ncol_t, wspace=0.05, hspace=0.3)
        for j, (l, lab) in enumerate(lines):
            tax = fig.add_subplot(sub[j // ncol_t, j % ncol_t])
            if j == 0:
                letter(tax, r_i, x=0.0, y=0.95)
            im, _ = mne.viz.plot_topomap(topo[p, l], info, axes=tax, show=False, cmap=spec.get("cmap", "RdBu_r"),
                                         vlim=(-v, v), contours=levels, sensors=False, extrapolate=TOPO["extrapolate"],
                                         image_interp=TOPO["image_interp"], sphere=sphere,
                                         mask_params=dict(markeredgewidth=0.3))  # rule L11: no marks; MNE takes the
                                         # contour width (0.15 pt) from this parameter even without a mask
            a = im.get_array()
            if np.ma.count(a):
                peak = max(peak, float(np.ma.abs(a).max()))
            tax.text(0.5, -0.04, lab, transform=tax.transAxes, ha="center", va="top", fontsize=6)
            n_maps += 1
        lab_ax = fig.add_subplot(gs[r_i, 0])
        lab_ax.axis("off")
        lab_ax.text(0.5, 0.5, plabel, rotation=90, ha="center", va="center", fontsize=7.5, fontweight="bold",
                    transform=lab_ax.transAxes)  # facet name at the left of its row
        if r_i == 0:  # one component per figure: window title once, above the first block
            pos = gs[0, 1].get_position(fig)
            fig.text((pos.x0 + pos.x1) / 2, pos.y1 + 0.005, f"{comp['name']}  {comp['tmin_ms']:g}–{comp['tmax_ms']:g} ms",
                     ha="center", va="bottom", fontsize=6.5)
    cax = fig.add_subplot(gs[:, 3])
    cp = cax.get_position()
    h = min(0.6, cp.height)
    cax.set_position([cp.x0, 0.5 - h / 2 * (1 - 0) - 0.02, cp.width, h])
    cb = fig.colorbar(im, cax=cax, ticks=[-v, 0, v])
    cb.ax.set_yticklabels([f"{-v:.1f}".replace("-", "−"), "0", f"{v:.1f}"])
    cb.set_label("µV", fontsize=6, labelpad=1)
    cb.outline.set_linewidth(0.4)
    cb.ax.tick_params(labelsize=6, width=0.4, length=2)
    return fig, peak, n_maps, [W, H]


def open_items(spec):
    """Spec fields still marked as unconfirmed (rule QA 4)."""
    flat = json.dumps(spec, ensure_ascii=False)
    return sorted({k for k, x in spec.items() if re.search(r"to be confirmed|not recorded", json.dumps(x), re.I)}) \
        if re.search(r"to be confirmed|not recorded", flat, re.I) else []


def plot(spec):
    """One figure per component: waveform panels stacked vertically (one per condition, or per group), each with
    one topomap per line to its right, all over the component window (= the gray band)."""
    check_spec(spec)
    plt.rcParams.update(STYLE)
    data, times, info, meta = load(spec)
    conds, groups = list(spec["conditions"]), list(data)
    ms = times * 1000
    tol = 500 / info["sfreq"]  # half a sample: FIF stores times as float32
    lo, hi = spec.get("xlim_ms", [ms[0], ms[-1]])
    if lo < ms[0] - tol or hi > ms[-1] + tol or not lo < 0 < hi:
        die(f"xlim_ms {lo, hi} must lie within the data ({ms[0]:g}–{ms[-1]:g} ms) and include 0")
    t = sample_mask(ms, lo, hi)
    negative_up = spec.get("polarity", "positive_up") == "negative_up"
    if spec.get("overlay", "groups") == "groups":   # compare groups within a panel; one panel per condition
        panels = [(c, spec["conditions"][c]) for c in conds]
        lines = [(g, g) for g in groups]
        get = lambda p, l: data[l][:, conds.index(p)]
        colors = spec.get("colors") or GROUP_COLORS
    else:                                            # compare conditions within a panel; one panel per group
        panels = [(g, g) for g in groups]
        lines = [(c, spec["conditions"][c]) for c in conds]
        get = lambda p, l: data[p][:, conds.index(l)]
        colors = spec.get("colors") or colors_for(len(conds), spec.get("ordered", False))
    if len(lines) > MAX_LINES or len(colors) < len(lines):
        die(f"{len(lines)} overlaid lines; at most {MAX_LINES} and one colour each ({len(colors)} available)")
    labels = [lab for _, lab in lines]  # rule L10: names only; n goes in the caption facts
    kind, comps = spec.get("kind", "combo"), spec.get("components", [])
    for comp in comps:  # preflight every window before drawing anything
        w = sample_mask(ms, comp["tmin_ms"], comp["tmax_ms"])
        if not w.any() or comp["tmin_ms"] < ms[0] - tol or comp["tmax_ms"] > ms[-1] + tol:
            die(f"{comp['name']}: window {comp['tmin_ms']}–{comp['tmax_ms']} ms is outside the data")
    layout = spec.get("layout", "roi")
    if kind != "erp":  # one figure per component, its window is the band
        jobs = [dict(c, bands=[c]) for c in comps]
    elif layout == "grid":
        jobs = [dict(channels=sum(spec["channels"], []), bands=comps)]
    elif layout == "single":
        jobs = [dict(channels=[c], bands=comps) for c in (info.ch_names if spec["channels"] == "all" else spec["channels"])]
    else:
        jobs = [dict(channels=spec["channels"], bands=comps)]
    miss = sorted({ch for j in jobs for ch in j["channels"] if ch not in info.ch_names})
    if miss:
        die(f"channels {miss} not in data")
    if kind == "erp" and layout == "grid":
        return plot_grid(spec, data, info, meta, panels, lines, get, colors, labels, ms, t, lo, hi, negative_up, comps)
    sphere = common_sphere(info)
    computed = []
    for comp in jobs:
        idx = [info.ch_names.index(c) for c in comp["channels"]]
        w = sample_mask(ms, comp["tmin_ms"], comp["tmax_ms"]) if kind != "erp" else t  # erp draws no maps
        stats, topo = {}, {}
        for p, _ in panels:
            for l, _ in lines:
                m, e, tp = line_stats(get(p, l), idx, t, w)
                e = e if spec.get("error", "none") == "sem" else None  # rule S2: no band unless asked
                stats[p, l], topo[p, l] = (m, e), tp
        computed.append((comp, w, stats, topo))
    leg_size = corner = None  # kind "topo" has no waveforms, so no legend to place
    if kind != "topo":
        leg_size = legend_size(spec, len(panels), labels, colors)
        corner = "between" if len(panels) >= 2 else single_panel_corner(
            [[st[panels[0][0], l] for l, _ in lines] for _, _, st, _ in computed],
            [data_ylim(st) for _, _, st, _ in computed],
            [[(b["tmin_ms"], b["tmax_ms"]) for b in c["bands"]] for c, _, _, _ in computed], ms[t], lo, hi, leg_size)
    outs, batch = [], None
    if kind == "erp" and spec["channels"] == "all":  # rule O3: one file per channel, one versioned folder
        batch = versioned(out_root(spec) / "ERP", f"ERP-all-channels_{comparison(spec)}")
        batch.mkdir()
    for comp, w, stats, topo in computed:
        v = v_sensor = max(max(np.abs(a).max() for a in topo.values()), 1e-6)
        gap_mm = GAP_MM
        for _ in range(3 if kind != "topo" else 0):  # at most: widen colour limit, widen gap, final check
            fig, peak, n_lines, n_maps, size, placed = draw(spec, comp, panels, lines, colors, stats, topo, v, info,
                                                            ms, t, lo, hi, negative_up, sphere, leg_size, corner,
                                                            gap_mm)
            changed = False
            if peak > v:  # interpolation overshoots the sensor range: the colour limit must cover the maps
                v, changed = peak, True
            if placed is None and gap_mm == GAP_MM:  # rule L7: widen the waveform-map gap for the legend
                gap_mm, changed = leg_size[3] + 6, True
            if not changed:
                break
            plt.close(fig)
        if kind == "topo":
            fig, peak, n_maps, size = draw_topo(spec, comp, panels, lines, topo, v, info, sphere)
            if peak > v:
                plt.close(fig)
                v = peak
                fig, peak, n_maps, size = draw_topo(spec, comp, panels, lines, topo, v, info, sphere)
            n_lines, placed = 0, "no legend (maps only)"
        if peak > v or placed is None:
            die(f"{comp.get('name', ', '.join(comp['channels']))}: the figure did not pass its own checks (colour limit {v:.2f} vs maps {peak:.2f}; "
                f"legend {placed}); try a taller height_mm")
        want = len(panels) * len(lines)
        if (n_lines, n_maps) != (0 if kind == "topo" else want, 0 if kind == "erp" else want):
            die(f"drew {n_lines} lines / {n_maps} maps for kind {kind!r}, expected {want} of each drawn element")
        chans = "-".join(map(safe, comp["channels"]))
        if kind == "erp":  # rule O3
            stem = f"{'ERP-ROI' if layout == 'roi' else 'ERP'}_{chans}{band_part(comps)}_{comparison(spec)}"
            out = batch / f"{stem}{batch.name[-4:]}" if batch else versioned(out_root(spec) / "ERP", stem)
        else:
            win = f"{comp['tmin_ms']:g}-{comp['tmax_ms']:g}ms"
            stem = {"combo": f"ERP-topo_{comp['name']}_{chans}_{win}",
                    "topo": f"topo_{comp['name']}_{win}"}[kind] + f"_{comparison(spec)}"
            out = versioned(out_root(spec) / KIND_DIR[kind], stem)
        for ext in ("svg", "png"):  # rule T5: PNG to view, SVG with editable text to adjust
            fig.savefig(f"{out}.{ext}", dpi=600 if ext == "png" else None)
        plt.close(fig)
        caption(spec, comp, meta, groups, conds, out, ms, v, sphere, kind)
        write_run(spec, meta, out, comp, ms, size, n_lines, n_maps, legend=placed, gap_mm=float(gap_mm),
                  colour_limit_uV=float(v), sensor_max_uV=float(v_sensor), interpolated_max_uV=float(peak),
                  sphere_m=sphere)
        outs.append(out)
    print("wrote", *([batch] if batch else [f"{o}.png/.svg" for o in outs]), sep="\n  ")


def band_part(comps):
    """File-name part for the gray bands of an erp figure, e.g. _N400-350-500ms (rule O3)."""
    return "".join(f"_{c['name']}-{c['tmin_ms']:g}-{c['tmax_ms']:g}ms" for c in comps)


def write_run(spec, meta, out, comp, ms, size, n_lines, n_maps, **extra):
    """_run.json: everything needed to reproduce and audit the figure; `qa` is filled in by the agent."""
    bands = [dict(name=b["name"], window_samples_ms=[float(x) for x in ms[sample_mask(ms, b["tmin_ms"], b["tmax_ms"])][[0, -1]]])
             for b in comp["bands"]]
    Path(f"{out}_run.json").write_text(json.dumps(dict(
        spec=spec, channels=comp["channels"], bands=bands, **extra, open_items=open_items(spec),
        inputs=meta["inputs"], ids=meta["ids"], contract=meta["contract"],
        code_md5=hashlib.md5(Path(__file__).read_bytes()).hexdigest(), rules="references/rules.md v1",
        versions=dict(mne=mne.__version__, matplotlib=matplotlib.__version__, numpy=np.__version__),
        size_mm=size, lines=n_lines, maps=n_maps,
        qa="PENDING: the agent records the visual QA result here after checking the PNG"),
        indent=1, ensure_ascii=False), encoding="utf8")


def plot_grid(spec, data, info, meta, panels, lines, get, colors, labels, ms, t, lo, hi, negative_up, comps):
    """kind "erp", layout "grid": one figure per facet level (group or condition), a panel per channel at its grid
    cell, the lines overlaid (rule K1)."""
    rows = spec["channels"]
    grid = [[info.ch_names.index(c) for c in r] for r in rows]
    styles = line_styles(spec, len(lines))
    what = "conditions" if spec.get("overlay", "groups") == "conditions" else "groups"
    outs = []
    for p, plabel in panels:
        x = np.array([get(p, l).mean(0) for l, _ in lines])  # (line, ch, t): subject mean
        stem = f"ERP-grid-{len(rows)}x{max(len(r) for r in rows)}_{what}_{safe(plabel)}{band_part(comps)}"  # rule O3
        out = versioned(out_root(spec) / "ERP", stem)
        n = wave_grid(spec, "", grid, info, x, labels, colors, styles, ms, t, lo, hi, negative_up, plabel, out,
                      bands=comps, dpi=600)
        comp = dict(channels=sum(rows, []), bands=comps)
        caption(spec, comp, meta, list(data), list(spec["conditions"]), out, ms, 0, None, "erp")
        write_run(spec, meta, out, comp, ms, list(canvas_size(spec)), n, 0, legend="under the grid")
        outs.append(out)
    print("wrote", *[f"{o}.png/.svg" for o in outs], sep="\n  ")


def caption(spec, comp, meta, groups, conds, out, ms, v, sphere, kind):
    """Caption facts; only elements that the figure of this kind actually draws are described."""
    k = meta["contract"]
    L = [f"# Caption facts for {out.name}", ""]
    if open_items(spec):
        L.append(f"- OPEN (not confirmed): {', '.join(open_items(spec))}")
    L.append(f"- Claim: {spec['claim']}")
    L.append(f"- Key comparison: {spec['key_comparison']}")
    L.append("- Groups: " + ", ".join(f"{g} (n = {len(meta['ids'][g])})" for g in groups))
    if spec.get("exclude"):
        L.append("- Excluded: " + "; ".join(f"{i} ({r})" for i, r in spec["exclude"].items()))
    for i, c in enumerate(conds):
        per = np.array([s[i] for g in groups for s in meta["nave"][g]])
        L.append(f"- {spec['conditions'][c]}: trials per subject mean {per.mean():.1f} (range {per.min()}–{per.max()})")
    L.append(f"- Trial selection: {spec.get('query') or 'as stored in the files (no further selection)'}")
    L.append(f"- Time-locked to: {spec['time_locked_to']}; baseline {k['baseline']} s; "
             f"filter {k['filter'][0]}–{k['filter'][1]} Hz; reference: {spec['reference']}")
    if kind == "erp":
        how = {"single": "channel", "grid": "one panel per channel:", "roi": "mean of"}[spec.get("layout", "roi")]
        L.append(f"- Waveforms: {how} {', '.join(comp['channels'])}")
    for b in comp["bands"]:
        a = ms[sample_mask(ms, b["tmin_ms"], b["tmax_ms"])]
        band = {"combo": "; gray band = topography window", "erp": "; gray band", "topo": ""}[kind]
        roi = {"combo": f"mean of {', '.join(comp['channels'])}; ", "topo": f"ROI {', '.join(comp['channels'])}; ",
               "erp": ""}[kind]
        L.append(f"- {b['name']}: {roi}window {b['tmin_ms']:g}–{b['tmax_ms']:g} ms "
                 f"(samples {a[0]:g}–{a[-1]:g} ms){band}; source: {b['window_source']}")
    if kind != "topo" and spec.get("error", "none") == "sem":
        L.append("- Lines: mean across subjects; shading: ± SEM across subjects at each time point (descriptive, not a test)"
                 + ("; groups with n < 2 have no shading" if any(len(meta['ids'][g]) < 2 for g in groups) else ""))
    elif kind != "topo":
        L.append("- Lines: mean across subjects (no error band)")
    if kind != "erp":
        per = "one per waveform line (same subjects and condition)" if kind == "combo" else "one per group × condition"
        L.append(f"- Topographies: {per}, mean over the window; no electrode marks; shared "
                 f"symmetric colour scale ±{v:.1f} µV and {TOPO['contours']} shared contour intervals; interpolation "
                 f"{TOPO['image_interp']}, extrapolation {TOPO['extrapolate']}, head sphere "
                 f"{[round(s, 4) for s in sphere]} m, MNE {mne.__version__}")
    if kind != "topo":
        L.append(f"- Display: {spec.get('xlim_ms', 'full epoch')} ms; polarity {spec.get('polarity', 'positive_up').replace('_', ' ')}")
    if spec.get("stats_note"):
        L.append(f"- Statistics (from the author): {spec['stats_note']}")
    Path(f"{out}_caption.md").write_text("\n".join(L) + "\n", encoding="utf8")


# ---------- explore: overview figures before windows are known (not paper figures) ----------
EXPLORE_REQUIRED = {"data", "conditions"}
EXPLORE_OPTIONAL = {"width_mm", "height_mm", "group_by", "groups", "exclude", "query", "colors", "linestyles", "ordered", "xlim_ms", "polarity",
                    "channels", "components", "differences", "topo_scale", "cmap"}
EXPLORE_CHANNELS = [["F3", "Fz", "F4"], ["C3", "Cz", "C4"], ["P3", "Pz", "P4"]]  # rows front to back, left to right


def check_explore(spec):
    keys = set(spec)
    if EXPLORE_REQUIRED - keys:
        die(f"explore spec is missing {sorted(EXPLORE_REQUIRED - keys)}")
    if keys - EXPLORE_REQUIRED - EXPLORE_OPTIONAL:
        die(f"unsupported explore keys {sorted(keys - EXPLORE_REQUIRED - EXPLORE_OPTIONAL)}")
    if spec.get("topo_scale", "global") not in ("component", "global"):
        die("topo_scale must be 'component' or 'global'")
    for d in spec.get("differences", []):
        if len(d) != 2 or any(c not in spec["conditions"] for c in d):
            die(f"difference {d}: two condition keys from 'conditions'")
    for c in spec.get("components", []):
        if not {"name", "tmin_ms", "tmax_ms"} <= set(c) or not all(
                isinstance(x, (int, float)) and np.isfinite(x) for x in (c["tmin_ms"], c["tmax_ms"]))                 or not c["tmin_ms"] < c["tmax_ms"]:
            die(f"component {c}: needs name, tmin_ms < tmax_ms, both finite numbers")


def wave_grid(spec, title, grid, info, x, labels, colors, styles, ms, t, lo, hi, negative_up, facet, out, bands=(),
              dpi=300):
    """One figure: a panel per channel at its grid cell, every line of one facet overlaid (x: line × channel × time,
    subject means); gray bands only for given windows; one shared y-range; legend in one row centred under the grid.
    Returns the number of lines drawn."""
    nr, nc = len(grid), max(len(r) for r in grid)
    W, H = canvas_size(spec)  # rule T6
    fig = plt.figure(figsize=(W * MM, H * MM))
    leg_cols = len(labels) if len(labels) <= 4 else -(-len(labels) // 2)  # one row, two rows if more than 4
    leg_mm = 4 + 4 * -(-len(labels) // leg_cols)
    gs = GridSpec(nr, nc, figure=fig, hspace=0.6, wspace=0.35,
                  left=10 / W, right=1 - 4 / W, top=1 - 10 / H, bottom=(6 + leg_mm) / H)
    x = x[:, :, t]
    chans = [i for r in grid for i in r]
    ylim = data_ylim({(c, i): (x[c, i], None) for c in range(len(x)) for i in chans})
    first, n = None, 0
    for r, row in enumerate(grid):
        for c, ch in enumerate(row):
            ax = fig.add_subplot(gs[r, c])
            for b in bands:
                ax.axvspan(b["tmin_ms"], b["tmax_ms"], color="0.88", lw=0, zorder=0)
            for k, (col, ls, lab) in enumerate(zip(colors, styles, labels)):
                ax.plot(ms[t], x[k, ch], color=col, ls=ls, lw=0.8, label=lab)
                n += 1
            ax.set_title(info.ch_names[ch], pad=6, fontsize=7, fontweight="bold")
            cross_axes(ax, fig, lo, hi, ylim, negative_up, ms[t], x[:, ch].min(0), x[:, ch].max(0))
            first = first or ax
    h, lab = first.get_legend_handles_labels()
    order = [i for c in range(leg_cols) for i in range(c, len(h), leg_cols)]  # matplotlib fills columns; read rows
    h, lab = [h[i] for i in order], [lab[i] for i in order]
    fig.legend(h, lab, loc="lower center", bbox_to_anchor=(0.5, 1 / H), ncol=leg_cols, **LEGEND_KW)
    fig.text(0.5, 1 - 3 / H, f"{title} · {facet}" if title else facet, ha="center", va="top", fontsize=8,
             fontweight="bold")
    fig.savefig(f"{out}.png", dpi=dpi)
    fig.savefig(f"{out}.svg")
    plt.close(fig)
    return n


def topo_table(spec, data, conds, labels, comps, info, ms, sphere, facet, out):
    """Rows = conditions (+ difference rows), columns = components; colour scale per column or global; difference
    rows get their own scale (differences are much smaller). Each scale covers its interpolated maps (rule S5)."""
    diffs = spec.get("differences", [])
    rows = [(labels[k], data[:, k]) for k in range(len(conds))]
    rows += [(spec["conditions"][a] + "\n− " + spec["conditions"][b], data[:, conds.index(a)] - data[:, conds.index(b)])
             for a, b in diffs]  # within-subject difference, then averaged below
    n_main = len(conds)
    vals = [[x[:, :, sample_mask(ms, c["tmin_ms"], c["tmax_ms"])].mean(axis=(0, 2)) for c in comps] for _, x in rows]
    per_comp = spec.get("topo_scale", "global") == "component"
    nr, ncmp = len(rows), len(comps)
    key = lambda i, j: (i < n_main, j if per_comp else None)  # which maps share one colour scale
    v = {}
    for i in range(nr):
        for j in range(ncmp):  # 1e-6 floor: an all-zero map (identical conditions) still gets increasing levels
            v[key(i, j)] = max(v.get(key(i, j), 1e-6), float(np.abs(vals[i][j]).max()))
    W, H = canvas_size(spec)  # rule T6
    bar_mm = 6.0 if per_comp else 0.0  # horizontal bar (1.2 mm, 1.5 mm below the maps) + its tick labels

    def render(v):
        fig = plt.figure(figsize=(W * MM, H * MM))
        gs = GridSpec(nr + (1 if diffs else 0), ncmp + 1, figure=fig,
                      height_ratios=[1] * n_main + ([0.25] if diffs else []) + [1] * len(diffs),
                      width_ratios=[1] * ncmp + [0.12], hspace=0.12, wspace=0.08,
                      left=30 / W, right=1 - 12 / W, top=1 - 14 / H, bottom=(4 + bar_mm) / H)
        peak = dict.fromkeys(v, 0.0)
        for i, (lab, _) in enumerate(rows):
            gr = i if i < n_main else i + 1
            for j, c in enumerate(comps):
                vk = v[key(i, j)]
                ax = fig.add_subplot(gs[gr, j])
                im, _ = mne.viz.plot_topomap(vals[i][j], info, axes=ax, show=False, cmap=spec.get("cmap", "RdBu_r"),
                                             vlim=(-vk, vk), contours=np.linspace(-vk, vk, TOPO["contours"] + 1),
                                             sensors=False, extrapolate=TOPO["extrapolate"],
                                             image_interp=TOPO["image_interp"], sphere=sphere)
                a = im.get_array()
                if np.ma.count(a):
                    peak[key(i, j)] = max(peak[key(i, j)], float(np.ma.abs(a).max()))
                if i == 0:
                    ax.set_title(f"{c['name']}\n{c['tmin_ms']:g}–{c['tmax_ms']:g} ms", fontsize=6.5, pad=3)
                if j == 0:
                    ax.text(-0.08, 0.5, lab, transform=ax.transAxes, ha="right", va="center", fontsize=6.5)
            if not per_comp and i in (0, n_main):
                vk = v[key(i, 0)]
                cax = fig.add_subplot(gs[gr:gr + (n_main if i == 0 else len(diffs)), -1])
                cb = fig.colorbar(im, cax=cax, ticks=[-vk, 0, vk])
                cb.ax.set_yticklabels([f"{-vk:.1f}".replace("-", "−"), "0", f"{vk:.1f} µV"], fontsize=5.5)
                cb.outline.set_linewidth(0.4)
        if per_comp:  # one small horizontal bar under each column (and one under the difference block)
            for j in range(ncmp):
                for blk, (r0, r1) in enumerate(((0, n_main), (n_main, nr)) if diffs else ((0, n_main),)):
                    vk = v[key(r0, j)]
                    pos = gs[(r1 - 1) + (1 if blk else 0), j].get_position(fig)
                    cax = fig.add_axes([pos.x0 + pos.width * 0.15, pos.y0 - 2.7 / H, pos.width * 0.7, 1.2 / H])
                    sm = plt.cm.ScalarMappable(cmap=spec.get("cmap", "RdBu_r"), norm=plt.Normalize(-vk, vk))
                    cb = fig.colorbar(sm, cax=cax, orientation="horizontal", ticks=[-vk, 0, vk])
                    cb.ax.set_xticklabels([f"{-vk:.1f}".replace("-", "−"), "0", f"{vk:.1f} µV"], fontsize=5)
                    cb.outline.set_linewidth(0.3)
                    cb.ax.tick_params(length=1.5, width=0.3, pad=1)
        fig.text(0.5, 1 - 3 / H, f"Topographies by condition and component · {facet}", ha="center", va="top",
                 fontsize=8, fontweight="bold")
        return fig, peak

    fig, peak = render(v)
    if any(peak[k] > v[k] for k in v):  # interpolation overshoots the sensor range: widen those scales, redraw
        plt.close(fig)
        v = {k: max(v[k], peak[k]) for k in v}
        fig, peak = render(v)
    fig.savefig(f"{out}.png", dpi=300)
    fig.savefig(f"{out}.svg")
    plt.close(fig)


def explore(spec):
    """Overview before windows are chosen: (1) waveforms at a 3 × 3 grid of channels (frontal / central / parietal ×
    left / midline / right), (2) topographies per condition × component (+ difference maps). One set per group."""
    check_explore(spec)
    plt.rcParams.update(STYLE)
    data, times, info, _ = load(spec)
    conds, groups = list(spec["conditions"]), list(data)
    labels = [spec["conditions"][c] for c in conds]
    colors = spec.get("colors") or colors_for(len(conds), spec.get("ordered", False))
    if len(conds) > MAX_LINES or len(colors) < len(conds):  # rule S8: zip() would drop conditions silently
        die(f"{len(conds)} conditions; at most {MAX_LINES} and one colour each ({len(colors)} available)")
    styles = line_styles(spec, len(conds))
    ms = times * 1000
    tol = 500 / info["sfreq"]  # half a sample: FIF stores times as float32
    lo, hi = spec.get("xlim_ms", [ms[0], ms[-1]])
    if lo < ms[0] - tol or hi > ms[-1] + tol or not lo < hi:
        die(f"xlim_ms {lo, hi} must lie within the data ({ms[0]:g}–{ms[-1]:g} ms)")
    for c in spec.get("components", []):  # a window past the data would be averaged over its overlap only
        if c["tmin_ms"] < ms[0] - tol or c["tmax_ms"] > ms[-1] + tol or not sample_mask(ms, c["tmin_ms"], c["tmax_ms"]).any():
            die(f"{c['name']}: window {c['tmin_ms']}–{c['tmax_ms']} ms is outside the data ({ms[0]:g}–{ms[-1]:g} ms)")
    t = sample_mask(ms, lo, hi)
    neg = spec.get("polarity", "positive_up") == "negative_up"
    rows = spec.get("channels", EXPLORE_CHANNELS)
    missing = [c for r in rows for c in r if c not in info.ch_names]
    if missing:
        die(f"channels {missing} are not in the data")
    grid = [[info.ch_names.index(c) for c in r] for r in rows]
    sphere = common_sphere(info)
    root, shape = out_root(spec), f"{len(rows)}x{max(len(r) for r in rows)}"
    outs = []
    for g in groups:  # rule O3
        outs.append(versioned(root / "ERP", f"ERP-grid-{shape}_conditions_{safe(g)}"))
        wave_grid(spec, "Waveforms", grid, info, data[g].mean(0), labels, colors, styles, ms, t, lo, hi, neg, g, outs[-1])
        if spec.get("components"):
            names = "-".join(c["name"] for c in spec["components"])
            outs.append(versioned(root / "topo", f"topo-table_{safe(names)}_{safe(g)}"))
            topo_table(spec, data[g], conds, labels, spec["components"], info, ms, sphere, g, outs[-1])
    print("wrote", *[f"{o}.png/.svg" for o in outs], sep="\n  ")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    cmd, arg = sys.argv[1], sys.argv[2]
    if cmd == "inspect":
        inspect(arg)
    else:
        spec = json.loads(Path(arg).read_text(encoding="utf8"))
        {"windows": windows, "plot": plot, "explore": explore}[cmd](spec)
