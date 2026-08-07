import numpy as np
import matplotlib.pyplot as plt
from typing import List, Tuple, Dict
from dataclasses import dataclass

# ---------------- 数据结构 ----------------
@dataclass
class Region:
    x_min: float
    x_max: float
    y_min: float
    y_max: float

    @property
    def width(self) -> float:
        return self.x_max - self.x_min

    @property
    def height(self) -> float:
        return self.y_max - self.y_min

    def contains(self, xy: np.ndarray) -> np.ndarray:
        """xy: (N,2)"""
        return (
            (xy[:, 0] >= self.x_min)
            & (xy[:, 0] < self.x_max)
            & (xy[:, 1] >= self.y_min)
            & (xy[:, 1] < self.y_max)
        )

    def subdivide_3x3(self) -> List["Region"]:
        xs = np.linspace(self.x_min, self.x_max, 4)
        ys = np.linspace(self.y_min, self.y_max, 4)
        regs = []
        for i in range(3):
            for j in range(3):
                regs.append(
                    Region(xs[i], xs[i + 1], ys[j], ys[j + 1])
                )
        return regs


@dataclass
class Plane:
    a: float
    b: float
    c: float

    def predict(self, xy: np.ndarray) -> np.ndarray:
        return xy[:, 0] * self.a + xy[:, 1] * self.b + self.c


# ---------------- 核心算法 ----------------
class ARPF:
    def __init__(
        self,
        mse_threshold: float = 1e-3,
        min_region_size: float = 0.0,
        min_points_per_region: int = 3,
    ):
        self.tau = mse_threshold
        self.d_min = min_region_size
        self.min_pts = min_points_per_region
        self.regions: List[Region] = []
        self.planes: List[Plane] = []

    # ----------- 公有接口 -----------
    def fit(self, xyz: np.ndarray, root_region: Region):
        self.regions.clear()
        self.planes.clear()
        self._recursive_fit(xyz, root_region)

    def predict(self, xy: np.ndarray) -> np.ndarray:
        """给定二维坐标，返回对应的预测 z"""
        xy = np.asarray(xy)
        z = np.full(xy.shape[0], np.nan)
        for reg, plane in zip(self.regions, self.planes):
            mask = reg.contains(xy)
            z[mask] = plane.predict(xy[mask])
        return z
    
    def get_region_vertices(self) -> np.ndarray:
        """
        返回所有拟合区域的外接矩形顶点
        Returns
        -------
        np.ndarray
            shape = (num_regions, 4, 2)
            每个区域按 [左下, 右下, 右上, 左上] 顺序给出 4 个顶点
        """
        vertices = []
        for reg in self.regions:
            # 注意：Region 使用 [x_min, x_max) 左闭右开，但绘制/返回时
            # 通常把四角包含进去，所以直接用 x_max/y_max 即可
            vs = np.array([
                [reg.x_min, reg.y_min],  # 左下
                [reg.x_max, reg.y_min],  # 右下
                [reg.x_max, reg.y_max],  # 右上
                [reg.x_min, reg.y_max],  # 左上
            ])
            vertices.append(vs)
        return np.stack(vertices, axis=0)

    def get_plane_tilt_angles(self) -> np.ndarray:
        """
        返回每个拟合平面与 XOY 平面的夹角（弧度）
        计算方式：cosθ = |c| / √(a² + b² + c²)
        θ = arccos(|c| / √(a² + b² + c²))

        Returns
        -------
        np.ndarray
            shape = (num_regions,)
        """
        angles = []
        for plane in self.planes:
            a, b, c = plane.a, plane.b, plane.c
            denom = np.sqrt(a**2 + b**2 + c**2)
            # 防止除以 0（理论上不会，因为平面方程至少有一个系数非零）
            denom = max(denom, 1e-12)
            cos_theta = abs(c) / denom
            # 防止数值越界导致 arccos 报错
            cos_theta = np.clip(cos_theta, 0.0, 1.0)
            angles.append(np.arccos(cos_theta))
        return np.array(angles, dtype=np.float64)
    
    # ----------- 内部实现 -----------
    def _recursive_fit(self, xyz: np.ndarray, region: Region):
        # 1. 提取点
        mask = region.contains(xyz[:, :2])
        pts = xyz[mask]
        if pts.shape[0] < self.min_pts:
            return

        # 2. 最小二乘平面
        plane = self._fit_plane(pts)
        mse = self._compute_mse(pts, plane)

        # 3. 终止条件
        if mse <= self.tau or region.width <= self.d_min:
            self.regions.append(region)
            self.planes.append(plane)
            return

        # 4. 细分 3x3
        for sub in region.subdivide_3x3():
            self._recursive_fit(xyz, sub)

    # ----------- 静态工具 -----------
    @staticmethod
    def _fit_plane(pts: np.ndarray) -> Plane:
        """pts: (N,3)"""
        A = np.c_[pts[:, 0], pts[:, 1], np.ones(pts.shape[0])]
        abc, *_ = np.linalg.lstsq(A, pts[:, 2], rcond=None)
        return Plane(*abc)

    @staticmethod
    def _compute_mse(pts: np.ndarray, plane: Plane) -> float:
        pred = plane.predict(pts[:, :2])
        return float(np.mean((pts[:, 2] - pred) ** 2))


