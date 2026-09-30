# Task: ERP components in metaphor vs literal language — which components, which electrodes, which windows

Text-only task: search and read article pages / abstracts / methods (PMC full text is fine); do NOT download PDFs or
images. Write the result to `C:\dev\brain-plot\research\source\survey-metaphor-erp.md`. Be token-efficient.

Context: our study is metaphor **production** (Chinese, subject noun then verb; the figure is locked to the **verb**
onset; conditions metaphor / literal / repetition). We need, from the literature, the ERP components to look for and
for each one a rough electrode region and search range. Exact windows will then come from our own data.

## Find 12–18 studies
Scalp EEG, ERP comparison of metaphorical vs literal (or figurative vs literal) language; comprehension or
production; any language (Chinese studies welcome); prefer 2005–2026. Include every metaphor **production** study you
can find (e.g. Jończyk and colleagues), and studies time-locked to a verb or to the critical word of a phrase.

## For each study record (one table row)
- First author, year, journal, **DOI copied from the article page (never from memory; "n/a" if not seen)**
- Task (comprehension / production), stimulus (word pair, phrase, sentence), time-locking event (what is 0 ms)
- Reference (mastoids / average / other), number of channels
- Each component analysed: name, polarity, time window (ms), electrodes or region (as named in the paper), whether the
  window was a priori or data-driven
- Metaphor vs literal result per component (direction, one short phrase)

## Summary (≤ 25 lines, at the end)
For each component that appears in ≥ 2 studies (e.g. N1, P200, N400, P600 / LPC, late negativity): number of
studies, typical window (range of reported windows), typical region (frontal / fronto-central / central /
centro-parietal / parietal / occipital; left / midline / right), and how often it differed between metaphor and
literal. Name the studies behind each count. Then anything specific to production or verb-locked data.

## Rules
Facts only from the pages you read; "n/a" when not stated. Check every DOI on `https://api.crossref.org/works/<doi>`
(title must match). Final message ≤ 5 lines: number of studies, path of the file.
