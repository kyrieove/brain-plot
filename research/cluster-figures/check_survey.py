"""Check research/cluster-figures/survey.md: enough rows, every figure image present and readable."""
import re
import sys
from pathlib import Path

from PIL import Image

HERE = Path(__file__).parent
MIN_ROWS = 12

text = (HERE / "survey.md").read_text(encoding="utf-8")
rows = [l for l in text.splitlines() if re.match(r"\|\s*\d+\s*\|", l)]
problems = []
if len(rows) < MIN_ROWS:
    problems.append(f"{len(rows)} table rows, need >= {MIN_ROWS}")
for row in rows:
    cells = [c.strip() for c in row.strip("|").split("|")]
    num = cells[0]
    if not re.search(r"10\.\d{4,9}/\S+|https?://", row):
        problems.append(f"row {num}: no DOI or URL")
    imgs = re.findall(r"figures/[^\s)|`]+", row)
    if not imgs:
        problems.append(f"row {num}: no figures/ image path")
    for rel in imgs:
        p = HERE / rel
        if not p.is_file():
            problems.append(f"row {num}: missing {rel}")
            continue
        try:
            with Image.open(p) as im:
                w, h = im.size
            if min(w, h) < 300:
                problems.append(f"row {num}: {rel} only {w}x{h} px")
        except Exception as e:  # not an image (HTML error page etc.)
            problems.append(f"row {num}: {rel} unreadable ({e.__class__.__name__})")
print(f"{len(rows)} rows checked")
for p in problems:
    print("FAIL", p)
sys.exit(1 if problems else 0)
