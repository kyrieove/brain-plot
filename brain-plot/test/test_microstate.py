"""Regression checks for microstate_plot.py on synthetic data: python test/test_microstate.py  (prints OK)."""
import json
import sys
import tempfile
from pathlib import Path

import matplotlib.figure
import mne
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import microstate_plot as msp  # noqa: E402

CH = ["Fz", "Cz", "Pz", "Oz", "F3", "F4", "C3", "C4", "P3", "P4", "O1", "O2", "T7", "T8", "Fp1", "Fp2"]
SF = 250.0
rng = np.random.default_rng(1)
T = rng.normal(size=(3, len(CH)))
T -= T.mean(1, keepdims=True)
T /= np.linalg.norm(T, axis=1, keepdims=True)  # three planted templates
T[2] -= (T[2] @ T[0]) * T[0]
T[2] /= np.linalg.norm(T[2])  # keep the families distinct
# condition → planted (template, start ms, stop ms); A has a 12-ms blip of T0 inside T1 that must be merged away
PLAN = {"A": [(1, 100, 300), (0, 200, 212), (0, 300, 500), (2, 500, 800)], "B": [(1, 100, 300), (2, 300, 800)]}

SAVED = []
_savefig = matplotlib.figure.Figure.savefig
matplotlib.figure.Figure.savefig = lambda self, *a, **k: (SAVED.append(self), _savefig(self, *a, **k))[1]


def evoked(cond, seed, tmin=-0.2):
    times = np.arange(int(round(tmin * SF)), int(0.8 * SF) + 1) / SF
    x = np.random.default_rng(seed).normal(0, 0.3e-6, (len(CH), len(times)))
    for tpl, a, b in PLAN[cond]:
        on = (times * 1000 >= a) & (times * 1000 < b)
        x[:, on] = np.outer(T[tpl], np.full(on.sum(), 8e-6)) + x[:, on] * (tpl == 0 and b - a < 20)
    info = mne.create_info(CH, SF, "eeg")
    info.set_montage("standard_1020")
    return mne.EvokedArray(x, info, tmin=times[0], comment=f"x_{cond}", nave=40, baseline=None)


def spec(root, **kw):
    s = dict(data=str(root / "ev"), conditions={"A": "Go", "B": "NoGo"}, templates=str(root / "k{k:02d}.npz"), k=3,
             templates_source="synthetic")
    s.update(kw)
    return s


def fails(s, text):
    try:
        msp.plot(s)
    except SystemExit as e:
        assert text in str(e), f"expected '{text}' in: {e}"
        return
    raise AssertionError(f"expected failure containing '{text}'")


def inside_canvas(fig):
    R, W, H = fig.canvas.get_renderer(), fig.bbox.width, fig.bbox.height
    out = [b for a in fig.axes for b in [a.get_tightbbox(R)] if b.x0 < -0.5 or b.y0 < -0.5 or b.x1 > W + 0.5 or b.y1 > H + 0.5]
    out += [t.get_window_extent(R) for t in fig.texts if t.get_window_extent(R).x0 < -0.5]
    assert not out, f"outside the canvas: {out[:2]}"


# 0. polarity: a sign-flipped T1 map is T1 only when polarity is ignored
flip = np.outer(-T[1], np.ones(20))
assert (msp.segment(flip, T, SF, 30, sensitive=False) == 1).all()
assert not (msp.segment(flip, T, SF, 30, sensitive=True) == 1).any()

