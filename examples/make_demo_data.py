"""Synthetic ERP data for trying brain-plot without your own recordings.

    python examples/make_demo_data.py

Writes, next to this file:
  demo_data/<group>/<subject>_demo-ave.fif   two groups × 12 subjects, conditions "standard" and "target"
  demo_templates/k04.npz                     four microstate templates (npz `centers`, `ch_names`)

The data are made up: P1 (occipital, ~100 ms), N1 (occipito-temporal, ~170 ms) and P3 (parietal, ~380 ms; larger
for targets, smaller in the "Patient" group) plus noise, 500 Hz, -200 to 800 ms, average reference.
"""
from pathlib import Path

import mne
import numpy as np

MONTAGE = "colin27_1020" if "colin27_1020" in mne.channels.get_builtin_montages() else "standard_1020"  # MNE ≥ 1.14 drops the old name

HERE = Path(__file__).parent
SF, TMIN, TMAX = 500.0, -0.2, 0.8
CH = ["Fp1", "Fp2", "F7", "F3", "Fz", "F4", "F8", "FC5", "FC1", "FC2", "FC6", "T7", "C3", "Cz", "C4", "T8", "CP5",
      "CP1", "CP2", "CP6", "P7", "P3", "Pz", "P4", "P8", "PO3", "PO4", "O1", "Oz", "O2", "CPz", "FCz"]
# component: (scalp centres, spatial width in m, latency s, temporal width s, amplitude µV)
COMPONENTS = {"P1": (["O1", "O2"], 0.05, 0.100, 0.018, 3.0),
              "N1": (["P7", "P8"], 0.05, 0.170, 0.022, -4.0),
              "P3": (["Pz"], 0.07, 0.380, 0.080, 6.0),
              "frontal": (["Fz"], 0.06, 0.260, 0.040, -2.0)}
GAIN = {("Control", "standard"): {"P3": 0.35}, ("Control", "target"): {"P3": 1.0},
        ("Patient", "standard"): {"P3": 0.30}, ("Patient", "target"): {"P3": 0.65}}


def info():
    inf = mne.create_info(CH, SF, "eeg")
    inf.set_montage(MONTAGE)
    return inf


def topography(inf, centres, width):
    pos = np.array([ch["loc"][:3] for ch in inf["chs"]])
    cen = np.array([pos[CH.index(c)] for c in centres])
    d = np.linalg.norm(pos[:, None] - cen[None], axis=2).min(1)
    m = np.exp(-(d / width) ** 2)
    return m - m.mean()  # average reference


def main():
    inf = info()
    times = np.arange(int(round(TMIN * SF)), int(round(TMAX * SF)) + 1) / SF
    maps = {k: topography(inf, c, w) for k, (c, w, *_) in COMPONENTS.items()}
    rng = np.random.default_rng(7)
    for g in ("Control", "Patient"):
        folder = HERE / "demo_data" / g
        folder.mkdir(parents=True, exist_ok=True)
        for s in range(12):
            jitter = rng.normal(0, 0.012)  # subject latency shift
            evs = []
            for cond in ("standard", "target"):
                x = np.zeros((len(CH), len(times)))
                for k, (_, _, lat, sd, amp) in COMPONENTS.items():
                    a = amp * GAIN[g, cond].get(k, 1.0) * rng.normal(1, 0.15)
                    x += np.outer(maps[k] / np.abs(maps[k]).max(), a * np.exp(-((times - lat - jitter) / sd) ** 2))
                noise = rng.normal(0, 0.6, x.shape)
                noise = np.apply_along_axis(lambda v: np.convolve(v, np.ones(9) / 9, "same"), 1, noise)
                x = (x + noise - (x + noise).mean(0)) * 1e-6  # average reference, volts
                evs.append(mne.EvokedArray(x, inf, tmin=TMIN, comment=cond, nave=int(rng.integers(40, 60))))
            for e in evs:
                e.apply_baseline((None, 0), verbose="error")
            mne.write_evokeds(folder / f"{g[0]}{s + 1:02d}_demo-ave.fif", evs, overwrite=True, verbose="error")
    out = HERE / "demo_templates"
    out.mkdir(exist_ok=True)
    centers = np.array([maps[k] / np.linalg.norm(maps[k]) for k in ("P1", "N1", "frontal", "P3")])
    np.savez(out / "k04.npz", centers=centers, ch_names=np.array(CH))
    print("wrote", HERE / "demo_data", "and", out / "k04.npz")


if __name__ == "__main__":
    main()
