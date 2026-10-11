"""Build the GN waves spec (test 01 + 03) with recommended channels and render it."""
import sys, json
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "brain-plot"))
import cluster_plot as cp
spec = json.load(open(HERE.parent / "cluster-before-after" / "spec_gn.json"))
run = cp.read_run(spec)
wc = {}
for t in run["tests"]:
    if t["meta"].get("kind") in ("condition_pooled", "condition_group"):
        for c in t["clusters"]:
            wc[f"{t['slug']}/{c['cluster_id']}"] = cp.recommend_channels(t, c, run["times_ms"], run["ch_names"])
spec = {**spec, "layout": "waves", "waves_channels": wc}
json.dump(spec, open(HERE / "spec_gn_waves.json", "w"), indent=1)
print(wc)
for o in cp.plot(spec):
    print(o)
