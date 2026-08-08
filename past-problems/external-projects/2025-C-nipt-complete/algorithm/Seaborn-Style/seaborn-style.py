import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt

# Seaborn 的主要预设风格
styles = ['darkgrid', 'whitegrid', 'dark', 'white', 'ticks']

# 创建一个 3x2 的图表布局，以容纳所有风格的预览
fig, axes = plt.subplots(3, 2, figsize=(12, 8), sharex=True, sharey=True)
axes = axes.flatten() # 将 3x2 的 axes 数组展平为一维

# 生成一些示例数据
x = np.linspace(0, 10, 100)
y = np.sin(x)

# 遍历每种风格并在对应的子图上绘图
for i, style in enumerate(styles):
    # 设置当前的图表风格
    sns.set_style(style)
    ax = axes[i]
    # 在当前子图上绘制一个简单的带有两个偏移正弦波的线图
    ax.plot(x, y + i * 0.5, label='sin(x)')
    ax.plot(x, np.cos(x) + i * 0.5, label='cos(x)')
    ax.set_title(f"Style: '{style}'")
    ax.legend()

# 隐藏最后一个未使用的子图
axes[-1].set_visible(False)

# 调整整体布局，防止标题和标签重叠
plt.tight_layout()

# 保存图表为图片文件
plt.savefig('seaborn_styles_preview.pdf')