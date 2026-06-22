# math-2026 · 数学建模国赛工作区

2026 全国大学生数学建模竞赛（CUMCM）备赛与参赛工作区。

工具栈：**Python**（建模求解）+ **LaTeX / Typst**（论文写作）。

## 目录结构

```
.
├── code/            # 建模与求解代码（18 个可复用模块，改数据就能跑）
│   ├── README.md       # 模块速查：题型→该用哪个
│   └── notebooks/      # 数据探索 notebook 模板
├── data/            # 原始数据与中间数据
├── figures/         # 生成的图表
├── docs/            # 文档、笔记、论文草稿
│   ├── 备赛指南.md       # 赛事规则 + 题型 + 模型 + 时间管理（核验版）
│   ├── 论文写作模板.md   # 摘要填空模板 + 可复用句式 + 2026 合规结论
│   └── 资源汇总.md       # 历年真题 + 优秀开源项目索引
├── templates/       # 论文模板（LaTeX / Typst，均已编译验证）
│   ├── CUMCMThesis/    # 国赛 LaTeX 模板 + 论文骨架.tex（半成品，赛时填空）
│   └── cumcm-typst/    # 国赛 Typst 模板 + 论文骨架.typ（半成品）
├── past-problems/   # 历年真题与获奖实例（2013–2024）
├── mock-contests/   # 全真模拟赛（复盘模板 + 提交 checklist）
├── tools/           # verify_env.py 环境自检
└── refs/            # 参考文献、参考书
```

## 环境自检
```bash
.venv\Scripts\python.exe tools\verify_env.py     # Windows，应显示「通过 18 / 失败 0」
```

## 快速开始

- 资源与学习路径见 [docs/资源汇总.md](docs/资源汇总.md)
- LaTeX 模板：`templates/CUMCMThesis/`
- Typst 模板：`templates/cumcm-typst/`
