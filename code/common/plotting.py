"""论文级绘图模板：中文字体 + 统一风格 + 高分辨率导出。

用法：
    from code.common.plotting import setup_style, save_fig
    setup_style()
    fig, ax = plt.subplots()
    ax.plot(...)
    save_fig(fig, "figures/q1_result.png")

赛时只需 import + setup_style()，所有图风格统一、可直接进论文。
"""
from __future__ import annotations

import os
import matplotlib
import matplotlib.pyplot as plt


def setup_style(font_size: int = 12) -> None:
    """设置全局绘图风格：中文显示、负号、字号、网格。

    自动尝试常见中文字体，找不到则提示（图仍能出，中文可能变方框）。
    """
    # 按优先级尝试系统中常见的中文字体
    candidates = [
        "PingFang SC",      # macOS
        "Songti SC",        # macOS 宋体
        "Microsoft YaHei",  # Windows 微软雅黑
        "SimHei",           # Windows 黑体
        "WenQuanYi Zen Hei",  # Linux
        "Noto Sans CJK SC",
    ]
    available = {f.name for f in matplotlib.font_manager.fontManager.ttflist}
    chosen = next((c for c in candidates if c in available), None)
    if chosen:
        plt.rcParams["font.sans-serif"] = [chosen]
    else:
        print("[plotting] 未找到中文字体，中文可能显示为方框。"
              "可手动设置 plt.rcParams['font.sans-serif']。")

    plt.rcParams.update({
        "axes.unicode_minus": False,   # 正常显示负号
        "font.size": font_size,
        "axes.titlesize": font_size + 2,
        "axes.labelsize": font_size,
        "axes.grid": True,
        "grid.alpha": 0.3,
        "grid.linestyle": "--",
        "figure.figsize": (8, 5),
        "figure.dpi": 110,
        "savefig.dpi": 300,            # 论文配图 ≥300 dpi
        "savefig.bbox": "tight",
    })


def save_fig(fig, path: str) -> str:
    """保存图到指定路径（自动建目录），返回路径。"""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    fig.savefig(path)
    print(f"[plotting] 已保存: {path}")
    return path


if __name__ == "__main__":
    import numpy as np
    setup_style()
    x = np.linspace(0, 10, 200)
    fig, ax = plt.subplots()
    ax.plot(x, np.sin(x), label="正弦曲线")
    ax.plot(x, np.cos(x), label="余弦曲线")
    ax.set_xlabel("时间 t / s")
    ax.set_ylabel("幅值")
    ax.set_title("绘图风格演示（中文测试）")
    ax.legend()
    save_fig(fig, "figures/_demo_plotting.png")
