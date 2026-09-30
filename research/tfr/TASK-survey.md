# Task: survey of EEG time-frequency figure layouts (for the brain-plot TFR module)

Goal: find how recent papers lay out sensor-level EEG time-frequency figures, so we can pick one house layout.
Save everything in `C:\dev\brain-plot\research\tfr\`. Work token-efficiently: search, open only what you need,
no PDF downloads, no long quotes.

## Collect 12–15 papers
- Journals: Nature Communications, eLife, Journal of Neuroscience, NeuroImage, Psychophysiology, Cortex (others
  only if these give too few); years 2023–2026; human scalp EEG (not MEG/iEEG/source-only); at least 6 papers from
  language / cognitive ERP-style tasks.
- Each must contain a time-frequency figure (ERSP/power and/or ITC) in the main text.
- Open access only for figures: save the TFR figure image (from the publisher's or PMC's page, e.g. the figure's
  full-size JPG/PNG) as `figures/<first-author><year>_fig<N>.<ext>`. Do not download PDFs or supplements.

## For each paper record (table in `survey.md`)
DOI (copy it from the article page, never from memory) · journal · year · figure number · what the figure shows:
- layout: ROI-average TF map(s) / channel array / condition × group grid / difference map; panel count and shape
- topomaps: yes/no; for which band × time window; where placed (row under, side, inset)
- units and baseline (dB / % / z; baseline window in ms); frequency range and time range shown
- colour map; colour bar placement; significance marks (contours / masks / none)
- time and frequency axis style (linear / log frequency axis), how many frequency ticks
- saved image file name (or "not OA")

## Then summarise (end of `survey.md`, ≤ 25 lines)
The 2–3 most common layouts with counts; the typical baseline window and unit; typical frequency range; colour map;
how topomaps are combined with TF maps. State which papers each count comes from.

## Rules
- Only facts you saw on the article page. If a field is not visible, write "n/a". Do not guess DOIs.
- Final message: ≤ 10 lines — number of papers, number of figure images saved, the path of `survey.md`.
