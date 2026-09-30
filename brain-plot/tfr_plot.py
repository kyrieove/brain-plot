"""Time-frequency module for brain-plot (rules TF1…, docs/rules.md; agent guide references/tfr.md).

    python tfr_plot.py plot <spec.json>

Per-subject time-frequency averages of single-trial epochs -> group grand average -> one figure per group,
panels = conditions in a grid, ROI-mean TF maps, with optional windows and topomap rows.
"""
import gc
import hashlib
import json
import shutil
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import mne
import numpy as np

import erp_plot as ep

REQUIRED = {"data", "conditions", "channels", "measure"}
OPTIONAL = {
    "groups", "group_by", "exclude", "query", "grid", "freqs", "n_cycles",
    "decim", "baseline_ms", "baseline_mode", "xlim_ms", "windows", "cmap",
    "width_mm", "height_mm",
}


def check_spec(spec):
    keys = set(spec)
    if REQUIRED - keys:
        ep.die(f"spec is missing required keys: {sorted(REQUIRED - keys)}")
    if keys - REQUIRED - OPTIONAL:
        ep.die(f"unsupported spec keys {sorted(keys - REQUIRED - OPTIONAL)} (see references/spec.md)")
    if spec["measure"] not in ("power", "itc"):
        ep.die(f"measure must be 'power' or 'itc' (got {spec['measure']!r}); set measure to 'power' or 'itc'")
    if not isinstance(spec["channels"], list) or not spec["channels"]:
        ep.die("channels must be a non-empty list of channel names; provide at least one channel")
    if "grid" in spec:
        if not isinstance(spec["grid"], list) or not all(isinstance(r, list) for r in spec["grid"]):
            ep.die("grid must be a list of lists of condition keys")
        for r in spec["grid"]:
            for k in r:
                if k not in spec["conditions"]:
                    ep.die(f"grid key {k!r} not found in conditions ({list(spec['conditions'])}); use valid condition keys in grid")
    if "windows" in spec:
        if not isinstance(spec["windows"], list):
            ep.die("windows must be a list of window dicts")
        for w in spec["windows"]:
            req_w = {"name", "fmin", "fmax", "tmin_ms", "tmax_ms"}
            if req_w - set(w):
                ep.die(f"window is missing keys: {sorted(req_w - set(w))}")
            if w["fmin"] >= w["fmax"]:
                ep.die(f"window {w.get('name')!r} has fmin >= fmax ({w['fmin']} >= {w['fmax']}); fmin must be less than fmax")
            if w["tmin_ms"] >= w["tmax_ms"]:
                ep.die(f"window {w.get('name')!r} has tmin_ms >= tmax_ms ({w['tmin_ms']} >= {w['tmax_ms']}); tmin_ms must be less than tmax_ms")


def get_freqs(spec):
    freqs_spec = spec.get("freqs", {"fmin": 3, "fmax": 40, "n": 30})
    if isinstance(freqs_spec, dict):
        fmin = float(freqs_spec.get("fmin", 3))
        fmax = float(freqs_spec.get("fmax", 40))
        n = int(freqs_spec.get("n", 30))
        return np.geomspace(fmin, fmax, n)
    return np.array(freqs_spec, dtype=float)


def get_n_cycles(spec, freqs):
    n_cycles_spec = spec.get("n_cycles", "freqs/2")
    if n_cycles_spec == "freqs/2":
        return freqs / 2.0, freqs[0] / 2.0
    val = float(n_cycles_spec)
    return val, val


