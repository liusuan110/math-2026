import matplotlib.font_manager

# 列出当前 Matplotlib 能找到使用的所有字体类型
font_list = sorted([f.name for f in matplotlib.font_manager.fontManager.ttflist])
for font in font_list:
        print(font)