# 00_style

本目录提供全项目统一绘图风格，参考 SciencePlots 的科研论文风格设计，并针对数学建模竞赛论文做了简化。

## 使用方式

```python
from science_style import apply_science_style, save_figure

apply_science_style()
# draw figure ...
save_figure(fig, "output/my_figure")
```

## 设计约束

- 默认 Times New Roman。
- 默认白色背景。
- 默认适配 IEEE 双栏或论文半页宽度。
- 同时输出 PNG 300 dpi、SVG、PDF。
- 中文注释保留，但图中尽量使用英文变量名和符号，便于论文统一。