with tempfile.TemporaryDirectory() as d:
    root = Path(d)
    for cond in "AB":  # split layout: <condition>/<group>/<subject>_<condition>-ave.fif
        for g, n in (("G1", 3), ("G2", 2)):
            (root / "ev" / cond / g).mkdir(parents=True)
            for i in range(n):
                evoked(cond, 10 * i + len(g) + ord(cond)).save(root / "ev" / cond / g / f"{g}s{i}_{cond}-ave.fif",
                                                              verbose="error")
    np.savez(root / "k03.npz", centers=T * 3.0)  # scaled: templates are re-normalised
    np.savez(root / "k02.npz", centers=T[[2, 1]])

    # 1. segmentation recovers the planted windows (one sample = 4 ms), merges the 12-ms blip, numbers by latency
    out = msp.plot(spec(root))
    run = json.loads(Path(f"{out}_run.json").read_text(encoding="utf8"))
    assert out.name == "topo-butterfly-ribbon_K3_A-B_v01" and out.parent.name == "microstate"
    assert run["order_by_display"] == [1, 0, 2], run["order_by_display"]  # T1 first, then T0, then T2
    segs = {c: [(round(a), s) for a, _, s in v] for c, v in run["labels_ms"].items()}
    # before 100 ms only noise (split at random); from there the planted runs, and no run for the 12-ms blip
    go, nogo = segs["Go"][-3:], segs["NoGo"][-2:]
    assert [x[1] for x in go] == ["S1", "S2", "S3"] and go[0][0] <= 100 and [x[0] for x in go[1:]] == [300, 500], segs
    assert [x[1] for x in nogo] == ["S1", "S3"] and nogo[0][0] <= 100 and nogo[1][0] == 300, segs
    assert 0.08 < run["low_gfp_fraction"]["Go"] < 0.17, run["low_gfp_fraction"]  # 0–100 ms is baseline-level noise
    assert run["spans"]["NoGo"].get("S2") is None  # T0 never occurs in NoGo: shown as "—" under its map
    cap = Path(f"{out}_caption.md").read_text(encoding="utf8")
    assert "signed" in cap and "Hatched" in cap and "synthetic" in cap
    inside_canvas(SAVED[-1])

    # 2. templates named by channel are aligned by name; the result is identical
    order = list(reversed(CH))
    np.savez(root / "k03.npz", centers=T[:, [CH.index(c) for c in order]], ch_names=np.array(order))
    out2 = msp.plot(spec(root))
    assert out2.name.endswith("_v02") and (out.parent / "_history" / f"{out.name}.png").exists()  # rule O2
    assert json.loads(Path(f"{out2}_run.json").read_text(encoding="utf8"))["labels_ms"] == run["labels_ms"]

    # 3. GFP block, per-group rows, across-K identity colours (K=2's templates are K=3's T2 and T1)
    msp.plot(spec(root, blocks=["topo", "butterfly", "gfp", "ribbon"], per_group=True, groups=["G1"], width_mm=254,
                  height_mm=143))
    inside_canvas(SAVED[-1])
    # rule MS9: more than two rows need a grid; a 1 × 2 grid puts the maps in a row above it
    fails(spec(root, per_group=True), "give 'grid'")
    out4 = msp.plot(spec(root, grid=[["A", "B"]], height_mm=75))
    fig = SAVED[-1]
    inside_canvas(fig)
    heads = [a for a in fig.axes if a.get_title() == "" and not a.get_xticks().size]  # template maps
    panels = [a for a in fig.axes if "N = " in a.get_title()]
    assert len(panels) == 2 and min(h.get_position().y0 for h in heads) > max(p.get_position().y1 for p in panels)
    assert panels[0].get_position().y0 == panels[1].get_position().y0  # side by side
    fails(spec(root, grid=[["A"]]), "every condition exactly once")
    # rule MS10: panel shape; the message proposes heights that work
    fails(spec(root, height_mm=300), "height_mm")
    out3 = msp.plot(spec(root, figure="by-K", k=[2, 3]))
    fam = json.loads(Path(f"{out3}_run.json").read_text(encoding="utf8"))["families"]
    assert out3.name == "topo-by-K_K2-3_v01" and sorted(fam["K2"]) == sorted(fam["K3"][i] for i in (0, 2)), fam
    inside_canvas(SAVED[-1])

    # 4. errors stop the script
    fails(spec(root, k=[3]), "one integer")
    fails(spec(root, blocks=["topo"]), "'butterfly' and/or 'gfp'")
    fails(spec(root, colour="x"), "unsupported microstate keys")
    np.savez(root / "k04.npz", centers=T[:, :10])
    fails(spec(root, k=4), "expected 4 templates")
    np.savez(root / "k04.npz", centers=np.r_[T, T[:1]][:, :10])
    fails(spec(root, k=4), "order must match")
    for f in (root / "ev" / "A" / "G2").glob("*"):
        f.unlink()
    fails(spec(root), "missing a condition file")

with tempfile.TemporaryDirectory() as d:  # no pre-stimulus samples: low GFP cannot be judged
    root = Path(d)
    for cond in "AB":
        (root / "ev" / cond / "G").mkdir(parents=True)
        evoked(cond, 1, tmin=0.0).save(root / "ev" / cond / "G" / f"s1_{cond}-ave.fif", verbose="error")
    np.savez(root / "k03.npz", centers=T)
    fails(spec(root), "no pre-stimulus samples")

print("OK")
