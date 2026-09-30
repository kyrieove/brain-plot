# Task: EEG time-frequency studies of metaphor vs literal language — baselines, ROIs, bands, windows

Text-only task: search and read article pages/abstracts/methods; do NOT download PDFs or images; do not use a browser.
Write the result to `C:\dev\brain-plot\research\tfr\survey-metaphor.md`. Be token-efficient.

## Find 8–12 studies
Scalp EEG (or MEG if EEG is scarce, marked as MEG), time-frequency analysis (power and/or ITC; oscillations), comparing
metaphorical vs literal language (comprehension or production; words, word pairs, sentences; any language; Chinese
studies welcome). Any year, prefer 2010–2026. Include every metaphor **production** study you can find, even if few.

## For each study record (one table row)
- First author, year, journal, title, **DOI copied from the article page (never from memory; "n/a" if not seen)**
- Task (comprehension / production; stimulus type; presentation: word-by-word? sentence?)
- Time-locking event (which word/stimulus is 0 ms)
- **Baseline window** (ms, relative to what) and normalisation (dB / % / z / none)
- **Frequency bands** analysed (Hz)
- **Channels / ROIs** (names, or regions)
- **Time windows** (ms) and whether they were a priori or data-driven (cluster permutation over all samples, etc.)
- Main time-frequency result for metaphor vs literal (band, direction, where, when) — one short sentence

## Summary (≤ 20 lines, at the end)
Most common baseline windows (with counts); most common bands, ROIs and time windows for metaphor vs literal; how many
used cluster-based (data-driven) vs a-priori windows; anything specific to production. Name the studies behind each count.

## Rules
Facts only from the pages you read; "n/a" when not stated. Final message ≤ 5 lines: number of studies, path of the file.
