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

import matplotlib.backends.backend_agg
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


def renderer(fig):
    """The figure's renderer; matplotlib ≥ 3.11 detaches a closed pyplot figure from its Agg canvas."""
    if not hasattr(fig.canvas, "get_renderer"):
        matplotlib.backends.backend_agg.FigureCanvasAgg(fig)
    return fig.canvas.get_renderer()


def inset_clear(fig):
    """Rule L12, measured again on the saved figure with code of its own (not the script's audit): every map, colour bar
    and window text lies inside a waveform panel and touches neither the gray band, nor a curve (mean ± SEM), nor an
    axis line, nor any text of that panel, nor another part of the block. Returns the number of parts checked."""
    R = renderer(fig)
    waves = [a for a in fig.axes if a.get_legend_handles_labels()[0]]
    heads = [a for a in fig.axes if a not in waves]
    assert waves and heads, "no waveform panels or no maps"
    mm = lambda v: v * 25.4 / fig.dpi
    maps = [a for a in heads if min(mm(a.get_window_extent(R).width), mm(a.get_window_extent(R).height)) > 3]  # not the bar
    parts = [(a.get_tightbbox(R), a) for a in maps]  # the one colour bar stands at the figure's edge, outside the panels
    for w in waves:  # maps of a panel stand in one row (up to 4): two maps are never stacked
        inside = [a for a in maps if w.get_window_extent(R).x0 <= a.get_window_extent(R).x0 <= w.get_window_extent(R).x1
                  and w.get_window_extent(R).y0 <= a.get_window_extent(R).y0 <= w.get_window_extent(R).y1]
        if len(inside) <= 4:
            assert len({round(a.get_window_extent(R).y0, 1) for a in inside}) == 1, "maps of one panel are stacked"
    checked = 0
    for bb, ax in parts:
        host = [w for w in waves if w.get_window_extent(R).x0 <= (bb.x0 + bb.x1) / 2 <= w.get_window_extent(R).x1
                and w.get_window_extent(R).y0 <= (bb.y0 + bb.y1) / 2 <= w.get_window_extent(R).y1]
        assert len(host) == 1, f"a map part belongs to {len(host)} panels"
        w, inner = host[0], host[0].get_window_extent(R)
        assert inner.x0 - 0.5 <= bb.x0 and bb.x1 <= inner.x1 + 0.5 and inner.y0 - 0.5 <= bb.y0 and bb.y1 <= inner.y1 + 0.5, \
            "a map part leaves its panel"
        for p_ in w.patches:  # the gray window band
            assert not bb.overlaps(p_.get_window_extent(R)), "a map part overlaps the gray window band"
        for n in ("left", "bottom"):
            assert not bb.overlaps(w.spines[n].get_window_extent(R)), f"a map part overlaps the {n} axis"
        for t in w.texts:
            if t.get_visible() and t.get_text():
                assert not bb.overlaps(t.get_window_extent(R)), f"a map part overlaps the text {t.get_text()!r}"
        for ln in w.lines:
            tf = ln.get_transform()
            xy = tf.transform(ln.get_xydata())
            if abs(xy[0, 0] - xy[-1, 0]) < 1e-3:  # vertical line (e.g. 0 ms in box mode)
                x_val = xy[0, 0]
                y_lo, y_hi = sorted([xy[0, 1], xy[-1, 1]])
                assert not (bb.x0 < x_val < bb.x1 and max(y_lo, bb.y0) < min(y_hi, bb.y1)), "a map part covers a vertical line"
            else:
                xs = np.linspace(xy[0, 0], xy[-1, 0], 20 * len(xy))
                ys = np.interp(xs, xy[:, 0], xy[:, 1])
                assert not ((xs > bb.x0) & (xs < bb.x1) & (ys > bb.y0) & (ys < bb.y1)).any(), "a map part covers a curve"
        for coll in w.collections:  # SEM bands
            box = coll.get_window_extent(R)
            if box.width > 0:
                v = coll.get_paths()[0].vertices
                pts = w.transData.transform(v)
                assert not ((pts[:, 0] > bb.x0) & (pts[:, 0] < bb.x1) & (pts[:, 1] > bb.y0) & (pts[:, 1] < bb.y1)).any(), \
                    "a map part covers an error band"
        checked += 1
    for i, (b0, _) in enumerate(parts):
        for b1, _ in parts[i + 1:]:
            assert not b0.overlaps(b1), "two parts of the map blocks overlap"
    return checked


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
    out = root.parent / f"brain_plot_{root.name}"
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
    clean("combo side, box axes", ep.plot,
          dict(base, conditions=dict(list(COND.items())[:3]), components=[n400], axes="box"), out)
    clean("combo, 3 groups × 4 panels (2 × 2 map blocks)", ep.plot,
          dict(base, conditions=dict(list(COND.items())[:4]), components=[n400]), out)
    clean("erp roi, negative up + SEM, P1 (µV headroom)", ep.plot,
          dict(base, conditions=dict(list(COND.items())[:4]), kind="erp", channels=p1["channels"], polarity="negative_up",
               error="sem", xlim_ms=[-100, 600], components=[{k: v for k, v in p1.items() if k != "channels"}]), out)
    units = [t for a in SAVED[-1].axes for t in a.texts if t.get_text() == "µV"]
    assert units and all(t.get_bbox_patch() is None for t in units), "µV needed a white box: no headroom (rule T1)"
    clean("erp roi with box axes", ep.plot,
          dict(base, conditions=dict(list(COND.items())[:4]), kind="erp", channels=p1["channels"], polarity="negative_up",
               error="sem", xlim_ms=[-100, 600], components=[{k: v for k, v in p1.items() if k != "channels"}], axes="box", height_mm=140), out)
    stops("axes: diagonal stops", ep.plot,
          dict(base, conditions=dict(list(COND.items())[:3]), components=[n400], axes="diagonal"), "axes")
    clean("topo, 7 conditions × 3 groups", ep.plot,
          dict(base, conditions=COND, overlay="conditions", kind="topo", components=[n400]), out)
    clean("erp single panel, 7 conditions (legend inside)", ep.plot,
          dict(base, groups=["G1"], conditions=COND, overlay="conditions", kind="erp", channels=["Pz"],
               components=[]), out)
    clean("erp grid 3 × 3 with an N400 band near the panel centre", ep.plot,
          dict(base, groups=["G1", "G2"], conditions=six, overlay="conditions", kind="erp", layout="grid",
               channels=[["F3", "Fz", "F4"], ["C3", "Cz", "C4"], ["P3", "Pz", "P4"]],
               components=[{k: v for k, v in n400.items() if k != "channels"}], **pairs), out)
    clean("erp grid 3 × 3, box axes", ep.plot,
          dict(base, groups=["G1", "G2"], conditions=six, overlay="conditions", kind="erp", layout="grid",
               channels=[["F3", "Fz", "F4"], ["C3", "Cz", "C4"], ["P3", "Pz", "P4"]],
               components=[{k: v for k, v in n400.items() if k != "channels"}], axes="box", **pairs), out)
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
    _, log = quiet(ep.explore, dict(base, conditions=dict(list(COND.items())[:4]), groups=["G1"], axes="box",
                                    components=[dict(name="N400", tmin_ms=350, tmax_ms=500)]))
    assert "WARNING: layout" not in log, log

    # ERP, maps inside the panels (rule L12; user rules 2026-09-29): panels in a grid, each with its maps and colour bar
    # inside it, nothing over the gray band, curves, axes or texts; the script audits every figure and stops on a clash
    inset = dict(base, groups=["G1", "G2"], map_placement="inset", components=[n400])
    c = lambda *ks: {k: COND[k] for k in ks}
    six = c(*(f"c{i}" for i in range(1, 7)))
    grid6 = [["c1", "c2", "c3"], ["c4", "c5", "c6"]]
    for label, spec, n_panels in (
            ("inset 2 × 2 design", dict(inset, conditions=c("c1", "c2", "c3", "c4"), grid=[["c1", "c2"], ["c3", "c4"]]), 4),
            ("inset 2 × 3 design", dict(inset, conditions=six, grid=grid6), 6),
            ("inset 2 × 3 design, box axes", dict(inset, conditions=six, grid=grid6, axes="box"), 6),
            ("inset, panels = 3 groups in a row", dict(inset, groups=["G1", "G2", "G3"], overlay="conditions",
                                                     conditions=c("c1", "c2"), width_mm=185), 3),
            ("inset 2 × 2, negative up, SEM, N1", dict(inset, conditions=c("c1", "c2", "c3", "c4"), polarity="negative_up",
                                                      error="sem", components=[dict(name="N1", tmin_ms=150, tmax_ms=200,
                                                                                    channels=["P7", "P8"])]), 4),
            ("inset, one panel", dict(inset, conditions=c("c1")), 1),
            ("inset 3 × 2 design, 3 lines per panel", dict(inset, groups=["G1", "G2", "G3"], conditions=six,
                                                           grid=[["c1", "c2"], ["c3", "c4"], ["c5", "c6"]]), 6)):
        clean(label, ep.plot, spec, out)
        run = json.loads(max(out.rglob("ERP-topo-inset_*_run.json"), key=lambda f: f.stat().st_mtime_ns).read_text("utf8"))
        per = len(spec["conditions"]) if spec.get("overlay") == "conditions" else len(spec["groups"])  # lines per panel
        lay = run["inset_layout"]
        assert lay["colour_bar"] == "figure right" and lay["spacing_tier"] in (0, 1) \
            and lay["maps_rows_columns"] == [1, per], (label, lay)  # (the tier depends on the font's text widths)
        parts = n_panels * per  # the maps; the one shared colour bar is at the figure's edge
        assert run["maps"] == n_panels * per and run["inset_audit"] == dict(panels=n_panels, parts_checked=parts, clashes=[]), run["inset_audit"]
        assert inset_clear(SAVED[-1]) == parts, label
        cap = max(out.rglob("ERP-topo-inset_*_caption.md"), key=lambda f: f.stat().st_mtime_ns).read_text("utf8")
        if n_panels == 6 and per == 2:  # letters follow the grid's reading order: a b c / d e f
            assert "- (a) Cond 1 —" in cap and "- (c) Cond 3 —" in cap and "- (d) Cond 4 —" in cap and "inside the panel" in cap, cap
        mm = lambda a: a.get_window_extent(renderer(SAVED[-1])).width * 25.4 / SAVED[-1].dpi
        mh = lambda a: a.get_window_extent(renderer(SAVED[-1])).height * 25.4 / SAVED[-1].dpi
        bars = [a for a in SAVED[-1].axes if not a.get_legend_handles_labels()[0] and min(mm(a), mh(a)) < 3]
        assert len(bars) == 1 and abs(min(mm(bars[0]), mh(bars[0])) - 2.0) < 0.05, "one shared colour bar, 2 mm thick"
    # adaptive spacing (user 2026-09-29): 3 panels in a row, narrower and narrower canvases. Where the switch to the tighter
    # spacing happens depends on the font's text widths (Arial vs DejaVu), so: every width gives either a figure that
    # passes all checks or the stop, and some width in the range must have needed the tighter spacing
    tiers = set()
    for w in (160, 165, 170, 175):
        row = dict(inset, groups=["G1", "G2", "G3"], overlay="conditions", conditions=c("c1", "c2"), width_mm=w)
        try:
            clean(f"inset 3 panels in a row at {w} mm", ep.plot, row, out)
        except SystemExit as e:
            assert "in one row inside the waveform panels" in str(e), e
            continue
        run = json.loads(max(out.rglob("ERP-topo-inset_*_run.json"), key=lambda f: f.stat().st_mtime_ns).read_text("utf8"))
        assert run["inset_audit"]["clashes"] == [] and inset_clear(SAVED[-1]) == 3 * 2, w
        tiers.add(run["inset_layout"]["spacing_tier"])
    stops("inset grid missing a panel", ep.plot, dict(inset, conditions=c("c1", "c2", "c3"), grid=[["c1", "c2"], ["c1", "c3"]]),
          "grid must be rows of equal length holding each panel key once")
    stops("inset grid with another panel key", ep.plot, dict(inset, conditions=c("c1", "c2"), grid=[["c1", "cX"]]),
          "grid must hold every panel once")
    stops("grid without inset", ep.plot, dict(base, groups=["G1"], conditions=c("c1", "c2"), grid=[["c1", "c2"]],
                                              components=[n400]), "'grid' arranges the panels of map_placement 'inset'")
    clean("inset, 3 lines in the 2 × 3 panels: three maps in one row fit (no colour bar or window text inside)", ep.plot,
          dict(inset, groups=["G1", "G2", "G3"], conditions=six, grid=[["c1", "c2", "c3"], ["c4", "c5", "c6"]]), out)
    assert inset_clear(SAVED[-1]) == 6 * 3
    stops("inset on a narrow canvas: 2 lines cannot fit", ep.plot,
          dict(inset, conditions=six, grid=[["c1", "c2", "c3"], ["c4", "c5", "c6"]], width_mm=89), "rule L12")
    stops("inset with long line names in narrow panels", ep.plot,
          dict(inset, conditions={f"c{i}": f"A very long condition name {i}" for i in range(1, 7)},
               overlay="conditions", groups=["G1", "G2", "G3"], grid=[["G1", "G2", "G3"]], width_mm=120), "rule L12")

    # microstate: templates from the data at five latencies (named channels), K = 3–8
    x = np.mean([e.data for e in mne.read_evokeds(next((root / "G1").iterdir()))], 0)
    times = np.arange(-100, 501) / 500
    for k in range(3, 9):
        c = x[:, [int(np.argmin(np.abs(times - s))) for s in np.linspace(0.08, 0.7, k)]].T
        np.savez(root.parent / f"k{k:02d}.npz", centers=c - c.mean(1, keepdims=True), ch_names=np.array(CH))
    ms = dict(base, templates=str(root.parent / "k{k:02d}.npz"), k=5)
    clean("microstate, one condition on the default canvas", msp.plot, dict(ms, conditions={"c1": "Go"}), out)
    clean("microstate, two conditions stacked (GN layout)", msp.plot, dict(ms, conditions={"c1": "Go", "c2": "NoGo"}), out)
    # long condition names: the ranges ("Incongruent 133–201") are far wider than these small maps in any font, so the
    # figure must leave them to the caption (with short names, whether they fit depends on the font: Arial vs DejaVu)
    clean("microstate, K = 8, both panel types (small maps: ranges left to the caption)", msp.plot,
          dict(ms, k=8, conditions={"c1": "Congruent", "c2": "Incongruent"}, blocks=["topo", "butterfly", "gfp", "ribbon"]),
          out)
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
