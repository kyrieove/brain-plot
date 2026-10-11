"""Check a survey table (default survey.md; arg 1 = file name, arg 2 = min rows): enough rows, every figure image present and readable.
A file named survey-besa.md / survey-mne.md must name BESA / MNE in every row."""
import re
import sys
from pathlib import Path

from PIL import Image

HERE = Path(__file__).parent
SURVEY = sys.argv[1] if len(sys.argv) > 1 else "survey.md"
MIN_ROWS = int(sys.argv[2]) if len(sys.argv) > 2 else 12

text = (HERE / SURVEY).read_text(encoding="utf-8")
rows = [l for l in text.splitlines() if re.match(r"\|\s*\d+\s*\|", l)]
problems = []
if len(rows) < MIN_ROWS:
    problems.append(f"{len(rows)} table rows, need >= {MIN_ROWS}")
for row in rows:
    cells = [c.strip() for c in row.strip("|").split("|")]
    num = cells[0]
    for tool in ("BESA", "MNE"):
        if tool.lower() in SURVEY and tool.lower() not in row.lower():
            problems.append(f"row {num}: {tool} not named")
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
