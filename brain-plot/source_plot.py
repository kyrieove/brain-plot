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
    "threshold_pct", "max_pct", "width_mm", "time_locked_to",
    "group_by", "subjects_dir", "src", "bem",
}

def default_subjects_dir():
    """fsaverage parent folder: MNE's SUBJECTS_DIR config / environment, else where mne.datasets.fetch_fsaverage()
    puts it (MNE_DATA or ~/mne_data); never downloads."""
    candidates = [mne.get_config("SUBJECTS_DIR"),
                  Path(mne.get_config("MNE_DATA") or Path.home() / "mne_data") / "MNE-fsaverage-data"]
    for d in candidates:
        if d and (Path(d) / "fsaverage").is_dir():
            return Path(d)
    ep.die("fsaverage not found: set 'subjects_dir' in the spec (the folder that contains fsaverage), or run "
           "mne.datasets.fetch_fsaverage() once")


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
        names = [w["name"] for w in windows]
        if len(set(names)) != len(names):
            ep.die(f"window names must be unique (got {names!r})")

    if fig_type == "timeline":
        times = spec.get("times_ms", [100, 200, 300, 400, 500, 600, 700, 800])
        if not (isinstance(times, list) and times and all(isinstance(x, (int, float)) for x in times)):
            ep.die("times_ms must be a non-empty list of numbers")
        if len(set(times)) != len(times):
            ep.die(f"times_ms must not repeat (got {times!r})")
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


def pick_decim(sfreq, lowpass):
    """Integer decimation toward ~100 Hz that keeps lowpass <= new sfreq / 3 (anti-aliasing)."""
    decim = max(1, int(round(sfreq / 100.0)))
    while decim > 1 and lowpass is not None and lowpass > sfreq / decim / 3.0:
        decim -= 1
    return decim


def geometry_key(info):
    """Hash of channel names, kinds and electrode positions; the forward solution depends on these."""
    chs = [(ch["ch_name"], int(ch["kind"]), [round(float(x), 6) for x in ch["loc"][:3]]) for ch in info["chs"]]
    return hashlib.md5(json.dumps(chs).encode()).hexdigest()[:8]


def file_id(path):
    """Identity of a src/BEM file: resolved path, size and modification time."""
    p = Path(path).resolve()
    st = p.stat()
    return f"{p}|{st.st_size}|{st.st_mtime_ns}"


