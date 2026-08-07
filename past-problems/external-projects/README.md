# 外部完整工程索引

这些项目来自公开 GitHub 仓库，现已作为普通文件纳入本仓库，便于在 Windows 和 Mac 两端同步查看。原项目来源仍保留在下方索引中；使用时请尊重各项目许可与署名要求，不应直接复制到参赛论文中。

## 建议阅读顺序

### 已深读/已纳入的完整工程

1. `2020-B-desert-game-national-first/`
   - 来源：https://github.com/seanys/CUMCM2020-Desert-Game
   - 题目：2020 年 B 题“穿越沙漠”
   - 自述奖项：全国一等奖
   - 内容：42 页论文、LaTeX 源稿、题目与附件、动态规划、路径规划、博弈与仿真代码、结果数据和作图文件。
   - 先看：`README.md` → `沙漠游戏.pdf` → `dynamic programming/DP.py` → `game/problem3.py`。
   - 注意：部分代码依赖 FICO Xpress；当前项目环境未安装该商业求解器。

2. `2023-B-multibeam-survey/`
   - 来源：https://github.com/trilliverse/CUMCM2023B
   - 题目：2023 年 B 题“多波束测线问题”
   - 内容：四问 Notebook 与 Python 脚本、MATLAB 绘图、原始附件、结果表、模型验证、Sobol 灵敏度分析、Word 论文稿。
   - 先看：`README.md` → `thesis/5_4.docx` → `Task1.ipynb` 至 `Task4.ipynb` → `validate_model.py`。
   - 注意：仓库未说明获奖等级；复现灵敏度分析需另装 `SALib`，部分图使用 MATLAB。

3. `2023-C-vegetable-pricing/`
   - 来源：https://github.com/heatingma/CMUCM-2023
   - 题目：2023 年 C 题“蔬菜类商品的自动定价与补货决策”
   - 内容：39 页论文、四份原始 Excel 数据、处理后数据、ARIMA、LSTM 残差拟合、价格弹性、整数规划、训练权重与结果图。
   - 先看：`report/report.pdf` → `README.md` → `arima.py` → `models.py` → `integer_program.py` → `main.py`。
   - 注意：仓库未说明获奖等级，也没有依赖清单；完整运行需要 `torch`、`statsmodels`、`pulp` 等包，占用约 298 MB。

### 2026-08-07 新增下载材料

4. `2023-A-heliostat-national-first/`
   - 来源：https://github.com/linggm3/2023_CUMCM_National-First-Prize
   - 题目：2023 年 A 题“定日镜场优化设计”
   - 自述奖项：全国一等奖
   - 内容：正式论文、题目 PDF、答辩 PPT、MATLAB 代码、数据、结果图。
   - 先看：`README.md` -> `定日镜场优化设计模型.pdf` -> `支撑材料/`。
   - 学习重点：A 题工程类优化的“物理建模 -> 效率分解 -> 布局优化 -> 可视化结果”链条，尤其适合学习如何把复杂机理问题拆成可计算模块。

5. `2024-A-beijing-first/`
   - 来源：https://github.com/WitBlue6/2024CUMCM
   - 题目：2024 年 A 题
   - 自述奖项：北京赛区一等奖
   - 内容：问题 1 至问题 5 源码、输出结果、题目 PDF。
   - 先看：`README.md` -> `题目/A题.pdf` -> `代码/draw.py` -> `输出/`。
   - 注意：原作者说明问题 4 在特定时刻仍存在路线选择待优化点，学习时可重点比较“可交付结果”和“仍可改进处”。

6. `2023-B-multibeam-national-second/`
   - 来源：https://github.com/zhangzeyu2002/2023_CUMCM_Problem_B
   - 题目：2023 年 B 题“多波束测线问题”
   - 自述奖项：全国二等奖
   - 内容：论文 PDF、支撑材料压缩包；支撑材料已展开到 `支撑材料_extracted/`，包含 MATLAB 代码和 Excel 数据。
   - 先看：`README.md` -> `基于多目标规划的多波束测线布设模型.pdf` -> `支撑材料_extracted/`。
   - 学习重点：B 题工程几何/路径规划的多目标规划写法，尤其适合和 `2023-B-multibeam-survey/` 对照阅读。

7. `2024-B-complete-paper-code/`
   - 来源：https://github.com/Chang-Liu6/CUMCM2024
   - 题目：2024 年 B 题
   - 内容：题目 PDF、最终论文、Python 代码。
   - 先看：`README.md` -> `question/B题.pdf` -> `thesis/` -> `codes/`。
   - 学习重点：B 题决策优化的论文结构和 Python 求解组织方式；该仓库未明确奖项，按“完整论文代码样例”使用。

8. `2023-C-vegetable-pricing-shanghai-second/`
   - 来源：https://github.com/kalipolis/CUMCM2023_C
   - 题目：2023 年 C 题“蔬菜类商品的自动定价与补货决策”
   - 自述奖项：上海市二等奖
   - 内容：论文 PDF、Python Notebook、Python 脚本、处理后 Excel 数据。
   - 先看：`readme.md` -> `论文定稿.pdf` -> `代码/` -> `数据/`。
   - 学习重点：C 题数据分析链路，包括清洗、聚类、回归、ARIMA/GRU 预测和规划求解。

未下载项：GitHub Topic 中出现的 `aprlost/2024-CUMCM-C` 在克隆时返回仓库不存在或不可访问，因此未纳入本地。当前工作区已有 `past-problems/recent-examples/2024-C题_农作物种植_广东二等奖/`，可作为 2024 C 题参考。

## 已做检查

- 三个工程均已完整下载，并保留来源地址。
- 上传到本仓库时排除了嵌套 `.git` 历史目录和 `.DS_Store` 系统文件；工程内容文件、论文、代码、数据、模型中间文件和结果图均纳入同步。
- 所有 Python 文件通过基础语法检查。
- 2023 B 的四个 Notebook 均为有效文件，Word 论文包结构正常。
- 2020 B 与 2023 C 的论文 PDF 可正常打开，抽查首页、中间页和末页未发现缺页、乱码或明显排版损坏。
- 尚未宣称“一键复现”：三个仓库都缺少完整、锁定版本的环境说明，其中 2020 B 和 2023 C 还需要当前环境没有的依赖。
- 2026-08-07 新增的五个工程均已作为普通文件下载；嵌套 `.git` 目录已移除。
- `2023-B-multibeam-national-second/支撑材料.zip` 已展开，展开后包含 10 个 MATLAB 脚本和 4 个 Excel 文件。

检查日期：2026-08-07
