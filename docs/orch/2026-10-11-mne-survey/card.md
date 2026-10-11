# mne-survey — how papers that ran their cluster test in MNE-Python show the result

## Goal
`research/cluster-figures/survey-mne.md` exists: a table of >= 20 papers (open access or reached through the user's Chrome, see step 3) whose methods say the cluster-based permutation test was run in MNE-Python, one row per paper, with the result figure downloaded to `research/cluster-figures/figures/` and described field by field, plus a short "Takeaways for the columns layout" section. Purpose: the user wants to restyle brain-plot's `columns` cluster figure (channel x time raster grouped Left/Midline/Right + a row of 8 topomaps, 100 ms bins) after how MNE users publish it.

## Risk
low

## Parameters
- Minimum rows: 20 (stop at 30). Sensor-space ERP/EEG/MEG only (no source-space, no time-frequency, no decoding) — same scope as the existing `research/cluster-figures/survey.md`.
- "Ran in MNE-Python" = the methods name MNE(-Python) and one of `permutation_cluster_test`, `permutation_cluster_1samp_test`, `spatio_temporal_cluster_test`, `spatio_temporal_cluster_1samp_test` or MNE's TFCE option. Papers that only preprocessed in MNE but ran the cluster test elsewhere (FieldTrip, BESA, Eelbrain, R) do not count.
- Date range: prefer 2015–2026. Spread the 20+ rows over different groups, journals, years and figure types — not 20 variants of one lab's figure. Papers already in `survey.md` may appear again if they meet the MNE criterion.
- Image files: `research/cluster-figures/figures/mne_NN_<firstauthor><year>_fig<k>.<ext>`, min side >= 300 px.
- Table row format: first cell is the row number `| 1 |`; every row names `MNE`, a DOI or URL, and exactly the image path(s) as `figures/mne_...`.

## Files
may change: `research/cluster-figures/survey-mne.md`, `research/cluster-figures/survey-besa.md` (a parallel card writes it; never touch it), `research/cluster-figures/figures/` / read-only: `research/cluster-figures/survey.md`, `research/cluster-figures/check_survey.py`, `brain-plot/`, `docs/`

## Steps (N = 5)
1. Read `research/cluster-figures/survey.md` (the existing, tool-agnostic survey: its table columns, its scope paragraph, how it records sources) and reuse its column set. Add two columns: `MNE evidence` (a quote under 15 words from the methods naming MNE and the cluster function/test, plus the MNE version if stated) and `MNE-native display` (does the figure look like MNE's own plotting — `plot_topomap` with `mask`, `plot_joint`, `plot_compare_evokeds` with a shaded cluster bar, the tutorial-style cluster time course with a green/red bar — or was it re-drawn/composited in Illustrator or another tool).
2. Find candidates. Use web search and open-access full text (Europe PMC, PMC, Frontiers, PLOS, Scientific Reports, MDPI, eLife, bioRxiv, JNeurosci/eNeuro, Cerebral Cortex, NeuroImage open access) with queries such as: "MNE-Python" "cluster-based permutation"; "spatio_temporal_cluster_test"; "permutation_cluster_1samp_test"; "mne.stats" ERP cluster; "MNE-Python" "cluster permutation" topography; also code-availability statements ("analysis code" github "mne"). Keep a paper only if its methods meet the Parameters criterion and its figure shows that result.
3. For each kept paper: open the figure and caption, download the image from the publisher/PMC page (open access first. Paywalled papers are allowed too — the user authorised it on 2026-10-11 — but only through the user's own already-logged-in Chrome via `agent-browser --cdp 9222 <command>` (Chrome listens on 127.0.0.1:9222; `agent-browser skills get core` explains the commands). Rules for that Chrome: open your own new tab for each paper and close only tabs you opened; never close, navigate or reuse the user's other tabs; never type a username/password, never accept a login/consent/CAPTCHA prompt, never use saved credentials — if a page asks for a login, skip that paper. Prefix every agent-browser call with `timeout 90` so a hang cannot block you; if `timeout 25 agent-browser --cdp 9222 get url` fails, Chrome is unavailable — continue open-access only. No sci-hub or pirate mirrors, ever. Save only the figure image (right-click-equivalent: extract the image URL from the page and download it, or screenshot the figure element); do not download PDFs or full texts. Record in the row's source cell whether it came via open access or via the user's Chrome), open the downloaded file to confirm it is the right figure, and fill every column from what the figure/caption/methods actually show. Unknown = `n/a`; never guess. Resolve each DOI on Crossref (`https://api.crossref.org/works/<DOI>`) and confirm title + first author match.
4. Add also 1–2 rows for MNE's own tutorial/example pages that show cluster output (mne.tools; URL + access date instead of DOI; image saved the same way).
5. Under the table write three sections in `survey-mne.md`: `## Summary` (counts per layout / colour value / significance display / channel order / topomap time choice / marker style, each with the row numbers, like survey.md), `## Takeaways for the columns layout` (<= 12 bullets, concrete and visual: what MNE-user figures do that brain-plot's columns layout does not — how significant channels/times are marked, whether cluster p-values are printed on the figure, channel ordering, how topomaps relate to the raster or waveform, colour scales, what the caption states — each bullet cites row numbers), and `## Dropped` (candidates rejected and why, one line each). If after searching hard fewer than 20 verified rows exist, deliver what you have and say how many and what you tried — never pad with papers that do not meet the criterion. Any count claimed in the text must equal the table row count.

## Check
`python research/cluster-figures/check_survey.py survey-mne.md 20`

## Don't
- No commits, no other files, no refactors beyond the steps.
- Run scripts in the foreground and wait; before replying, stop any background task still running.
- Reuse existing functions; don't copy existing logic.
- No rm, no git push, no git checkout . / restore . / reset --hard.
- Do not edit `brain-plot/` code, `survey.md`, `survey-besa.md` or `check_survey.py`. Do not invent papers, quotes, DOIs or figure details; a row you could not verify against the downloaded figure is dropped.
- Do not download anything except figure images (open-access papers, or paywalled ones through the rules in step 3) and MNE documentation pages into `research/cluster-figures/figures/`.
