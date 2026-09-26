"""Microstate figures from saved templates and per-subject MNE files (plan: docs/plan-microstate.md).

    python microstate_plot.py plot <spec.json>

Draws only: the templates are read, never re-fitted. Each condition's subject-equal grand average is labelled sample by
sample with its best-matching template (the reference figures' method), and the figure shows the templates, the
butterfly plot, the GFP and the segmentation. Outputs go to brain-plot/microstate/ next to the data folder, versioned
(rules O1–O3); the rules are MS1–MS8 in references/rules.md.
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
from matplotlib import patheffects
from matplotlib.patches import FancyBboxPatch, Rectangle

import erp_plot as ep

REQUIRED = {"data", "conditions", "templates", "k"}
OPTIONAL = {"templates_source", "hatch", "figure", "blocks", "groups", "exclude", "per_group", "grid", "window_ms", "min_segment_ms", "polarity", "width_mm",
            "height_mm", "identity_threshold", "cmap", "reference", "time_locked_to", "flat_channels"}
BLOCKS = {"topo": "topo", "butterfly": "butterfly", "gfp": "GFP", "ribbon": "ribbon"}  # block → file-name part
STATE_COLOURS = ["#00468B", "#ED0000", "#42B540", "#0099B4", "#925E9F", "#FDAF91", "#AD002A", "#7A8A8A", "#1B1919",
                 "#D4A017"]  # rule MS5: the reference palette, by display number
IDENTITY_COLOURS = STATE_COLOURS + ["#B8860B", "#E75480", "#2E8B7A", "#6B4C9A", "#8B5A2B", "#5B8FF9"]
TRACE, SOFT = "#171b21", "#5a626d"
MAP_MAX_MM = 22.0  # largest template map on the states figure
GFP_LABEL_MM = (4.6, 2.3)  # "GFP" at 6 pt: width, height (rule MS7c placement)
MM = ep.MM


def check(spec):
    keys = set(spec)
    if REQUIRED - keys:
        ep.die(f"microstate spec is missing {sorted(REQUIRED - keys)}")
    if keys - REQUIRED - OPTIONAL:
        ep.die(f"unsupported microstate keys {sorted(keys - REQUIRED - OPTIONAL)} (see references/spec.md)")
    fig = spec.get("figure", "states")
    if fig not in ("states", "by-K"):
        ep.die("figure must be 'states' or 'by-K'")
    k = spec["k"]
    ok = isinstance(k, int) and k >= 2 if fig == "states" else         isinstance(k, list) and k and all(isinstance(x, int) and x >= 2 for x in k)
    if not ok:
        ep.die("k: one integer ≥ 2 for figure 'states', a list of them for 'by-K'")
    blocks = spec.get("blocks", ["topo", "butterfly", "ribbon"])
    if not blocks or set(blocks) - set(BLOCKS) or len(set(blocks)) != len(blocks) or not {"butterfly", "gfp"} & set(blocks):
        ep.die(f"blocks: a list from {list(BLOCKS)} with 'butterfly' and/or 'gfp', no repeats")
    if "ribbon" in blocks and "butterfly" not in blocks:
        ep.die("blocks: 'ribbon' is drawn under the butterfly plot; add 'butterfly' or drop 'ribbon' (the GFP panel is "
               "coloured by state itself)")
    if spec.get("polarity", "sensitive") not in ("sensitive", "insensitive"):
        ep.die("polarity must be 'sensitive' or 'insensitive' (as in the analysis that made the templates)")
    lo, hi = spec.get("window_ms", [0, 800])
    if not lo < hi:
        ep.die("window_ms needs start < end")
    g = spec.get("grid")
    if g is not None and (spec.get("per_group") or not isinstance(g, list) or not all(isinstance(r, list) and r for r in g)
                          or sorted(sum(g, [])) != sorted(spec["conditions"])):
        ep.die("grid: rows of condition keys using every condition exactly once (not with per_group) — rule MS9")
    if g and len(spec["conditions"]) > 2 and max(len(r) for r in g) < 2:
        ep.die("grid: more than two conditions need at least two columns; one column would stack them (rule MS9)")
    labels = list(spec["conditions"].values())
    if len(set(labels)) != len(labels):
        ep.die(f"condition labels must be unique (each names one row of panels): {labels}")
    if "templates_source" in spec and not ep.text(spec["templates_source"]):
        ep.die("templates_source must be a non-empty string when given")
    if not isinstance(spec.get("hatch", False), bool):
        ep.die("hatch must be true or false")


# ---------- computation ----------
def load_templates(spec, k, info):
    """K × channels, average-referenced and unit-norm, columns in the data's channel order."""
    path = Path(str(spec["templates"]).format(k=k))
    if not path.exists():
        ep.die(f"template file not found: {path}")
    z = np.load(path, allow_pickle=False)
    names = None
    if path.suffix == ".npz":
        if "centers" not in z:
            ep.die(f"{path.name}: needs an array 'centers' (K × channels)")
        names = [str(x) for x in z["ch_names"]] if "ch_names" in z else None
        z = z["centers"]
    c = np.asarray(z, float)
    if c.ndim != 2 or c.shape[0] != k:
        ep.die(f"{path.name}: expected {k} templates, found shape {c.shape}")
    if names:
        if sorted(names) != sorted(info.ch_names):
            ep.die(f"{path.name}: template channels differ from the data's")
        c = c[:, [names.index(ch) for ch in info.ch_names]]
    elif c.shape[1] != len(info.ch_names):
        ep.die(f"{path.name}: {c.shape[1]} template channels, {len(info.ch_names)} in the data (order must match)")
    else:
        print(f"WARNING: {path.name} has no ch_names; its columns are assumed to follow the data's channel order "
              f"({', '.join(info.ch_names[:4])}, …). Save ch_names with the templates to have them matched by name.")
    c = c - c.mean(1, keepdims=True)
    norm = np.linalg.norm(c, axis=1, keepdims=True)
    if not np.isfinite(c).all() or not (norm > 1e-12).all():
        ep.die(f"{path.name}: templates must be finite and non-flat after average reference")
    return c / norm, path


