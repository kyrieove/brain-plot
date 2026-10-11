# besa-survey — how papers that used BESA show cluster-permutation results

## Goal
`research/cluster-figures/survey-besa.md` exists: a table of >= 20 papers (open access or reached through the user's Chrome, see step 3) whose methods say the cluster-based permutation test was run in BESA (BESA Statistics, or BESA Research's statistics module), one row per paper, with the result figure downloaded to `research/cluster-figures/figures/` and described field by field, plus a short "Takeaways for the columns layout" section. Purpose: the user wants to restyle brain-plot's `columns` cluster figure (channel x time raster grouped Left/Midline/Right + a row of 8 topomaps, 100 ms bins) after how BESA users publish it.

## Risk
low

## Parameters
- Minimum rows: 20 (stop at 30). Sensor-space ERP/EEG/MEG only (no source-space, no time-frequency, no decoding) — same scope as the existing `research/cluster-figures/survey.md`.
- Date range: prefer 2015–2026; older BESA papers are allowed when they are the best example of a figure type. Spread the 20+ rows over different groups, journals, years and figure types — not 20 variants of one lab's figure. BESA Statistics is a niche tool: search hard (many query variants, Google Scholar-style phrasing, Europe PMC full-text search "BESA Statistics", citations of the BESA Statistics manual, BESA's publication list); if after exhausting that fewer than 20 verified rows exist, deliver what you have and say how many and what you tried — never pad with papers that do not name BESA for the cluster test.
- Image files: `research/cluster-figures/figures/besa_NN_<firstauthor><year>_fig<k>.<ext>`, min side >= 300 px.
- Table row format: first cell is the row number `| 1 |`; every row names `BESA`, a DOI or URL, and exactly the image path(s) as `figures/besa_...`.

## Files
may change: `research/cluster-figures/survey-besa.md`, `research/cluster-figures/survey-mne.md` (a parallel card writes it; never touch it), `research/cluster-figures/figures/` / read-only: `research/cluster-figures/survey.md`, `research/cluster-figures/check_survey.py`, `brain-plot/`, `docs/`

## Steps (N = 5)
1. Read `research/cluster-figures/survey.md` (the existing, BESA-agnostic survey: its table columns, its scope paragraph, how it records sources) and reuse its column set; do not repeat any paper already in it unless it used BESA. Add two columns: `BESA evidence` (a quote under 15 words from the methods naming BESA and the cluster test, plus the BESA version if stated) and `BESA-native display` (does the figure look like BESA Statistics' own output — channel-by-time map of cluster p-values/t-values with cluster outlines, cluster-ID labels, BESA's colour scale, 3D/flat head maps — or was it re-drawn in MATLAB/Python/Illustrator).
2. Find candidates. Use web search and open-access full text (Europe PMC, PMC, Frontiers, PLOS, Scientific Reports, MDPI, eLife, bioRxiv) with queries such as: "BESA Statistics" cluster permutation; "BESA Statistics 2.0|2.1|2.3"; "cluster-based permutation test" "BESA"; "BESA Research" "permutation" ERP; "Maris Oostenveld" "BESA Statistics"; also the BESA website's publication list and BESA's own documentation/tutorial pages for BESA Statistics (what its cluster result display looks like: screenshots, manuals). Keep a paper only if its methods text names BESA as the software running the cluster permutation test, and its figure shows that result.
3. For each kept paper: open the figure and caption, download the image from the publisher/PMC page (open access first. Paywalled papers are allowed too — the user authorised it on 2026-10-11 — but only through the user's own already-logged-in Chrome via `agent-browser --cdp 9222 <command>` (Chrome listens on 127.0.0.1:9222; `agent-browser skills get core` explains the commands). Rules for that Chrome: open your own new tab for each paper and close only tabs you opened; never close, navigate or reuse the user's other tabs; never type a username/password, never accept a login/consent/CAPTCHA prompt, never use saved credentials — if a page asks for a login, skip that paper. Prefix every agent-browser call with `timeout 90` so a hang cannot block you; if `timeout 25 agent-browser --cdp 9222 get url` fails, Chrome is unavailable — continue open-access only. No sci-hub or pirate mirrors, ever. Save only the figure image (right-click-equivalent: extract the image URL from the page and download it, or screenshot the figure element); do not download PDFs or full texts. Record in the row's source cell whether it came via open access or via the user's Chrome), open the downloaded file to confirm it is the right figure, and fill every column from what the figure/caption/methods actually show. Unknown = `n/a`; never guess. Resolve each DOI on Crossref (`https://api.crossref.org/works/<DOI>`) and confirm title + first author match.
4. Add also 1–3 rows for BESA's own documentation/tutorial pages if they show example cluster output (URL + access date instead of DOI; image saved the same way).
5. Under the table write three sections in `survey-besa.md`: `## Summary` (counts per layout / colour value / significance display / channel order / topomap time choice / marker style, each with the row numbers, like survey.md), `## Takeaways for the columns layout` (<= 12 bullets, concrete and visual: what BESA-style figures do that brain-plot's columns layout does not — e.g. how clusters are outlined or labelled, whether p-values or cluster mass are printed on the figure, how channels are ordered, how topomaps relate to the raster, colour scales, what the caption states — each bullet cites row numbers), and `## Dropped` (candidates rejected and why, one line each). The README-level claim "N papers used BESA" must equal the table row count.

## Check
`python research/cluster-figures/check_survey.py survey-besa.md 20`

## Don't
- No commits, no other files, no refactors beyond the steps.
- Run scripts in the foreground and wait; before replying, stop any background task still running.
- Reuse existing functions; don't copy existing logic.
- No rm, no git push, no git checkout . / restore . / reset --hard.
- Do not edit `brain-plot/` code, `survey.md` or `check_survey.py`. Do not invent papers, quotes, DOIs or figure details; a row you could not verify against the downloaded figure is dropped.
- Do not download anything except figure images (open-access papers, or paywalled ones through the rules in step 3) and BESA documentation pages into `research/cluster-figures/figures/`.

## Acceptance
- verdict: accepted (low risk, no review). Claude spot-check: Crossref on 5 DOIs (title/first author match; Hsu 2020 online vs 2021 issue), opened 2 figures (Trumpp 2025 fig 1 = sensor ERP + t topomaps, BESA doc cluster example) — both match their rows.
- files: research/cluster-figures/survey-besa.md
- check: `python research/cluster-figures/check_survey.py survey-besa.md 20` → exit 1 on first run (checker matched "BESA" case-sensitively, row 3 says "Besa"); checker fixed to case-insensitive, `--recheck` → exit 0, 27 rows
- tokens:
  - round 1: exec deepseek-v4.1-flash: fresh 130k, cached 6432k, out 85k  (codex-besa-survey.jsonl)
- review findings: 0 real / 0 false positive / 0 missed (low, no review)
- claude fix: check_survey.py tool-name match made case-insensitive (committed separately)
- note: figures/ also holds ~27 unreferenced images from the two interrupted earlier runs (e.g. besa_03_ludyga2018_fig2.jpg), plus 2 dropped-paper images; git-ignored, left in place
