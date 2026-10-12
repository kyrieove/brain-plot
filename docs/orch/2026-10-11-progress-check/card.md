# progress-check — read-only recon to verify the token-weather progress lane

## Goal
The reply lists, in observable terms: (a) every line starting with `## ` in `HANDOFF.md`, in file order; (b) the output of `git log --oneline -n 5` for this repo. Nothing else is needed.

## Risk
low

## Parameters
- heading match: lines that start with `## ` exactly (two hashes and a space); ignore `### ` and deeper.
- git: exactly `git log --oneline -n 5`, run from the repo root.

## Files
read-only: `HANDOFF.md`

## Steps (N = 3)
1. Read `HANDOFF.md` and copy every line that starts with `## `, in order.
2. Run `git log --oneline -n 5` from the repo root and copy its output unchanged.
3. Reply with the STATUS line first, then the headings from step 1 and the output from step 2. Do not edit or create any file.

## Don't
No commits, no other files, no refactors beyond the steps. Run scripts in the foreground and wait. Reuse existing functions; don't copy existing logic. No rm, no git push, no git checkout . / restore . / reset --hard.
