# math-2026 | 全国大学生数学建模竞赛工作区

这是 2026 年全国大学生数学建模竞赛（CUMCM）的备赛与正式比赛工作区。

仓库现在按“正式比赛主工作区 + 资料库 + 工具库 + 模板库”的方式组织：

1. `contest-workspace/`：正式比赛当天主要工作的地方，放赛题数据、代码、结果、图片、论文和提交材料。
2. `code/`：可复用建模算法模板库。
3. `MathModel-Figure-Toolkit/`：论文绘图模板库。
4. `templates/`：LaTeX / Typst 论文模板库。
5. `past-problems/`、`refs/`：历年赛题、优秀工程、论文和长期参考资料。

Windows 侧主要负责建模开发、数据处理、绘图和环境自检；Mac 侧可以继续承担论文写作、排版和最终润色。

## 快速入口

| 任务 | 优先查看 |
|---|---|
| 正式比赛开始工作 | `contest-workspace/` |
| 放官方赛题附件 | `contest-workspace/data/raw/` |
| 写本次赛题代码 | `contest-workspace/code/` |
| 放模型结果和表格 | `contest-workspace/results/` |
| 放论文最终用图 | `contest-workspace/figures/final/` |
| 写正式论文 | `contest-workspace/paper/` |
| 放最终提交材料 | `contest-workspace/submission/` |
| 检查 Windows 环境 | `tools/verify_env.py`、`docs/windows-开发环境.md` |
| 查可复用建模代码 | `code/README.md`、`code/` |
| 查论文模板 | `templates/CUMCM2026-Complete-LaTeX/`、`templates/CUMCMThesis/`、`templates/cumcm-typst/` |
| 查绘图模板 | `MathModel-Figure-Toolkit/` |
| 查历年真题 | `past-problems/2020-2025-A-B-C-E题汇总/` |
| 学习优秀工程 | `past-problems/external-projects/`、`refs/external-tools/` |
| 阅读方法总结 | `docs/` |
| 查看模拟赛工程 | `mock-contests/` |

## 总体架构

```text
.
├── contest-workspace/             # 正式比赛主工作区
├── code/                          # 可复用建模与求解代码模板
├── MathModel-Figure-Toolkit/      # 数学建模论文绘图模板库
├── templates/                     # LaTeX / Typst 论文模板
├── past-problems/                 # 历年赛题、附件、获奖工程与复现资料
├── refs/                          # 长期参考资料和外部工具型项目
├── docs/                          # 备赛文档、方法总结、论文写作规范
├── external-tools/                # 第三方绘图/科研工具源码
├── mock-contests/                 # 模拟赛完整工程与复盘资料
├── tools/                         # 仓库级工具脚本
├── requirements.txt               # 根环境依赖
└── .gitignore                     # 本地环境、缓存、输出文件忽略规则
```

## 正式比赛主工作区

`contest-workspace/` 是比赛当天最重要的目录。正式赛题相关的输入、代码、结果、论文和最终提交材料都应尽量放在这里，避免散落在仓库根目录。

```text
contest-workspace/
├── README.md                      # 正式比赛工作区说明
├── data/                          # 官方附件、清洗数据、中间数据
│   ├── raw/                       # 官方原始附件
│   ├── interim/                   # 临时清洗结果、抽样检查数据
│   └── processed/                 # 稳定的建模输入数据
├── code/                          # 本次赛题代码
│   ├── common/                    # 公共读取、清洗、绘图、评价函数
│   ├── q1/                        # 问题一代码
│   ├── q2/                        # 问题二代码
│   ├── q3/                        # 问题三代码
│   └── q4/                        # 扩展问题、敏感性分析或附加实验
├── figures/                       # 本次论文图片
│   ├── q1/                        # 问题一候选图
│   ├── q2/                        # 问题二候选图
│   ├── q3/                        # 问题三候选图
│   └── final/                     # 最终写入论文的精选图
├── results/                       # 模型输出和实验结果
│   ├── tables/                    # 论文表格、指标汇总、参数表
│   └── models/                    # 模型参数、权重、小型可复现结果
├── paper/                         # 论文源文件、草稿、编译产物
├── notes/                         # 选题分析、假设、符号、会议记录
└── submission/                    # 最终提交包和提交前检查材料
```