def runs(lab):
    """(start, stop, state) of each run of equal labels."""
    edges = np.flatnonzero(np.diff(lab)) + 1
    starts, stops = np.r_[0, edges], np.r_[edges, len(lab)]
    return [(int(a), int(b), int(lab[a])) for a, b in zip(starts, stops)]


def merge_short(lab, sim, min_samples):
    """Runs shorter than min_samples take the adjacent state that fits them better (reference method)."""
    lab = lab.copy()
    for _ in range(max(10, len(lab))):
        short = [r for r in runs(lab) if r[1] - r[0] < min_samples]
        if not short or min_samples <= 1:
            break
        changed = False
        for a, _, s in short:
            rs = runs(lab)  # earlier replacements can merge runs
            i = next((i for i, r in enumerate(rs) if r[0] == a and r[2] == s), None)
            if i is None or rs[i][1] - rs[i][0] >= min_samples:
                continue
            nb = [rs[j][2] for j in (i - 1, i + 1) if 0 <= j < len(rs)]
            if nb:
                a, b = rs[i][:2]
                lab[a:b] = max(nb, key=lambda t: sim[a:b, t].mean())
                changed = True
        if not changed:
            break
    return lab


def segment(x, centers, sfreq, min_ms, sensitive):
    """x: channels × samples (µV). Label = best template per sample after average reference and unit norm."""
    u = x.T - x.T.mean(1, keepdims=True)
    u = u / np.maximum(np.linalg.norm(u, axis=1, keepdims=True), 1e-12)
    sim = u @ centers.T
    sim = sim if sensitive else np.abs(sim)
    return merge_short(sim.argmax(1), sim, max(1, int(round(min_ms / 1000 * sfreq))))


def longest_runs(labels, ms, k):
    """Per cell: state → (onset, offset) ms of its longest run, as drawn: edges() (half-way between samples, rule MS2)."""
    out = {}
    for cell, lab in labels.items():
        best = {}
        for a, b, s in runs(lab):
            if b - a > best.get(s, (0,))[0]:
                best[s] = (b - a, *map(float, edges(ms, a, b)))
        out[cell] = {s: v[1:] for s, v in best.items()}
    return out


def display_order(spans, k):
    """Rule MS4: states numbered by (median onset + median offset) / 2 of their longest runs across cells; absent last."""
    def middle(s):
        on = [v[s][0] for v in spans.values() if s in v]
        off = [v[s][1] for v in spans.values() if s in v]
        return (np.median(on) + np.median(off)) / 2 if on else np.inf
    return sorted(range(k), key=middle)


