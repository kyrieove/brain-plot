"""Source reconstruction module for brain-plot (dSPM on fsaverage; docs/rules.md SRC1-SRC6).

    python source_plot.py plot <spec.json>

Per-subject epochs -> average reference + baseline -> noise cov -> evoked -> forward solution on
fsaverage -> inverse operator (dSPM/sLORETA/eLORETA) -> grand average stc -> publication figure
with inflated cortical maps and horizontal colorbars.
"""
import hashlib
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mne
import numpy as np
import pyvista
pyvista.OFF_SCREEN = True

import erp_plot as ep

REQUIRED = {"data", "conditions"}
OPTIONAL = {
    "subjects", "exclude", "query", "method", "lambda2", "loose", "depth",
    "noise_cov_ms", "baseline_ms", "figure", "windows", "times_ms", "half_width_ms",
    "threshold_pct", "max_pct", "width_mm", "height_mm", "time_locked_to",
    "group_by", "subjects_dir", "src", "bem",
}

DEFAULT_SUBJECTS_DIR = r"C:\Users\ASUS\mne_data\MNE-fsaverage-data"


def check_spec(spec):
    keys = set(spec)
    if REQUIRED - keys:
        ep.die(f"spec is missing required keys: {sorted(REQUIRED - keys)}")
    if keys - REQUIRED - OPTIONAL:
        ep.die(f"unsupported spec keys {sorted(keys - REQUIRED - OPTIONAL)} (see references/spec.md)")
    if not isinstance(spec["conditions"], dict) or not spec["conditions"]:
        ep.die("conditions must be a non-empty {key: label} dictionary")

    fig_type = spec.get("figure", "windows")
    if fig_type not in ("windows", "timeline"):
        ep.die(f"figure must be 'windows' or 'timeline' (got {fig_type!r})")

    method = spec.get("method", "dSPM")
    if method not in ("dSPM", "sLORETA", "eLORETA"):
        ep.die(f"method must be 'dSPM', 'sLORETA', or 'eLORETA' (got {method!r})")

    noise_cov = spec.get("noise_cov_ms", [-200, 0])
    if not (isinstance(noise_cov, (list, tuple)) and len(noise_cov) == 2 and noise_cov[0] < noise_cov[1]):
        ep.die(f"noise_cov_ms must be [tmin, tmax] with tmin < tmax (got {noise_cov!r})")
    if noise_cov[1] > 0:
        ep.die(f"noise_cov_ms cannot end after 0 ms (got {noise_cov!r})")

    baseline = spec.get("baseline_ms", [-200, 0])
    if not (isinstance(baseline, (list, tuple)) and len(baseline) == 2 and baseline[0] < baseline[1]):
        ep.die(f"baseline_ms must be [tmin, tmax] with tmin < tmax (got {baseline!r})")

    if fig_type == "windows":
        windows = spec.get("windows")
        if not (isinstance(windows, list) and windows):
            ep.die("figure 'windows' requires a non-empty list of window dicts in 'windows'")
        for w in windows:
            req_w = {"name", "tmin_ms", "tmax_ms"}
            if req_w - set(w):
                ep.die(f"window dict missing keys: {sorted(req_w - set(w))}")
            if w["tmin_ms"] >= w["tmax_ms"]:
                ep.die(f"window {w.get('name')!r}: tmin_ms ({w['tmin_ms']}) must be less than tmax_ms ({w['tmax_ms']})")

    if fig_type == "timeline":
        times = spec.get("times_ms", [100, 200, 300, 400, 500, 600, 700, 800])
        if not (isinstance(times, list) and times and all(isinstance(x, (int, float)) for x in times)):
            ep.die("times_ms must be a non-empty list of numbers")
        half_w = spec.get("half_width_ms", 50)
        if not (isinstance(half_w, (int, float)) and half_w > 0):
            ep.die("half_width_ms must be a positive number")

    thresh_pct = spec.get("threshold_pct", 90.0)
    max_pct = spec.get("max_pct", 99.5)
    if not (0 <= thresh_pct < max_pct <= 100):
        ep.die(f"must have 0 <= threshold_pct < max_pct <= 100 (got {thresh_pct}, {max_pct})")


