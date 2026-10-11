"""Prototype: four candidate 'waves' layouts x several designs (2 conditions, 2x2, 2x3, 2x4), GN test 01 data.
Adaptive rule shared by all candidates: factor A = the two conditions that were contrasted (colour); factor B = any
extra between-subject factor (levels): 1 level -> nothing extra, 2-4 levels -> facets (B, C, D) or line styles (A)."""
import sys, json
from pathlib import Path
import numpy as np, mne
from scipy import stats
import matplotlib.pyplot as plt
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "brain-plot"))
import cluster_plot as cp
import erp_plot as ep

spec = json.load(open(HERE.parent / "cluster-before-after" / "spec_gn.json"))
run = cp.read_run(spec); run_dir = Path(spec["data"])
T = run["tests"][0]
Z = np.load(HERE / "roi_cache.npz")
tt = Z["times"]
CL = [c for c in T["clusters"] if c["cluster_id"] in (8, 9)]
COND = ("NoGO", "GO")
COL = {"NoGO": ep.LANCET[1], "GO": ep.LANCET[0]}
LS = ["-", "--", ":", "-."]
DESIGNS = {"2": [None], "2x2": ["TD", "RD"], "2x3": ["TD", "MD", "RD"], "2x4": ["TD", "MD", "RD", "ADHD"]}
W = 180.0


def cell(cid, level, cond):
    """(n_sub, n_t) ROI waves of one cell; level None pools all groups."""
    if level is None:
        return np.vstack([Z[f"{cid}|{g}|{cond}"] for g in ("TD", "MD", "RD", "ADHD")])
    return Z[f"{cid}|{level}|{cond}"]


def mci(x):
    n = len(x)
    return x.mean(0), stats.t.ppf(0.975, n - 1) * x.std(0, ddof=1) / np.sqrt(n)


def diffwave(cid, level):
    a, b = cell(cid, level, COND[0]), cell(cid, level, COND[1])
    if level is None:   # paired: pooled order is group-then-subject for both conds, so rows align
        pass
    return mci(a - b)


def ylims(levels, diff=False):
    lo, hi = 0.0, 0.0
    for c in CL:
        for lv in levels:
            for cond in COND:
                m, h = mci(cell(c["cluster_id"], lv, cond))
                lo, hi = min(lo, (m - h).min()), max(hi, (m + h).max())
    pad = 0.06 * (hi - lo)
    return lo - pad, hi + pad


def dlims(levels):
    lo, hi = 0.0, 0.0
    for c in CL:
        for lv in levels:
            m, h = diffwave(c["cluster_id"], lv)
            lo, hi = min(lo, (m - h).min()), max(hi, (m + h).max())
    pad = 0.08 * (hi - lo)
    return lo - pad, hi + pad


def draw_wave(ax, cid, level, c, ylim, ls="-", legend=False, label_level=None, neg_up=True):
    ax.axvspan(c["time_start_ms"], c["time_end_ms"], color="0.9", lw=0, zorder=0)
    for cond in COND:
        m, h = mci(cell(cid, level, cond))
        ax.fill_between(tt, m - h, m + h, color=COL[cond], alpha=0.15, lw=0)
        ax.plot(tt, m, color=COL[cond], lw=0.9, ls=ls, label=cond if label_level is None else f"{cond} · {label_level}")
    ax.axvline(0, color="0.5", lw=0.4, ls="--"); ax.axhline(0, color="0.5", lw=0.4)
    ax.set_ylim(*ylim); ax.set_xlim(tt[0], tt[-1])
    if neg_up:
        ax.invert_yaxis()


def draw_diff(ax, cid, level, c, ylim, neg_up=True):
    ax.axvspan(c["time_start_ms"], c["time_end_ms"], color="0.9", lw=0, zorder=0)
    m, h = diffwave(cid, level)
    ax.fill_between(tt, m - h, m + h, color="0.2", alpha=0.15, lw=0)
    ax.plot(tt, m, color="0.1", lw=0.9)
    ax.axhline(0, color="0.5", lw=0.4); ax.axvline(0, color="0.5", lw=0.4, ls="--")
    ax.set_ylim(*ylim); ax.set_xlim(tt[0], tt[-1])
    if neg_up:
        ax.invert_yaxis()


