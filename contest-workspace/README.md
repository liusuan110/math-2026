# 正式比赛工作区

这里是正式比赛当天优先使用的主工作区。根目录的 `code/`、`templates/`、`MathModel-Figure-Toolkit/`、`past-problems/` 和 `refs/` 主要作为工具库、模板库和参考资料；正式赛题的输入、代码、结果、论文和提交材料都尽量收拢到本目录。

## 目录结构

```text
contest-workspace/
├── data/          # 官方附件、清洗数据、中间数据
├── code/          # 本次赛题代码，按问题组织
├── figures/       # 本次论文最终用图
├── results/       # 模型输出、表格、参数、评估结果
├── paper/         # 论文源文件、草稿、编译产物
├── notes/         # 选题分析、假设、符号、会议记录
└── submission/    # 最终提交包和提交前检查材料
```

## 推荐使用方式

1. 拿到赛题后，把官方题面和附件放进 `data/raw/`。
2. 数据清洗脚本放进 `code/common/` 或对应问题目录，清洗结果放进 `data/processed/`。
3. 每个问题尽量有独立入口脚本，例如 `code/q1/solve_q1.py`。
4. 模型输出表、参数和评估指标放进 `results/`。
5. 论文最终采用的图片统一放进 `figures/final/`。
6. 论文源文件放进 `paper/`，最终提交文件放进 `submission/`。

## 和根目录的关系

- 需要模型模板时，从根目录 `code/` 复制到这里再改。
- 需要论文模板时，从根目录 `templates/` 复制到 `paper/`。
- 需要绘图模板时，从根目录 `MathModel-Figure-Toolkit/` 复制或调用。
- 需要查往年题和优秀工程时，到根目录 `past-problems/` 和 `refs/`。

