# Plan: microstate figures (agreed with the user 2026-09-26, grilling session)

Reference figures: `C:\Users\ASUS\Dropbox\metaphor_production\gn_manuscript\05-microstate_GA\10_v10_all_participants\figures`
(made by `05-microstate_GA/code/gen_fig_per_k_independent.py`, `gen_fig_k_template_strip.py`).

## Scope
1. A microstate branch of brain-plot that only draws: it reads saved templates, never re-clusters. Its layout need not
   match the ERP figures.
2. Code in `brain-plot/microstate_plot.py`, reusing the loader, output root and versioning of `erp_plot.py`; own tests
   and rules.

## Data and computation
3. The loader also reads `<condition>/<group>/<ID>_*-ave.fif` (one file per subject and condition: the files the
   templates were fitted on); the existing layouts keep working.
4. Templates: npz/npy with a K × channels array; aligned by `ch_names` if the file has them, else the data's channel
   order with a channel-count check.
5. Segmentation as in the reference script: subject-equal grand average per condition; per sample average-reference
   centring + unit norm; polarity-sensitive (signed) best template; runs shorter than the minimum segment length
   (default 30 ms) merge into the better-fitting neighbour. Window, polarity mode and minimum length are spec keys and
   recorded in `_run.json`.
6. Low-GFP marking (truthful display): samples whose GFP is below the 95th percentile of the same grand average's
   pre-stimulus GFP keep their state colour and number with a hatch overlay; no text note on the figure. No
   pre-stimulus samples → the script stops. (The analysis's own unclassified thresholds are per CV fold for single
   participants, not applicable to the grand average.)

## Figures
7. The spec lists blocks, e.g. `blocks: ["topo", "butterfly", "gfp", "ribbon"]`; fixed placement rules: topomap
   column left (frames in state colours), one row per condition (optionally per condition × group) on the right. New
   block types can be added later without changing old specs.
8. Improvements on the reference: time ranges under the maps per condition (`—` where a state is absent); ribbon
   labels `S1`, `S2`, … as on the maps; the GFP trace labelled "GFP" at its end.
9. Across-K figure: one row per K, templates matched across K by identity and coloured by identity; no time ranges.
10. Numbering: within a K by median assigned latency (reference rule); colours: the 10-colour Lancet-style palette of
    the reference (`#00468B`, `#ED0000`, `#42B540`, `#0099B4`, `#925E9F`, `#FDAF91`, `#AD002A`, `#7A8A8A`, `#1B1919`,
    `#D4A017`), following the number.
11. Canvas: `width_mm` × `height_mm`, default 180 × 110 mm (slides e.g. 254 × 143 mm); PNG + SVG.

## Outputs
12. `brain-plot/microstate/`, named by content, versioned with `_history/`: `topo-butterfly-ribbon_K5_GO-NoGO_v01`,
    `topo-butterfly-GFP-ribbon_K5_GO-NoGO_v01`, `topo-by-K_K3-9_v01`.
13. `_caption.md` (facts for writing a caption) and `_run.json` per figure.

## Interview
14. Analysis parameters are read from the analysis docs and locked config; the user is asked only: which K, the
    figure's role, which conditions/groups, which blocks.

## Order (commit + push after each tested step)
1. Loader layout + `microstate_plot.py` main figure (topo, butterfly, GFP, ribbon, low-GFP hatch).
2. Across-K figure.
3. Rules, spec, SKILL.md interview.
4. Reproduce K = 5 and K = 3–9 from the v10 data and compare with the reference figures.