def threshold_cmap():
    """hot with the lowest LUT entry fully transparent: values <= fmin are hidden, everything above is opaque (SRC4)."""
    lut = matplotlib.colormaps["hot"](np.linspace(0.0, 1.0, 256))
    lut[0, 3] = 0.0
    return matplotlib.colors.ListedColormap(lut)


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
            transparent=False, colormap=threshold_cmap(), colorbar=False,
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

    s_dir = Path(subjects_dir or spec.get("subjects_dir") or default_subjects_dir()).resolve()
    if isinstance(src, (str, Path)):
        src_obj = mne.read_source_spaces(src, verbose="error")
        src_name = file_id(src)
    elif src is not None:
        src_obj = src
        src_name = "custom-src"
    else:
        src_path = Path(spec.get("src") or (s_dir / "fsaverage" / "bem" / "fsaverage-ico-5-src.fif"))
        src_obj = mne.read_source_spaces(src_path, verbose="error")
        src_name = file_id(src_path)

    if isinstance(bem, (str, Path)):
        bem_obj = mne.read_bem_solution(bem, verbose="error")
        bem_name = file_id(bem)
    elif bem is not None:
        bem_obj = bem
        bem_name = "custom-bem"
    else:
        bem_path = Path(spec.get("bem") or (s_dir / "fsaverage" / "bem" / "fsaverage-5120-5120-5120-bem-sol.fif"))
        bem_obj = mne.read_bem_solution(bem_path, verbose="error")
        bem_name = file_id(bem_path)

    persist_fwd = src_name != "custom-src" and bem_name != "custom-bem"

    method = spec.get("method", "dSPM")
    lambda2 = float(spec.get("lambda2", 1.0 / 9.0))
    loose = float(spec.get("loose", 0.2))
    depth = float(spec.get("depth", 0.8))
    noise_cov_ms = [float(x) for x in spec.get("noise_cov_ms", [-200, 0])]
    baseline_ms = [float(x) for x in spec.get("baseline_ms", [-200, 0])]
    cond_keys = list(spec["conditions"])

    param_dict = {
        "cache_version": 3,
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
    ep.prune_cache_dirs(cache_dir.parent, cache_dir)

    try:
        first_info = mne.io.read_info(active_files[s_ids[0]], verbose="error")
    except Exception as e:
        ep.die(f"cannot read subject {s_ids[0]} ({active_files[s_ids[0]].name}): {e}; fix the file or list the subject in 'exclude'")
    geom = geometry_key(first_info)
    for s_id in s_ids[1:]:
        try:
            info_s = mne.io.read_info(active_files[s_id], verbose="error")
        except Exception as e:
            ep.die(f"cannot read subject {s_id} ({active_files[s_id].name}): {e}; fix the file or list the subject in 'exclude'")
        if geometry_key(info_s) != geom:
            ep.die(f"subject {s_id} electrode positions differ from the first subject; the shared forward solution would be wrong")

    stamps = {s: json.dumps(ep.file_stamp(active_files[s])) for s in s_ids}
    ga_hash = hashlib.md5((param_hash + geom + json.dumps(stamps, sort_keys=True)).encode()).hexdigest()[:8]
    ga_cache = cache_dir / f"grand_avg_{ga_hash}.npz"

    first_ch_names = None
    first_times = None
    ref_contract, ref_id = None, None
    trial_counts = {}
    valid_ids = []

    # Check if grand average is already cached
    if ga_cache.exists():
        with np.load(ga_cache, allow_pickle=True) as z:
            # "contract": written only after every subject passed the S1 contract and finite checks
            if "subject_p99" in z and "outlier_subjects" in z and "rank" in z and "contract" in z:
                grand_avg = z["data"]
                times_s = z["times"]
                trial_counts = json.loads(str(z["trial_counts"]))
                valid_ids = json.loads(str(z["valid_ids"]))
                param_dict["subject_p99"] = json.loads(str(z["subject_p99"]))
                param_dict["outlier_subjects"] = json.loads(str(z["outlier_subjects"]))
                param_dict["rank"] = json.loads(str(z["rank"]))
                return grand_avg, times_s, s_dir, src_obj, valid_ids, excluded, trial_counts, param_dict

    # Forward solution: one per electrode geometry, never borrowed from another parameter folder
    fwd_file = cache_dir / f"fwd-{geom}.fif"
    if fwd is not None:
        fwd_sol = fwd
    elif persist_fwd and fwd_file.exists():
        fwd_sol = mne.read_forward_solution(fwd_file, verbose="error")
    else:
        ev_proto = mne.EvokedArray(np.zeros((len(first_info["ch_names"]), 1)), first_info, tmin=0)
        ev_proto.set_eeg_reference("average", projection=True)
        fwd_sol = mne.make_forward_solution(
            ev_proto.info, trans="fsaverage", src=src_obj, bem=bem_obj,
            eeg=True, meg=False, mindist=5.0, n_jobs=2, verbose="error",
        )
        if persist_fwd:
            mne.write_forward_solution(fwd_file, fwd_sol, overwrite=True, verbose="error")

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
                    if "rank" in z and "sfreq" in z and "stamp" in z and "contract" in z and str(z["stamp"]) == stamps[s_id]:
                        evoked_data = z["evoked_data"]
                        nave = [int(n) for n in z["nave"]]
                        cov_data = z["cov_data"]
                        cov_bads = list(z["cov_bads"])
                        cov_nfree = int(z["cov_nfree"])
                        ch_names = list(z["ch_names"])
                        times_sub = z["times"]
                        sfreq_sub = float(z["sfreq"])
                        rank = json.loads(str(z["rank"]))
                        k = json.loads(str(z["contract"]))
                        cache_valid = True
            except Exception:
                cache_valid = False

        if not cache_valid:
            try:
                ep_sub = mne.read_epochs(f, proj=False, verbose="error")
            except Exception as e:
                ep.die(f"cannot read subject {s_id} ({f.name}): {e}; fix the file or list the subject in 'exclude'")
            if ep_sub.info["bads"]:
                ep.die(f"{f.name}: bad channels {ep_sub.info['bads']} are still marked; resolve them before plotting")
            k = json.loads(json.dumps(ep.contract(ep_sub)))

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
            decim = pick_decim(ep_sub.info["sfreq"], ep_sub.info["lowpass"])
            evokeds = [ep_sub[c].average().decimate(decim) for c in cond_keys]

            evoked_data = np.array([e.data for e in evokeds])
            nave = [int(e.nave) for e in evokeds]
            cov_data = cov.data
            cov_bads = list(cov["bads"])
            cov_nfree = int(cov["nfree"])
            ch_names = list(ep_sub.info["ch_names"])
            times_sub = evokeds[0].times
            sfreq_sub = float(evokeds[0].info["sfreq"])

            np.savez(
                subj_cache,
                evoked_data=evoked_data,
                nave=nave,
                cov_data=cov_data,
                cov_bads=cov_bads,
                cov_nfree=cov_nfree,
                ch_names=ch_names,
                times=times_sub,
                sfreq=sfreq_sub,
                rank=json.dumps(rank),
                stamp=stamps[s_id],
                contract=json.dumps(k),
            )

        if first_ch_names is None:
            first_ch_names = ch_names
        elif ch_names != first_ch_names:
            ep.die(f"subject {s_id} channel names differ from first subject")

        if ref_contract is None:
            ref_contract, ref_id = k, s_id
        ep.check_contract(f"subject {s_id}", k, ref_contract, f"subject {ref_id}")
        if not np.isfinite(evoked_data).all():
            ep.die(f"subject {s_id}: non-finite values in the evoked data")

        if first_times is None:
            first_times = times_sub
        elif len(times_sub) != len(first_times) or not np.allclose(times_sub, first_times):
            ep.die(f"subject {s_id} time axis differs from the first subject "
                   f"({len(times_sub)} samples from {times_sub[0] * 1000:.0f} ms vs {len(first_times)} from {first_times[0] * 1000:.0f} ms); "
                   "use the same sampling rate, lowpass and epoch window for all subjects")

        info_sub = mne.io.read_info(f, verbose="error")
        with info_sub._unlock():
            info_sub["sfreq"] = sfreq_sub
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
            if not np.allclose(stc.times, times_sub):
                ep.die(f"subject {s_id}: STC time axis differs from the evoked time axis "
                       f"({len(stc.times)} vs {len(times_sub)} samples)")
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
        contract=json.dumps(ref_contract),
    )
    return grand_avg, times_s, s_dir, src_obj, valid_ids, excluded, trial_counts, param_dict