def load_and_compute(spec):
    check_spec(spec)
    groups, groups_all = ep.select_files(spec)
    first_unit = next(iter(groups.values()))[0]
    first_file = ep.unit_files(first_unit)[0]

    try:
        ep_test = mne.read_epochs(first_file, preload=False, verbose="error")
    except Exception as e:
        ep.die(f"cannot read epochs file {first_file}: {e}")

    info = ep_test.info
    missing = [ch for ch in spec["channels"] if ch not in info.ch_names]
    if missing:
        ep.die(f"channels {missing} not in data channels ({info.ch_names}); choose channels present in the data")

    freqs = get_freqs(spec)
    n_cycles, n_cycles_fmin = get_n_cycles(spec, freqs)

    edge_sec = (n_cycles_fmin / freqs[0]) / 2.0
    edge_ms = edge_sec * 1000.0

    epoch_tmin_ms = ep_test.times[0] * 1000.0
    epoch_tmax_ms = ep_test.times[-1] * 1000.0
    valid_tmin_ms = epoch_tmin_ms + edge_ms
    valid_tmax_ms = epoch_tmax_ms - edge_ms

    xlim_ms = spec.get("xlim_ms", [-500, 1500])
    lo, hi = float(xlim_ms[0]), float(xlim_ms[1])
    tol = 1e-3

    if lo < valid_tmin_ms - tol:
        ep.die(f"xlim_ms start ({lo:g} ms) reaches into the edge zone (< {valid_tmin_ms:g} ms, half the longest wavelet {edge_ms:g} ms from epoch start {epoch_tmin_ms:g} ms); widen epochs or adjust xlim_ms/freqs/n_cycles")
    if hi > valid_tmax_ms + tol:
        ep.die(f"xlim_ms end ({hi:g} ms) reaches into the edge zone (> {valid_tmax_ms:g} ms, half the longest wavelet {edge_ms:g} ms from epoch end {epoch_tmax_ms:g} ms); widen epochs or adjust xlim_ms/freqs/n_cycles")

    if spec["measure"] == "power":
        baseline_ms = spec.get("baseline_ms", [-500, -200])
        blo, bhi = float(baseline_ms[0]), float(baseline_ms[1])
        if blo < valid_tmin_ms - tol:
            ep.die(f"baseline_ms start ({blo:g} ms) reaches into the edge zone (< {valid_tmin_ms:g} ms, half the longest wavelet {edge_ms:g} ms from epoch start {epoch_tmin_ms:g} ms); widen epochs or adjust baseline_ms/freqs/n_cycles")
        if bhi > valid_tmax_ms + tol:
            ep.die(f"baseline_ms end ({bhi:g} ms) reaches into the edge zone (> {valid_tmax_ms:g} ms, half the longest wavelet {edge_ms:g} ms from epoch end {epoch_tmax_ms:g} ms); widen epochs or adjust baseline_ms/freqs/n_cycles")
        if blo >= bhi:
            ep.die(f"baseline_ms start ({blo:g} ms) must be less than end ({bhi:g} ms); adjust baseline_ms")

    for w in spec.get("windows", []):
        if w["fmin"] < freqs[0] - 1e-6 or w["fmax"] > freqs[-1] + 1e-6 or w["tmin_ms"] < lo - tol or w["tmax_ms"] > hi + tol:
            ep.die(f"window {w.get('name')!r} ({w['fmin']}–{w['fmax']} Hz, {w['tmin_ms']}–{w['tmax_ms']} ms) outside freqs ({freqs[0]:g}–{freqs[-1]:g} Hz) or xlim_ms ({lo:g}–{hi:g} ms); adjust window bounds to stay inside freqs and xlim_ms")

    n_cycles_label = spec.get("n_cycles", "freqs/2")
    n_cycles_label = n_cycles_label if isinstance(n_cycles_label, str) else float(n_cycles_label)
    baseline_ms = spec.get("baseline_ms", [-500, -200])
    decim = spec.get("decim")
    if decim is None:
        decim = max(1, int(round(info["sfreq"] / 100.0)))

    tf_dict = {
        "freqs": [round(float(f), 4) for f in freqs],
        "n_cycles": n_cycles_label,
        "decim": int(decim),
        "query": spec.get("query"),
        "conditions": list(spec["conditions"]),
    }
    param_hash = hashlib.md5(json.dumps(tf_dict, sort_keys=True).encode()).hexdigest()[:8]
    cache_dir = ep.out_root(spec) / ".cache" / "tfr" / param_hash
    cache_dir.mkdir(parents=True, exist_ok=True)

    sub_tfrs = {}
    trial_counts = {}
    valid_ids = {}

    for g, fs in groups.items():
        valid_ids[g] = []
        trial_counts[g] = {}
        for u in fs:
            f = ep.unit_files(u)[0]
            s_id = ep.uid(f)
            cfile = cache_dir / f"{s_id}.h5"
            tfr_dict = {}
            counts = {}

            if cfile.exists():
                cfile.touch()
                try:
                    loaded = mne.time_frequency.read_tfrs(cfile)
                    for obj in loaded:
                        c, mtype = obj.comment.split("/")
                        tfr_dict.setdefault(c, {})[mtype] = obj
                        counts[c] = int(obj.nave)
                except Exception:
                    tfr_dict = {}

            if not tfr_dict:
                try:
                    ep_sub = mne.read_epochs(f, proj=False, verbose="error")
                except Exception as e:
                    print(f"WARNING: skipping unreadable/incomplete file {f.name}: {e}")
                    continue

                if spec.get("query"):
                    ep_sub = ep_sub[spec["query"]]

                objs_to_save = []
                for c in spec["conditions"]:
                    if len(ep_sub[c]) == 0:
                        ep.die(f"{f.name}: no trials left for '{c}' (query={spec.get('query')!r})")
                    p, itc = ep_sub[c].compute_tfr(
                        "morlet", freqs=freqs, n_cycles=n_cycles, decim=decim,
                        return_itc=True, average=True,
                    )
                    p.comment = f"{c}/power"
                    itc.comment = f"{c}/itc"
                    tfr_dict.setdefault(c, {})["power"] = p
                    tfr_dict.setdefault(c, {})["itc"] = itc
                    counts[c] = int(p.nave)
                    objs_to_save.extend([p, itc])

                mne.time_frequency.write_tfrs(cfile, objs_to_save, overwrite=True)
                del ep_sub
                gc.collect()

            sub_tfrs[g, s_id] = tfr_dict
            trial_counts[g][s_id] = counts
            valid_ids[g].append(s_id)

        if not valid_ids[g]:
            ep.die(f"group {g!r} has no valid readable subject files")

    tfr_cache_root = ep.out_root(spec) / ".cache" / "tfr"
    if tfr_cache_root.exists():
        for old_dir in sorted([p for p in tfr_cache_root.iterdir() if p.is_dir()], key=lambda p: p.stat().st_mtime_ns, reverse=True)[ep.CACHE_KEEP:]:
            if old_dir != cache_dir:
                shutil.rmtree(old_dir, ignore_errors=True)

    measure = spec["measure"]
    grand_avg = {}
    for g in groups:
        for c in spec["conditions"]:
            sub_arrs = []
            for s_id in valid_ids[g]:
                tfr = sub_tfrs[g, s_id][c][measure].copy()
                if measure == "power":
                    b_sec = (baseline_ms[0] / 1000.0, baseline_ms[1] / 1000.0)
                    b_mode = spec.get("baseline_mode", "logratio")
                    tfr.apply_baseline(b_sec, mode=b_mode)
                    if b_mode == "logratio":
                        tfr.data *= 10.0
                sub_arrs.append(tfr.data)
            grand_avg[g, c] = np.mean(sub_arrs, axis=0)

    sample_tfr = next(iter(sub_tfrs.values()))[next(iter(spec["conditions"]))]["power"]
    times = sample_tfr.times * 1000.0

    tf_params = dict(
        freqs={"fmin": float(freqs[0]), "fmax": float(freqs[-1]), "n": len(freqs)},
        n_cycles=n_cycles_label,
        decim=int(decim),
        baseline_ms=baseline_ms if measure == "power" else None,
        baseline_mode=spec.get("baseline_mode", "logratio") if measure == "power" else None,
        xlim_ms=[lo, hi],
        query=spec.get("query"),
    )

    return grand_avg, times, freqs, info, valid_ids, trial_counts, tf_params


