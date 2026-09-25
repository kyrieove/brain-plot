"""Regression checks on synthetic data: python test/test_erp_plot.py  (prints OK or fails on an assert)."""
import json
import sys
import tempfile
from pathlib import Path

import matplotlib.figure
import mne
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import erp_plot as ep  # noqa: E402

CH = ["Fz", "Cz", "Pz", "Oz", "F3", "F4", "C3", "C4", "P3", "P4", "O1", "O2", "T7", "T8", "Fp1", "Fp2"]


def make_subject(path, conds, tmin=-0.2, n_t=301, seed=0, bads=()):
    info = mne.create_info(CH, 500.0, "eeg")
    info.set_montage("standard_1020")
    info["bads"] = list(bads)
    rng = np.random.default_rng(seed)
    evs = [mne.EvokedArray(rng.normal(0, 2e-6, (len(CH), n_t)), info, tmin=tmin, comment=c, nave=30,
                           baseline=(None, 0)) for c in conds]
    mne.write_evokeds(path, evs, overwrite=True, verbose="error")


def spec(root, **kw):
    s = dict(data=str(root), conditions={"A": "Low", "B": "Mid", "C": "High"},
             components=[dict(name="P3", channels=["Cz", "Pz"], tmin_ms=250, tmax_ms=350, window_source="test")],
             claim="test", key_comparison="test", time_locked_to="stimulus onset", reference="average",
             out=str(root / "out" / "fig"))
    s.update(kw)
    return s


SAVED = []  # every figure saved, to measure its layout afterwards
_savefig = matplotlib.figure.Figure.savefig
matplotlib.figure.Figure.savefig = lambda self, *a, **k: (SAVED.append(self), _savefig(self, *a, **k))[1]


def texts_of(fig):
    R = fig.canvas.get_renderer()
    ts = list(fig.texts) + [t for a in fig.axes for t in a.texts + [a.title] + a.get_xticklabels() + a.get_yticklabels()]
    return [(t.get_text(), t.get_window_extent(R)) for t in ts if t.get_visible() and t.get_text().strip()]


def inside_canvas(fig):
    """Every text and every axes lies within the fixed canvas (rule T6)."""
    R, W, H = fig.canvas.get_renderer(), fig.bbox.width, fig.bbox.height
    boxes = texts_of(fig) + [("axes", a.get_tightbbox(R)) for a in fig.axes]
    out = [(n, b) for n, b in boxes if b.x0 < -0.5 or b.y0 < -0.5 or b.x1 > W + 0.5 or b.y1 > H + 0.5]
    assert not out, f"outside the canvas: {out[:3]}"


def fails(s, text):
    try:
        ep.plot(s)
    except SystemExit as e:
        assert text in str(e), f"expected '{text}' in: {e}"
        return
    raise AssertionError(f"expected failure containing '{text}'")


# 0. numbers: ROI = mean of channels within subject; SEM over subjects; topography = window mean
x = np.zeros((3, 2, 5))
x[:, 0] = np.array([1.0, 2.0, 6.0])[:, None]  # channel 0 per subject
x[:, 1] = 3.0                                   # channel 1
x[:, :, 2:4] += 10                              # samples 2-3 (the window) raised by 10
m, e, tp = ep.line_stats(x, [0, 1], np.ones(5, bool), np.array([0, 0, 1, 1, 0], bool))
roi = np.array([2.0, 2.5, 4.5])                 # per-subject ROI means outside the window
assert np.allclose(m[0], roi.mean()) and np.allclose(e[0], roi.std(ddof=1) / np.sqrt(3))
assert np.allclose(tp, [3.0 + 10, 3.0 + 10])
assert ep.line_stats(x[:1], [0], np.ones(5, bool), np.ones(5, bool))[1] is None  # n = 1: no SEM
yt, _ = ep.nice_ticks([-1.9, 5.3])  # N400 case: negative side must be labelled
assert min(yt) < 0 and max(yt) > 0, yt

# 0a. topomap-only block shape adapts to line and panel count on the fixed 180 x 120 canvas; never an empty row
assert [ep.topo_block(m, n, 180, 120) for m, n in [(3, 2), (6, 2), (7, 2), (4, 1), (6, 4)]] ==     [(1, 3), (2, 3), (2, 4), (2, 2), (1, 6)]

# 0b. window selection never widens: 305-355 ms at 500 Hz (float32 times, as read from FIF) -> 306..354 ms, 25 samples
ms = (np.arange(-100, 501) / 500).astype(np.float32).astype(float) * 1000
sel = ms[ep.sample_mask(ms, 305, 355)]
assert len(sel) == 25 and round(sel[0]) == 306 and round(sel[-1]) == 354, (len(sel), sel[0], sel[-1])
m8 = ep.sample_mask(ms, -200, 800)
assert m8[0] and round(ms[m8][-1]) == 800  # float32 end points are kept

