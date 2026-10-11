# Plan: cluster `waves` layout v2 (grilled with the user, 2026-10-11 night)

Replaces the waves layout of card `docs/orch/2026-10-11-cluster-waves`. Prototypes: `docs/cluster-waves-candidates/`.

## Purpose
Describe where (topomap) and when / what shape (ERP) a significant cluster is. Descriptive only: channels and window were
selected by the test itself, so the figure is not a second test. The caption says so.

## Decisions
1. **Unit**: one figure per test; one block per significant cluster; a block = 1 topomap + 1 ERP panel.
2. **Which tests**: t contrasts with a single difference wave (`condition_pooled`, `condition_group`). Tests with no
   significant cluster and interaction (F) tests are skipped with one line in the terminal and `_run.json` — the rest of the
   batch is drawn (never a hard stop).
3. **Topomap**: µV difference (A − B), mean over the peak window. Peak time = time of maximum sum over the cluster's channels
   of |t|; window = peak ± 25 ms (50 ms), clipped to the cluster window. Spec may give `peak_window_ms` instead.
   White dots = channels significant in >= half of the window's samples (same MARK_FRAC rule as columns); the ERP channels
   get an extra black ring. Label under the map: `peak 340 ms`.
4. **ERP**: the two sides of the contrast only (two conditions, or two groups for a group contrast), each the mean over
   the user-chosen channels, with 95 % CI (t, df = n − 1), cluster window shaded gray, negative up.
5. **ERP channels** (`waves_channels`): user decides, per cluster or one list for all. Missing -> stop with an error that
   names the recommended list (the six channels with the largest sum of |t| inside the cluster window). The interview
   proposes that list; the user confirms. Averaging all cluster channels is NOT done (average reference makes the mean of
   a near-whole-scalp cluster ~0; survey: BESA 8 rows use one or two representative electrodes, MNE 3 rows use 6–8 sensors).
6. **Block title**: `Cluster 9: 260–800 ms, p < 0.001, 44 channels` (colon and commas, no middle dot). p < 0.001 reads
   `p < 0.001`.
7. **Layout (adaptive on the cluster count n)**: 1 block one column, ERP full width; 2–6 blocks two columns (three
   clusters = 2 + 1); more than 6 split into parts of 6 blocks (`_part1`, `_part2`).
8. **Axes**: y range shared by all blocks of a figure; x axis defaults to the whole evoked epoch (spec can restrict to the
   tested window). One µV colour bar per figure.
9. **Caption**: says the ERP channels were chosen by the user, the cluster is inferred as a whole (Sassenhagen &
   Draschkow 2019) and the figure is descriptive.

## Not in scope
Interaction clusters, designs with more than two sides in one test, per-level facets (a test's figure shows only what the
test compared).