def topo_setup():
    info = cp.first_info(run, run_dir)
    info = cp.picked_info(info, run["ch_names"], "cache")
    sphere = ep.common_sphere(info)
    T["uv"] = Z["uv"][:, :]
    maps = cp.maps_of(T, run["times_ms"], run["ch_names"], "clusters", [], True)
    maps = [m for m, c in zip(maps, T["clusters"]) if c["cluster_id"] in (8, 9)]
    return info, sphere, maps, cp.topo_limits(maps, True, info, sphere)


INFO, SPHERE, MAPS, TL = topo_setup()


def topo(fig, r_mm, k, H, label=True):
    vec, marked, lab = MAPS[k]
    return cp.draw_map(fig, [r_mm[0], H - r_mm[1] - r_mm[3], r_mm[2], r_mm[3]], vec, marked, lab if label else "",
                       TL[3], TL[1], TL[2], INFO, SPHERE, W, H)


def title(fig, x, y, c, H, n=None):
    fig.text(x / W, 1 - y / H, f"Cluster {c['cluster_id']} · p = {c['p_cluster']:g} · {len(c['channels'])} ch · "
             f"{c['time_start_ms']:g}–{c['time_end_ms']:g} ms", ha="left", va="bottom", fontsize=6)


def cbar(fig, H, y0, h, im):
    cp.colorbar(fig, [W - 11.0, y0, 2.0, h], im, [-TL[0], 0.0, TL[0]], "µV", W, H)


def xlab(ax, last):
    xt, labs, _ = ep.x_ticks(ax, ax.figure, tt[0], tt[-1], zero=True)
    ax.set_xticks(xt); ax.set_xticklabels(labs if last else [])
    if last:
        ax.set_xlabel("Time (ms)")


def legend_row(fig, H, handles, labels, ncol=None):
    fig.legend(handles, labels, ncol=ncol or len(labels), frameon=False, fontsize=5, loc="lower center",
               bbox_to_anchor=(0.5, 2.0 / H))


# ---------------------------------------------------------------- A: overlay (one axis per cluster, line style = level)
def cand_A(levels):
    map_mm, gap, top, bot = 24.0, 12.0, 8.0, 16.0
    n = len(CL); H = top + n * (map_mm + gap) - gap + bot
    fig = plt.figure(figsize=(W * ep.MM, H * ep.MM)); yl = ylims(levels)
    wx = 6 + map_mm + gap; ww = W - 14 - wx
    axs = [fig.add_axes([wx / W, 1 - (top + r * (map_mm + gap) + map_mm) / H, ww / W, map_mm / H]) for r in range(n)]
    im = None
    for r, (c, ax) in enumerate(zip(CL, axs)):
        for j, lv in enumerate(levels):
            draw_wave(ax, c["cluster_id"], lv, c, yl, ls=LS[j])
        xlab(ax, r == n - 1); ax.set_ylabel("µV")
        im = topo(fig, [6, top + r * (map_mm + gap), map_mm, map_mm], r, H); title(fig, wx, top + r * (map_mm + gap) - 2, c, H)
    cbar(fig, H, bot, n * (map_mm + gap) - gap, im)
    hs = [plt.Line2D([], [], color=COL[c], lw=1) for c in COND]
    hl = [plt.Line2D([], [], color="k", lw=1, ls=LS[j]) for j in range(len(levels) if levels[0] else 0)]
    legend_row(fig, H, hs + hl, list(COND) + [str(l) for l in levels if l])
    return fig