with tempfile.TemporaryDirectory() as d:
    root = Path(d) / "data"
    for g, n in (("G1", 3), ("G2", 1)):
        (root / g).mkdir(parents=True)
        for i in range(n):
            make_subject(root / g / f"{g}s{i}_x-ave.fif", "ABC", seed=hash((g, i)) % 1000)

    # 1. groups overlaid, 3 conditions, short display range, single-subject group (no SEM)
    ep.plot(spec(root, xlim_ms=[-100, 400], error="sem"))
    run = json.loads((root / "out" / "fig_P3_run.json").read_text(encoding="utf8"))
    assert run["lines"] == run["maps"] == 3 * 2
    assert run["legend"] in ("between panels", "widened gap"), run["legend"]  # default legend path (rule L7)
    assert run["open_items"] == []
    svg = (root / "out" / "fig_P3.svg").read_text(encoding="utf8")
    assert 'width="510.23622pt"' in svg, "SVG is not 180 mm wide"
    assert "n < 2 have no shading" in (root / "out" / "fig_P3_caption.md").read_text(encoding="utf8")
    marks = [l for a in SAVED[-1].axes for l in a.lines if l.get_marker() not in ("None", None, "", " ")]
    assert not marks, "topomaps carry electrode marks (rule L11)"

    # 2. conditions overlaid, ordered, negative up, one group
    early = [dict(name="P3", channels=["Cz", "Pz"], tmin_ms=100, tmax_ms=200, window_source="test")]
    ep.plot(spec(root, groups=["G1"], overlay="conditions", ordered=True, polarity="negative_up", components=early,
                 time_locked_to="TO BE CONFIRMED"))
    run = json.loads((root / "out" / "fig_P3_run.json").read_text(encoding="utf8"))
    assert run["legend"] == "inside panel" and run["open_items"] == ["time_locked_to"]
    assert "OPEN (not confirmed): time_locked_to" in (root / "out" / "fig_P3_caption.md").read_text(encoding="utf8")

    # 3. spec and input errors stop the script
    fails(spec(root, difference=["A", "B"]), "unsupported spec keys")
    fails(spec(root, exclude={"nobody": "x"}), "excluded IDs not found")
    fails(spec(root, query="RT > 0"), "cannot be applied to averaged")
    fails(spec(root, xlim_ms=[-100, 300]), "window must lie inside xlim_ms")
    fails(spec(root, xlim_ms=[240, 400]), "include 0")
    fails(spec(root, components=[dict(name="P3", channels=["Cz", "Cz"], tmin_ms=250, tmax_ms=350,
                                      window_source="t")]), "without repeats")
    fails(spec(root, components=[dict(name="P3.late", channels=["Cz"], tmin_ms=250, tmax_ms=350,
                                      window_source="t")]), "becomes a file name")
    fails(spec(root, reference=""), "'reference' must be a non-empty string")
    fails(spec(root, groups=["G1"], overlay="conditions"), "gray band reaches into the legend")  # one panel, late band
    fails(spec(root, legend="upper_left"), "unsupported spec keys")
    fails(spec(root, components=[dict(name=n, channels=["Cz"], tmin_ms=250, tmax_ms=350, window_source="t")
                                 for n in ("N2", "n2")]), "unique ignoring case")
    fails(spec(root, components=[dict(name="X", channels=["Cz"], tmin_ms=900, tmax_ms=950, window_source="t")]),
          "outside the data")
    for k in range(3, 9):  # 8 groups > 7 colours
        (root / f"G{k}").mkdir()
        make_subject(root / f"G{k}" / f"G{k}s0_x-ave.fif", "ABC", seed=k)
    fails(spec(root), "at most 7")
    fails(spec(root, groups=["G1", "G3"], exclude={"G3s0": "t"}), "groups left empty")

    # 4. mismatched time grid and marked bad channels are refused
    make_subject(root / "G3" / "G3s0_x-ave.fif", "ABC", tmin=-0.1, seed=3)
    fails(spec(root, groups=["G1", "G3"]), "differs from")
    make_subject(root / "G3" / "G3s0_x-ave.fif", "ABC", seed=3, bads=["Oz"])
    fails(spec(root, groups=["G1", "G3"]), "bad channels")
    make_subject(root / "G3" / "G3s0_x-ave.fif", "ABA", seed=3)  # two Evoked objects called "A"
    fails(spec(root, groups=["G1", "G3"]), "share a comment")
    evs = mne.read_evokeds(root / "G1" / "G1s1_x-ave.fif", verbose="error")
    proj = mne.compute_proj_evoked(evs[0], n_eeg=1, verbose="error")
    for e in evs:
        e.add_proj(proj)  # unapplied SSP
    mne.write_evokeds(root / "G3" / "G3s0_x-ave.fif", evs, overwrite=True, verbose="error")
    fails(spec(root, groups=["G1", "G3"]), "unapplied projectors")

    # 4b. single-type figures (round 5): topo skips the waveform legend; captions describe only drawn elements;
    #     one waveform panel keeps its letter inside the canvas
    late = [dict(name="N4", channels=["Cz", "Pz"], tmin_ms=350, tmax_ms=390, window_source="test")]
    ep.plot(spec(root, groups=["G1"], overlay="conditions", kind="topo", components=late))
    cap = (root / "out" / "fig_N4_caption.md").read_text(encoding="utf8")
    assert "Lines:" not in cap and "gray band" not in cap and "polarity" not in cap and "Topographies" in cap
    ep.plot(spec(root, groups=["G1"], overlay="conditions", kind="erp", components=early))
    cap = (root / "out" / "fig_P3_caption.md").read_text(encoding="utf8")
    assert "Topographies" not in cap and "topography window" not in cap and "Lines:" in cap
    inside_canvas(SAVED[-1])
    assert any(t == "a" for t, _ in texts_of(SAVED[-1]))

    # 5. cache is invalidated when an input file changes
    s = spec(root, groups=["G1"])
    before = ep.load(s)[0]["G1"].copy()
    make_subject(root / "G1" / "G1s0_x-ave.fif", "ABC", seed=999)
    after = ep.load(s)[0]["G1"]
    assert not np.allclose(before, after), "stale cache returned after an input file changed"

