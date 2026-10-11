# cluster-short-names — cluster output file names must fit Windows MAX_PATH again

## Goal
Commit f88c676 made cluster figure names carry the full test folder name (`..._columns_t01_condition_main_effect_all-t03_within_td_condition_effect_topo-bins100ms_v01.png`); on the GN data (Dropbox, deep folders) the full path is 263 characters, over Windows' 260 limit, so `savefig` fails with FileNotFoundError. Names become short again — `..._columns_t01-t03_topo-bins100ms_v07.png` — while staying unique: a test's short id is the leading digits of its folder name (`01`, `03`); if two tests of one figure share those digits, or a folder name has no leading digits, that figure falls back to the full `ep.safe(slug)` of every test.

## Risk
low — file names only; no figure content or numbers change.

## Parameters
- short id = `re.match(r"\d+", slug).group(0)` (digits only, as in the old code before f88c676); fall back as described in Goal.
- Output names are unchanged for existing unique full-slug cases only through the fallback; a figure of tests `01_...` and `03_...` is named `..._t01-t03_...`; `side` and `waves` figures (one test each) use `t01`.

## Files
may change: `brain-plot/cluster_plot.py`, `brain-plot/test/test_cluster.py`

## Steps (N = 3)
1. `brain-plot/cluster_plot.py`: add `def stem_ids(slugs)` next to `bins_of_times`: returns one id per slug — the leading digits of each slug; if any slug has no leading digits or the digits are not all different, return `[ep.safe(s) for s in slugs]` instead. One docstring line saying why (MAX_PATH, uniqueness).
2. `brain-plot/cluster_plot.py`: use it at the three stem sites. `plot_columns`: `ids = stem_ids([t["slug"] for t in tests])`, stem `f"cluster_{color}-{display}_columns_t{'-t'.join(ids)}_topo-{topo_part}"`. `plot_side` (currently `_t{ep.safe(t['slug'])}_topo-`) and `plot_waves` (currently `cluster_waves_t{ep.safe(t['slug'])}`): the figure is one test, but its id must still be unique among the tests of the same call, so compute `ids = stem_ids([x["slug"] for x in tests])` once before the per-test loop and use `ids[i]` for the i-th test (use the loop's existing index or `enumerate`; do not restructure the loops otherwise).
3. `brain-plot/test/test_cluster.py`: add one block before the final summary print: `stem_ids(["01_condition_main_effect_all", "03_within_td_condition_effect"]) == ["01", "03"]`; `stem_ids(["01_a", "01_b"]) == ["01_a", "01_b"]`; `stem_ids(["alpha", "02_b"]) == ["alpha", "02_b"]`. The existing default-render assertions (`"_t01_" in o01.name`, `"_t03_" in o03.name`) must still pass unchanged; if a different existing assertion depends on the long names, change only that assertion and say which.

## Check
```
python brain-plot/test/test_cluster.py
```

## Don't
- No commits. Change only what the steps name.
- Run scripts in the foreground and wait; before replying, stop any background task still running.
- Reuse existing functions; don't copy existing logic.
- No rm, no git push, no git checkout . / restore . / reset --hard.
