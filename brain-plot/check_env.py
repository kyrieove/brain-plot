"""Environment check for brain-plot, standard library only (works before MNE is installed):

    python check_env.py

Prints this interpreter, the versions of the packages the scripts need, whether Arial/Helvetica is available, and
"OK" or what to install. Run it with the Python you will use for erp_plot.py / microstate_plot.py.
"""
import importlib
import sys

NEED = {"mne": (1, 6), "matplotlib": (3, 8), "numpy": (1, 23), "scipy": (1, 9)}
OPTIONAL = {"pandas": "only for `query` / `group_by` on Epochs metadata"}


def version(mod):
    parts = []
    for p in str(getattr(mod, "__version__", "0")).split(".")[:2]:
        digits = "".join(ch for ch in p if ch.isdigit())
        parts.append(int(digits or 0))
    return tuple(parts)


def main():
    problems = []
    print(f"python      {sys.version.split()[0]}  ({sys.executable})")
    if sys.version_info < (3, 10):
        problems.append("Python 3.10 or newer is needed")
    for name, low in NEED.items():
        try:
            mod = importlib.import_module(name)
            ok = version(mod) >= low
            print(f"{name:11s} {mod.__version__}" + ("" if ok else f"  (need ≥ {'.'.join(map(str, low))})"))
            if not ok:
                problems.append(f"upgrade {name} to ≥ {'.'.join(map(str, low))}")
        except ImportError:
            print(f"{name:11s} missing")
            problems.append(f"install {name}")
    for name, why in OPTIONAL.items():
        try:
            print(f"{name:11s} {importlib.import_module(name).__version__}")
        except ImportError:
            print(f"{name:11s} missing ({why})")
    fonts = []
    for f in ("Arial", "Helvetica"):
        try:
            from matplotlib import font_manager
            font_manager.findfont(f, fallback_to_default=False)  # raises when the family is not installed
            fonts.append(f)
        except Exception:
            pass
    print("font        " + (fonts[0] if fonts else "no Arial/Helvetica: matplotlib uses DejaVu Sans (wider; layout "
                             "checks still hold)"))
    print("OK" if not problems else "PROBLEMS: " + "; ".join(problems) + "  →  pip install -r requirements.txt")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
