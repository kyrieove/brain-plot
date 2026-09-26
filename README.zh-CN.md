# brain-plot

用 MNE 文件画可直接投稿的 **ERP** 和 **EEG 微状态**图，风格统一固定。

brain-plot 是一个 [Claude Code](https://claude.com/claude-code) 技能，外加两个普通的 Python 脚本。智能体先读你的数据，
再分几轮问你几个问题（读者首先要看到什么、比较什么、画哪些成分），把答案写成一份 JSON spec，你确认后画图，
最后自己检查出图的 PNG。脚本也可以脱离智能体、直接在命令行运行。

[English](README.md)

| ERP 波形 + 地形图（`combo`） | 微状态模板 + 分段 |
|---|---|
| ![ERP](docs/images/example-erp.png) | ![microstate](docs/images/example-microstate.png) |

![微状态模板 + 蝴蝶图 + 分段色带](docs/images/example-microstate-butterfly.png)

*示例图来自作者的隐喻产出研究（未发表数据，请勿转用）。*

这是个人工具，目前只分享给几位同学试用，后续还会改动。

## 能画什么

| 图 | 命令 / spec | 内容 |
|---|---|---|
| ERP + 地形图 | `erp_plot.py plot`，`kind: "combo"`（默认） | 每个成分一张：纵向排列的波形分图（ROI 平均），时间窗画成灰带，右侧每条线一张地形图，共用色标 |
| 只画地形图 | `kind: "topo"` | 每个分图一块地形图，一个色标 |
| 按通道画波形 | `kind: "erp"`，`layout: "roi"` / `"single"` / `"grid"` | ROI 平均、每个通道一张（`channels: "all"`）或通道网格 |
| 总览 | `erp_plot.py explore` | 3 × 3 波形网格 + 条件 × 成分地形图表，用来选时间窗 |
| 候选时间窗 | `erp_plot.py windows` | 只给启发式建议，由你决定 |
| 微状态 | `microstate_plot.py plot`，`figure: "states"` | 模板地形图、butterfly 或 GFP 图、每个条件的分段色带（用你已保存的模板） |
| 跨 K 对比 | `figure: "by-K"` | 每个 K 一行模板，按模板身份着色 |

每张图输出 PNG（600 dpi）和文字可编辑的 SVG，另有 `_caption.md`（按分图列出写图注用的事实）和 `_run.json`
（spec、被试 ID、采样点边界、软件版本，足以复现）。

**只负责画图。** 不做统计、预处理、微状态聚类、源定位或时频图。不支持（脚本会停下）：差异波、偏侧化成分
（N2pc、LRP）、CSD、显著性标记、超过 7 条叠加线。

## 安装

需要 Python ≥ 3.10。

```bash
git clone https://github.com/kyrieove/brain-plot.git
cd brain-plot
pip install -r requirements.txt
```

检查环境（没装 MNE 也能运行）：`python brain-plot/check_env.py`，会列出版本和字体，最后显示 "OK" 或缺什么。
装有 Arial 或 Helvetica 字体时效果最好；没有的话 matplotlib 会用 DejaVu Sans 代替。

作为 Claude Code 技能使用时，把 `brain-plot/` 文件夹链接到 `~/.claude/skills/`：

```bash
# macOS / Linux
ln -s "$PWD/brain-plot" ~/.claude/skills/brain-plot
```
```bat
:: Windows（cmd）
mklink /J "%USERPROFILE%\.claude\skills\brain-plot" "%CD%\brain-plot"
```

## 检查安装（合成数据）

```bash
python examples/make_demo_data.py
python brain-plot/erp_plot.py plot examples/specs/p3_combo.json
python brain-plot/erp_plot.py plot examples/specs/grid_by_condition.json
python brain-plot/microstate_plot.py plot examples/specs/microstate_k4.json
```

图会出现在 `examples/brain-plot/` 下（`ERP_topo/`、`ERP/`、`microstate/`）。数据是编造的，只用来确认能正常运行。

## 在 Claude Code 里使用

```
/brain-plot 你的数据文件夹
```

或者直接说，比如"画两组的 P3，带地形图"。智能体会：

1. **读数据**：组、条件、试次、通道、时间范围、滤波、参考，以及你的分析笔记（如果有）；
2. **分轮提问**，每个问题都附推荐答案：图的类型和宽度、读者首先要看到什么、关键比较（哪个变量叠在同一分图里）、
   组和剔除、成分、通道和时间窗；
3. 展示 **spec**，等你确认；
4. **画图**，打开 PNG 按 QA 清单检查（重叠、时间窗一致、色标、待确认项），再把文件和图注事实交给你。

颜色、极性、字体、色图都用默认风格，除非你提出修改。

## 不用智能体

```bash
python brain-plot/erp_plot.py inspect  数据文件夹
python brain-plot/erp_plot.py explore  explore.json
python brain-plot/erp_plot.py windows  spec.json
python brain-plot/erp_plot.py plot     spec.json
python brain-plot/microstate_plot.py plot microstate.json
```

spec 里的相对路径（`data`、`templates`）按 spec 文件所在文件夹解析。全部字段见
[`brain-plot/references/spec.md`](brain-plot/references/spec.md)。

## 输入数据

- 每个被试一个 MNE 文件：`*-epo.fif`（条件 = 事件名）或 `*-ave.fif`（条件 = comment）。被试 ID 取文件名第一个
  `_`、`-` 或 `.` 之前的部分（BIDS 命名 `sub-01_…` 取 `sub-01`）。
- 分组方式：子文件夹（`data/<组>/<被试>…`）、元数据列（`group_by`），或 `data/<条件>/<组>/<被试>…-ave.fif`。
  平铺的文件夹算一个组。
- EEG 以伏特为单位，带电极位置（已设 montage）。所有被试的通道、采样率、时间点、基线和滤波必须一致；脚本不会
  重参考、重采样或插值，不一致就停下并说明哪里不同。标记为坏的通道、整段平直的通道也会停下（保持 0 µV 的参考
  电极可以用 `flat_channels` 放行）。

## 输出

全部写到**数据文件夹旁边**的 `brain-plot/` 里，按类型分子文件夹，文件名说明图的内容；只画部分组或条件时，文件名会加上
`_grp-…` / `_cond-…`。不会覆盖：重画生成 `_v02`，旧版本移到 `_history/`。每张图的版面都由代码检查（文字互相重叠、文字或
图例压线、文字超出画布），问题会打印出来并写进 `_run.json` 的 `layout_issues`。缓存（`brain-plot/.cache/`，保留最近用过的
6 份，每份可能几十 MB）让后续运行更快，输入文件变化时自动重建。

## 规则和测试

- [`brain-plot/references/rules.md`](brain-plot/references/rules.md)：完整规则（科学、版面、风格、输出、微状态、QA）。
- 测试：`python brain-plot/test/test_erp_plot.py`、`python brain-plot/test/test_microstate.py` 和
  `python brain-plot/test/test_layout.py`（接近真实规模：64 导、7 个条件、3 组；都应输出 `OK`）。
- `docs/`、`HANDOFF.md`、`research/` 是开发笔记和审查记录。

## 许可

MIT，见 [LICENSE](LICENSE)。
