# 外部完整工程索引

这些项目来自公开 GitHub/Gitee 仓库，现已作为普通文件纳入本仓库，便于在 Windows 和 Mac 两端同步查看。原项目来源仍保留在下方索引中；使用时请尊重各项目许可与署名要求，不应直接复制到参赛论文中。

## 建议阅读顺序

资料按用途分为四类：

- 主读工程：优先完整研读，学习建模主线、论文结构和代码复现方式。
- 同题对照：同一题目的不同解法，用于比较模型取舍。
- 资料库：题目和优秀论文合集，按需检索，不建议全部通读。
- 链接备查：不在仓库内保存全文或工具，仅保留来源入口。

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

### 2026-08-07 非 GitHub 来源新增材料

9. `gitee-2024-B-cumcm-cherzing/`
   - 来源：https://gitee.com/Cherzing/2024_CUMCM_B
   - 题目：2024 年 B 题
   - 内容：24 个 Python 源码文件，覆盖抽样检验、遗传算法、MILP 和敏感性分析。
   - 先看：`README.md` -> `代码/Question1/` -> `代码/Question2/` -> `代码/Question3/`。
   - 注意：原仓库 README 中奖项位置留空，因此只按“代码对照样例”使用；本目录原有题目 PDF 与 `2024-B-complete-paper-code/question/B题.pdf` 完全重复，已删除副本。

10. `gitee-cumcm-past-questions/`
   - 来源：https://gitee.com/jiufafeng/cumcm-past-questions
   - 定位：CUMCM 历年赛题与优秀论文合集。
   - 内容：`全国大学生数学建模竞赛(CUMCM)优秀论文/` 覆盖 2012-2021 年；`全国大学生数学建模竞赛(CUMCM)历年赛题/` 覆盖 2001-2022 年，含 PDF、Word、Excel、图片和压缩附件。
   - 先看：`全国大学生数学建模竞赛(CUMCM)优秀论文/2021/`、`全国大学生数学建模竞赛(CUMCM)优秀论文/2020/`，再按 A/B/C 题挑近似题型。
   - 学习重点：老题的“摘要写法、模型假设、符号表、结果表组织、灵敏度/误差分析”。

### 官方优秀论文展示链接

这些页面适合赛前精读结构，但不建议下载后提交到公开仓库。

- 2023 官方论文展示总入口：https://dxs.moe.gov.cn/zx/hd/sxjm/sxjmlw/2023qgdxssxjmjslwzs/2023gjsbqgdxssxjmjslwzs.shtml
- 2023 A 题展示：A0165、A0127、A092
- 2023 B 题展示：B477、B311、B226
- 2023 C 题展示：C228、C126、C050
- 2023 C 题官方讲评：https://dxs.moe.gov.cn/zx/a/hd_sxjm_sxjmstjp_2023sxjmstjp/231207/1869893.shtml
- 中国大学生在线优秀论文展示页整理工具：https://gitee.com/CUITsxjm/China-University-Students-Online-Website-National-Competition-Outstanding-Papers-Crawling

## 已做检查

- 三个工程均已完整下载，并保留来源地址。
- 上传到本仓库时排除了嵌套 `.git` 历史目录和 `.DS_Store` 系统文件；工程内容文件、论文、代码、数据、模型中间文件和结果图均纳入同步。
- 所有 Python 文件通过基础语法检查。
- 2023 B 的四个 Notebook 均为有效文件，Word 论文包结构正常。
- 2020 B 与 2023 C 的论文 PDF 可正常打开，抽查首页、中间页和末页未发现缺页、乱码或明显排版损坏。
- 尚未宣称“一键复现”：三个仓库都缺少完整、锁定版本的环境说明，其中 2020 B 和 2023 C 还需要当前环境没有的依赖。
- 2026-08-07 新增的五个工程均已作为普通文件下载；嵌套 `.git` 目录已移除。
- `2023-B-multibeam-national-second/支撑材料.zip` 已展开，展开后包含 10 个 MATLAB 脚本和 4 个 Excel 文件。
- 非 GitHub 来源保留了两个 Gitee 资料目录，并移除嵌套 `.git` 目录。
- `gitee-cumcm-past-questions/` 当前含 1208 个文件，其中包括 63 个 PDF、111 个 Word 文档、86 个 Excel 文件和若干图片/压缩附件。
- 2026-08-07 进行了去重整理：删除 `2020-B-desert-game-national-first/paper/沙漠游戏.pdf`，保留根目录 `沙漠游戏.pdf`；删除 `gitee-2024-B-cumcm-cherzing/B题题目.pdf`，保留 `2024-B-complete-paper-code/question/B题.pdf`；删除 `gitee-cumcm-past-questions/全国大学生数学建模竞赛(CUMCM)历年赛题/2014/全国大学生数学建模竞赛参赛规则.pdf`，保留 2013 年同哈希副本；删除非工程类 `gitee-official-paper-crawler/` 目录，仅保留来源链接。

检查日期：2026-08-07