# ---------------------------------------------------------------- B: facets (one panel per level, per cluster row)
def cand_B(levels, diff=False):
    k = len(levels); map_mm, gap, top, bot = 24.0, 14.0, 12.0, 16.0
    n = len(CL); sub = 0.0 if not diff else 14.0
    row_h = map_mm + (sub + 2 if diff else 0)
    H = top + n * (row_h + gap) - gap + bot
    fig = plt.figure(figsize=(W * ep.MM, H * ep.MM)); yl = ylims(levels); dl = dlims(levels) if diff else None
    x0 = 6 + map_mm + 10; pw = (W - 14 - x0 - (k - 1) * 3.0) / k
    im = None
    for r, c in enumerate(CL):
        y = top + r * (row_h + gap)
        for j, lv in enumerate(levels):
            ax = fig.add_axes([(x0 + j * (pw + 3.0)) / W, 1 - (y + map_mm) / H, pw / W, map_mm / H])
            draw_wave(ax, c["cluster_id"], lv, c, yl)
            last = r == n - 1 and not diff
            xlab(ax, last)
            if j == 0:
                ax.set_ylabel("µV")
            else:
                ax.set_yticklabels([])
            if r == 0 and lv:
                ax.set_title(lv, fontsize=6)
            if diff:
                ax2 = fig.add_axes([(x0 + j * (pw + 3.0)) / W, 1 - (y + map_mm + 2 + sub) / H, pw / W, sub / H])
                draw_diff(ax2, c["cluster_id"], lv, c, dl)
                xlab(ax2, r == n - 1)
                if j == 0:
                    ax2.set_ylabel("Δ µV")
                else:
                    ax2.set_yticklabels([])
        im = topo(fig, [6, y, map_mm, map_mm], r, H); title(fig, x0, y - (7 if levels[0] else 2), c, H)
    cbar(fig, H, bot, n * (row_h + gap) - gap, im)
    legend_row(fig, H, [plt.Line2D([], [], color=COL[c], lw=1) for c in COND] + ([plt.Line2D([], [], color="0.1", lw=1)] if diff else []),
               list(COND) + (["NoGO − GO"] if diff else []))
    return fig


def cand_C(levels):
    return cand_B(levels, diff=True)


# ---------------------------------------------------------------- D: clusters as columns, topo on top, level rows under
def cand_D(levels):
    n = len(CL); k = len(levels); top, bot = 8.0, 16.0; map_mm, wh, g = 26.0, 22.0, 3.0
    H = top + map_mm + 8 + k * wh + (k - 1) * g + bot
    fig = plt.figure(figsize=(W * ep.MM, H * ep.MM)); yl = ylims(levels)
    left, right, cg = 18.0, 14.0, 8.0; cw = (W - left - right - (n - 1) * cg) / n
    im = None
    for i, c in enumerate(CL):
        x = left + i * (cw + cg)
        im = topo(fig, [x + (cw - map_mm) / 2, top, map_mm, map_mm], i, H)
        fig.text((x + cw / 2) / W, 1 - (top - 2) / H, f"Cluster {c['cluster_id']} · p = {c['p_cluster']:g} · {len(c['channels'])} ch",
                 ha="center", va="bottom", fontsize=6)
        for j, lv in enumerate(levels):
            ax = fig.add_axes([x / W, 1 - (top + map_mm + 8 + j * (wh + g) + wh) / H, cw / W, wh / H])
            draw_wave(ax, c["cluster_id"], lv, c, yl)
            xlab(ax, j == k - 1)
            if i == 0:
                ax.set_ylabel("µV")
                if lv:
                    fig.text(3.0 / W, 1 - (top + map_mm + 8 + j * (wh + g) + wh / 2) / H, lv, rotation=90, ha="center",
                             va="center", fontsize=6, fontweight="bold")
            else:
                ax.set_yticklabels([])
    cbar(fig, H, bot + (H - top - map_mm - bot) , map_mm, im) if False else cbar(fig, H, H - top - map_mm, map_mm, im)
    legend_row(fig, H, [plt.Line2D([], [], color=COL[c], lw=1) for c in COND], list(COND))
    return fig


CANDS = {"A": cand_A, "B": cand_B, "C": cand_C, "D": cand_D}

if __name__ == "__main__":
    plt.rcParams.update(ep.STYLE)
    out = HERE / "img"; out.mkdir(exist_ok=True)
    for dn, lv in DESIGNS.items():
        for cn, fn in CANDS.items():
            f = fn(lv)
            f.savefig(out / f"{cn}_{dn}.png", dpi=220)
            plt.close(f)
            print("wrote", f"{cn}_{dn}.png")
