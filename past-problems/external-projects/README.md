# 外部完整工程索引

这些项目来自公开 GitHub 仓库，各自保留独立的 `.git` 目录，便于查看来源和后续更新。它们只用于本地学习，不应直接复制到参赛论文或公开再分发。

## 建议阅读顺序

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

## 已做检查

- 三个工程均已完整下载，并保留来源地址与当前提交记录。
- 所有 Python 文件通过基础语法检查。
- 2023 B 的四个 Notebook 均为有效文件，Word 论文包结构正常。
- 2020 B 与 2023 C 的论文 PDF 可正常打开，抽查首页、中间页和末页未发现缺页、乱码或明显排版损坏。
- 尚未宣称“一键复现”：三个仓库都缺少完整、锁定版本的环境说明，其中 2020 B 和 2023 C 还需要当前环境没有的依赖。

检查日期：2026-08-06