def select_source_files(spec):
    selection_spec = {k: v for k, v in spec.items() if k != "group_by"}
    groups, _ = ep.select_files(selection_spec)
    by_id = {}
    excl = spec.get("exclude", {})
    if isinstance(excl, list):
        excl = {i: "" for i in excl}
    for units in groups.values():
        for unit in units:
            for f in ep.unit_files(unit):
                if not f.name.endswith("-epo.fif"):
                    ep.die(f"{f.name}: source reconstruction requires epochs files")
                by_id[ep.uid(unit)] = f

    if "subjects" in spec:
        req_subs = spec["subjects"]
        if not isinstance(req_subs, list) or not all(isinstance(x, str) for x in req_subs):
            ep.die("spec 'subjects' must be a list of subject IDs")
        for s in req_subs:
            if s not in by_id:
                ep.die(f"requested subject {s!r} not found in data files")
        active_ids = [s for s in req_subs if s not in excl]
    else:
        active_ids = [s for s in sorted(by_id) if s not in excl]

    if not active_ids:
        ep.die("no subjects left after exclude / subjects filtering")

    return {s: by_id[s] for s in active_ids}, excl


class BrainRenderer:
    def __init__(self, subjects_dir, src):
        self.subjects_dir = str(subjects_dir)
        self.src = src
        self.vertno = {
            "lh": src[0]["vertno"],
            "rh": src[1]["vertno"],
        }

    def render(self, hemi, values, fmin, fmid, fmax, figure="figure", row="row", col="col"):
        b = mne.viz.Brain(
            "fsaverage", hemi, "inflated",
            subjects_dir=self.subjects_dir,
            background="white", cortex="low_contrast",
            show=True, size=800,
        )
        b.show_view("lateral")
        v = self.vertno[hemi]
        b.add_data(
            values, fmin=fmin, fmid=fmid, fmax=fmax,
            transparent=True, colormap="hot", colorbar=False,
            vertices=v, hemi=hemi, smoothing_steps=10,
        )
        raw_img = b.screenshot()
        b.close()

        mask = ~np.all(raw_img >= 254, axis=-1)
        if float(np.mean(mask)) < 0.20:
            ep.die(f"blank brain image: {figure} {row} {col} {hemi}")

        r0, r1 = np.where(mask.any(axis=1))[0][[0, -1]]
        c0, c1 = np.where(mask.any(axis=0))[0][[0, -1]]
        return raw_img[r0:r1 + 1, c0:c1 + 1]

