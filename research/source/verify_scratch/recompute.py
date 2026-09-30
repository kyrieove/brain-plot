"""Independent plain-MNE source estimates for TASK-verify.md."""
import json, os, sys
from pathlib import Path
import mne
import numpy as np
ROOT = Path(r"C:\dev\brain-plot")
DATA = Path(r"D:\1-python_datasets\metaphor production\derivatives\preprocessed_epochs_verb")
OUT = ROOT / "research" / "source" / "verify_scratch"
SUBJECTS_DIR = Path(r"C:\Users\ASUS\mne_data\MNE-fsaverage-data")
CACHE = Path(r"D:\1-python_datasets\metaphor production\derivatives\brain_plot_preprocessed_epochs_verb\.cache\source\5869447f")
CONDITIONS = ["Hmet", "Hlit", "Hrep", "Lmet", "Llit", "Lrep"]

def prepare(epochs):
    epochs = epochs["acc == 1"]
    epochs.set_eeg_reference("average", projection=True)
    epochs.apply_baseline((-0.2, 0.0))
    cov = mne.compute_covariance(epochs, tmin=-0.2, tmax=0.0, method="shrunk", rank=None, verbose="error")
    evokeds = [epochs[c].average().crop(-0.2, 1.0).decimate(5) for c in CONDITIONS]
    return epochs, cov, evokeds

def label_means(stc, src, labels):
    t300 = (stc.times >= .3 - 1e-9) & (stc.times <= .5 + 1e-9)
    t100 = (stc.times >= .1 - 1e-9) & (stc.times <= .2 + 1e-9)
    out = {}
    for name in ("superiortemporal-lh", "lateraloccipital-lh"):
        label = labels[name]
        verts = src[0]["vertno"]
        ix = np.flatnonzero(np.isin(verts, label.vertices))
        out[name + "_300_500"] = float(stc.data[ix][:, t300].mean())
        if name == "lateraloccipital-lh":
            out[name + "_100_200"] = float(stc.data[ix][:, t100].mean())
    return out

def main():
    ep1 = mne.read_epochs(DATA / "sub1-epo.fif", preload=True, proj=False, verbose="error")
    _, cov1, evs1 = prepare(ep1)
    fwd = mne.read_forward_solution(CACHE / "fsaverage-fwd.fif", verbose="error")
    inv1 = mne.minimum_norm.make_inverse_operator(evs1[0].info, fwd, cov1, loose=.2, depth=.8, verbose="error")
    src = inv1["src"]
    labels = {x.name: x for x in mne.read_labels_from_annot("fsaverage", parc="aparc", hemi="lh", subjects_dir=SUBJECTS_DIR, verbose="error")}
    independent = {}
    for c, ev in zip(CONDITIONS, evs1):
        stc = mne.minimum_norm.apply_inverse(ev, inv1, lambda2=1/9, method="dSPM", pick_ori=None, verbose="error")
        if c == "Hmet":
            independent = label_means(stc, src, labels)

    # Module comparison occurs only after the independent plain-MNE calculation above.
    sys.path.insert(0, str(ROOT / "brain-plot"))
    import source_plot
    spec_path = Path(r"D:\1-python_datasets\metaphor production\derivatives\brain_plot_preprocessed_epochs_verb\specs\source_timeline.json")
    # Existing module cache stores numpy.int64 nave values; adapt JSON serialization only for this verification call.
    original_dumps = source_plot.json.dumps
    source_plot.json.dumps = lambda obj, **kw: original_dumps(obj, default=lambda x: x.item() if isinstance(x, np.generic) else str(x), **kw)
    spec = json.loads(spec_path.read_text(encoding="utf-8")); spec["subjects"] = ["sub1"]
    original_savez = source_plot.np.savez
    source_plot.np.savez = lambda *a, **kw: None
    ga, times, _, msrc, _, _, _, _ = source_plot.load_and_compute(spec)
    source_plot.np.savez = original_savez
    mstc = mne.SourceEstimate(ga[CONDITIONS.index("Hmet")], vertices=[msrc[0]["vertno"], msrc[1]["vertno"]], tmin=float(times[0]), tstep=float(times[1]-times[0]), subject="fsaverage")
    module = label_means(mstc, msrc, labels)

    rows = []
    files = sorted(DATA.glob("sub*-epo.fif"), key=lambda p: int(p.stem[3:].split("-")[0]))
    print("Epoch files found:", len(files), flush=True)
    for index, path in enumerate(files, 1):
        sid = path.stem.split("-")[0]
        if sid == "sub27":
            continue
        print(f"[{index}/{len(files)}] {sid}", flush=True)
        ep, cov, evs = prepare(mne.read_epochs(path, preload=True, proj=False, verbose="error"))
        inv = mne.minimum_norm.make_inverse_operator(evs[0].info, fwd, cov, loose=.2, depth=.8, verbose="error")
        for c, ev in zip(CONDITIONS, evs):
            stc = mne.minimum_norm.apply_inverse(ev, inv, lambda2=1/9, method="dSPM", pick_ori=None, verbose="error")
            mask = (stc.times >= .6 - 1e-9) & (stc.times <= .8 + 1e-9)
            vmap = stc.data[:, mask].mean(axis=1)
            amp = np.abs(ev.data[:, mask])
            ch, ti = np.unravel_index(amp.argmax(), amp.shape)
            rows.append({"subject": sid, "condition": c, "n": int(ev.nave), "mean_vertices": float(vmap.mean()), "p99_vertices": float(np.percentile(vmap, 99)), "max_channel_uV": float(amp.max()*1e6), "peak_channel": ev.ch_names[ch], "peak_time_ms": float(ev.times[mask][ti]*1000)})
    summary = {}
    for c in CONDITIONS:
        cr = [r for r in rows if r["condition"] == c]
        summary[c] = {k: {s: float(f([r[k] for r in cr])) for s, f in (("median", np.median), ("max", np.max))} for k in ("mean_vertices", "p99_vertices")}
    med = summary["Llit"]["mean_vertices"]["median"]
    outliers = []
    for r in rows:
        if r["condition"] == "Llit" and r["mean_vertices"] > 3*med:
            sr = [x for x in rows if x["subject"] == r["subject"]]
            outliers.append({"subject": r["subject"], "llit_mean": r["mean_vertices"], "threshold": 3*med, "conditions": {x["condition"]: {k: x[k] for k in ("n", "max_channel_uV", "peak_channel", "peak_time_ms")} for x in sr}})
    result = {"independent_sub1_Hmet": independent, "module_sub1_Hmet": module, "relative_difference_pct": {k: abs(independent[k]-module[k])/abs(module[k])*100 for k in independent}, "summary_600_800": summary, "llit_outliers_gt_3x_median": outliers, "n_subjects": len(set(r["subject"] for r in rows)), "trial_counts": {s: {c: next(r["n"] for r in rows if r["subject"] == s and r["condition"] == c) for c in CONDITIONS} for s in sorted(set(r["subject"] for r in rows), key=lambda x: int(x[3:]))}}
    (OUT / "results.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()