### 比赛当天怎么用

1. 把官方题面和附件放入 `contest-workspace/data/raw/`。
2. 从根目录 `code/` 复制合适的模型模板到 `contest-workspace/code/`，按问题改写。
3. 清洗后的稳定数据放入 `contest-workspace/data/processed/`。
4. 模型输出表、参数和评估结果放入 `contest-workspace/results/`。
5. 绘图脚本可先输出候选图到 `contest-workspace/figures/q1/`、`q2/`、`q3/`。
6. 论文最终采用的图片统一复制到 `contest-workspace/figures/final/`。
7. 从 `templates/CUMCM2026-Complete-LaTeX/` 或 `templates/cumcm-typst/` 复制论文模板到 `contest-workspace/paper/`。
8. 最终提交 PDF、附件和必要代码整理到 `contest-workspace/submission/`。

## 代码模板库

`code/` 是通用建模代码模板库，目标是“换数据、改参数、能快速跑”。正式比赛中不要直接在这里写一次性实验，建议复制到 `contest-workspace/code/` 后再改。

```text
code/
├── clustering/                    # 聚类与降维
├── common/                        # 通用绘图、敏感性分析等工具
├── evaluation/                    # AHP、熵权、TOPSIS、灰色评价等
├── graph/                         # 图论与网络模型
├── mechanism/                     # 几何判据、轨迹仿真、参数反演、微分方程
├── notebooks/                     # 数据探索 notebook 模板
├── optimization/                  # 线性规划、非线性规划、全局优化、启发式算法
├── prediction/                    # 回归、ARIMA、灰色预测、机器学习预测
├── preprocessing/                 # 数据清洗与预处理
└── simulation/                    # 蒙特卡洛与仿真
```

当前覆盖的模型类型：

- 预测：回归、ARIMA、灰色预测、机器学习预测。
- 优化：线性规划、非线性规划、全局优化、启发式算法。
- 评价：AHP、熵权法、TOPSIS、模糊灰色评价。
- 统计与聚类：PCA、聚类、相关性分析。
- 机理与仿真：三维几何判据、轨迹仿真、参数反演、ODE、蒙特卡洛、图论模型。

## 绘图工具库

`MathModel-Figure-Toolkit/` 是面向数学建模论文的绘图模板库，用于快速产出统一、清晰、适合论文排版的图。

```text
MathModel-Figure-Toolkit/
├── 00_style/                      # 统一科研绘图风格
├── 01_framework_templates/        # 框架图模板
├── 02_result_visualization/       # 预测、评价、统计类结果图
├── 03_algorithm_flow/             # 算法流程图
├── 04_common_model_templates/     # 常见模型结构图
├── 05_paper_assets/               # 论文插图规范与图注模板
├── 06_AI_Model_Figures/           # AI / GNN / 信号处理结构图
└── 07_competition_ready_templates/# 赛时可直接使用的绘图模板
```

已验证的能力：

- Python 主绘图链可用。
- MATLAB `exportgraphics` 可用。
- MATLAB 可识别 `export_fig` 和 `gramm`。
- `pyvista` / `vtk` 已安装，可用于三维绘图。

正式比赛优先使用 `MathModel-Figure-Toolkit/07_competition_ready_templates/`。

## 论文模板库

`templates/` 存放论文排版模板：

```text
templates/
├── CUMCM2026-Complete-LaTeX/       # 当前推荐的完整 LaTeX 模板
├── CUMCMThesis/                   # 国赛 LaTeX 模板参考工程
└── cumcm-typst/                   # Typst 论文模板
```

建议比赛开始后，把选定模板复制到 `contest-workspace/paper/`，然后只在正式比赛工作区内修改论文。

## 历年题和参考资料

`past-problems/` 用于查题型、看建模套路、学习优秀论文组织方式，不建议在这里直接写正式比赛代码。