def load_and_compute(spec, subjects_dir=None, src=None, bem=None, fwd=None):
    check_spec(spec)
    active_files, excluded = select_source_files(spec)
    s_ids = sorted(active_files)

    s_dir = Path(subjects_dir or spec.get("subjects_dir") or DEFAULT_SUBJECTS_DIR).resolve()
    if isinstance(src, (str, Path)):
        src_obj = mne.read_source_spaces(src, verbose="error")
        src_name = Path(src).name
    elif src is not None:
        src_obj = src
        src_name = "custom-src"
    else:
        src_path = Path(spec.get("src") or (s_dir / "fsaverage" / "bem" / "fsaverage-ico-5-src.fif"))
        src_obj = mne.read_source_spaces(src_path, verbose="error")
        src_name = src_path.name

    if isinstance(bem, (str, Path)):
        bem_obj = mne.read_bem_solution(bem, verbose="error")
        bem_name = Path(bem).name
    elif bem is not None:
        bem_obj = bem
        bem_name = "custom-bem"
    else:
        bem_path = Path(spec.get("bem") or (s_dir / "fsaverage" / "bem" / "fsaverage-5120-5120-5120-bem-sol.fif"))
        bem_obj = mne.read_bem_solution(bem_path, verbose="error")
        bem_name = bem_path.name

    method = spec.get("method", "dSPM")
    lambda2 = float(spec.get("lambda2", 1.0 / 9.0))
    loose = float(spec.get("loose", 0.2))
    depth = float(spec.get("depth", 0.8))
    noise_cov_ms = [float(x) for x in spec.get("noise_cov_ms", [-200, 0])]
    baseline_ms = [float(x) for x in spec.get("baseline_ms", [-200, 0])]
    cond_keys = list(spec["conditions"])

    param_dict = {
        "cache_version": 2,
        "conditions": cond_keys,
        "query": spec.get("query"),
        "baseline_ms": baseline_ms,
        "noise_cov_ms": noise_cov_ms,
        "method": method,
        "lambda2": lambda2,
        "loose": loose,
        "depth": depth,
        "src": src_name,
        "bem": bem_name,
    }
    param_hash = hashlib.md5(json.dumps(param_dict, sort_keys=True).encode()).hexdigest()[:8]
    cache_dir = ep.out_root(spec) / ".cache" / "source" / param_hash
    cache_dir.mkdir(parents=True, exist_ok=True)

    sorted_subj_str = "_".join(s_ids)
    ga_hash = hashlib.md5((param_hash + sorted_subj_str).encode()).hexdigest()[:8]
    ga_cache = cache_dir / f"grand_avg_{ga_hash}.npz"

    # Forward solution
    fwd_file = cache_dir / "fsaverage-fwd.fif"
    if fwd is not None:
        fwd_sol = fwd
    elif fwd_file.exists():
        fwd_sol = mne.read_forward_solution(fwd_file, verbose="error")
    else:
        sibling_fwds = list(cache_dir.parent.glob("*/fsaverage-fwd.fif"))
        if sibling_fwds:
            fwd_sol = mne.read_forward_solution(sibling_fwds[0], verbose="error")
            mne.write_forward_solution(fwd_file, fwd_sol, overwrite=True, verbose="error")
        else:
            first_ep = mne.read_epochs(active_files[s_ids[0]], preload=False, proj=False, verbose="error")
            first_info = first_ep.info.copy()
            with first_info._unlock():
                first_info["sfreq"] = 100.0
            ev_proto = mne.EvokedArray(np.zeros((len(first_info["ch_names"]), 10)), first_info, tmin=0)
            ev_proto.set_eeg_reference("average", projection=True)
            fwd_sol = mne.make_forward_solution(
                ev_proto.info, trans="fsaverage", src=src_obj, bem=bem_obj,
                eeg=True, meg=False, mindist=5.0, n_jobs=2, verbose="error",
            )
            mne.write_forward_solution(fwd_file, fwd_sol, overwrite=True, verbose="error")

    first_ch_names = None
    trial_counts = {}
    valid_ids = []

    # Check if grand average is already cached
    if ga_cache.exists():
        with np.load(ga_cache, allow_pickle=True) as z:
            if "subject_p99" in z and "outlier_subjects" in z and "rank" in z:
                grand_avg = z["data"]
                times_s = z["times"]
                trial_counts = json.loads(str(z["trial_counts"]))
                valid_ids = json.loads(str(z["valid_ids"]))
                param_dict["subject_p99"] = json.loads(str(z["subject_p99"]))
                param_dict["outlier_subjects"] = json.loads(str(z["outlier_subjects"]))
                param_dict["rank"] = json.loads(str(z["rank"]))
                return grand_avg, times_s, s_dir, src_obj, valid_ids, excluded, trial_counts, param_dict

    running_sum = None
    times_s = None
    subject_p99 = {}
    subject_ranks = {}

    for i_sub, s_id in enumerate(s_ids):
        print(f"[{i_sub+1}/{len(s_ids)}] {s_id}", flush=True)
        f = active_files[s_id]
        subj_cache = cache_dir / f"{s_id}.npz"
        cache_valid = False
        if subj_cache.exists():
            try:
                with np.load(subj_cache, allow_pickle=True) as z:
                    if "rank" in z:
                        evoked_data = z["evoked_data"]
                        nave = [int(n) for n in z["nave"]]
                        cov_data = z["cov_data"]
                        cov_bads = list(z["cov_bads"])
                        cov_nfree = int(z["cov_nfree"])
                        ch_names = list(z["ch_names"])
                        times_sub = z["times"]
                        rank = json.loads(str(z["rank"]))
                        cache_valid = True
            except Exception:
                cache_valid = False

        if not cache_valid:
            try:
                ep_sub = mne.read_epochs(f, proj=False, verbose="error")
            except Exception as e:
                print(f"WARNING: skipping unreadable subject {s_id}: {e}")
                continue

            ep_sub = ep.query_epochs(ep_sub, f, cond_keys, spec.get("query"))
            t_epoch_min = ep_sub.times[0] * 1000.0
            t_epoch_max = ep_sub.times[-1] * 1000.0
            if noise_cov_ms[0] < t_epoch_min - 1e-3 or noise_cov_ms[1] > t_epoch_max + 1e-3:
                ep.die(f"noise_cov_ms [{noise_cov_ms[0]}, {noise_cov_ms[1]}] ms outside epoch range [{t_epoch_min:.0f}, {t_epoch_max:.0f}] ms")
            if noise_cov_ms[1] > 0:
                ep.die(f"noise_cov_ms [{noise_cov_ms[0]}, {noise_cov_ms[1]}] ms ends after 0 ms")

            ep_sub.set_eeg_reference("average", projection=True)
            ep_sub.apply_baseline((baseline_ms[0] / 1000.0, baseline_ms[1] / 1000.0))

            rank = mne.compute_rank(ep_sub, tol=1e-6, tol_kind="relative")

            cov = mne.compute_covariance(
                ep_sub, tmin=noise_cov_ms[0] / 1000.0, tmax=noise_cov_ms[1] / 1000.0,
                method="shrunk", rank=rank, verbose="error",
            )
            sfreq = ep_sub.info["sfreq"]
            decim = max(1, int(round(sfreq / 100.0)))
            t_min_crop = max(ep_sub.times[0], -0.2)
            t_max_crop = min(ep_sub.times[-1], 1.0)
            evokeds = [ep_sub[c].average().crop(tmin=t_min_crop, tmax=t_max_crop).decimate(decim) for c in cond_keys]

            evoked_data = np.array([e.data for e in evokeds])
            nave = [int(e.nave) for e in evokeds]
            cov_data = cov.data
            cov_bads = list(cov["bads"])
            cov_nfree = int(cov["nfree"])
            ch_names = list(ep_sub.info["ch_names"])
            times_sub = evokeds[0].times

            np.savez(
                subj_cache,
                evoked_data=evoked_data,
                nave=nave,
                cov_data=cov_data,
                cov_bads=cov_bads,
                cov_nfree=cov_nfree,
                ch_names=ch_names,
                times=times_sub,
                rank=json.dumps(rank),
            )

        if first_ch_names is None:
            first_ch_names = ch_names
        elif ch_names != first_ch_names:
            ep.die(f"subject {s_id} channel names differ from first subject")

        info_sub = mne.io.read_info(f, verbose="error")
        with info_sub._unlock():
            info_sub["sfreq"] = 100.0
        ev_proto = mne.EvokedArray(evoked_data[0], info_sub, tmin=times_sub[0], nave=nave[0])
        ev_proto.set_eeg_reference("average", projection=True)
        info_with_proj = ev_proto.info

        cov_sub = mne.Covariance(cov_data, ch_names, cov_bads, info_with_proj["projs"], cov_nfree)
        inv = mne.minimum_norm.make_inverse_operator(info_with_proj, fwd_sol, cov_sub, loose=loose, depth=depth, rank=rank, verbose="error")

        trial_counts[s_id] = {c: int(n) for c, n in zip(cond_keys, nave)}
        valid_ids.append(s_id)
        subject_p99[s_id] = {}
        subject_ranks[s_id] = rank["eeg"] if isinstance(rank, dict) and "eeg" in rank else rank

        for i, c in enumerate(cond_keys):
            ev_obj = mne.EvokedArray(evoked_data[i], info_with_proj, tmin=times_sub[0], nave=nave[i])
            stc = mne.minimum_norm.apply_inverse(ev_obj, inv, lambda2=lambda2, method=method, pick_ori=None, verbose="error")
            stc_arr = stc.data.astype(np.float32)

            if running_sum is None:
                running_sum = np.zeros((len(cond_keys), stc_arr.shape[0], stc_arr.shape[1]), dtype=np.float32)
                times_s = stc.times

            running_sum[i] += stc_arr

            # 99th percentile over vertices of stc averaged over whole 0..1000 ms
            t_mask_0_1 = (stc.times >= -1e-4) & (stc.times <= 1.0 + 1e-4)
            if np.any(t_mask_0_1):
                mean_vert = stc_arr[:, t_mask_0_1].mean(axis=-1)
            else:
                mean_vert = stc_arr.mean(axis=-1)
            val_p99 = float(np.percentile(mean_vert, 99.0))
            subject_p99[s_id][c] = round(val_p99, 4)

    if not valid_ids:
        ep.die("no valid subjects could be computed")

    grand_avg = running_sum / float(len(valid_ids))

    outlier_subjects = []
    for c in cond_keys:
        cond_vals = [subject_p99[s][c] for s in valid_ids if c in subject_p99.get(s, {})]
        if cond_vals:
            med = float(np.median(cond_vals))
            for s in valid_ids:
                val = subject_p99.get(s, {}).get(c)
                if val is not None and val > 3.0 * med:
                    outlier_subjects.append(f"{s} ({c})")

    param_dict["subject_p99"] = subject_p99
    param_dict["outlier_subjects"] = outlier_subjects
    param_dict["rank"] = subject_ranks

    np.savez(
        ga_cache,
        data=grand_avg,
        times=times_s,
        trial_counts=json.dumps(trial_counts),
        valid_ids=json.dumps(valid_ids),
        subject_p99=json.dumps(subject_p99),
        outlier_subjects=json.dumps(outlier_subjects),
        rank=json.dumps(subject_ranks),
    )
    return grand_avg, times_s, s_dir, src_obj, valid_ids, excluded, trial_counts, param_dict