def write_run_json(out, spec, valid_ids, trial_counts, tf_params, color_limits, layout_issues, size_mm):
    data = dict(
        spec=spec,
        ids=valid_ids,
        trials=trial_counts,
        tf_params=tf_params,
        color_limits=color_limits,
        layout_issues=layout_issues,
        code_md5=hashlib.md5(Path(__file__).read_bytes()).hexdigest(),
        versions=dict(mne=mne.__version__, matplotlib=matplotlib.__version__, numpy=np.__version__),
        size_mm=size_mm,
        qa="PENDING: the agent records the visual QA result here after checking the PNG",
    )
    Path(f"{out}_run.json").write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf8")


def write_caption_md(out, spec, group, n_subj, tf_params):
    measure_str = "Total power (dB relative to baseline)" if spec["measure"] == "power" else "Inter-trial phase coherence (ITC)"
    f_info = tf_params["freqs"]
    lines = [
        f"# Caption for {out.name}",
        "",
        f"- **Measure**: {measure_str}",
        "- **Method**: Morlet wavelets",
        f"- **Frequencies**: {f_info['fmin']:.1f}–{f_info['fmax']:.1f} Hz ({f_info['n']} log-spaced)",
        f"- **Wavelet cycles**: {tf_params['n_cycles']}",
    ]
    if spec["measure"] == "power":
        b_ms = tf_params["baseline_ms"]
        lines.append(f"- **Baseline**: {b_ms[0]:g} to {b_ms[1]:g} ms ({tf_params['baseline_mode']})")
    else:
        lines.append("- **Baseline**: None (ITC)")
    lines.extend([
        f"- **Group**: {group} (N = {n_subj})",
        f"- **ROI channels**: {', '.join(spec['channels'])}",
        f"- **Time range**: {tf_params['xlim_ms'][0]:g} to {tf_params['xlim_ms'][1]:g} ms",
    ])
    if spec.get("windows"):
        w_strs = [f"{w['name']} ({w['fmin']:g}–{w['fmax']:g} Hz, {w['tmin_ms']:g}–{w['tmax_ms']:g} ms)" for w in spec["windows"]]
        lines.append(f"- **Windows**: {'; '.join(w_strs)}")
    else:
        lines.append("- **Windows**: None")
    lines.append("")
    Path(f"{out}_caption.md").write_text("\n".join(lines), encoding="utf8")


