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
from matplotlib.patches import FancyBboxPatch, Rectangle

import erp_plot as ep

REQUIRED = {"data", "conditions", "templates", "k", "templates_source"}
OPTIONAL = {"figure", "blocks", "groups", "exclude", "per_group", "window_ms", "min_segment_ms", "polarity", "width_mm",
            "height_mm", "identity_threshold", "cmap", "reference", "time_locked_to"}
BLOCKS = {"topo": "topo", "butterfly": "butterfly", "gfp": "GFP", "ribbon": "ribbon"}  # block → file-name part
STATE_COLOURS = ["#00468B", "#ED0000", "#42B540", "#0099B4", "#925E9F", "#FDAF91", "#AD002A", "#7A8A8A", "#1B1919",
                 "#D4A017"]  # rule MS5: the reference palette, by display number
IDENTITY_COLOURS = STATE_COLOURS + ["#B8860B", "#E75480", "#2E8B7A", "#6B4C9A", "#8B5A2B", "#5B8FF9"]
TRACE, SOFT = "#171b21", "#5a626d"
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
    if spec.get("polarity", "sensitive") not in ("sensitive", "insensitive"):
        ep.die("polarity must be 'sensitive' or 'insensitive' (as in the analysis that made the templates)")
    lo, hi = spec.get("window_ms", [0, 800])
    if not lo < hi:
        ep.die("window_ms needs start < end")
    if not ep.text(spec["templates_source"]):
        ep.die("templates_source must say which analysis made the templates")


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
    c = c - c.mean(1, keepdims=True)
    return c / np.linalg.norm(c, axis=1, keepdims=True), path


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
    """Per cell: state → (onset, offset) ms of its longest run (offset = end of its last sample)."""
    step = ms[1] - ms[0]
    out = {}
    for cell, lab in labels.items():
        best = {}
        for a, b, s in runs(lab):
            if b - a > best.get(s, (0,))[0]:
                best[s] = (b - a, float(ms[a]), float(ms[b - 1] + step))
        out[cell] = {s: v[1:] for s, v in best.items()}
    return out


def display_order(spans, k):
    """Rule MS4: states numbered by the median midpoint of their longest runs across cells; absent states last."""
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


def hatch(ax, ms, mask, y0, y1):
    """Rule MS3: diagonal white hatch over low-GFP runs; the state colour stays visible underneath."""
    step = ms[1] - ms[0]
    for a, b, v in runs(mask.astype(int)):
        if v:
            ax.add_patch(Rectangle((ms[a], y0), ms[b - 1] - ms[a] + step, y1 - y0, fill=False, hatch="//////",
                                   ec="white", lw=0, zorder=4))


def time_axis(ax, lo, hi, labelled):
    ax.set_xlim(lo, hi)
    step = 200 if hi - lo >= 600 else 100
    ax.set_xticks(np.arange(np.ceil(lo / step) * step, hi + 1e-9, step))
    ax.tick_params(axis="x", labelsize=6, length=2, pad=1.5)
    if labelled:
        ax.set_xlabel("Time (ms)", fontsize=7, labelpad=1)


