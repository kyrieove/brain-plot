# Task: is an ERP component's polarity its absolute voltage sign or the direction of its deflection?

Text-only; no PDFs, no images. Write only `C:\dev\brain-plot\research\source\polarity.md`. Be brief and token-efficient.

Question: in ERP methodology, is a "positive" component (P2/P200, P3, LPC/P600) defined by a peak whose voltage is
above 0 µV, or by a positive-going deflection (a local maximum relative to the surrounding waveform), which can sit
below 0 µV when it rides on a slow negative shift or depends on the reference/baseline? And how do collapsed
localizers / peak-picking methods define a component's peak and window?

Sources to check (methods texts and methods papers; quote ≤ 15 words each, give page/section when visible):
Luck (2014) *An Introduction to the Event-Related Potential Technique* (2nd ed.) — chapter on ERP components /
"Rule" list; Luck & Gaspelin (2017) Psychophysiology, "How to get statistically significant effects in any ERP
experiment (and why you shouldn't)" (collapsed localizer); Kappenman & Luck (2016) or Luck (2005) on peak amplitude
vs mean amplitude; Keil et al. (2014) Psychophysiology publication guidelines (peak definition); any ERP methods text
that explicitly says the sign of a component is relative to a baseline or neighbouring deflections.
DOIs copied from article pages; check each on `https://api.crossref.org/works/<doi>` (it worked from this machine
earlier; if not reachable, write "not checked").

## Output (`polarity.md`, ≤ 40 lines)
1. Answer in 3 lines: which definition the methods literature uses, with the sources behind it.
2. How a localizer should pick a component's peak (local extremum of the given polarity in a search range? prominence?
   relative to adjacent deflections?) and how windows/ROIs are usually derived from the collapsed waveform.
3. Table: source, DOI, the relevant statement (≤ 15-word quote or paraphrase), page/section.
Final message ≤ 4 lines.
