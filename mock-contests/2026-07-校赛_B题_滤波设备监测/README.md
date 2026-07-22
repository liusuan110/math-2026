# 2026 校赛 B 题：滤波设备监测与维护决策

本目录是本题的唯一工作入口。问题一至问题四均已形成可复现的正式结果；所有数值结论以 `data/results/` 的流水线输出为准。

## 当前进度

| 模块 | 状态 | 已有产物 |
|---|---|---|
| 输入与数据质量 | 已完成 | 10 台设备、114,977 条监测记录和 127 条维护记录通过校验 |
| 问题一数据层 | 已完成 | 7,377 行日级面板、数据质量表、维护事件汇总 |
| 问题一正式模型 | 第一版完成 | Fourier/月份稳健性、设备线性趋势、维护事件研究、5 张论文图 |
| 问题二正式模型 | 第一版完成 | 三类模型时间留出、分层退化状态、2,000 路径寿命区间、4 张论文图 |
| 问题三正式模型 | 第一版完成 | 129 组策略、2,000 路径复验、逐设备/统一方案、9 张结果表、1 份关键摘要及 4 张图 |
| 问题四正式模型 | 第一版完成 | 129 组策略全空间筛选、56 个设备—策略对 2,000 路径复验、545 个二维价格场景、1,104 个单因素点、10 张结果表、1 份关键摘要及 4 张图 |
| 论文 | 第五版完成 | 问题一至问题四均已回填并完成编译与逐页检查 |

更完整的交接状态见 [`docs/当前进度.md`](docs/当前进度.md)。问题三和问题四的正式结果分别见 [`docs/问题三结果说明.md`](docs/问题三结果说明.md) 与 [`docs/问题四结果说明.md`](docs/问题四结果说明.md)。

## 目录

```text
.
├── data/
│   ├── raw/             # 原始题目与附件（只读，本地保存，不提交 Git）
│   ├── processed/       # 可重建的日级面板和特征
│   └── results/         # 四问的表格、参数和策略结果
├── docs/                # 数据字典、建模路线和决策记录
├── figures/generated/   # 代码生成的论文图
├── paper/               # 从仓库 CUMCM Typst 模板生成的论文入口
├── src/filter_monitoring/
│   ├── config.py        # 统一阈值、成本、日期和路径
│   ├── io.py            # 附件读取与输入校验
│   ├── preprocess.py    # 日级聚合和维护事件对齐
│   ├── q1_analysis.py   # 问题一：数据与规律
│   ├── q2_lifetime.py   # 问题二：固定维护下寿命
│   ├── q3_optimization.py # 问题三：维护策略优化
│   └── q4_sensitivity.py  # 问题四：价格敏感性
├── tests/               # 不依赖原始附件的基础自检
└── run_pipeline.py      # 统一运行入口
```

## 立即可运行

在本目录中执行：

```bash
../../.venv/bin/python run_pipeline.py audit
../../.venv/bin/python run_pipeline.py q1-data
../../.venv/bin/python run_pipeline.py q1
../../.venv/bin/python run_pipeline.py q2
../../.venv/bin/python run_pipeline.py q3
../../.venv/bin/python run_pipeline.py q4
../../.venv/bin/python -m unittest discover -s tests -v
```

`audit` 只检查三份附件是否齐全、工作表是否正确；`q1-data` 只重建确定性数据层；`q1` 会拟合趋势—季节—维护周期模型并执行维护事件研究；`q2` 会执行时间留出和留一设备验证，再按现行维护规律完成 2,000 路径、30 年上限的寿命外推；`q3` 会搜索周期和状态触发策略，再用 2,000 路径输出逐设备与全厂统一方案；`q4` 会复用问题三物理路径重定价，输出价格稳定区、切换边界和最小最大后悔方案。

首次运行前，在仓库根目录执行：

```bash
/usr/bin/python3 -m venv .venv
.venv/bin/python -m pip install -r mock-contests/2026-07-校赛_B题_滤波设备监测/requirements.txt
```

论文编译命令：

```bash
typst compile --font-path paper/fonts paper/main.typ paper/main.pdf --root .
```

## 四问的数据依赖

```text
原始监测值 + 维护记录
        │
        ▼
日级面板、缺失/异常标记、维护前后窗口
        │
        ├── 问题一：周期、趋势、维护效果、关键指标
        ├── 问题二：固定维护安排下的寿命分布
        ├── 问题三：在寿命约束下优化维护策略与年均成本
        └── 问题四：购置价/维护价扰动下的策略边界
```

## 口径约定

- 设备统一命名为 `A1`—`A10`，原始工作表 `A_1`—`A_10` 在读取时转换。
- 性能寿命判据：滚动一年平均性能首次低于 `37`，且维护后无法恢复到阈值之上。
- 成本统一使用“万元”：购置 `300`、中维护 `3`、大维护 `12`。
- 原始附件永不覆盖；所有中间结果都写入 `data/processed/` 或 `data/results/`。
- 维护效果先做描述性事件研究，再进入带季节项和退化状态的统一模型，避免把季节回升误判成维修收益。

## 文件保留规则

- `data/raw/` 是本地只读输入，不提交 Git，也不手工修改；
- `data/processed/`、`data/results/`、`figures/generated/` 和 `paper/main.pdf` 均可重建；
- `paper/versions/` 只保存已经确认的里程碑 PDF；
- `__pycache__`、日志和临时渲染文件不保留；
- 正式数字必须来自 `data/results/`，不得只存在于论文正文或聊天记录中。
