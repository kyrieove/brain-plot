# Task: survey of EEG source-localization figure layouts (for the brain-plot source module)

Goal: find how recent papers lay out cortical source maps from scalp EEG, so we can pick one house layout.
Text-only task: read article pages / PMC full text; do NOT download PDFs or images. Write the result to
`C:\dev\brain-plot\research\source\survey.md`. Be token-efficient: search, open only what you need, no long quotes.

## Collect 12–15 papers
- Journals: NeuroImage, Journal of Neuroscience, Cortex, Brain and Language, Psychophysiology, Human Brain Mapping,
  Nature Communications, eLife (others only if these give too few); years 2020–2026.
- Human scalp EEG (not MEG-only, not iEEG) with a distributed-source figure (MNE / dSPM / sLORETA / eLORETA / LORETA)
  in the main text; at least 6 from language or cognitive ERP tasks.

## For each paper record (table in `survey.md`)
DOI (copied from the article page, never from memory) · journal · year · figure number, and from the figure legend and
methods:
- inverse method and parameters (λ² / SNR, loose, depth); head model (template fsaverage / MNI / individual MRI);
  channel count
- what is shown: time-window mean / single latency / time course; per condition / difference / statistics map
- surface (inflated / pial / glass brain / slices); views (lateral, medial, ventral, dorsal; lh/rh)
- panel arrangement (rows × columns and what each axis is)
- colour map, one-sided or diverging, how limits or thresholds were set; colour bar placement
- ROI time courses next to the maps? (yes/no, which atlas labels)
- "n/a" for anything not stated

## Then summarise (end of `survey.md`, ≤ 25 lines)
The 2–3 most common layouts with counts; the typical inverse method, λ², head model, views; how limits were set;
how often ROI time courses accompany the maps. Name the papers behind each count.

## Rules
Facts only from pages you read. Do not guess DOIs. Final message ≤ 10 lines: number of papers, path of `survey.md`.
