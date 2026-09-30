"""Download the surveyed TFR figures (open access) from Europe PMC: DOI -> PMCID -> full-text XML -> figure graphic."""
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE / "figures"
OUT.mkdir(exist_ok=True)
UA = {"User-Agent": "brain-plot-survey/1.0 (research use)"}


def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read()


rows = [l for l in (HERE / "survey.md").read_text("utf8").splitlines() if l.startswith("| [")]
for row in rows:
    doi = re.search(r"doi\.org/(10\.[^)]+)\)", row).group(1)
    fig = re.search(r"Fig\. (\d+)", row).group(1)
    try:
        q = urllib.parse.quote(f'DOI:"{doi}"')
        hit = __import__("json").loads(get(f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?query={q}&format=json&resultType=lite"))
        pmcid = next((r.get("pmcid") for r in hit["resultList"]["result"] if r.get("pmcid")), None)
        if not pmcid:
            print(doi, "no PMCID")
            continue
        root = ET.fromstring(get(f"https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML"))
        href = None
        for f in root.iter("fig"):
            label = (f.findtext("label") or "").strip()
            if re.fullmatch(rf"(Figure|Fig\.?)\s*{fig}\.?", label, re.I):
                g = f.find("graphic")
                href = next((v for k, v in g.attrib.items() if k.endswith("href")), None) if g is not None else None
                break
        if not href:
            print(doi, pmcid, f"fig {fig} not found")
            continue
        name = f"{doi.split('/')[-1].replace('.', '_')}_fig{fig}.jpg"
        (OUT / name).write_bytes(get(f"https://europepmc.org/articles/{pmcid}/bin/{href}.jpg"))
        print(doi, pmcid, "->", name)
    except Exception as e:  # one failed paper must not stop the rest
        print(doi, "failed:", e, file=sys.stderr)