def plot(spec):
    plt.rcParams.update(ep.STYLE)
    grand_avg, times, freqs, info, valid_ids, trial_counts, tf_params = load_and_compute(spec)

    cond_keys = list(spec["conditions"])
    grid = spec.get("grid") or [cond_keys[i:i + 3] for i in range(0, len(cond_keys), 3)]
    nr = len(grid)
    nc = max(len(r) for r in grid)
    windows = spec.get("windows", [])
    nw = len(windows)
    measure = spec["measure"]

    lo, hi = float(tf_params["xlim_ms"][0]), float(tf_params["xlim_ms"][1])
    t_mask = (times >= lo - 1e-3) & (times <= hi + 1e-3)
    times_plot = times[t_mask]

    W = float(spec.get("width_mm", 180))
    left_mm = 16.0
    right_mm = 20.0
    wspace_mm = 9.0
    pw = (W - left_mm - right_mm - (nc - 1) * wspace_mm) / nc
    ph = pw / 1.4

    top_mm = 14.0
    hspace_mm = 18.0
    tf_h = top_mm + nr * ph + (nr - 1) * hspace_mm + 16.0
    topo_h = 26.0 * nw
    H = float(spec.get("height_mm", tf_h + topo_h))

    roi_idx = [info.ch_names.index(ch) for ch in spec["channels"]]
    sphere = ep.common_sphere(info)

    out_paths = []

    for g, subs in valid_ids.items():
        fig = plt.figure(figsize=(W * ep.MM, H * ep.MM))
        fig.text(0.5, 1 - 3.0 / H, str(g), ha="center", va="top", fontsize=8, fontweight="bold")

        roi_tf = {}
        for c in cond_keys:
            roi_tf[c] = grand_avg[g, c][roi_idx, :, :][:, :, t_mask].mean(axis=0)

        if measure == "power":
            max_val = max(np.max(np.abs(roi_tf[c])) for c in cond_keys)
            v = float(np.ceil(max_val * 10) / 10)
            if v == 0:
                v = 1.0
            vmin, vmax = -v, v
            cmap = spec.get("cmap", "RdBu_r")
        else:
            max_val = max(np.max(roi_tf[c]) for c in cond_keys)
            v = float(np.ceil(max_val * 100) / 100)
            if v == 0:
                v = 1.0
            vmin, vmax = 0.0, v
            cmap = spec.get("cmap", "Reds")

        panel_idx = 0
        im = None
        y_top = H - top_mm

        for r_idx, row in enumerate(grid):
            y_bottom = y_top - (r_idx + 1) * ph - r_idx * hspace_mm
            for c_idx, c_key in enumerate(row):
                x_left = left_mm + c_idx * (pw + wspace_mm)
                ax = fig.add_axes([x_left / W, y_bottom / H, pw / W, ph / H])

                im = ax.pcolormesh(
                    times_plot, freqs, roi_tf[c_key],
                    shading="gouraud", cmap=cmap, vmin=vmin, vmax=vmax, rasterized=True,
                )
                ax.set_yscale("log")
                ax.set_ylim(freqs[0], freqs[-1])
                ax.set_xlim(lo, hi)

                ax.spines["left"].set_position(("axes", 0))
                ax.spines["bottom"].set_position(("axes", 0))
                ax.spines["left"].set_linewidth(0.6)
                ax.spines["bottom"].set_linewidth(0.6)
                ax.spines["top"].set_visible(False)
                ax.spines["right"].set_visible(False)
                ax.tick_params(
                    bottom=True, left=True, top=False, right=False,
                    direction="out", length=2.5, width=0.6, pad=1.5, labelsize=6,
                )

                y_ticks = [f for f in [4, 8, 13, 30] if freqs[0] <= f <= freqs[-1]]
                ax.yaxis.set_minor_locator(plt.NullLocator())
                ax.yaxis.set_minor_formatter(plt.NullFormatter())
                ax.set_yticks(y_ticks)
                ax.set_yticklabels([str(f) for f in y_ticks])

                xt, labs, _ = ep.x_ticks(ax, fig, lo, hi, zero=True)
                ax.set_xticks(xt)
                ax.set_xticklabels(labs)

                if c_idx == 0:
                    ax.set_ylabel("Frequency (Hz)", fontsize=6, labelpad=2)
                else:
                    ax.set_ylabel("")

                if r_idx == nr - 1:
                    ax.set_xlabel("Time (ms)", fontsize=6, labelpad=2)
                else:
                    ax.set_xlabel("")

                ax.axvline(0, color="0.3", lw=0.4, ls=":", zorder=2)

                m_title = "Power" if measure == "power" else "ITC"
                ax.set_title(f"{m_title} · " + ", ".join(spec["channels"]), pad=6, fontsize=7)
                ep.letter(ax, panel_idx)

                cond_ytext = -26 if r_idx == nr - 1 else -18
                ax.annotate(
                    spec["conditions"][c_key], (0.5, 0),
                    xycoords="axes fraction", xytext=(0, cond_ytext),
                    textcoords="offset points", ha="center", va="top",
                    fontsize=7.5, fontweight="bold",
                )

                for w in windows:
                    rect = Rectangle(
                        (w["tmin_ms"], w["fmin"]),
                        w["tmax_ms"] - w["tmin_ms"], w["fmax"] - w["fmin"],
                        fill=False, edgecolor="black", linestyle="--", linewidth=0.6, zorder=3,
                    )
                    ax.add_patch(rect)
                    ax.text(w["tmin_ms"] + 4, w["fmax"] * 1.04, w["name"], fontsize=6, ha="left", va="bottom", zorder=4)

                panel_idx += 1

        top_y_grid = H - top_mm
        bot_y_grid = y_top - nr * ph - (nr - 1) * hspace_mm
        bh = min(0.45 * (top_y_grid - bot_y_grid), 45.0)
        cbar_x = left_mm + nc * pw + (nc - 1) * wspace_mm + 7.0
        cax = fig.add_axes([cbar_x / W, ((top_y_grid + bot_y_grid) / 2 - bh / 2) / H, 2.0 / W, bh / H])

        cb_ticks = [-v, 0, v] if measure == "power" else [0, v]
        cb = fig.colorbar(im, cax=cax, ticks=cb_ticks)
        if measure == "power":
            cb.ax.set_yticklabels([f"{-v:.1f}".replace("-", "−"), "0", f"{v:.1f}"])
        else:
            cb.ax.set_yticklabels(["0", f"{v:.2f}"])
        cb.ax.set_title("dB" if measure == "power" else "ITC", fontsize=6, pad=3)
        cb.ax.tick_params(labelsize=6, width=0.4, length=2)
        cb.outline.set_linewidth(0.4)

        reading_conds = [c for r in grid for c in r]
        n_conds = len(reading_conds)
        color_limits = dict(panels=dict(v=v, vmin=vmin, vmax=vmax, cmap=cmap))

        for w_idx, w in enumerate(windows):
            row_top = bot_y_grid - 15.0 - w_idx * 26.0
            row_h = 24.0
            f_mask = (freqs >= w["fmin"] - 1e-6) & (freqs <= w["fmax"] + 1e-6)
            wt_mask = (times >= w["tmin_ms"] - 1e-3) & (times <= w["tmax_ms"] + 1e-3)

            row_topos = [grand_avg[g, c][:, f_mask, :][:, :, wt_mask].mean(axis=(1, 2)) for c in reading_conds]
            max_topo = max(np.max(np.abs(val)) for val in row_topos)
            dec = 10 if measure == "power" else 100  # labels show 1 / 2 decimals
            v_row = float(np.ceil(max_topo * dec) / dec) or 1.0
            lo_row = -v_row if measure == "power" else 0.0  # ITC is 0…1: no negative half
            color_limits[f"window_{w['name']}"] = dict(v=v_row, vmin=lo_row, vmax=v_row)

            levels = np.linspace(lo_row, v_row, ep.TOPO["contours"] + 1)
            fig.text(
                left_mm / W, (row_top - 1.0) / H,
                f"{w['name']}  {w['fmin']:g}–{w['fmax']:g} Hz, {w['tmin_ms']:g}–{w['tmax_ms']:g} ms",
                ha="left", va="top", fontsize=6.5,
            )

            W_topo = nc * pw + (nc - 1) * wspace_mm
            map_size_mm = min(16.0, (W_topo - (n_conds - 1) * 3.0) / n_conds)
            map_gap = (W_topo - n_conds * map_size_mm) / max(1, n_conds - 1)
            map_y = row_top - 5.0 - map_size_mm
            last_im = None

            for m_idx, (c_key, t_val) in enumerate(zip(reading_conds, row_topos)):
                mx = left_mm + m_idx * (map_size_mm + map_gap)
                tax = fig.add_axes([mx / W, map_y / H, map_size_mm / W, map_size_mm / H])
                last_im, _ = mne.viz.plot_topomap(
                    t_val, info, axes=tax, show=False, cmap=cmap,
                    vlim=(lo_row, v_row), contours=levels, sensors=False,
                    extrapolate=ep.TOPO["extrapolate"], image_interp=ep.TOPO["image_interp"],
                    sphere=sphere, mask_params=dict(markeredgewidth=0.3),
                )
                tax.text(0.5, -0.06, spec["conditions"][c_key], transform=tax.transAxes, ha="center", va="top", fontsize=5.5)

            cax_row = fig.add_axes([cbar_x / W, map_y / H, 2.0 / W, map_size_mm / H])
            cb_row = fig.colorbar(last_im, cax=cax_row, ticks=[lo_row, 0, v_row] if lo_row else [0, v_row])
            cb_row.ax.set_yticklabels(([f"{-v_row:.1f}".replace("-", "−")] if lo_row else []) + ["0", f"{v_row:.1f}" if lo_row else f"{v_row:.2f}"])
            cb_row.ax.set_title("dB" if measure == "power" else "ITC", fontsize=6, pad=2)
            cb_row.ax.tick_params(labelsize=6, width=0.4, length=2)
            cb_row.outline.set_linewidth(0.4)

        win_part = ("_" + "-".join(ep.safe(w["name"]) for w in windows)) if windows else ""
        out_stem = f"TFR-{measure}_{'-'.join(map(ep.safe, spec['channels']))}_{ep.safe(g)}{win_part}"
        out = ep.versioned(ep.out_root(spec) / "TFR", out_stem)

        issues = ep.report_layout(fig, out.name)
        fig.savefig(f"{out}.png", dpi=600)
        fig.savefig(f"{out}.svg")
        plt.close(fig)

        write_run_json(out, spec, valid_ids, trial_counts, tf_params, color_limits, issues, [W, H])
        write_caption_md(out, spec, g, len(subs), tf_params)
        ep.archive(out)
        out_paths.append(out)
        print("wrote", f"{out}.png/.svg")

    return out_paths


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) < 3 or sys.argv[1] != "plot":
        ep.die("usage: python tfr_plot.py plot <spec.json>")
    plot(ep.read_spec(sys.argv[2]))
