# Skill evals (round 6, item 13)

Agent-level checks of the skill as a whole; the script regressions live in `test/`. Run each case in a fresh session
with the skill installed, on the synthetic data the tests build (or any small copy), and mark pass/fail against the
expectation. Cases 1–4 and 9–11 are the holdout: do not tune SKILL.md wording on them.

## Trigger (should the skill load?)
| # | Request | Expected |
|---|---|---|
| 1 | 画 N400 的 ERP 波形图和地形图，论文用 | load; ERP branch (`erp_plot.py`) |
| 2 | Plot the microstate templates for K = 5 with the GFP | load; microstate branch (`microstate_plot.py`) |
| 3 | 帮我对 ERP 做重复测量方差分析 | do not load (statistics) |
| 4 | Preprocess this EEG: filter, ICA, re-reference | do not load (preprocessing) |
| 5 | 用 pycrostates 给这批 epoch 聚类 | do not load (clustering; the skill only draws saved templates) |
| 6 | 我还不知道 P300 窗口在哪，先看看数据 | load; `explore` (optionally `windows` with a combo spec) |
| 7 | 把所有电极的 ERP 各画一张 | load; `kind: "erp"`, `layout: "single"`, `channels: "all"` |
| 8 | 画源定位结果的脑图 | do not load (source data unsupported) |

## Output (does the skill behave?)
| # | Request (synthetic data) | Must happen | Must not happen |
|---|---|---|---|
| 9 | combo figure, two groups, window from the user | interview rounds; written spec confirmed before `plot`; PNG checked; `qa` filled in `_run.json` | invented `time_locked_to`/`reference`; asks the user for `time_locked_to`, `reference`, the display range, the window's source, the figure's role, the statistics, polarity or colours; no question on the claim or key comparison; statistics in the caption that the user did not give |
| 10 | microstate states figure for six conditions | asks for / proposes a `grid`; `polarity` and minimum run taken from the analysis config | six conditions stacked; N in panel titles |
| 11 | ERP grid of F3…P4 with an N400 band | band named on every panel; files under `brain-plot/ERP/` versioned | overwriting an earlier version; writing inside the data folder |
| 12 | `windows` on a `kind: "erp"` spec | tells the user `windows` needs a combo/topo spec with ROI channels | a crash or a guessed ROI |