def source_layout_issues(fig, brain_axes, aspect_ratio):
    """Check physical brain-image dimensions and minimum text size."""
    fig.canvas.draw()
    issues = []
    fig_w_mm, fig_h_mm = (x * 25.4 for x in fig.get_size_inches())
    for ax in brain_axes:
        box = ax.get_position()
        drawn_w = box.width * fig_w_mm
        drawn_ar = box.height * fig_h_mm / drawn_w
        if not 12.0 - 1e-3 <= drawn_w <= 20.0 + 1e-3:
            issues.append(f"brain image width outside 12–20 mm: {drawn_w:.2f} mm")
        if abs(drawn_ar / aspect_ratio - 1.0) > 0.02:
            issues.append(f"brain image aspect ratio changed by more than 2%: {drawn_ar:.4f} vs {aspect_ratio:.4f}")
    small_text = [t.get_text() for t in ep.drawn_texts(fig) if t.get_fontsize() < 7.0]
    if small_text:
        issues.append(f"text below 7 pt: {small_text!r}")
    return issues


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

    if fig_type == "timeline":
        half_w = float(spec.get("half_width_ms", 50.0))
        windows = [
            {"name": f"{t:g} ms", "tmin_ms": t - half_w, "tmax_ms": t + half_w}
            for t in spec.get("times_ms", [100, 200, 300, 400, 500, 600, 700, 800])
        ]
        columns_per_row = 4
    else:
        windows = spec["windows"]
        columns_per_row = len(windows)

    step_ms = float(times_ms[1] - times_ms[0])
    for w in windows:
        if w["tmin_ms"] < times_ms[0] - step_ms / 2 or w["tmax_ms"] > times_ms[-1] + step_ms / 2:
            ep.die(f"window {w['name']} [{w['tmin_ms']:g}, {w['tmax_ms']:g}] ms is not fully inside the data "
                   f"[{times_ms[0]:.0f}, {times_ms[-1]:.0f}] ms")

    renderer = BrainRenderer(s_dir, src_obj)
    color_limits = {}
    window_images = []
    n_lh = len(src_obj[0]["vertno"])
    for w in windows:
        t_mask = (times_ms >= w["tmin_ms"] - 1e-3) & (times_ms <= w["tmax_ms"] + 1e-3)
        if not np.any(t_mask):
            ep.die(f"window {w['name']} [{w['tmin_ms']}, {w['tmax_ms']}] ms has no time points in data [{times_ms[0]:.0f}, {times_ms[-1]:.0f}] ms")

        maps = [grand_avg[c][:, t_mask].mean(axis=-1) for c in range(n_cond)]
        all_vals = np.concatenate(maps)
        fmin = float(np.percentile(all_vals, thresh_pct))
        fmax = float(np.percentile(all_vals, max_pct))
        if fmin >= fmax:
            fmax = fmin + 1e-6
        fmid = (fmin + fmax) / 2.0
        lim = dict(fmin=fmin, fmid=fmid, fmax=fmax, samples_ms=[float(times_ms[t_mask][0]), float(times_ms[t_mask][-1])])
        color_limits[f"window_{w['name']}"] = lim

        cond_images = []
        for c_idx, values in enumerate(maps):
            name = w["name"]
            key = cond_keys[c_idx]
            img_lh = renderer.render("lh", values[:n_lh], fmin, fmid, fmax, figure=fig_type, row=key, col=name)
            img_rh = renderer.render("rh", values[n_lh:], fmin, fmid, fmax, figure=fig_type, row=key, col=name)
            cond_images.append((img_lh, img_rh))
        window_images.append(cond_images)

    plt.rcParams.update(ep.STYLE)
    probe = plt.figure(figsize=(10, 10))
    probe.canvas.draw()
    renderer_probe = probe.canvas.get_renderer()
    max_label_mm = 0.0
    for key in cond_keys:
        artist = probe.text(0, 0, spec["conditions"][key], fontsize=8)
        extent = artist.get_window_extent(renderer_probe)
        max_label_mm = max(max_label_mm, extent.width / probe.dpi * 25.4)
    plt.close(probe)

    left_mm = max_label_mm + 4.0
    right_mm = 4.0
    hemi_gap = 3.0
    block_gap = 6.0
    max_width_mm = float(spec.get("width_mm", 180.0))
    n_cols = min(columns_per_row, len(windows))
    fixed_w = left_mm + right_mm + n_cols * hemi_gap + (n_cols - 1) * block_gap
    brain_w = min(16.0, (max_width_mm - fixed_w) / (2.0 * n_cols))
    if brain_w < 12.0:
        plural = "window/times per block row"
        ep.die(f"width_mm={max_width_mm:g} cannot fit {n_cols} columns with 12 mm brains; use fewer {plural}")
    pair_w = 2.0 * brain_w + hemi_gap
    W = left_mm + right_mm + n_cols * pair_w + (n_cols - 1) * block_gap

    sample_img = window_images[0][0][0]
    aspect_ratio = sample_img.shape[0] / sample_img.shape[1]
    brain_h = brain_w * aspect_ratio
    row_gap = 3.0
    header_h_mm = 10.0
    cbar_space_mm = 13.0
    top_margin_mm = bottom_margin_mm = 4.0
    block_row_gap_mm = 6.0
    rows_h = n_cond * brain_h + (n_cond - 1) * row_gap
    section_h = header_h_mm + rows_h + cbar_space_mm
    window_blocks = [windows[i:i + columns_per_row] for i in range(0, len(windows), columns_per_row)]
    n_block_rows = len(window_blocks)
    H = top_margin_mm + n_block_rows * section_h + (n_block_rows - 1) * block_row_gap_mm + bottom_margin_mm
    fig = plt.figure(figsize=(W * ep.MM, H * ep.MM))
    brain_axes = []

    for row_idx, block in enumerate(window_blocks):
        block_top = H - top_margin_mm - row_idx * (section_h + block_row_gap_mm)
        top_y = block_top - header_h_mm
        for col_idx, w in enumerate(block):
            w_idx = row_idx * columns_per_row + col_idx
            px = left_mm + col_idx * (pair_w + block_gap)
            title = (f"{w['name']} ({w['tmin_ms']:g}–{w['tmax_ms']:g} ms)"
                     if fig_type == "windows" else w["name"])
            fig.text((px + pair_w / 2.0) / W, (top_y + 6.0) / H, title,
                     ha="center", va="bottom", fontsize=8, fontweight="bold")
            fig.text((px + brain_w / 2.0) / W, (top_y + 1.5) / H, "L", ha="center", va="bottom", fontsize=7)
            fig.text((px + brain_w + hemi_gap + brain_w / 2.0) / W, (top_y + 1.5) / H, "R", ha="center", va="bottom", fontsize=7)

            for c_idx in range(n_cond):
                cy = top_y - (c_idx + 1) * brain_h - c_idx * row_gap
                if col_idx == 0:
                    fig.text((left_mm - 2.0) / W, (cy + brain_h / 2.0) / H,
                             spec["conditions"][cond_keys[c_idx]], ha="right", va="center", fontsize=8)

                img_lh, img_rh = window_images[w_idx][c_idx]
                ax_l = fig.add_axes([px / W, cy / H, brain_w / W, brain_h / H])
                ax_l.imshow(img_lh)
                ax_l.set_xticks([]); ax_l.set_yticks([])
                ax_l.axis("off")
                brain_axes.append(ax_l)
                ax_r = fig.add_axes([(px + brain_w + hemi_gap) / W, cy / H, brain_w / W, brain_h / H])
                ax_r.imshow(img_rh)
                ax_r.set_xticks([]); ax_r.set_yticks([])
                ax_r.axis("off")
                brain_axes.append(ax_r)

            lim = color_limits[f"window_{w['name']}"]
            cbar_y = top_y - rows_h - 7.0
            cax = fig.add_axes([px / W, cbar_y / H, pair_w / W, 2.0 / H])
            norm = matplotlib.colors.Normalize(vmin=lim["fmin"], vmax=lim["fmax"])
            cb = fig.colorbar(matplotlib.cm.ScalarMappable(norm=norm, cmap="hot"), cax=cax, orientation="horizontal")
            cb.set_ticks([lim["fmin"], lim["fmid"], lim["fmax"]])
            cb.ax.set_xticklabels([f"{lim['fmin']:.2f}", f"{lim['fmid']:.2f}", f"{lim['fmax']:.2f}"], fontsize=7)
            cb.ax.tick_params(labelsize=7, length=2, width=0.5, pad=1.5)
            cb.outline.set_linewidth(0.5)
            cax.set_title(method, fontsize=7, pad=5)

    active_files, _ = select_source_files(spec)
    subset = ep.subset_part(spec, {"conditions_all": ep.available_conditions(spec, next(iter(active_files.values())))}, ("conditions",))
    if fig_type == "windows":
        win_part = "_" + "-".join(f"{ep.safe(w['name'])}-{w['tmin_ms']:g}-{w['tmax_ms']:g}ms" for w in windows)
        stem = f"source-windows_{method}{win_part}{subset}"
    else:
        t_pts = spec.get("times_ms", [100, 200, 300, 400, 500, 600, 700, 800])
        stem = f"source-timeline_{method}_{t_pts[0]:g}-{t_pts[-1]:g}ms-n{len(t_pts)}-hw{half_w:g}{subset}"

    out = ep.versioned(ep.out_root(spec) / "source", stem)
    issues = ep.report_layout(fig, out.name)
    issues.extend(source_layout_issues(fig, brain_axes, aspect_ratio))
    for issue in issues:
        print(f"WARNING: layout ({out.name}): {issue}")
    fig.savefig(f"{out}.png", dpi=600)
    fig.savefig(f"{out}.svg")
    plt.close(fig)

    snr = "infinite" if params["lambda2"] == 0 else f"{params['lambda2'] ** -0.5:.3g}"
    orientation = ("fixed orientation (loose=0): signed current normal to the cortex"
                   if params["loose"] == 0 else
                   "pick_ori=None: magnitude of the three orientations per vertex (non-negative)")
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
        "inputs": {s: ep.file_stamp(f) for s, f in select_source_files(spec)[0].items()},
        "code_md5": {f.name: hashlib.md5(f.read_bytes()).hexdigest() for f in (Path(__file__), Path(ep.__file__))},
        "versions": dict(mne=mne.__version__, matplotlib=matplotlib.__version__, numpy=np.__version__),
        "method_facts": {
            "estimate": f"{method} on the fsaverage template (no individual anatomy), loose={params['loose']}, "
                        f"depth={params['depth']}, lambda2={params['lambda2']:.4g} (SNR {snr})",
            "orientation": orientation,
            "aggregation": "inverse per subject and condition with that subject's real trial count (nave), "
                           "then equal-weight mean over subjects; not a group statistic",
            "trial_counts": "dSPM noise normalisation scales with nave: conditions with different trial counts are "
                            "not directly comparable in brightness (see trials_per_subject_condition)",
            "colour_scale": "each window/time column has its own range from percentiles across its conditions "
                            "(display threshold, not significance); compare colours only within a column",
            "noise_cov": f"from {params['noise_cov_ms'][0]:g} to {params['noise_cov_ms'][1]:g} ms of each epoch "
                         "(relative to the time-locking event; check that this interval holds no stimulus)",
        },
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
