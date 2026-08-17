# CLAUDE.md

2026 年全国大学生数学建模竞赛（CUMCM）备赛与比赛工作区。

## 机器分工

- **Windows**：建模开发、跑程序、出数据和图。
- **Mac（本机）**：论文写作、排版、编译、终稿检查。

本机默认承担论文侧工作。除非明确要求，不要在 Mac 上重跑重型建模任务。

## 环境事实（已实测，勿凭猜测改写）

| 项 | 状态 |
|---|---|
| TeX Live 2026，`xelatex` / `latexmk` / `bibtex` / `biber` | `/Library/TeX/texbin`，可用 |
| `typst` 0.14.2 | `/opt/homebrew/bin/typst`，可用 |
| 中文字体 SimSun / SimHei / KaiTi / FangSong | 齐全，`cumcmthesis.cls` 无缺字体 |
| `.venv`（Python 3.9.6 + numpy/scipy/pandas/matplotlib） | 可用，Mac 端可临时补图 |
| `tools/verify_env.py` | 25 / 25 全通过 |
| `pandoc` | **未安装**（只有出 Word 版才需要） |
| `timeout` | **macOS 没有**，需要时用 `gtimeout`（`brew install coreutils`） |

## 硬性约定

### 1. 中文路径必须有 UTF-8 locale

仓库里大量中文目录名和文件名。`LANG` / `LC_ALL` 未设置时 zsh 会把中文路径打成乱码、`cd` 直接失败。
已写入 `~/.zshrc` 和 `.vscode/settings.json` 的 `terminal.integrated.env.osx`。若在裸环境执行，先设：

```bash
export LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8
```

### 2. 正式赛题只在 `contest-workspace/` 内写

根目录 `code/`、`MathModel-Figure-Toolkit/`、`templates/` 都是**模板库**，赛时复制出去改，不要就地改写。

```
contest-workspace/
├── data/{raw,interim,processed}   # raw 放官方原始附件
├── code/{common,q1,q2,q3,q4}
├── figures/{q1,q2,q3,final}       # final/ 才是论文用图
├── results/{tables,models}
├── paper/                         # 从 templates/ 复制模板到这里
├── notes/                         # 假设、符号、参数口径、进度
└── submission/                    # 最终提交包
```

### 3. 论文取数纪律

沿用 `mock-contests/2026-08-第2次_2022A_波浪能/paper/handoff/` 验证过的交接契约：

- 图**只**从 `figures/final/` 引用，不引诊断图、验证图。
- 表**只**从 `results/tables/` 引用。
- 关键数值以 handoff 的 `结果与结论.md` 和各问 `*_final_summary.json` 为准。
- **不**从控制台输出、临时 PDF 渲染目录或 `results/models/` 中间文件抄数字。
- 正文每个数字都要能和代码/附录对上。

Windows 侧交过来的 handoff 目录标准结构：`模型与公式.md`、`结果与结论.md`、`问题N正文草稿.md`、`图表索引.md`、`复现说明.md`、`写作待办.md`。

## 编译命令

LaTeX（主用，`templates/CUMCM2026-Complete-LaTeX/`）：

```bash
latexmk -xelatex main.tex
```

Typst（`main.typ` 会 `#import "../lib.typ"`，**必须**带 `--root`，否则报 access denied）：

```bash
typst compile --root templates/cumcm-typst templates/cumcm-typst/template/main.typ
```

`.vscode/settings.json` 里的 LaTeX-Workshop 配置是 macOS 专用（绝对路径指向 texbin），Windows 端如需编译要另配。

## 格式合规红线（2026 规范）

- 正文 **≤ 30 页**（不是旧的 20 页说法）。
- 摘要 **≤ 1 页**，含标题和关键词，**无需英文摘要**，每问都要有带数字的量化结论。
- **不要目录**。
- 页码从**摘要页**起用阿拉伯数字、页脚居中、连续编号。
- 纸质版顺序：承诺书 → 编号页 → 摘要 → 正文；**电子版不含承诺书和编号页，第一页就是摘要**
  （LaTeX 用 `\documentclass[withoutpreface]{cumcmthesis}`，Typst 设 `cover-display:false`）。
- 论文单文件 **≤ 20MB**，建议非图片 PDF（文字可检索）。支撑材料单个 ZIP/RAR，同样 ≤ 20MB。
- 所有图要有编号 + 标题 + 坐标轴单位；所有表用三线表；公式要编号。

完整清单见 `mock-contests/提交checklist.md`。**正式赛以当年官方《报名和参赛须知》为准。**

## 参考文档

- `docs/备赛指南.md` — 时间线、规则、分工
- `docs/论文写作模板.md` — 可复用段落与句式、格式合规对照
- `docs/优秀论文排版画图与摘要写作方法.md` — 排版、图表、摘要写法
- `docs/往年优秀工程建模手法分析.md` — 历年题建模套路
- `mock-contests/提交checklist.md` — 提交前逐项核对