def plot_states(spec, data, info, meta, ms, sphere):
    k, blocks = spec["k"], spec.get("blocks", ["topo", "butterfly", "ribbon"])
    lo, hi = spec.get("window_ms", [0, 800])
    w = ep.sample_mask(ms, lo, hi)
    if w.sum() < 2 or lo < ms[0] - 1 or hi > ms[-1] + 1:
        ep.die(f"window_ms {lo, hi} must lie inside the data ({ms[0]:g}–{ms[-1]:g} ms)")
    centers, tpath = load_templates(spec, k, info)
    cells = cells_of(spec, data, meta)
    sens = spec.get("polarity", "sensitive") == "sensitive"
    labels = {c: segment(x[:, w], centers, info["sfreq"], spec.get("min_segment_ms", 30), sens) for c, (x, _) in cells.items()}
    lows = {c: low_gfp(x, ms, w) for c, (x, _) in cells.items()}
    spans = longest_runs(labels, ms[w], k)
    order = display_order(spans, k)
    pos = {s: i for i, s in enumerate(order)}
    col = {s: STATE_COLOURS[pos[s] % len(STATE_COLOURS)] for s in range(k)}
    t = ms[w]

    W, H = ep.canvas_size(dict(width_mm=spec.get("width_mm", 180), height_mm=spec.get("height_mm", 110)))
    fig = plt.figure(figsize=(W * MM, H * MM))
    top, bottom, side = 6.0, 9.0, 4.0
    x_right = side
    if "topo" in blocks:  # rule MS6: template column at the left, one or two columns of framed maps
        ncol = 1 if k <= 5 else 2
        nrow = -(-k // ncol)
        n_sub = len(cells) if len(cells) <= 4 else 0  # per-cell time ranges only while they stay legible
        extra = 3.5 + 2.3 * n_sub + 1.0  # mm: state label above, one range line per cell below, spacing
        s = min((H - top - bottom) / nrow - extra, 18.0)
        zone = ncol * s + (ncol - 1) * 4
        y_top = H - top - (H - top - bottom - nrow * (s + extra)) / 2
        vmax = float(np.abs(centers).max())
        short = {c: c.split(" · ")[0] if len(cells) > 1 else "" for c in cells}
        for i, st in enumerate(order):
            r, cc = i % nrow, i // nrow
            sub = "\n".join(f"{short[c]} {spans[c][st][0]:.0f}–{spans[c][st][1]:.0f}".strip() if st in spans[c]
                            else f"{short[c]} —".strip() for c in cells) if n_sub else ""  # rule MS7a
            framed_map(fig, W, H, side + cc * (s + 4), y_top - r * (s + extra) - 3.5 - s, s,
                       centers[st], info, sphere, vmax, col[st], f"S{i + 1}", sub, spec.get("cmap", "RdBu_r"))
        x_right = side + zone + 6
    panels = [b for b in ("butterfly", "gfp") if b in blocks]
    ylab = 11.0  # room for the y label and ticks of each time panel
    avail = W - x_right - side - ylab * len(panels) - 2
    widths = [avail * (1.3 if p == "butterfly" and len(panels) == 2 else 1.0) / (2.3 if len(panels) == 2 else 1)
              for p in panels]
    n = len(cells)
    rib = 3.2 if "ribbon" in blocks else 0.0
    gap = 9.0
    row_h = (H - top - bottom - (n - 1) * gap) / n
    amp = max(np.abs(x[:, w]).max() for x, _ in cells.values()) * 1.08
    gmax = max(x[:, w].std(0).max() for x, _ in cells.values()) * 1.10
    for r, (cell, (x, n_subj)) in enumerate(cells.items()):
        y0 = H - top - (r + 1) * row_h - r * gap
        lab, low = labels[cell], lows[cell]
        gfp = x[:, w].std(0)
        bounds = [t[a] for a, _, _ in runs(lab)[1:]]
        xx = x_right + ylab
        for p, pw in zip(panels, widths):
            ax = mm_axes(fig, W, H, xx, y0 + rib + (1.0 if rib else 0), pw, row_h - rib - (1.0 if rib else 0))
            if p == "butterfly":
                ax.plot(t, x[:, w].T, color=TRACE, alpha=0.42, lw=0.28, zorder=2)
                ax.plot(t, gfp, color=TRACE, lw=1.0, zorder=3)
                ax.annotate("GFP", (t[-1], gfp[-1]), xytext=(0, 2), textcoords="offset points", fontsize=6,
                            ha="right", va="bottom", color=TRACE)  # rule MS7c: inside the panel
                ax.set_ylim(-amp, amp)
                ax.set_ylabel("Amplitude (µV)", fontsize=7, labelpad=1)
                ax.set_title(f"{cell} | N = {n_subj}", fontsize=7, fontweight="bold", pad=2.5)
                for b in bounds:
                    ax.axvline(b, color=SOFT, lw=0.5, ls=":", zorder=1)
            else:
                ax.plot(t, gfp, color=TRACE, lw=0.8, zorder=3)
                for a, b, st in runs(lab):
                    ax.fill_between(t[a:b + 1], 0, gfp[a:b + 1], color=col[st], lw=0, zorder=2)
                hatch(ax, t, low, 0, gmax)
                ax.set_ylim(0, gmax)
                ax.set_ylabel("GFP (µV)", fontsize=7, labelpad=1)
                ax.set_title(f"{cell} | GFP", fontsize=7, fontweight="bold", pad=2.5)
            ax.tick_params(labelsize=6, length=2, pad=1.5)
            time_axis(ax, t[0], t[-1] + (t[1] - t[0]), labelled=False)
            if rib and p == "butterfly":  # rule MS7b: ribbon under the butterfly, labelled S1, S2, …
                ax.tick_params(axis="x", labelbottom=False)
                rax = mm_axes(fig, W, H, xx, y0, pw, rib)
                step = t[1] - t[0]
                for a, b, st in runs(lab):
                    rax.add_patch(Rectangle((t[a], 0), t[b - 1] - t[a] + step, 1, color=col[st], lw=0))
                    if (t[b - 1] - t[a]) > 0.045 * (t[-1] - t[0]):
                        rax.text((t[a] + t[b - 1] + step) / 2, 0.5, f"S{pos[st] + 1}", ha="center", va="center",
                                 fontsize=5.5, color="white", fontweight="bold", zorder=5)
                hatch(rax, t, low, 0, 1)
                rax.set_ylim(0, 1)
                rax.set_yticks([])
                for sp in ("left", "right", "top"):
                    rax.spines[sp].set_visible(False)
                time_axis(rax, t[0], t[-1] + step, labelled=r == n - 1)
            elif r == n - 1:
                ax.set_xlabel("Time (ms)", fontsize=7, labelpad=1)
            xx += pw + ylab
    stem = f"{'-'.join(BLOCKS[b] for b in blocks)}_K{k}_{'-'.join(map(ep.safe, spec['conditions']))}" \
           + ("_by-group" if spec.get("per_group") else "")  # rule O3
    extra = dict(order_by_display=[int(s) for s in order], labels_ms={c: [[float(t[a]), float(t[b - 1]), f"S{pos[st] + 1}"]
                                                                      for a, b, st in runs(l)] for c, l in labels.items()},
                 low_gfp_fraction={c: float(v.mean()) for c, v in lows.items()})
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
    lo, hi = spec.get("window_ms", [0, 800])
    w = ep.sample_mask(ms, lo, hi)
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
    for r, (k, centers, order) in enumerate(rows):
        y = H - top - r * (s + extra) - 3.5 - s
        fig.text(side / W, (y + s / 2) / H, f"K = {k}", fontsize=7.5, fontweight="bold", va="center")
        for i, st in enumerate(order):
            framed_map(fig, W, H, side + lab_w + i * s * 1.18, y, s, centers[st], info, sphere, vmax,
                       IDENTITY_COLOURS[fam[k, st]], f"S{i + 1}", "", spec.get("cmap", "RdBu_r"))
    stem = f"topo-by-K_K{'-'.join(map(str, ks)) if ks != list(range(ks[0], ks[-1] + 1)) else f'{ks[0]}-{ks[-1]}'}"
    return fig, stem, paths, dict(families={f"K{k}": [fam[k, s] for s in o] for k, _, o in rows})


def caption(spec, meta, out, paths, facts):
    k = meta["contract"]
    L = [f"# Caption facts for {out.name}", "",
         f"- Templates: {spec['templates_source']} ({', '.join(p.name for p in paths)}); K = {spec['k']}",
         "- Groups: " + ", ".join(f"{g} (n = {len(v)})" for g, v in meta["ids"].items())]
    if spec.get("exclude"):
        L.append("- Excluded: " + "; ".join(f"{i} ({r})" for i, r in spec["exclude"].items()))
    L.append(f"- Grand average: each subject's condition average, subjects weighted equally; baseline {k['baseline']} s, "
             f"filter {k['filter'][0]}–{k['filter'][1]} Hz" + (f", reference: {spec['reference']}" if spec.get("reference") else ""))
    L.append(f"- Segmentation: each sample of the grand average (average reference, unit norm) gets the template with the "
             f"highest {'signed' if spec.get('polarity', 'sensitive') == 'sensitive' else 'absolute'} spatial correlation; "
             f"runs shorter than {spec.get('min_segment_ms', 30)} ms take the better-fitting neighbour; window "
             f"{spec.get('window_ms', [0, 800])} ms" + (f", time-locked to {spec['time_locked_to']}" if spec.get("time_locked_to") else ""))
    if "spans" in facts:
        L.append("- Hatched: GFP below the 95th percentile of the same average's pre-stimulus GFP (fraction of the window: "
                 + ", ".join(f"{c} {v:.0%}" for c, v in facts["low_gfp_fraction"].items()) + ")")
        for c, sp in facts["spans"].items():
            L.append(f"- {c}: " + "; ".join(f"{s} {a:.0f}–{b:.0f} ms (longest run)" for s, (a, b) in sorted(sp.items(), key=lambda x: int(x[0][1:]))))
    else:
        L.append(f"- Colours: one per template identity across K (signed r ≥ {spec.get('identity_threshold', 0.9)} with the "
                 "family's first template); numbers within a row by median latency")
    L.append(f"- Maps: templates, symmetric colour scale, no electrode marks; MNE {mne.__version__}")
    Path(f"{out}_caption.md").write_text("\n".join(L) + "\n", encoding="utf8")


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
    caption(spec, meta, out, paths, facts)
    Path(f"{out}_run.json").write_text(json.dumps(dict(
        spec=spec, templates=[str(p) for p in paths], **facts, inputs=meta["inputs"], ids=meta["ids"],
        contract=meta["contract"], code_md5=hashlib.md5(Path(__file__).read_bytes()).hexdigest(),
        size_mm=list(fig.get_size_inches() / MM), versions=dict(mne=mne.__version__, matplotlib=matplotlib.__version__),
        qa="PENDING: the agent records the visual QA result here after checking the PNG"),
        indent=1, ensure_ascii=False, default=float), encoding="utf8")
    print("wrote", f"{out}.png/.svg")
    return out


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    if sys.argv[1] != "plot":
        ep.die("usage: python microstate_plot.py plot <spec.json>")
    plot(json.loads(Path(sys.argv[2]).read_text(encoding="utf8")))
