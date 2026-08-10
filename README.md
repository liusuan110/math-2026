# math-2026 | 全国大学生数学建模竞赛工作区

这是 2026 年全国大学生数学建模竞赛（CUMCM）的备赛与正式比赛工作区。

仓库定位不是单一代码项目，而是一个完整的竞赛工作台：Windows 侧主要负责建模开发、数据处理、绘图和自动化检查；Mac 侧可继续承担论文写作、排版和最终润色。仓库内容围绕三件事组织：

1. 赛题求解：Python / MATLAB 建模代码、数据处理、结果复现。
2. 论文产出：LaTeX / Typst 模板、摘要写作、图表规范、提交检查。
3. 备赛资料：历年赛题、优秀论文、开源工程、建模方法和复盘文档。

## 快速入口

| 任务 | 优先查看 |
|---|---|
| 检查 Windows 本机环境 | `tools/verify_env.py`、`docs/windows-开发环境.md` |
| 找建模代码模板 | `code/README.md`、`code/` |
| 找论文模板 | `templates/CUMCM2026-Complete-LaTeX/`、`templates/CUMCMThesis/`、`templates/cumcm-typst/` |
| 找绘图模板 | `MathModel-Figure-Toolkit/` |
| 查历年真题 | `past-problems/2020-2025-A-B-C-E题汇总/` |
| 学习优秀工程 | `past-problems/external-projects/`、`refs/external-tools/` |
| 看建模与论文方法总结 | `docs/` |
| 正式比赛放数据 | `data/` |
| 正式比赛放成图 | `figures/` |
| 模拟赛工程 | `mock-contests/` |

## 当前仓库架构

```text
.
├── code/                         # 可复用建模与求解代码模板
│   ├── clustering/                # 聚类与降维
│   ├── common/                    # 通用绘图、敏感性分析等工具
│   ├── evaluation/                # AHP、熵权、TOPSIS、灰色评价等
│   ├── graph/                     # 图论与网络模型
│   ├── mechanism/                 # 机理模型、微分方程模型
│   ├── notebooks/                 # 数据探索 notebook 模板
│   ├── optimization/              # 线性规划、非线性规划、启发式算法
│   ├── prediction/                # 回归、ARIMA、灰色预测、机器学习预测
│   ├── preprocessing/             # 数据清洗与预处理
│   └── simulation/                # 蒙特卡洛与仿真
│
├── data/                         # 正式比赛数据与中间数据入口
├── figures/                      # 正式论文图片与图表输出入口
├── docs/                         # 备赛文档、方法总结、论文写作规范
├── templates/                    # 论文排版模板
│   ├── CUMCM2026-Complete-LaTeX/  # 当前推荐的完整 LaTeX 模板
│   ├── CUMCMThesis/              # 国赛 LaTeX 模板参考工程
│   └── cumcm-typst/              # Typst 论文模板
│
├── MathModel-Figure-Toolkit/     # 数学建模论文绘图模板库
│   ├── 00_style/                  # 统一绘图风格
│   ├── 01_framework_templates/    # 框架图模板
│   ├── 02_result_visualization/   # 预测、评价、统计类结果图
│   ├── 03_algorithm_flow/         # 算法流程图
│   ├── 04_common_model_templates/ # 常见模型结构图
│   ├── 05_paper_assets/           # 论文插图规范与图注模板
│   ├── 06_AI_Model_Figures/       # AI / GNN / 信号处理结构图
│   └── 07_competition_ready_templates/
│
├── past-problems/                # 历年赛题、附件、获奖工程与复现资料
│   ├── 2020-2025-A-B-C-E题汇总/   # 近年 ABC/E 题官方题目与附件
│   ├── external-projects/         # 下载整理的优秀开源工程
│   ├── recent-examples/           # 近期样例与补充材料
│   └── solutions-2013-2019/       # 早期优秀论文与解题材料
│
├── refs/                         # 长期参考资料，不直接作为赛题输入
│   ├── coursework/                # 课程作业、模型讲义、小型练习文档
│   └── external-tools/            # 外部工具型参考项目，例如 Beacon
│
├── external-tools/               # 可复用第三方绘图/科研工具源码
│   └── figure-tools/              # SciencePlots、tueplots、export_fig、gramm、pyvista 等
│
├── mock-contests/                # 模拟赛完整工程与复盘资料
├── tools/                        # 仓库级工具脚本
├── requirements.txt              # 根环境依赖
└── .gitignore                    # 本地环境、缓存、输出文件忽略规则
```

## 目录职责边界

### `code/`

这里放通用建模代码模板，目标是“换数据、改参数、能快速跑”。正式比赛中，如果某个模型已经确定，可以从这里复制到当次赛题工程里再改，不建议直接在模板文件上做一次性实验。

当前覆盖的模型类型包括：

- 预测：回归、ARIMA、灰色预测、机器学习预测。
- 优化：线性规划、非线性规划、启发式算法。
- 评价：AHP、熵权法、TOPSIS、模糊灰色评价。
- 统计与聚类：PCA、聚类、相关性分析。
- 机理与仿真：ODE、蒙特卡洛、图论模型。

### `data/`