def plot(spec, subjects_dir=None, src=None, bem=None, fwd=None):
    grand_avg, times_s, s_dir, src_obj, valid_ids, excluded, trial_counts, params = load_and_compute(
        spec, subjects_dir=subjects_dir, src=src, bem=bem, fwd=fwd,
    )
    times_ms = times_s * 1000.0
    cond_keys = list(spec["conditions"])
    n_cond = len(cond_keys)
    method = spec.get("method", "dSPM")
    fig_type = spec.get("figure", "windows")
    thresh_pct = float(spec.get("threshold_pct", 90.0))
    max_pct = float(spec.get("max_pct", 99.5))

    renderer = BrainRenderer(s_dir, src_obj)
    color_limits = {}

    if fig_type == "windows":
        windows = spec["windows"]
        n_windows = len(windows)
        win_images = []  # [w_idx][c_idx] -> (img_lh, img_rh)

        for w_idx, w in enumerate(windows):
            t_mask = (times_ms >= w["tmin_ms"] - 1e-3) & (times_ms <= w["tmax_ms"] + 1e-3)
            if not np.any(t_mask):
                ep.die(f"window {w['name']} [{w['tmin_ms']}, {w['tmax_ms']}] ms has no time points in data [{times_ms[0]:.0f}, {times_ms[-1]:.0f}] ms")

            w_maps = [grand_avg[c][:, t_mask].mean(axis=-1) for c in range(n_cond)]
            all_w_vals = np.concatenate(w_maps)

            fmin = float(np.percentile(all_w_vals, thresh_pct))
            fmax = float(np.percentile(all_w_vals, max_pct))
            if fmin >= fmax:
                fmax = fmin + 1e-6
            fmid = float((fmin + fmax) / 2.0)
            color_limits[f"window_{w['name']}"] = dict(fmin=fmin, fmid=fmid, fmax=fmax)

            n_lh = len(src_obj[0]["vertno"])
            w_cond_imgs = []
            for c_idx in range(n_cond):
                vals_lh = w_maps[c_idx][:n_lh]
                vals_rh = w_maps[c_idx][n_lh:]
                c_name = cond_keys[c_idx]
                w_name = w["name"]
                img_lh = renderer.render("lh", vals_lh, fmin, fmid, fmax, figure=fig_type, row=c_name, col=w_name)
                img_rh = renderer.render("rh", vals_rh, fmin, fmid, fmax, figure=fig_type, row=c_name, col=w_name)
                w_cond_imgs.append((img_lh, img_rh))
            win_images.append(w_cond_imgs)

        # Matplotlib figure layout
        W = float(spec.get("width_mm", 180.0))
        plt.rcParams.update(ep.STYLE)

        fig_probe = plt.figure(figsize=(10, 10))
        fig_probe.canvas.draw()
        R_probe = fig_probe.canvas.get_renderer()
        max_label_mm = 0.0
        for c_key in cond_keys:
            t_probe = fig_probe.text(0, 0, spec["conditions"][c_key], fontsize=7)
            ext = t_probe.get_window_extent(R_probe)
            w_mm = ext.width / (fig_probe.dpi / 72.0) * 25.4 / 72.0
            max_label_mm = max(max_label_mm, w_mm)
        plt.close(fig_probe)

        left_mm = max(24.0, max_label_mm + 4.0)
        right_mm = 5.0
        hemi_gap = 1.0
        pair_gap = 4.0
        avail_w = W - left_mm - right_mm
        brain_w = (avail_w - (n_windows - 1) * pair_gap - n_windows * hemi_gap) / (2 * n_windows)
        pair_w = 2 * brain_w + hemi_gap

        # sample aspect ratio from first rendered image
        sample_img = win_images[0][0][0]
        ar = sample_img.shape[0] / sample_img.shape[1]
        brain_h = brain_w * ar
        row_gap = 1.5

        top_margin_mm = 4.0
        header_h_mm = 8.0
        cbar_space_mm = 11.0
        bottom_margin_mm = 4.0

        rows_h = n_cond * brain_h + (n_cond - 1) * row_gap
        default_H = top_margin_mm + header_h_mm + rows_h + cbar_space_mm + bottom_margin_mm
        H = float(spec.get("height_mm", default_H))

        fig = plt.figure(figsize=(W * ep.MM, H * ep.MM))
        top_y = H - top_margin_mm - header_h_mm

        for w_idx, w in enumerate(windows):
            px = left_mm + w_idx * (pair_w + pair_gap)
            fig.text((px + pair_w / 2.0) / W, (top_y + 4.5) / H,
                     f"{w['name']} ({w['tmin_ms']:g}–{w['tmax_ms']:g} ms)",
                     ha="center", va="bottom", fontsize=7, fontweight="bold")
            fig.text((px + brain_w / 2.0) / W, (top_y + 1.0) / H, "L", ha="center", va="bottom", fontsize=6)
            fig.text((px + brain_w + hemi_gap + brain_w / 2.0) / W, (top_y + 1.0) / H, "R", ha="center", va="bottom", fontsize=6)

            for c_idx in range(n_cond):
                cy = top_y - (c_idx + 1) * brain_h - c_idx * row_gap
                if w_idx == 0:
                    fig.text((left_mm - 2.0) / W, (cy + brain_h / 2.0) / H,
                             spec["conditions"][cond_keys[c_idx]],
                             ha="right", va="center", fontsize=7)

                img_lh, img_rh = win_images[w_idx][c_idx]
                ax_l = fig.add_axes([px / W, cy / H, brain_w / W, brain_h / H])
                ax_l.imshow(img_lh)
                ax_l.set_xticks([]); ax_l.set_yticks([]); ax_l.axis("off")

                ax_r = fig.add_axes([(px + brain_w + hemi_gap) / W, cy / H, brain_w / W, brain_h / H])
                ax_r.imshow(img_rh)
                ax_r.set_xticks([]); ax_r.set_yticks([]); ax_r.axis("off")

            # Horizontal colorbar under block
            lim = color_limits[f"window_{w['name']}"]
            cbar_w = min(pair_w * 0.85, 32.0)
            cbar_x = px + (pair_w - cbar_w) / 2.0
            cbar_y = top_y - rows_h - cbar_space_mm + 3.0
            cax = fig.add_axes([cbar_x / W, cbar_y / H, cbar_w / W, 2.0 / H])
            norm = matplotlib.colors.Normalize(vmin=lim["fmin"], vmax=lim["fmax"])
            cb = fig.colorbar(matplotlib.cm.ScalarMappable(norm=norm, cmap="hot"), cax=cax, orientation="horizontal")
            cb.set_ticks([lim["fmin"], lim["fmid"], lim["fmax"]])
            cb.ax.set_xticklabels([f"{lim['fmin']:.2f}", f"{lim['fmid']:.2f}", f"{lim['fmax']:.2f}"], fontsize=6)
            cb.ax.tick_params(labelsize=6, length=2, width=0.5, pad=1.5)
            cb.outline.set_linewidth(0.5)
            cax.set_title(method, fontsize=6.5, pad=2)

        win_part = "_" + "-".join(ep.safe(w["name"]) for w in windows)
        stem = f"source-windows_{method}{win_part}{ep.name_part(spec)}"

    elif fig_type == "timeline":
        times = spec.get("times_ms", [100, 200, 300, 400, 500, 600, 700, 800])
        half_w = float(spec.get("half_width_ms", 50.0))
        n_times = len(times)

        # Global color limits over entire timeline
        all_time_maps = []
        for t_val in times:
            t_mask = (times_ms >= (t_val - half_w) - 1e-3) & (times_ms <= (t_val + half_w) + 1e-3)
            if not np.any(t_mask):
                ep.die(f"time point {t_val} ms (±{half_w} ms) has no samples in data [{times_ms[0]:.0f}, {times_ms[-1]:.0f}] ms")
            all_time_maps.append([grand_avg[c][:, t_mask].mean(axis=-1) for c in range(n_cond)])

        all_vals = np.concatenate([np.concatenate(m) for m in all_time_maps])
        fmin = float(np.percentile(all_vals, thresh_pct))
        fmax = float(np.percentile(all_vals, max_pct))
        if fmin >= fmax:
            fmax = fmin + 1e-6
        fmid = float((fmin + fmax) / 2.0)
        color_limits["timeline"] = dict(fmin=fmin, fmid=fmid, fmax=fmax)

        # Render all maps
        n_lh = len(src_obj[0]["vertno"])
        time_images = []
        for t_idx, t_val in enumerate(times):
            cond_imgs = []
            for c_idx in range(n_cond):
                vals_lh = all_time_maps[t_idx][c_idx][:n_lh]
                vals_rh = all_time_maps[t_idx][c_idx][n_lh:]
                c_name = cond_keys[c_idx]
                t_name = f"{t_val:g} ms"
                img_lh = renderer.render("lh", vals_lh, fmin, fmid, fmax, figure=fig_type, row=c_name, col=t_name)
                img_rh = renderer.render("rh", vals_rh, fmin, fmid, fmax, figure=fig_type, row=c_name, col=t_name)
                cond_imgs.append((img_lh, img_rh))
            time_images.append(cond_imgs)

        # Split into blocks of up to 4 columns
        col_blocks = [times[i:i + 4] for i in range(0, n_times, 4)]
        img_blocks = [time_images[i:i + 4] for i in range(0, n_times, 4)]
        n_vert_blocks = len(col_blocks)

        W = float(spec.get("width_mm", 180.0))
        plt.rcParams.update(ep.STYLE)

        fig_probe = plt.figure(figsize=(10, 10))
        fig_probe.canvas.draw()
        R_probe = fig_probe.canvas.get_renderer()
        max_label_mm = 0.0
        for c_key in cond_keys:
            t_probe = fig_probe.text(0, 0, spec["conditions"][c_key], fontsize=7)
            ext = t_probe.get_window_extent(R_probe)
            w_mm = ext.width / (fig_probe.dpi / 72.0) * 25.4 / 72.0
            max_label_mm = max(max_label_mm, w_mm)
        plt.close(fig_probe)

        left_mm = max(24.0, max_label_mm + 4.0)
        right_mm = 5.0
        hemi_gap = 1.0
        pair_gap = 4.0
        n_cols_max = max(len(b) for b in col_blocks)
        avail_w = W - left_mm - right_mm
        brain_w = (avail_w - (n_cols_max - 1) * pair_gap - n_cols_max * hemi_gap) / (2 * n_cols_max)
        pair_w = 2 * brain_w + hemi_gap

        sample_img = time_images[0][0][0]
        ar = sample_img.shape[0] / sample_img.shape[1]
        brain_h = brain_w * ar
        row_gap = 1.5

        top_margin_mm = 4.0
        header_h_mm = 8.0
        block_gap_mm = 8.0
        cbar_space_mm = 11.0
        bottom_margin_mm = 4.0

        rows_h = n_cond * brain_h + (n_cond - 1) * row_gap
        default_H = (
            top_margin_mm
            + n_vert_blocks * (header_h_mm + rows_h)
            + (n_vert_blocks - 1) * block_gap_mm
            + cbar_space_mm
            + bottom_margin_mm
        )
        H = float(spec.get("height_mm", default_H))

        fig = plt.figure(figsize=(W * ep.MM, H * ep.MM))

        for vb_idx, (b_times, b_imgs) in enumerate(zip(col_blocks, img_blocks)):
            block_top = H - top_margin_mm - vb_idx * (header_h_mm + rows_h + block_gap_mm)
            top_y = block_top - header_h_mm

            for c_col, (t_val, cond_pair_imgs) in enumerate(zip(b_times, b_imgs)):
                px = left_mm + c_col * (pair_w + pair_gap)
                fig.text((px + pair_w / 2.0) / W, (top_y + 4.5) / H,
                         f"{t_val:g} ms", ha="center", va="bottom", fontsize=7, fontweight="bold")
                fig.text((px + brain_w / 2.0) / W, (top_y + 1.0) / H, "L", ha="center", va="bottom", fontsize=6)
                fig.text((px + brain_w + hemi_gap + brain_w / 2.0) / W, (top_y + 1.0) / H, "R", ha="center", va="bottom", fontsize=6)

                for c_idx in range(n_cond):
                    cy = top_y - (c_idx + 1) * brain_h - c_idx * row_gap
                    if c_col == 0:
                        fig.text((left_mm - 2.0) / W, (cy + brain_h / 2.0) / H,
                                 spec["conditions"][cond_keys[c_idx]],
                                 ha="right", va="center", fontsize=7)

                    img_lh, img_rh = cond_pair_imgs[c_idx]
                    ax_l = fig.add_axes([px / W, cy / H, brain_w / W, brain_h / H])
                    ax_l.imshow(img_lh)
                    ax_l.set_xticks([]); ax_l.set_yticks([]); ax_l.axis("off")

                    ax_r = fig.add_axes([(px + brain_w + hemi_gap) / W, cy / H, brain_w / W, brain_h / H])
                    ax_r.imshow(img_rh)
                    ax_r.set_xticks([]); ax_r.set_yticks([]); ax_r.axis("off")

        # One colorbar for the whole figure, under the last block
        last_block_bot = H - top_margin_mm - (n_vert_blocks - 1) * (header_h_mm + rows_h + block_gap_mm) - header_h_mm - rows_h
        cbar_w = 40.0
        grid_w = n_cols_max * pair_w + (n_cols_max - 1) * pair_gap
        cbar_x = left_mm + (grid_w - cbar_w) / 2.0
        cbar_y = last_block_bot - cbar_space_mm + 3.0
        cax = fig.add_axes([cbar_x / W, cbar_y / H, cbar_w / W, 2.0 / H])
        norm = matplotlib.colors.Normalize(vmin=fmin, vmax=fmax)
        cb = fig.colorbar(matplotlib.cm.ScalarMappable(norm=norm, cmap="hot"), cax=cax, orientation="horizontal")
        cb.set_ticks([fmin, fmid, fmax])
        cb.ax.set_xticklabels([f"{fmin:.2f}", f"{fmid:.2f}", f"{fmax:.2f}"], fontsize=6)
        cb.ax.tick_params(labelsize=6, length=2, width=0.5, pad=1.5)
        cb.outline.set_linewidth(0.5)
        cax.set_title(method, fontsize=6.5, pad=2)

        stem = f"source-timeline_{method}{ep.name_part(spec)}"


    out = ep.versioned(ep.out_root(spec) / "source", stem)
    issues = ep.report_layout(fig, out.name)
    fig.savefig(f"{out}.png", dpi=600)
    fig.savefig(f"{out}.svg")
    plt.close(fig)

    run_record = {
        "spec": spec,
        "figure": fig_type,
        "method": method,
        "parameters": params,
        "subjects_used": valid_ids,
        "excluded": excluded,
        "trials_per_subject_condition": trial_counts,
        "subject_p99": params.get("subject_p99", {}),
        "outlier_subjects": params.get("outlier_subjects", []),
        "rank": params.get("rank", {}),
        "render_check": "ok",
        "color_limits": color_limits,
        "layout_issues": issues,
        "hemisphere_check": None,
        "canvas_size_mm": [W, H],
    }
    Path(f"{out}_run.json").write_text(json.dumps(run_record, indent=2, ensure_ascii=False), encoding="utf8")
    ep.archive(out)
    print("wrote", f"{out}.png/.svg")
    return [out]


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) < 3 or sys.argv[1] != "plot":
        ep.die("usage: python source_plot.py plot <spec.json>")
    plot(ep.read_spec(sys.argv[2]))