# 6. groups from a metadata column in a flat folder of epochs files
with tempfile.TemporaryDirectory() as d:
    root = Path(d) / "flat"
    root.mkdir()
    import pandas as pd
    info = mne.create_info(CH, 500.0, "eeg")
    info.set_montage("standard_1020")
    for i, g in enumerate(["HI", "HI", "LO"]):
        ev = np.repeat([1, 2], 5)
        md = pd.DataFrame(dict(WM=[g] * 10))
        epo = mne.EpochsArray(np.random.default_rng(i).normal(0, 2e-6, (10, len(CH), 301)), info, tmin=-0.2,
                              events=np.c_[np.arange(10) * 400, np.zeros(10, int), ev], event_id=dict(A=1, B=2),
                              metadata=md, baseline=(None, 0), verbose="error")
        epo.save(root / f"s{i}-epo.fif", verbose="error")
    s = spec(root, conditions={"A": "A", "B": "B"}, group_by="WM", groups=["HI", "LO"], overlay="conditions")
    ep.plot(s)
    assert json.loads((root / "out" / "fig_P3_run.json").read_text(encoding="utf8"))["ids"] == {"HI": ["s0", "s1"], "LO": ["s2"]}

    # 7. explore: 3 × 3 waveforms + topomap table per group; unknown channel stops
    ex = dict(data=str(root), conditions={"A": "A", "B": "B"}, group_by="WM", out=str(root / "ex" / "x"),
              components=[dict(name="P3", tmin_ms=250, tmax_ms=350)], differences=[["A", "B"]])
    ep.explore(ex)
    assert all((root / "ex" / f"x_{g}_{k}.png").exists() for g in ("HI", "LO") for k in ("waves", "topo"))
    try:
        ep.explore(dict(ex, channels=[["Fz", "FCz"]]))
        raise AssertionError("explore accepted a channel that is not in the data")
    except SystemExit as e:
        assert "FCz" in str(e)

# 8. seven waveform panels on the default canvas: nothing leaves it, no two texts overlap (rule T6)
with tempfile.TemporaryDirectory() as d:
    root = Path(d) / "seven"
    root.mkdir()
    for i in range(2):
        make_subject(root / f"s{i}_x-ave.fif", "ABCDEFG", seed=i)
    ep.plot(spec(root, conditions={c: c for c in "ABCDEFG"}, kind="erp"))
    fig = SAVED[-1]
    inside_canvas(fig)
    ts = [(t, b) for t, b in texts_of(fig) if t in "ABCDEFG" or "," in t]  # facet labels and ROI titles
    hit = [(t0, t1) for i, (t0, b0) in enumerate(ts) for t1, b1 in ts[i + 1:] if b0.overlaps(b1)]
    assert not hit, f"overlapping texts: {hit}"

    # 9. explore preflight (round 5): window past the data, too few colours; zero difference maps; component bars
    ex = dict(data=str(root), conditions={"A": "A", "B": "B"}, out=str(root / "ex" / "x"),
              components=[dict(name="P3", tmin_ms=250, tmax_ms=350)])
    for bad, text in ((dict(components=[dict(name="L", tmin_ms=350, tmax_ms=500)]), "outside the data"),
                      (dict(colors=["red"]), "one colour each"),
                      (dict(conditions={c: c for c in "ABCDEFG"}, colors=["red", "blue"]), "one colour each")):
        try:
            ep.explore(dict(ex, **bad))
            raise AssertionError(f"explore accepted {bad}")
        except SystemExit as e:
            assert text in str(e), e
    for scale in ("global", "component"):
        ep.explore(dict(ex, differences=[["A", "A"]], topo_scale=scale, height_mm=180))
        inside_canvas(SAVED[-2])  # the topomap table (saved png then svg)

print("OK")
