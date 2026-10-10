"""Crop a region of a PNG (0-1 relative box) and scale it for visual QA.

python qa_crop.py <png> <x0> <y0> <x1> <y1> [--out path] [--width 800]
python qa_crop.py --selftest
"""
import argparse
import os
import sys
import tempfile

from PIL import Image


def crop(png, x0, y0, x1, y1, out=None, width=800):
    im = Image.open(png)
    w, h = im.size
    box = (round(x0 * w), round(y0 * h), round(x1 * w), round(y1 * h))
    if not (0 <= x0 < x1 <= 1 and 0 <= y0 < y1 <= 1) or box[2] <= box[0] or box[3] <= box[1]:
        raise ValueError(f"bad box {(x0, y0, x1, y1)}: need 0 <= x0 < x1 <= 1 and 0 <= y0 < y1 <= 1")
    c = im.crop(box)
    c = c.resize((width, max(1, round(c.height * width / c.width))), Image.LANCZOS)
    if out is None:
        fd, out = tempfile.mkstemp(suffix=".png", prefix="qa_crop_")
        os.close(fd)
    c.save(out)
    return out


def selftest():
    d = tempfile.mkdtemp()
    src = os.path.join(d, "src.png")
    Image.new("RGB", (400, 200), "white").save(src)
    out = crop(src, 0.25, 0.5, 0.75, 1.0, out=os.path.join(d, "o.png"), width=100)
    assert Image.open(out).size == (100, 50), Image.open(out).size
    try:
        crop(src, 0.6, 0, 0.4, 1)
    except ValueError:
        print("OK")
        return
    raise AssertionError("inverted box accepted")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
        sys.exit(0)
    p = argparse.ArgumentParser()
    p.add_argument("png")
    p.add_argument("box", nargs=4, type=float, metavar=("x0", "y0", "x1", "y1"))
    p.add_argument("--out")
    p.add_argument("--width", type=int, default=800)
    a = p.parse_args()
    print(crop(a.png, *a.box, out=a.out, width=a.width))
