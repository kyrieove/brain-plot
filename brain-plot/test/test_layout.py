"""Layout regression at realistic density: python test/test_layout.py  (prints OK or fails on an assert).

Synthetic data shaped like a real study: 64 channels (10-10, incl. TP9/TP10), 3 groups × 4 subjects, 7 conditions,
500 Hz, −200 to 1000 ms, with P1/N1/frontal/N400/late components. Every figure the matrix draws must pass the scripts'
own layout check (`layout_issues` empty: no overlapping texts, no text or legend on a line, nothing off the canvas),
and layouts that cannot be legible must stop with a height that works. The cases are the ones the 2026-09-26 audit
found broken (6 stacked panels, 2 × 2 map blocks, µV under lines with negative up, grid band names under channel
names, one-condition microstate figures, sign-flipped polarity-insensitive templates).
"""
import contextlib
import io
import json
import sys
import tempfile
from pathlib import Path

import matplotlib.figure
import mne
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import erp_plot as ep  # noqa: E402
import microstate_plot as msp  # noqa: E402

mne.set_log_level("error")
MONTAGE = "colin27_1020" if "colin27_1020" in mne.channels.get_builtin_montages() else "standard_1020"
CH = ["Fp1", "Fp2", "F7", "F3", "Fz", "F4", "F8", "FC5", "FC1", "FC2", "FC6", "T7", "C3", "Cz", "C4", "T8", "TP9", "CP5",
      "CP1", "CP2", "CP6", "TP10", "P7", "P3", "Pz", "P4", "P8", "PO9", "O1", "Oz", "O2", "PO10", "AF7", "AF3", "AF4",
      "AF8", "F5", "F1", "F2", "F6", "FT9", "FT7", "FC3", "FC4", "FT8", "FT10", "C5", "C1", "C2", "C6", "TP7", "CP3",
      "CPz", "CP4", "TP8", "P5", "P1", "P2", "P6", "PO7", "PO3", "POz", "PO4", "PO8"]
COND = {f"c{i}": f"Cond {i}" for i in range(1, 8)}
SAVED = []  # every figure saved, to inspect it afterwards
_savefig = matplotlib.figure.Figure.savefig
matplotlib.figure.Figure.savefig = lambda self, *a, **k: (SAVED.append(self), _savefig(self, *a, **k))[1]


def make_data(root):
    info = mne.create_info(CH, 500.0, "eeg")
    info.set_montage(MONTAGE)
    pos = np.array([c["loc"][:3] for c in info["chs"]])

    def topo(c, w):
        m = np.exp(-(np.linalg.norm(pos - pos[CH.index(c)], axis=1) / w) ** 2)
        return m - m.mean()
    t = np.arange(-100, 501) / 500
    comps = [(topo("Oz", .05), .10, .02, 3), (topo("P7", .05), .17, .02, -4), (topo("Fz", .06), .25, .04, -2),
             (topo("Cz", .07), .40, .07, -5), (topo("Pz", .07), .60, .10, 6)]
    rng = np.random.default_rng(1)
    for g in range(3):
        (root / f"G{g + 1}").mkdir(parents=True)
        for s in range(4):
            evs = []
            for c in range(7):
                x = sum(np.outer(m / np.abs(m).max(), a * (1 + 0.25 * c * (i == 3) - 0.1 * g * (i == 4))
                                 * np.exp(-((t - lat) / sd) ** 2)) for i, (m, lat, sd, a) in enumerate(comps))
                noise = np.apply_along_axis(lambda v: np.convolve(v, np.ones(7) / 7, "same"), 1,
                                            rng.normal(0, 0.8, x.shape))
                x = x + noise
                x -= x.mean(0)
                evs.append(mne.EvokedArray(x * 1e-6, info, tmin=-0.2, comment=f"c{c + 1}", nave=int(rng.integers(15, 40)),
                                           baseline=(None, 0)))
            mne.write_evokeds(root / f"G{g + 1}" / f"G{g + 1}s{s:02d}_x-ave.fif", evs, overwrite=True)
    return info


