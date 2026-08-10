# 物理 / 工程类三维图模板

## 用途

这个目录用于沉淀类似以下题型的三维机制图：

- 烟幕遮蔽、覆盖、轨迹规划
- 定日镜反射、遮挡、阴影
- 多波束测线、海底地形、覆盖宽度
- 板凳龙 / 机器人 / 车辆运动轨迹
- 任意需要解释空间几何判据的工程类题

## 当前模板

`physics_scene_3d_template.py` 使用 matplotlib 3D 生成：

- 来袭轨迹
- 无人机 / 运动体轨迹
- 目标点
- 有效覆盖区域
- 视线 / 判据辅助线

运行后输出：

- `output/physics_3d_scene.png`
- `output/physics_3d_scene.svg`
- `output/physics_3d_scene.pdf`

## 赛时改造方法

1. 把 `missile`、`vehicle`、`target`、`cloud_center` 换成题目中的真实变量。
2. 把虚线判据改成你的核心物理判据，例如遮挡、反射、碰撞、覆盖边界。
3. 保留关键时刻标注，不要只画一团复杂轨迹。
4. 如果图变复杂，优先拆成两张：一张机制图，一张结果图。
5. 若需要更强三维效果，参考 `external-tools/figure-tools/pyvista`。

