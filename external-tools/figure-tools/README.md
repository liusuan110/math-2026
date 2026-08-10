# 数学建模画图开源工具索引

本目录收集比赛期间可直接参考或复用的优秀开源画图工具。它和仓库原有的 `MathModel-Figure-Toolkit` 分工不同：

- `MathModel-Figure-Toolkit`：我们自己的赛时模板库，追求“拿来就画”。
- `external-tools/figure-tools`：外部优秀项目源码，追求“查例子、学风格、补能力”。

这些外部项目已经移除了各自的 `.git` 目录，作为普通源码目录保存在当前仓库中，避免嵌套 Git 仓库问题。使用时请保留原项目许可证和署名信息。

## 工具清单

| 工具 | 本地目录 | 主要用途 | 赛时建议 |
|---|---|---|---|
| SciencePlots | `SciencePlots/` | Python / matplotlib 科研论文风格 | 用于曲线图、柱状图、误差图、模型对比图的统一风格参考 |
| tueplots | `tueplots/` | 论文版面尺寸、字体、会议/期刊风格参数 | 用于控制图宽、字号、比例，避免图插入论文后字号失控 |
| export_fig | `export_fig/` | MATLAB 高质量导出 PNG/PDF/EPS | Windows / MATLAB 组出图时优先使用，替代默认截图 |
| gramm | `gramm/` | MATLAB 版 grammar-of-graphics 分组统计图 | 用于 MATLAB 里的分组柱状图、箱线图、散点分布和多因素对比 |
| PyVista | `pyvista/` | Python 三维科学与工程可视化 | 用于轨迹、空间几何、遮挡、覆盖、网格和物理机制图 |

## 按比赛图形需求选择

| 你要画的图 | 优先工具 | 说明 |
|---|---|---|
| 真实值 - 预测值对比曲线 | `MathModel-Figure-Toolkit` + SciencePlots | 先用我们自己的模板，不够美观时参考 SciencePlots |
| 参数敏感性曲线 / 热力图 | `MathModel-Figure-Toolkit` + tueplots | 重点控制字号、图宽、色条说明和单位 |
| 优化算法收敛曲线 | `MathModel-Figure-Toolkit` | 建议固定输出最优值、平均值、方差或多次运行带状区间 |
| 物理三维场景图 | PyVista / matplotlib 3D | 用于解释几何关系、运动轨迹、遮挡关系，不要只放最终数值 |
| 烟幕 / 光线 / 覆盖 / 反射判据图 | PyVista + Python 自写判据 | 先画机制图，再画优化结果，论文更容易讲清楚 |
| MATLAB 仿真结果图 | export_fig | MATLAB 默认导出经常字号和线宽不稳定，赛时必须统一导出 |
| MATLAB 分组统计图 | gramm | 适合多算法、多方案、多参数条件下的对比图 |
| 论文机制流程图 | draw.io / TikZ | 继续使用 `MathModel-Figure-Toolkit` 里的 draw.io 模板 |

## 推荐的赛时图形生产线

### Python 组

1. 建模代码先输出干净的 `csv/xlsx/json` 结果。
2. 画图脚本只负责读结果和生成图，不要把核心模型逻辑混在画图脚本里。
3. 每张图至少导出 `png` 和 `pdf/svg` 两种格式。
4. 论文优先插入 `pdf/svg`，答辩或交流优先用 `png`。
5. 图名使用题号和结论命名，例如 `q2_03_sensitivity_radius.pdf`。

### MATLAB 组

1. MATLAB 负责仿真、优化和快速探索。
2. 所有进入论文的 MATLAB 图必须统一线宽、字号、字体。
3. 优先用 `export_fig` 导出高分辨率图，不直接截屏。
4. 分组统计图优先参考 `gramm`，不要临时手写大量重复 `bar/scatter`。
5. 如果 MATLAB 图很难调美，可以导出数据给 Python 统一重画。

### 论文组

1. 每张图先问：这张图证明了哪一句结论？
2. 图注不要写“结果图”，要写变量、方法和主要发现。
3. 同一篇论文中，字体、线宽、配色、单位必须一致。
4. 物理类题至少保留一张机制图、一张判据图、一张优化过程图、一张鲁棒性/敏感性图。

## 偏物理 / 工程题的图形清单

如果我们选择类似 2025 A 烟幕、2025 B 碳化硅、2023 A 定日镜场这类题，建议至少准备这些图：

1. 场景几何示意图：对象、坐标系、关键距离、角度、方向。
2. 运动轨迹图：导弹/无人机/云团/光线/目标随时间的位置关系。
3. 判据解释图：遮挡、覆盖、反射、厚度、误差阈值等如何被计算。
4. 参数扫描图：核心变量变化时目标函数如何变化。
5. 优化收敛图：全局搜索是否稳定，是否只是一次偶然结果。
6. 方案对比图：原方案、优化方案、鲁棒方案之间的差异。
7. 敏感性 / 鲁棒性图：关键参数扰动后结论是否稳定。

## 外部来源

- SciencePlots: <https://github.com/garrettj403/SciencePlots>
- tueplots: <https://github.com/pnkraemer/tueplots>
- export_fig: <https://github.com/altmany/export_fig>
- gramm: <https://github.com/piermorel/gramm>
- PyVista: <https://github.com/pyvista/pyvista>