def cells_of(spec, data, meta):
    """Rows of the figure: subject-equal grand average per condition (or per condition × group)."""
    conds, groups = list(spec["conditions"]), list(data)
    cells = {}
    for i, c in enumerate(conds):
        if spec.get("per_group"):
            for g in groups:
                cells[f"{spec['conditions'][c]} · {g}"] = (data[g][:, i].mean(0), len(meta["ids"][g]))
        else:
            x = np.concatenate([data[g][:, i] for g in groups])
            cells[spec["conditions"][c]] = (x.mean(0), len(x))
    return cells


def low_gfp(x, ms, w):
    """Rule MS3: samples in the window whose GFP is below the 95th percentile of the same average's pre-stimulus GFP."""
    gfp = x.std(0)
    pre = ms < 0
    if not pre.any():
        ep.die("the data have no pre-stimulus samples, so low-GFP periods cannot be judged (keep the baseline)")
    return gfp[w] < np.percentile(gfp[pre], 95)


# ---------- drawing ----------
def mm_axes(fig, W, H, x, y, w, h):
    """Axes placed in millimetres from the lower-left corner (rule T6: fixed physical layout)."""
    return fig.add_axes([x / W, y / H, w / W, h / H])


def framed_map(fig, W, H, x, y, s, vec, info, sphere, vmax, colour, label, sub, cmap):
    ax = mm_axes(fig, W, H, x, y, s, s)
    mne.viz.plot_topomap(vec, info, axes=ax, show=False, cmap=cmap, vlim=(-vmax, vmax), contours=4, sensors=False,
                         extrapolate=ep.TOPO["extrapolate"], image_interp=ep.TOPO["image_interp"],
                         sphere=sphere)  # no electrode marks; MNE's default 0.5-pt contours, negative dashed
    x0, x1, y0, y1 = *ax.get_xlim(), *ax.get_ylim()
    ax.set_xlim(x0 - 0.08 * (x1 - x0), x1 + 0.08 * (x1 - x0))
    ax.set_ylim(y0 - 0.08 * (y1 - y0), y1 + 0.08 * (y1 - y0))
    ax.add_patch(FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0,rounding_size=0.08", transform=ax.transAxes,
                                fill=False, ec=colour, lw=1.2, clip_on=False))
    ax.text(0.5, 1.04, label, transform=ax.transAxes, ha="center", va="bottom", fontsize=7, fontweight="bold",
            color=colour)
    if sub:
        ax.text(0.5, -0.05, sub, transform=ax.transAxes, ha="center", va="top", fontsize=5.5, color=SOFT,
                linespacing=1.15)
    return ax


def gfp_label_spot(t, x, gfp, amp, pw, ph):
    """Rule MS7c: sample at which the "GFP" label (right-aligned, 2 pt above the curve) crosses the fewest channel
    samples; ties go to the latest time. Returns (index, whether no channel crosses it)."""
    w_ms = GFP_LABEL_MM[0] / pw * (t[-1] - t[0])  # label box in data units of the panel
    h_uv, off = GFP_LABEL_MM[1] / ph * 2 * amp, 0.7 / ph * 2 * amp
    best = None
    for i in range(len(t) - 1, -1, -1):
        s = (t >= t[i] - w_ms) & (t <= t[i])
        if t[i] - w_ms < t[0]:
            break
        y0 = gfp[i] + off
        if y0 + h_uv > amp:  # the label would leave the panel
            continue
        hits = int(((x[:, s] > y0) & (x[:, s] < y0 + h_uv)).sum() + (gfp[s] > y0).sum())
        if best is None or hits < best[1]:
            best = (i, hits)
        if hits == 0:
            break
    return (best[0], best[1] == 0) if best else (len(t) - 1, False)


def hatch(ax, ms, mask, y0, y1):
    """Rule MS3: diagonal white hatch over low-GFP runs; the state colour stays visible underneath."""
    for a, b, v in runs(mask.astype(int)):
        if v:
            x0, x1 = edges(ms, a, b)
            ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, hatch="//////", ec="white", lw=0, zorder=4))


def time_axis(ax, lo, hi, labelled):
    ax.set_xlim(lo, hi)
    step = 200 if hi - lo >= 600 else 100
    ax.set_xticks(np.arange(np.ceil(lo / step) * step, hi + 1e-9, step))
    ax.tick_params(axis="x", labelsize=6, length=2, pad=1.5)
    if labelled:
        ax.set_xlabel("Time (ms)", fontsize=7, labelpad=1)


