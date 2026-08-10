# MATLAB 出图模板

## 适用场景

- Windows 端用 MATLAB 做仿真、优化和数据处理。
- 需要把 MATLAB 图稳定导出到论文中。
- 不希望论文里出现 MATLAB 默认截图的粗糙观感。

## 使用方式

1. 打开 `matlab_publication_plot_template.m`。
2. 把示例数据替换成你的仿真结果。
3. 运行脚本。
4. 输出会保存到 `output/`，包含 `png` 和 `pdf`。

如果仓库中存在：

`external-tools/figure-tools/export_fig`

脚本会优先调用 `export_fig`。如果没有，也会自动回退到 MATLAB 自带 `exportgraphics`。

## 与 gramm 的关系

`external-tools/figure-tools/gramm` 适合画分组统计图，例如：

- 多方案对比
- 多参数分组散点图
- 箱线图
- 不同算法结果分布

如果只是普通曲线图，用本模板就够了；如果是复杂分组统计，再参考 `gramm`。

