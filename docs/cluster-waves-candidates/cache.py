"""Cache per-subject cluster-ROI waveforms (GN test 01, clusters 8 and 9) and the pooled uv difference for prototyping."""
import sys, json
from pathlib import Path
import numpy as np, mne
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "brain-plot"))
import cluster_plot as cp
spec = json.load(open(Path(__file__).resolve().parents[1] / "cluster-before-after" / "spec_gn.json"))
run = cp.read_run(spec); run_dir = Path(spec["data"])
t = run["tests"][0]
rows, root = cp.read_manifest(run_dir)
keep = [c for c in t["clusters"] if c["cluster_id"] in (8, 9)]
out = {}
for g, cond in sorted({(r["group"], r["condition"]) for r in rows}):
    rs = sorted([r for r in rows if r["group"] == g and r["condition"] == cond], key=lambda r: r["participant_id"])
    acc = {c["cluster_id"]: [] for c in keep}
    for r in rs:
        ev = mne.read_evokeds(root / r["file"], verbose="error")[0]
        for c in keep:
            acc[c["cluster_id"]].append(ev.data[[ev.ch_names.index(ch) for ch in c["channels"]]].mean(0) * 1e6)
        times = ev.times * 1000.0
    for cid, v in acc.items():
        out[f"{cid}|{g}|{cond}"] = np.array(v)
uv, n, info = cp.diff_uv(run, t, run_dir)
out["times"] = times; out["uv"] = uv
np.savez("roi_cache.npz", **out)
print({k: v.shape for k, v in out.items() if k != "uv"})
