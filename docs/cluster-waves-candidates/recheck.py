"""Independent check of the waves v2 numbers (plain numpy, no cluster_plot functions)."""
import csv, json
from pathlib import Path
import numpy as np, mne
run = Path(r"C:\Users\ASUS\Dropbox\metaphor_production\gn_manuscript\03-ERP_topomap\03_cluster_inference\01_cluster_based_permutation_0000_0800ms")
times = np.array([float(r["time_ms"]) for r in csv.DictReader(open(run / "time_axis.csv"))])
chs = [r["channel"] if "channel" in r else list(r.values())[0] for r in csv.DictReader(open(run / "channel_order.csv"))]
t01 = run / "01_condition_main_effect_all"
stat = np.load(t01 / "observed_statistic.npy")
rows = list(csv.DictReader(open(t01 / "cluster_summary_significant.csv")))
print(rows[0].keys())

for r in rows:
    cl = r["channels"].split(";"); idx = [chs.index(c) for c in cl]
    lo, hi = float(r["time_start_ms"]), float(r["time_end_ms"])
    m = (times >= lo - 1e-3) & (times <= hi + 1e-3)
    s = np.abs(stat[:, idx]).sum(1)
    k = np.where(m)[0][np.argmax(s[m])]
    print("cluster", r["cluster_id"], "peak", round(times[k]), "ms")
# waveform: NoGO mean over cluster 9 recommended channels at the sample nearest 334 ms
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "brain-plot"))
import cluster_plot as cp
spec = json.load(open(Path(__file__).resolve().parents[1] / "cluster-before-after" / "spec_gn_waves.json") if False else open(Path(__file__).resolve().parent / "spec_gn_waves.json"))
runr = cp.read_run(spec); t = runr["tests"][0]
c9 = [c for c in t["clusters"] if c["cluster_id"] == 9][0]
ch9 = spec["waves_channels"]["01_condition_main_effect_all/9"]
rowsm, root = cp.read_manifest(run)
vals = []
for r in rowsm:
    if r["condition"] != "NoGO": continue
    ev = mne.read_evokeds(root / r["file"], verbose="error")[0]
    i = int(np.argmin(np.abs(ev.times * 1000 - 334)))
    vals.append(ev.data[[ev.ch_names.index(c) for c in ch9], i].mean() * 1e6)
print("numpy NoGO mean over", ch9, "at 334 ms:", round(float(np.mean(vals)), 4), "n", len(vals))
tt, waves, _ = cp.cluster_waves(runr, t, run, {int(k.split("/")[1]): v for k, v in spec["waves_channels"].items() if k.startswith(t["slug"])})
j = int(np.argmin(np.abs(tt - 334)))
print("code  NoGO mean (cluster_waves) at", tt[j], ":", round(float(waves[9][0][j]), 4))