```text
past-problems/
├── 2020-2025-A-B-C-E题汇总/        # 近年官方题目与附件
├── external-projects/              # 下载整理的优秀开源工程
├── recent-examples/                # 近期样例与补充材料
└── solutions-2013-2019/            # 早期优秀论文与解题材料
```

`refs/` 存放长期参考资料：

```text
refs/
├── coursework/                     # 课程作业、模型讲义、小型练习文档
└── external-tools/                 # 工具型参考项目，例如 Beacon
```

`external-tools/` 存放第三方工具源码，目前主要服务绘图能力：

- `SciencePlots`
- `tueplots`
- `export_fig`
- `gramm`
- `pyvista`

## 文档区

`docs/` 放已经整理过、会反复阅读的备赛文档：

- `备赛指南.md`：比赛节奏、题型、团队分工。
- `往年优秀工程建模手法分析.md`：结合历年题目的建模方法总结。
- `优秀论文排版画图与摘要写作方法.md`：论文视觉、摘要和图表写法。
- `论文写作模板.md`：可复用论文段落与结构。
- `资源汇总.md`：资料入口和优秀工程索引。
- `windows-开发环境.md`：Windows 本机环境说明。

## 环境配置

推荐使用仓库自带虚拟环境：

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m pip install -r MathModel-Figure-Toolkit\requirements.txt
```

环境自检：

```powershell
.venv\Scripts\python.exe tools\verify_env.py
```

正常结果应显示：

```text
通过 18 / 失败 0
```

MATLAB 路径：

```text
D:\Matlab\bin\matlab.exe
```

MATLAB 绘图模板位于：

```text
MathModel-Figure-Toolkit/07_competition_ready_templates/matlab_export_templates/
```

## 推荐赛时工作流

### 第 0-3 小时：选题与拆题

1. 阅读 A/B/C 题，判断数据规模、模型复杂度和论文表达难度。
2. 在 `docs/往年优秀工程建模手法分析.md` 中对照类似题型。
3. 确定题目后，只在 `contest-workspace/` 中开展正式赛题工作。
4. 把官方附件放入 `contest-workspace/data/raw/`。

### 第 3-12 小时：数据理解与基线模型

1. 从根目录 `code/preprocessing/`、`code/prediction/`、`code/evaluation/`、`code/optimization/` 复制可用模板。
2. 在 `contest-workspace/code/` 中完成数据清洗和基线模型。
3. 同步记录变量定义、假设和符号到 `contest-workspace/notes/`。

### 第 12-36 小时：模型深化与结果图

1. 每个问题形成独立脚本和可复现实验结果。
2. 使用 `MathModel-Figure-Toolkit/` 统一出图风格。
3. 关键图优先保存为 PDF/SVG，最终入论文版本放到 `contest-workspace/figures/final/`。

### 第 36-72 小时：论文整合与提交

1. 在 `contest-workspace/paper/` 中完成论文。
2. 对照 `docs/优秀论文排版画图与摘要写作方法.md` 检查摘要、图注和结论。
3. 用 `mock-contests/提交checklist.md` 做最终提交检查。
4. 把最终 PDF、必要代码和附件整理到 `contest-workspace/submission/`。

## Git 与文件管理约定

建议提交进仓库的内容：

- 模型代码。
- 可复现实验脚本。
- 小型样例数据。
- 论文源文件。
- 关键文档和总结。
- 可复用绘图模板。

不建议提交的内容：

- `.venv/`
- `node_modules/`
- `.env`
- 日志文件。
- 临时输出。
- 大型缓存。
- 无法复现的中间垃圾文件。

如果某些大附件必须长期保存，优先确认是否需要 Git LFS。

## 当前整理状态

- 正式比赛主工作区已统一为 `contest-workspace/`。
- 原根目录 `data/` 和 `figures/` 已移动到 `contest-workspace/` 内。
- 课程/作业参考材料已归入 `refs/coursework/`。
- Beacon 的本地运行环境、依赖缓存、日志和 `.env` 已清理。
- 绘图工具链已补齐 Python、MATLAB、PyVista/VTK。
- `tools/verify_env.py` 当前自检通过 `22 / 22`，覆盖通用建模、物理几何/轨迹/反演、优化、绘图等模块。
