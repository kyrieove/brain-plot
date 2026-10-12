STATUS: done

**Files changed**
- `brain-plot/besa_to_run.py` (new) — `read_results`/`read_summary`/`read_avr`/`read_elp`/`positions`/`convert`/`verify`/`main(argv=None)`
- `brain-plot/test/test_besa.py` (new) — synthetic part (3 participants, 2 clusters, groups A/B) + real-data part
- `brain-plot/references/cluster.md` — new `## BESA Statistics input` section, placed right before `## Interview rounds`

**Could not do / deviation**
- Card step 5a asks the test to assert "manifest has 12 rows", but the same bullet prescribes 3 participants × 2 conditions and a threshold of `t.ppf(0.975, 2) = 4.30` (df = 2, N = 3). That structure gives 6 manifest rows; part (b)'s own "260 rows" = 130 × 2 fixes the rule as 2 rows per participant. I asserted 6 and did not add 3 more participants, which would move the threshold off the card's 4.30.
- Everything else follows the card, including `import sys` in step 1 (it ends up unused — `argparse` reads `sys.argv` itself).
- The Check was not run, per instructions; only `python -m py_compile brain-plot/besa_to_run.py brain-plot/test/test_besa.py` (both clean). No commits, no writes inside the Dropbox folder.