只放当前赛题或模拟赛正在使用的数据，包括：

- 原始附件。
- 清洗后的中间数据。
- 模型输出的结构化结果。

课程作业、参考论文、讲义材料不要放在这里，已经统一归入 `refs/coursework/`。

### `figures/`

正式论文用图的汇总入口。建议比赛当天按问题分目录，例如：

```text
figures/
├── q1/
├── q2/
├── q3/
└── paper-final/
```

Python / MATLAB 绘图脚本可以先输出到各自工程目录，最终入论文的版本再复制到这里。

### `docs/`

这里放已经整理过、会反复阅读的备赛文档：

- `备赛指南.md`：比赛节奏、题型、团队分工。
- `往年优秀工程建模手法分析.md`：结合历年题目的建模方法总结。
- `优秀论文排版画图与摘要写作方法.md`：论文视觉、摘要和图表写法。
- `论文写作模板.md`：可复用论文段落与结构。
- `资源汇总.md`：资料入口和优秀工程索引。
- `windows-开发环境.md`：Windows 本机环境说明。

### `templates/`

论文模板区，面向最终提交：

- `CUMCM2026-Complete-LaTeX/`：当前推荐的完整 LaTeX 模板，结构更完整，适合作为正式比赛主模板。
- `CUMCMThesis/`：经典 CUMCM LaTeX 模板参考。
- `cumcm-typst/`：Typst 方案，适合快速排版和结构化写作。

比赛前建议提前编译一次模板，确认字体、图片、参考文献和 PDF 导出都正常。

### `MathModel-Figure-Toolkit/`

这是仓库中的论文绘图模板库，目标是快速产出统一、清晰、适合论文排版的图。

它包含：

- Python 静态图模板。
- MATLAB 高质量导出模板。
- 预测结果、模型比较、敏感性分析、热力图、雷达图、PCA、聚类等常见结果图。
- TikZ / draw.io 风格的模型框架图。
- 物理 / 工程类 3D 场景绘图模板。

当前已验证：

- Python 主绘图链可用。
- MATLAB `exportgraphics` 可用。
- `export_fig` 和 `gramm` 可被 MATLAB 识别。
- `pyvista` / `vtk` 已安装并可用于三维绘图。

### `past-problems/`

历年真题和优秀工程资料区，不建议在这里直接写正式比赛代码。它的主要用途是查题型、看建模套路、学习优秀论文组织方式。

重点子目录：

- `2020-2025-A-B-C-E题汇总/`：近年官方题目与附件。
- `external-projects/`：优秀开源工程和获奖工程。
- `solutions-2013-2019/`：较早年份的论文和代码资料。

### `refs/`

长期参考资料区，和正式赛题输入区分开。

- `refs/coursework/`：课程作业、模型讲义、小型练习文档。
- `refs/external-tools/`：工具型参考项目，例如 Beacon。

这里的内容用于学习和借鉴，不作为当前赛题的数据源。

### `external-tools/`

第三方工具源码区，目前主要服务绘图能力：

- `SciencePlots`
- `tueplots`
- `export_fig`
- `gramm`
- `pyvista`

正式比赛优先使用 `MathModel-Figure-Toolkit/` 中整理好的模板；需要查高级用法时，再看这里的外部源码和示例。

### `mock-contests/`

模拟赛工程区，用于完整练习 3 天比赛流程。每个模拟赛工程可以保留自己的：

- 数据。
- 代码。
- 论文。
- 结果图。
- 复盘记录。

正式比赛开始后，建议新建一个独立的当次赛题工程，不要混入旧模拟赛目录。

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

1. 阅读 A/B/C 题，优先判断数据规模、模型复杂度和论文表达难度。
2. 在 `docs/往年优秀工程建模手法分析.md` 中对照类似题型。
3. 确定题目后，新建当次赛题工程目录。
4. 把官方附件放入 `data/` 或当次工程的 `data/`。

### 第 3-12 小时：数据理解与基线模型

1. 用 `code/preprocessing/` 完成数据清洗。
2. 用 `code/prediction/`、`code/evaluation/`、`code/optimization/` 快速跑基线。
3. 同步记录变量定义、假设和符号，避免论文后期补账。

### 第 12-36 小时：模型深化与结果图

1. 每个问题形成独立脚本和可复现实验结果。
2. 使用 `MathModel-Figure-Toolkit/` 统一出图风格。
3. 关键图优先保存为 PDF/SVG，论文用图再导出 PNG。

### 第 36-72 小时：论文整合与提交

1. 使用 `templates/CUMCM2026-Complete-LaTeX/` 或 `templates/cumcm-typst/` 完成论文。
2. 对照 `docs/优秀论文排版画图与摘要写作方法.md` 检查摘要、图注和结论。
3. 用 `mock-contests/提交checklist.md` 做最终提交检查。

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

- `data/` 已清理为赛题数据入口。
- 课程/作业参考材料已归入 `refs/coursework/`。
- Beacon 的本地运行环境、依赖缓存、日志和 `.env` 已清理。
- 绘图工具链已补齐 Python、MATLAB、PyVista/VTK。
- `tools/verify_env.py` 当前自检通过 `18 / 18`。