def window_mask(spec, ms):
    """Samples of window_ms; stops if the window reaches past the data or holds fewer than two samples."""
    lo, hi = spec.get("window_ms", [0, 800])
    w = ep.sample_mask(ms, lo, hi)
    if w.sum() < 2 or lo < ms[0] - 1 or hi > ms[-1] + 1:
        ep.die(f"window_ms {lo, hi} must lie inside the data ({ms[0]:g}–{ms[-1]:g} ms)")
    return w


def edges(t, a, b):
    """Rule MS2: the run [a, b) owns the time from half a sample before t[a] to half a sample after t[b-1] (clipped to
    the axis), so neighbouring runs meet between samples and no sample is drawn in two states."""
    h = (t[1] - t[0]) / 2
    return max(t[0], t[a] - h), min(t[-1] + 2 * h, t[b - 1] + h)


def under(t, y, a, b):
    """Polygon under y for the run [a, b), cut at the run's edges (values linearly interpolated there)."""
    x0, x1 = edges(t, a, b)
    xs = np.r_[x0, t[a:b], x1]
    return xs, np.interp(xs, t, y)


def plot_states(spec, data, info, meta, ms, sphere):
    k, blocks = spec["k"], spec.get("blocks", ["topo", "butterfly", "ribbon"])
    w = window_mask(spec, ms)
    centers, tpath = load_templates(spec, k, info)
    cells = cells_of(spec, data, meta)
    want = len(spec["conditions"]) * (len(data) if spec.get("per_group") else 1)
    if len(cells) != want:  # every requested condition (× group) is one row, never merged
        ep.die(f"{len(cells)} rows for {want} requested conditions (× groups); row names must be unique")
    sens = spec.get("polarity", "sensitive") == "sensitive"
    labels = {c: segment(x[:, w], centers, info["sfreq"], spec.get("min_segment_ms", 30), sens) for c, (x, _) in cells.items()}
    lows = {c: low_gfp(x, ms, w) if spec.get("hatch") else np.zeros(w.sum(), bool)  # rule MS3: opt-in
            for c, (x, _) in cells.items()}
    spans = longest_runs(labels, ms[w], k)
    order = display_order(spans, k)
    pos = {s: i for i, s in enumerate(order)}
    col = {s: STATE_COLOURS[pos[s] % len(STATE_COLOURS)] for s in range(k)}
    t = ms[w]

    names = list(cells)
    if spec.get("grid"):  # rule MS9: the user's rows × columns of conditions (e.g. a 2 × 3 design)
        grid = [[spec["conditions"][c] for c in row] for row in spec["grid"]]
    elif len(names) <= 2:
        grid = [[c] for c in names]
    elif spec.get("per_group"):
        ep.die(f"per_group gives {len(names)} rows (conditions × groups); at most 2 can be stacked and 'grid' takes "
               "conditions only — draw one figure per group instead (e.g. \"groups\": [\"" + list(data)[0] + "\"], no "
               "per_group) — rule MS9")
    else:
        ep.die(f"{len(names)} rows of time panels would be stacked; give 'grid' (rows × columns of condition keys, "
               "e.g. [[\"Hmet\",\"Hlit\",\"Hrep\"],[\"Lmet\",\"Llit\",\"Lrep\"]]) — rule MS9")
    R, C = len(grid), max(len(r) for r in grid)
    if C > 1 and {"butterfly", "gfp"} <= set(blocks):
        ep.die("a grid with several columns takes one time panel per condition: 'butterfly' or 'gfp', not both (rule MS9)")
    panels = [b for b in ("butterfly", "gfp") if b in blocks]
    rib = 3.2 if "ribbon" in blocks else 0.0
    top, bottom, side, gap, cgap, ylab = 6.0, 9.0, 4.0, 9.0, 4.0, 11.0
    maps_on_top = "topo" in blocks and C > 1  # rule MS6: a map row above a multi-column grid
    n_sub = len(cells) if len(cells) <= 4 and not maps_on_top else 0  # rule MS7a: ranges only while legible
    extra = 3.5 + 2.3 * n_sub + 1.0  # mm around a map: state label above, range lines below, spacing

    def layout(W, H):
        """Map positions and time-panel geometry for a W × H mm canvas."""
        maps, x_right, y_grid = [], side, H - top
        if maps_on_top:
            s = min(MAP_MAX_MM, (W - 2 * side) / (k * 1.25), 0.22 * H)
            x0 = (W - k * s * 1.25 + 0.25 * s) / 2
            maps = [(x0 + i * s * 1.25, H - top - 3.5 - s, s) for i in range(k)]
            y_grid = H - top - 3.5 - s - 8.0  # 8 mm between the map row and the first panel titles
        elif "topo" in blocks:
            def size(nc):  # map side for nc columns; the time panels keep at least half the canvas width
                return min((H - top - bottom) / -(-k // nc) - extra, MAP_MAX_MM, (W / 2 - side - 6 - (nc - 1) * 5) / nc)
            nc = max(range(1, 4), key=lambda n: (round(size(n), 1), -n))  # largest maps, fewest columns
            nr, s = -(-k // nc), size(nc)
            y_top = H - top - (H - top - bottom - nr * (s + extra)) / 2
            maps = [(side + (i // nr) * (s + 5), y_top - (i % nr) * (s + extra) - 3.5 - s, s) for i in range(k)]
            x_right = side + nc * s + (nc - 1) * 5 + 6
        cell_w = (W - x_right - side - (C - 1) * cgap) / C
        avail = cell_w - ylab * len(panels)
        share = [1.3 if p == "butterfly" and len(panels) == 2 else 1.0 for p in panels]  # butterfly wider than GFP
        widths = [avail * x / sum(share) for x in share]
        row_h = (y_grid - bottom - (R - 1) * gap) / R
        return maps, x_right, y_grid, cell_w, widths, row_h, row_h - rib - (1.0 if rib else 0)

    W, H = ep.canvas_size(dict(width_mm=spec.get("width_mm", 180), height_mm=spec.get("height_mm", 100 if C > 1 else 110)))
    maps, x_right, y_grid, cell_w, widths, row_h, ph = layout(W, H)
    def shapes_ok(g):
        return all(1.8 <= pw / g[6] <= 3.5 for pw in g[4])
    if not shapes_ok((maps, x_right, y_grid, cell_w, widths, row_h, ph)):  # rule MS10: every time panel
        ok = [h for h in range(60, 301) if shapes_ok(layout(W, h))]
        ep.die(f"time panels would be {' and '.join(f'{pw:.0f} × {ph:.0f} mm ({pw / ph:.1f})' for pw in widths)}; "
               "keep width:height 1.8–3.5 with "
               + (f"height_mm {ok[0]}–{ok[-1]} at width_mm {W:g}" if ok else "another width_mm or grid") + " (rule MS10)")
    fig = plt.figure(figsize=(W * MM, H * MM))
    vmax = float(np.abs(centers).max())
    short = {c: c.split(" · ")[0] if len(cells) > 1 else "" for c in cells}
    for i, (st, (mx, my, ms_)) in enumerate(zip(order, maps)):
        sub = "\n".join(f"{short[c]} {round(spans[c][st][0])}–{round(spans[c][st][1])}".strip() if st in spans[c]
                        else f"{short[c]} —".strip() for c in cells) if n_sub else ""  # rule MS7a
        framed_map(fig, W, H, mx, my, ms_, centers[st], info, sphere, vmax, col[st], f"S{i + 1}", sub,
                   spec.get("cmap", "RdBu_r"))
    amp = max(np.abs(x[:, w]).max() for x, _ in cells.values()) * 1.08
    gmax = max(x[:, w].std(0).max() for x, _ in cells.values()) * 1.10
    for r, row in enumerate(grid):
        for c_i, cell in enumerate(row):
            x = cells[cell][0]
            y0 = y_grid - (r + 1) * row_h - r * gap
            lab, low = labels[cell], lows[cell]
            gfp = x[:, w].std(0)
            bounds = [edges(t, a, b)[0] for a, b, _ in runs(lab)[1:]]  # rule MS2: same boundaries as the ribbon
            xx = x_right + c_i * (cell_w + cgap) + ylab
            for p, pw in zip(panels, widths):
                ax = mm_axes(fig, W, H, xx, y0 + rib + (1.0 if rib else 0), pw, ph)
                if p == "butterfly":
                    ax.plot(t, x[:, w].T, color=TRACE, alpha=0.42, lw=0.28, zorder=2)
                    ax.plot(t, gfp, color=TRACE, lw=1.0, zorder=3)
                    i, clear = gfp_label_spot(t, x[:, w], gfp, amp, pw, ph)
                    ax.annotate("GFP", (t[i], gfp[i]), xytext=(0, 2), textcoords="offset points", fontsize=6,
                                ha="right", va="bottom", color=TRACE,  # rule MS7c: inside the panel, off the traces
                                path_effects=[] if clear else [patheffects.withStroke(linewidth=1.5, foreground="white")])
                    ax.set_ylim(-amp, amp)
                    ax.set_title(cell, fontsize=7, fontweight="bold", pad=2.5)  # rule MS7d: condition only, n in the caption
                    for b in bounds:
                        ax.axvline(b, color=SOFT, lw=0.5, ls=":", zorder=1)
                else:
                    ax.plot(t, gfp, color=TRACE, lw=0.8, zorder=3)
                    for a, b, st in runs(lab):
                        xs, ys = under(t, gfp, a, b)
                        ax.fill_between(xs, 0, ys, color=col[st], lw=0, zorder=2)
                    for a, b, v in runs(low.astype(int)):  # rule MS3: hatch under the curve only
                        if v:
                            xs, ys = under(t, gfp, a, b)
                            ax.fill_between(xs, 0, ys, facecolor="none", hatch="//////", ec="white", lw=0, zorder=2.5)
                    ax.set_ylim(0, gmax)
                    ax.set_title("GFP" if "butterfly" in panels else cell, fontsize=7, fontweight="bold", pad=2.5)
                if c_i == 0 or len(panels) > 1:  # y label once per row of a grid (shared ranges)
                    ax.set_ylabel("Amplitude (µV)" if p == "butterfly" else "GFP (µV)", fontsize=7, labelpad=1)
                ax.tick_params(labelsize=6, length=2, pad=1.5)
                time_axis(ax, t[0], t[-1] + (t[1] - t[0]), labelled=False)
                if rib and p == "butterfly":  # rule MS7b: ribbon under the butterfly, labelled S1, S2, …
                    ax.tick_params(axis="x", labelbottom=False)
                    rax = mm_axes(fig, W, H, xx, y0, pw, rib)
                    step = t[1] - t[0]
                    for a, b, st in runs(lab):
                        x0, x1 = edges(t, a, b)
                        rax.add_patch(Rectangle((x0, 0), x1 - x0, 1, color=col[st], lw=0))
                        if (t[b - 1] - t[a]) > 0.045 * (t[-1] - t[0]) * C:
                            rax.text((t[a] + t[b - 1] + step) / 2, 0.5, f"S{pos[st] + 1}", ha="center", va="center",
                                     fontsize=5.5, color=ep.ink(col[st]), fontweight="bold", zorder=5)  # rule MS7b
                    hatch(rax, t, low, 0, 1)
                    rax.set_ylim(0, 1)
                    rax.set_yticks([])
                    for sp in ("left", "right", "top"):
                        rax.spines[sp].set_visible(False)
                    time_axis(rax, t[0], t[-1] + step, labelled=r == R - 1)
                elif r == R - 1:
                    ax.set_xlabel("Time (ms)", fontsize=7, labelpad=1)
                xx += pw + ylab
    stem = f"{'-'.join(BLOCKS[b] for b in blocks)}_K{k}_{'-'.join(map(ep.safe, spec['conditions']))}" \
           + ("_by-group" if spec.get("per_group") else "")  # rule O3
    extra = dict(colour_distinctness=ep.colour_check([col[s] for s in order], "state colours"),
                 order_by_display=[int(s) for s in order], labels_ms={c: [[float(t[a]), float(t[b - 1]), f"S{pos[st] + 1}"]
                                                                      for a, b, st in runs(l)] for c, l in labels.items()},
                 **({"low_gfp_fraction": {c: float(v.mean()) for c, v in lows.items()}} if spec.get("hatch") else {}))
    return fig, stem, [tpath], dict(cells={c: n for c, (_, n) in cells.items()}, spans={
        c: {f"S{pos[s] + 1}": v for s, v in sp.items()} for c, sp in spans.items()}, **extra)


def identity_families(rows, threshold):
    """Across K: a template joins the first family whose founding template it matches at r ≥ threshold (signed) and that
    its row has not used yet; otherwise it founds one (reference rule)."""
    reps, fam = [], {}
    for k, centers, order in rows:
        taken = set()
        for s in order:
            cand = [(float(centers[s] @ r), i) for i, r in enumerate(reps) if i not in taken and centers[s] @ r >= threshold]
            if cand:
                f = max(cand)[1]
            else:
                reps.append(centers[s])
                f = len(reps) - 1
            taken.add(f)
            fam[k, s] = f
    return fam


def plot_by_k(spec, data, info, meta, ms, sphere):
    ks = spec["k"]
    w = window_mask(spec, ms)
    cells = cells_of(spec, data, meta)
    sens = spec.get("polarity", "sensitive") == "sensitive"
    rows, paths = [], []
    for k in ks:
        centers, p = load_templates(spec, k, info)
        labels = {c: segment(x[:, w], centers, info["sfreq"], spec.get("min_segment_ms", 30), sens) for c, (x, _) in cells.items()}
        rows.append((k, centers, display_order(longest_runs(labels, ms[w], k), k)))
        paths.append(p)
    fam = identity_families(rows, spec.get("identity_threshold", 0.9))
    if max(fam.values()) >= len(IDENTITY_COLOURS):
        ep.die(f"{max(fam.values()) + 1} distinct templates but {len(IDENTITY_COLOURS)} identity colours")
    W, H = ep.canvas_size(dict(width_mm=spec.get("width_mm", 180), height_mm=spec.get("height_mm", 110)))
    fig = plt.figure(figsize=(W * MM, H * MM))
    top, bottom, side, lab_w = 4.0, 3.0, 4.0, 14.0
    extra = 5.0  # mm: state label above each map + spacing
    s = min((W - 2 * side - lab_w) / (max(ks) * 1.18), (H - top - bottom) / len(ks) - extra)
    vmax = max(float(np.abs(c).max()) for _, c, _ in rows)
    pad = (H - top - bottom - len(ks) * (s + extra)) / 2  # rows centred vertically on the fixed canvas
    for r, (k, centers, order) in enumerate(rows):
        y = H - top - pad - r * (s + extra) - 3.5 - s
        fig.text(side / W, (y + s / 2) / H, f"K = {k}", fontsize=7.5, fontweight="bold", va="center")
        for i, st in enumerate(order):
            framed_map(fig, W, H, side + lab_w + i * s * 1.18, y, s, centers[st], info, sphere, vmax,
                       IDENTITY_COLOURS[fam[k, st]], f"S{i + 1}", "", spec.get("cmap", "RdBu_r"))
    rng = f"{ks[0]}-{ks[-1]}" if len(ks) > 1 and ks == list(range(ks[0], ks[-1] + 1)) else "-".join(map(str, ks))
    stem = f"topo-by-K_K{rng}"
    return fig, stem, paths, dict(families={f"K{k}": [fam[k, s] for s in o] for k, _, o in rows},
                                  colour_distinctness=ep.colour_check([IDENTITY_COLOURS[f] for f in set(fam.values())],
                                                                      "identity colours"))


def caption(spec, meta, out, paths, facts):
    """Caption facts: what the whole figure shares, then one entry per panel row, named by its title (microstate figures
    carry no panel letters)."""
    k = meta["contract"]
    L = [f"# Caption facts for {out.name}", "", "## Whole figure", "",
         f"- Templates: " + (f"{spec['templates_source']} " if spec.get("templates_source") else "")
         + f"({', '.join(p.name for p in paths)}); K = {spec['k']}",
         "- Groups: " + ", ".join(f"{g} (n = {len(v)})" for g, v in meta["ids"].items())]
    if spec.get("exclude"):
        L.append("- Excluded: " + ep.excluded(spec))
    L.append(f"- Grand average: each subject's condition average, subjects weighted equally; baseline {k['baseline']} s, "
             f"filter {k['filter'][0]:g}–{k['filter'][1]:g} Hz" + (f", reference: {spec['reference']}" if spec.get("reference") else "")
             + " (identical in every panel, rule S1)")
    if spec.get("flat_channels"):
        L.append(f"- Flat channels kept (spec flat_channels, e.g. the reference electrode): {', '.join(spec['flat_channels'])}")
    L.append(f"- Segmentation: each sample of the grand average (average reference, unit norm) gets the template with the "
             f"highest {'signed' if spec.get('polarity', 'sensitive') == 'sensitive' else 'absolute'} spatial correlation; "
             f"runs shorter than {spec.get('min_segment_ms', 30)} ms take the better-fitting neighbour; window "
             f"{spec.get('window_ms', [0, 800])} ms" + (f", time-locked to {spec['time_locked_to']}" if spec.get("time_locked_to") else ""))
    if "low_gfp_fraction" in facts:
        L.append("- Hatched: GFP below the 95th percentile of the same average's pre-stimulus GFP")
    if "spans" not in facts:
        L.append(f"- Colours: one per template identity across K (signed r ≥ {spec.get('identity_threshold', 0.9)} with the "
                 "family's first template); numbers within a row by median latency")
    L.append(f"- Maps: templates after average reference and unit norm (unitless), symmetric colour scale, no electrode "
             f"marks; MNE {mne.__version__}")
    if any(not m["channel_order"].startswith("by name") for m in facts["templates_meta"]):
        L.append("- Template channels: no channel names stored; columns assumed to follow the data's channel order")
    L += ["", "## Panels (no letters; by title)", ""]
    if "spans" in facts:
        for c, sp in facts["spans"].items():
            runs_ = "; ".join(f"{s} {round(a)}–{round(b)} ms" for s, (a, b) in sorted(sp.items(), key=lambda x: int(x[0][1:])))
            L.append(f"- {c}: n = {facts['cells'][c]}; longest run per state (boundaries half-way between samples): {runs_}"
                     + (f"; hatched {facts['low_gfp_fraction'][c]:.0%} of the window" if "low_gfp_fraction" in facts else ""))
    else:
        L += [f"- K = {kk}: {len(fam)} templates, numbered S1–S{len(fam)}" for kk, fam in
              ((key[1:], v) for key, v in facts["families"].items())]
    Path(f"{out}_caption.md").write_text("\n".join(L) + "\n", encoding="utf8")


def template_meta(path):
    """Rule MS1 provenance: content digest of a template file and how its channels were matched."""
    named = path.suffix == ".npz" and "ch_names" in np.load(path, allow_pickle=False)
    return dict(file=str(path), md5=hashlib.md5(path.read_bytes()).hexdigest(),
                channel_order="by name (ch_names in the file)" if named else "assumed = data channel order (no ch_names)")


def plot(spec):
    check(spec)
    plt.rcParams.update(ep.STYLE)
    data, times, info, meta = ep.load(spec)
    ms = times * 1000
    sphere = ep.common_sphere(info)
    draw = plot_states if spec.get("figure", "states") == "states" else plot_by_k
    fig, stem, paths, facts = draw(spec, data, info, meta, ms, sphere)
    out = ep.versioned(ep.out_root(spec) / "microstate", stem)  # rules O1–O3
    for ext in ("svg", "png"):  # rule T5
        fig.savefig(f"{out}.{ext}", dpi=600 if ext == "png" else None)
    plt.close(fig)
    facts["templates_meta"] = [template_meta(p) for p in paths]
    caption(spec, meta, out, paths, facts)
    Path(f"{out}_run.json").write_text(json.dumps(dict(
        spec=spec, templates=[str(p) for p in paths], **facts, inputs=meta["inputs"], ids=meta["ids"],
        contract=meta["contract"], code_md5={f.name: hashlib.md5(f.read_bytes()).hexdigest() for f in
                                             (Path(__file__), Path(ep.__file__))},
        time_semantics="labels_ms: centres of each run's first and last sample; spans (and every drawn boundary): "
                       "half-way between samples (rule MS2)",
        size_mm=list(fig.get_size_inches() / MM), versions=dict(mne=mne.__version__, matplotlib=matplotlib.__version__),
        qa="PENDING: the agent records the visual QA result here after checking the PNG"),
        indent=1, ensure_ascii=False, default=float, allow_nan=False), encoding="utf8")  # strict JSON
    ep.archive(out)  # rule O2: older versions move only now that this one is complete
    print("wrote", f"{out}.png/.svg")
    return out


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    if sys.argv[1] != "plot":
        ep.die("usage: python microstate_plot.py plot <spec.json>")
    plot(ep.read_spec(sys.argv[2]))
