import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from matplotlib.patches import Circle, RegularPolygon
from matplotlib.path import Path
from matplotlib.projections import register_projection
from matplotlib.projections.polar import PolarAxes
from matplotlib.spines import Spine
from matplotlib.transforms import Affine2D


# 您提供的 radar_factory 函数，保持不变
def radar_factory(num_vars, frame='circle'):
    """
    Create a radar chart with `num_vars` Axes.
    (此函数为您提供，未作修改)
    """
    # calculate evenly-spaced axis angles
    theta = np.linspace(0, 2 * np.pi, num_vars, endpoint=False)

    class RadarTransform(PolarAxes.PolarTransform):

        def transform_path_non_affine(self, path):
            if path._interpolation_steps > 1:
                path = path.interpolated(num_vars)
            return Path(self.transform(path.vertices), path.codes)

    class RadarAxes(PolarAxes):

        name = 'radar'
        PolarTransform = RadarTransform

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.set_theta_zero_location('N')

        def fill(self, *args, closed=True, **kwargs):
            return super().fill(closed=closed, *args, **kwargs)

        def plot(self, *args, **kwargs):
            lines = super().plot(*args, **kwargs)
            for line in lines:
                self._close_line(line)

        def _close_line(self, line):
            x, y = line.get_data()
            if x[0] != x[-1]:
                x = np.append(x, x[0])
                y = np.append(y, y[0])
                line.set_data(x, y)

        def set_varlabels(self, labels):
            self.set_thetagrids(np.degrees(theta), labels)

        def _gen_axes_patch(self):
            if frame == 'circle':
                return Circle((0.5, 0.5), 0.5)
            elif frame == 'polygon':
                return RegularPolygon((0.5, 0.5), num_vars,
                                      radius=.5, edgecolor="k")
            else:
                raise ValueError("Unknown value for 'frame': %s" % frame)

        def _gen_axes_spines(self):
            if frame == 'circle':
                return super()._gen_axes_spines()
            elif frame == 'polygon':
                spine = Spine(axes=self,
                              spine_type='circle',
                              path=Path.unit_regular_polygon(num_vars))
                spine.set_transform(Affine2D().scale(.5).translate(.5, .5)
                                    + self.transAxes)
                return {'polar': spine}
            else:
                raise ValueError("Unknown value for 'frame': %s" % frame)

    register_projection(RadarAxes)
    return theta


# 原有的 example_data() 函数被移除，因为我们将直接使用您的数据

if __name__ == '__main__':
    # --- START: 修改部分 ---
    # 1. 直接定义您的数据
    data_dict = {
        '人均专著': [0.063758, 0.127515, 0.255031, 0.573819, 0.765092],
        '生师比': [0.597022, 0.597022, 0.497519, 0.199007, 0.000000],
        '科研经费': [0.344901, 0.413882, 0.482862, 0.689803, 0.027592],
        '逾期毕业率': [0.275343, 0.231092, 0.193151, 0.562658, 0.718952]
    }
    df = pd.DataFrame(data_dict)

    # 2. 定义雷达图的指标（spokes）
    spoke_labels = df.columns.tolist()

    # 3. 设置指标数量
    N = len(spoke_labels)

    # 4. 计算最佳解(Z+)和最劣解(Z-)
    # 假设“生师比”和“逾期毕业率”是成本型指标（越小越好）
    # “人均专著”和“科研经费”是效益型指标（越大越好）
    z_plus = [df['人均专著'].max(), df['生师比'].min(), df['科研经费'].max(), df['逾期毕业率'].min()]
    z_minus = [df['人均专著'].min(), df['生师比'].max(), df['科研经费'].min(), df['逾期毕业率'].max()]

    # 将所有数据整合
    case_data = df.values.tolist()
    case_data.append(z_plus)
    case_data.append(z_minus)

    # --- END: 修改部分 ---

    theta = radar_factory(N, frame='polygon')

    # 设置中文字体
    plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.rcParams['axes.unicode_minus'] = False

    # --- START: 绘图逻辑修改 ---
    # 原代码创建2x2子图，这里我们只创建一个子图
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='radar'))
    fig.subplots_adjust(top=0.85, bottom=0.1)

    # 设置网格线
    ax.set_rgrids([0.2, 0.4, 0.6, 0.8])
    # 设置图表标题
    ax.set_title("院校 TOPSIS 指标雷达图", weight='bold', size='large', position=(0.5, 1.1),
                 horizontalalignment='center', verticalalignment='center')

    # 定义颜色和图例标签
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 'green', 'red']
    labels = ['院校 A', '院校 B', '院校 C', '院校 D', '院校 E', '最佳解 (Z+)', '最劣解 (Z-)']

    # 在同一个ax上循环绘制所有数据
    for i, (d, color) in enumerate(zip(case_data, colors)):
        ax.plot(theta, d, color=color)
        # 填充院校数据区域
        if i < 5:
            ax.fill(theta, d, facecolor=color, alpha=0.25)
        else:  # 对最佳/最劣解使用虚线以示区别
            ax.lines[i].set_linestyle('--')
            ax.lines[i].set_linewidth(2)

    # 设置指标名称
    ax.set_varlabels(spoke_labels)

    # 创建图例
    legend = ax.legend(labels, loc=(0.9, .95),
                       labelspacing=0.1, fontsize='small')

    # 不再需要 fig.text, 因为标题已经设置在ax上
    # --- END: 绘图逻辑修改 ---

    plt.savefig("topsis_radar_chart_combined.png", dpi=300)
    print("雷达图已保存为 topsis_radar_chart_combined.png")
    plt.show()