def quiet(fn, *a):
    with contextlib.redirect_stdout(io.StringIO()) as out:
        r = fn(*a)
    return r, out.getvalue()


def runs_written(folder, since):
    return [f for f in folder.rglob("*_run.json") if f.stat().st_mtime_ns >= since and "_history" not in f.parts]


def clean(label, fn, spec, out_root):
    """Draw, then every _run.json written by this call must report no layout issues."""
    import time
    t0 = time.time_ns()
    quiet(fn, spec)
    written = runs_written(out_root, t0)
    assert written, f"{label}: nothing written"
    for f in written:
        issues = json.loads(f.read_text(encoding="utf8"))["layout_issues"]
        assert issues == [], f"{label} ({f.name}): {issues}"


def stops(label, fn, spec, text):
    try:
        quiet(fn, spec)
    except SystemExit as e:
        assert text in str(e), f"{label}: expected {text!r} in {e}"
        return str(e)
    raise AssertionError(f"{label}: expected a stop containing {text!r}")


with tempfile.TemporaryDirectory() as d:
    root = Path(d) / "data"
    info = make_data(root)
    out = root.parent / "brain-plot"
    n400 = dict(name="N400", channels=["Cz", "CPz", "Pz"], tmin_ms=350, tmax_ms=500)
    p1 = dict(name="P1", channels=["O1", "Oz", "O2"], tmin_ms=80, tmax_ms=120)
    pairs = dict(colors=["#1b7f79"] * 2 + ["#e0533d"] * 2 + ["#0072B2"] * 2, linestyles=["-", "--"] * 3)
    six = dict(list(COND.items())[:6])
    base = dict(data=str(root))

    # ERP: the shapes of real figures, and the audit's failures
    clean("combo, 6 conditions overlaid per group (N400 paper figure)", ep.plot,
          dict(base, groups=["G1", "G2"], conditions=six, overlay="conditions", components=[n400], **pairs), out)
    clean("combo, 3 groups × 3 condition panels", ep.plot,
          dict(base, conditions=dict(list(COND.items())[:3]), components=[n400]), out)
    clean("combo, 3 groups × 4 panels (2 × 2 map blocks)", ep.plot,
          dict(base, conditions=dict(list(COND.items())[:4]), components=[n400]), out)
    clean("erp roi, negative up + SEM, P1 (µV headroom)", ep.plot,
          dict(base, conditions=dict(list(COND.items())[:4]), kind="erp", channels=p1["channels"], polarity="negative_up",
               error="sem", xlim_ms=[-100, 600], components=[{k: v for k, v in p1.items() if k != "channels"}]), out)
    units = [t for a in SAVED[-1].axes for t in a.texts if t.get_text() == "µV"]
    assert units and all(t.get_bbox_patch() is None for t in units), "µV needed a white box: no headroom (rule T1)"
    clean("topo, 7 conditions × 3 groups", ep.plot,
          dict(base, conditions=COND, overlay="conditions", kind="topo", components=[n400]), out)
    clean("erp single panel, 7 conditions (legend inside)", ep.plot,
          dict(base, groups=["G1"], conditions=COND, overlay="conditions", kind="erp", channels=["Pz"],
               components=[]), out)
    clean("erp grid 3 × 3 with an N400 band near the panel centre", ep.plot,
          dict(base, groups=["G1", "G2"], conditions=six, overlay="conditions", kind="erp", layout="grid",
               channels=[["F3", "Fz", "F4"], ["C3", "Cz", "C4"], ["P3", "Pz", "P4"]],
               components=[{k: v for k, v in n400.items() if k != "channels"}], **pairs), out)
    six_panels = dict(base, groups=["G1", "G2"], conditions=six, components=[n400])  # overlay groups: 6 panels
    msg = stops("6 stacked panels on 120 mm", ep.plot, six_panels, "height_mm")
    assert "overlay 'conditions' (2 panels)" in msg, msg
    need = int(msg.split("use height_mm ")[1].split()[0])
    clean("6 stacked panels at the height the stop names", ep.plot, dict(six_panels, height_mm=need), out)
    stops("grid of 6 channel rows on 120 mm", ep.plot,
          dict(base, groups=["G1"], conditions=six, overlay="conditions", kind="erp", layout="grid",
               channels=[[c] for c in ("Fz", "FC1", "Cz", "CPz", "Pz", "Oz")], components=[]),
          "rows of channel panels")
    _, log = quiet(ep.explore, dict(base, conditions=dict(list(COND.items())[:4]), groups=["G1"],
                                    components=[dict(name="N1", tmin_ms=150, tmax_ms=200),
                                                dict(name="N400", tmin_ms=350, tmax_ms=500)],
                                    differences=[["c1", "c2"]]))
    assert "WARNING: layout" not in log, log

    # microstate: templates from the data at five latencies (named channels), K = 3–8
    x = np.mean([e.data for e in mne.read_evokeds(next((root / "G1").iterdir()))], 0)
    times = np.arange(-100, 501) / 500
    for k in range(3, 9):
        c = x[:, [int(np.argmin(np.abs(times - s))) for s in np.linspace(0.08, 0.7, k)]].T
        np.savez(root.parent / f"k{k:02d}.npz", centers=c - c.mean(1, keepdims=True), ch_names=np.array(CH))
    ms = dict(base, templates=str(root.parent / "k{k:02d}.npz"), k=5)
    clean("microstate, one condition on the default canvas", msp.plot, dict(ms, conditions={"c1": "Go"}), out)
    clean("microstate, two conditions stacked (GN layout)", msp.plot, dict(ms, conditions={"c1": "Go", "c2": "NoGo"}), out)
    clean("microstate, K = 8, both panel types (small maps: ranges left to the caption)", msp.plot,
          dict(ms, k=8, conditions={"c1": "Go", "c2": "NoGo"}, blocks=["topo", "butterfly", "gfp", "ribbon"]), out)
    run = json.loads(max(out.rglob("topo-butterfly-GFP-ribbon_K8*_run.json"), key=lambda f: f.stat().st_mtime_ns).read_text("utf8"))
    assert run["ranges_under_maps"] is False, run["ranges_under_maps"]
    clean("microstate, 2 × 3 grid, butterfly", msp.plot,
          dict(ms, conditions=six, grid=[["c1", "c2", "c3"], ["c4", "c5", "c6"]], k=8), out)
    clean("microstate, 2 × 3 grid, GFP", msp.plot,
          dict(ms, conditions=six, grid=[["c1", "c2", "c3"], ["c4", "c5", "c6"]], blocks=["topo", "gfp"]), out)
    clean("microstate, templates across K", msp.plot, dict(ms, figure="by-K", k=[3, 4, 5, 6, 7, 8],
                                                           conditions={"c1": "Go", "c2": "NoGo"}), out)
    c = np.load(root.parent / "k04.npz")["centers"]  # K = 4 comes back with its first map sign-flipped
    np.savez(root.parent / "k04.npz", centers=np.r_[-c[:1], c[1:]], ch_names=np.array(CH))
    clean("microstate across K, polarity ignored", msp.plot, dict(ms, figure="by-K", k=[3, 4, 5], polarity="insensitive",
                                                                  conditions={"c1": "Go", "c2": "NoGo"}), out)
    run = json.loads(max(out.rglob("topo-by-K_K3-5*_run.json"), key=lambda f: f.stat().st_mtime_ns).read_text("utf8"))
    assert -1 in run["shown_sign"]["K4"], run  # the flipped map joined its family (shown with its sign), not a new one
    msg = stops("microstate, both panel types in one row at 180 mm", msp.plot,
                dict(ms, conditions={"c1": "Go"}, blocks=["topo", "butterfly", "gfp", "ribbon"]), "rule MS10")
    assert "another width_mm or grid" in msg, msg

print("OK")
