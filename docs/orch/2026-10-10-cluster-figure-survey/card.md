# cluster-figure-survey — collect real ERP cluster-permutation result figures (images + sources)

## Goal
`research/cluster-figures/survey.md` holds a table of at least 12 real, published figures that show sensor-level
ERP (EEG/MEG event-related, channel × time) cluster-permutation or TFCE results, each with a verified DOI or
tutorial URL and a downloaded figure image under `research/cluster-figures/figures/`, plus a short summary of how
these figures are usually drawn. It feeds the drawing decisions in `docs/plan-cluster.md`. Research only, no code.

## Risk
low — literature lookup, no code; Claude opens every downloaded image and re-checks 2 DOIs at acceptance.

## Parameters
- Rows: >= 12 figures, at most 2 figures from the same paper. Target 14–18.
- Mix: >= 2 method/tutorial sources (e.g. MNE-Python sensor-level spatio-temporal cluster tutorial, FieldTrip
  `cluster_permutation_timelock` tutorial, Maris & Oostenveld 2007 J Neurosci Methods, Sassenhagen & Draschkow 2019
  Psychophysiology, Mensen & Khatami 2013 NeuroImage) and >= 10 empirical ERP papers published 2018–2026 in
  peer-reviewed journals, open access (eLife, J Neurosci, NeuroImage, Psychophysiology, Cortex, Brain and Language,
  Neuropsychologia, PLOS Biology/ONE, Scientific Reports, Frontiers, Imaging Neuroscience, Communications Biology).
  Cognitive / language / attention / inhibition tasks preferred. No preprints, no theses.
- In scope: figures whose content is a sensor-space ERP cluster or TFCE result: channel × time raster/image,
  topomap series with cluster channels marked, cluster-averaged waveforms with significant-time shading or bars,
  or any combination. Out of scope: time-frequency clusters, source-space clusters, MVPA decoding curves.
- DOI check: every DOI resolved with `https://api.crossref.org/works/<DOI>`; the returned title and first author
  must match what the row says. A DOI that does not resolve or does not match → drop the row. Tutorials: the URL
  must load; record the access date 2026-10-10.
- Image: the figure image from the publisher / PMC / eLife / tutorial page (full-size version when offered),
  saved as `research/cluster-figures/figures/NN_<firstauthor><year>_fig<k>.<png|jpg|gif>` (NN = row number,
  two digits; lowercase ASCII). Shorter side >= 300 px. Only open-access or tutorial images; no login, no paywall,
  no CAPTCHA. If a page will not give the image, drop that row and find another figure.

## Files
may change: `research/cluster-figures/survey.md`, `research/cluster-figures/figures/`
read-only: `research/cluster-figures/check_survey.py`, `docs/plan-cluster.md`, `docs/research-figure-conventions.md`, `brain-plot/`

## Steps (N = 4)
1. Search. Use web search and the sources in Parameters (PMC / Europe PMC full text, eLife figure pages,
   Frontiers, PLOS, mne.tools, fieldtriptoolbox.org). Find candidate figures that match "In scope". Read each
   candidate's figure caption and the methods sentence that names the test (cluster permutation / TFCE, t or F,
   n permutations if given). Keep a candidate only if the caption or methods say the figure shows that result.
2. Verify and download. For each kept figure: resolve the DOI on Crossref (Parameters), then download the figure
   image with a plain HTTP GET (e.g. `curl -L -o <path> <url>` or Python `urllib`) into
   `research/cluster-figures/figures/` with the file name from Parameters. After each download confirm the file is
   an image (not an HTML error page): Python `PIL.Image.open(path).size`. Keep going until there are >= 12 rows.
3. Write `research/cluster-figures/survey.md`:
   - First line `# Survey: ERP cluster-permutation result figures (2026-10-10)`, then one sentence on scope and how
     rows were selected.
   - One markdown table. The first cell of each row is the row number (`| 1 |`, `| 2 |` …, matching NN). Columns:
     `#` | `Source (authors year, journal)` | `DOI or URL` | `Fig.` | `Image` (relative path `figures/NN_...`) |
     `Test` (cluster perm / TFCE; t / F; tail; n perms) | `Layout` (which panels: raster, topomap row, waveforms,
     how arranged) | `Colour value` (t / F / µV / TFCE / p) | `Significance shown as` (only significant coloured,
     full map + contour, full map + opacity mask, shading/bar on waveforms, marked channels) | `Channel order`
     (anterior→posterior, by region/ROI, L/mid/R, montage order, n/a) | `Topomap times` (cluster window,
     fixed bins of X ms, component window, n/a) | `Channel marker` (dot, star, white circle, colour …) |
     `Comparisons per figure` | `Colormap / colourbar` | `Source of each field` (caption / methods / image).
   - Write `n/a` where the caption, methods and page text do not say it. Never guess a field from the image alone
     unless you can read the image; then write `image` in the last column.
   - Then `## Summary` with at most 10 lines: for each of these dimensions — layout, colour value, significance
     display, channel order, topomap times, channel marker, comparisons per figure — the counts across rows (e.g.
     `colour value: t 7, µV 4, F 2, n/a 1`) and the row numbers behind each count.
   - Then `## Dropped` listing candidates that were dropped and why (DOI mismatch, image unavailable, out of scope).
4. Run the Check and fix any row it reports until it passes.

## Check
`python research/cluster-figures/check_survey.py`

## Don't
- No code changes; write only the two paths under "may change".
- Do not invent or reconstruct a DOI, author, figure number or caption detail; every row must come from a page you
  actually opened. Do not reuse rows or counts from `docs/research-figure-conventions.md` (it failed a spot-check);
  you may use its paper names as search leads only.
- No preprints, no paywalled downloads, no login, no CAPTCHA.
- No commits.
- "Run scripts in the foreground and wait; before replying, stop any background task still running."
- "Reuse existing functions; don't copy existing logic."
- "No rm, no git push, no git checkout . / restore . / reset --hard."

## Acceptance
- verdict: accepted (Claude opened all 15 images as a contact sheet: content matches each row; Crossref re-check of rows 8 and 13: title, first author, journal match)
- files: research/cluster-figures/survey.md (committed); research/cluster-figures/figures/ (15 images, git-ignored: third-party figures, public repo)
- check: `python research/cluster-figures/check_survey.py` → exit 0 (run by run-card)
- tokens:
  - round 1: exec deepseek-v4.1-flash: fresh 103k, cached 5945k, out 68k  (codex-cluster-figure-survey.jsonl)
- review findings: 0 real / 0 false positive / 0 missed (low, no review)
- notes: no classic method papers (Maris & Oostenveld etc.) made it in; the 2 tutorials meet the >= 2 rule. All 13 empirical rows are 2025-2026.