# ---------------- 测试曲面采样 ----------------
def sample_hemisphere(n: int = 5000):
    """半球面 z = sqrt(1 - x^2 - y^2)"""
    xy = np.random.uniform(-1, 1, (n, 2))
    r2 = np.sum(xy ** 2, axis=1)
    mask = r2 <= 1
    xy = xy[mask]
    z = np.sqrt(1 - np.sum(xy ** 2, axis=1))
    return np.c_[xy, z]


def sample_cone(n: int = 5000):
    """半圆锥 z = sqrt(x^2 + y^2)"""
    theta = np.random.uniform(0, 2 * np.pi, n)
    r = np.random.uniform(0, 1, n)
    x = r * np.cos(theta)
    y = r * np.sin(theta)
    z = r
    return np.column_stack((x, y, z))


def sample_spiral(n: int = 5000):
    """一圈螺旋面 z = theta/(2pi)"""
    theta = np.random.uniform(0, 2 * np.pi, n)
    r = np.random.uniform(0.2, 1, n)
    x = r * np.cos(theta)
    y = r * np.sin(theta)
    z = theta / (2 * np.pi)
    return np.column_stack((x, y, z))


# ---------------- 可视化 ----------------
def plot_result(xyz, arpf: ARPF, title: str):
    fig = plt.figure(figsize=(14, 5))

    # 3D 散点
    ax1 = fig.add_subplot(131, projection="3d")
    ax1.scatter(xyz[:, 0], xyz[:, 1], xyz[:, 2], s=1)
    ax1.set_title("Original Points")

    # 预测面片
    ax2 = fig.add_subplot(132, projection="3d")
    for reg, plane in zip(arpf.regions, arpf.planes):
        xs = np.linspace(reg.x_min, reg.x_max, 5)
        ys = np.linspace(reg.y_min, reg.y_max, 5)
        X, Y = np.meshgrid(xs, ys)
        Z = plane.a * X + plane.b * Y + plane.c
        ax2.plot_wireframe(X, Y, Z, color="k", alpha=0.4)
    ax2.set_title("Fitted Planes")

    # 误差热图
    ax3 = fig.add_subplot(133)
    h = 200
    xg = np.linspace(xyz[:, 0].min(), xyz[:, 0].max(), h)
    yg = np.linspace(xyz[:, 1].min(), xyz[:, 1].max(), h)
    X, Y = np.meshgrid(xg, yg)
    xy_grid = np.column_stack((X.ravel(), Y.ravel()))
    Z_pred = arpf.predict(xy_grid).reshape(h, h)
    # 计算真实值（仅对测试曲面可视化）
    if "hemi" in title.lower():
        Z_true = np.sqrt(np.clip(1 - X ** 2 - Y ** 2, 0, None))
    elif "cone" in title.lower():
        Z_true = np.sqrt(X ** 2 + Y ** 2)
    else:
        theta = np.arctan2(Y, X) % (2 * np.pi)
        Z_true = theta / (2 * np.pi)
    err = np.abs(Z_pred - Z_true)
    im = ax3.imshow(err, extent=(xg[0], xg[-1], yg[0], yg[-1]), origin="lower", cmap="jet")
    plt.colorbar(im, ax=ax3, label="Absolute Error")
    ax3.set_title("Error Heatmap")
    fig.suptitle(title)
    plt.tight_layout()
    plt.show()


# ---------------- 主程序 ----------------
if __name__ == "__main__":
    # 共同参数
    tau = 5e-4
    d_min = 1e-4
    root = Region(-1, 1, -1, 1)

    # 半球面
    xyz = sample_hemisphere(100000)
    arpf = ARPF(mse_threshold=tau, min_region_size=d_min)
    arpf.fit(xyz, root)
    print(f"Hemisphere: {len(arpf.regions)} planes fitted")
    plot_result(xyz, arpf, "Hemisphere")
    verts = arpf.get_region_vertices()
    print("矩形顶点数组 shape:", verts.shape)
    # 例如打印前 3 个矩形
    print(verts[:3])
    angles = arpf.get_plane_tilt_angles()
    print("夹角数组 shape:", angles.shape)
    print("前 10 个夹角（弧度）:", angles[:10])

    # 半圆锥
    xyz = sample_cone(100000)
    arpf = ARPF(mse_threshold=tau, min_region_size=d_min)
    arpf.fit(xyz, root)
    print(f"Cone: {len(arpf.regions)} planes fitted")
    plot_result(xyz, arpf, "Cone")
    verts = arpf.get_region_vertices()
    print("矩形顶点数组 shape:", verts.shape)
    # 例如打印前 3 个矩形
    print(verts[:3])
    angles = arpf.get_plane_tilt_angles()
    print("夹角数组 shape:", angles.shape)
    print("前 10 个夹角（弧度）:", angles[:10])