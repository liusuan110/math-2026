# 烟幕干扰弹投放策略数学建模项目

## 1. 项目介绍

本项目用于求解2025年数学建模竞赛 A 题“烟幕干扰弹的投放策略”。

项目围绕无人机投放烟幕干扰弹的问题，建立导弹、无人机、烟幕弹和烟幕云团的三维运动模型，并通过几何遮蔽判定和数值优化方法，设计不同条件下的烟幕弹投放策略。

项目主要完成以下内容：

1. 建立导弹飞行模型。
2. 建立无人机等高度匀速直线飞行模型。
3. 建立烟幕弹脱离无人机后的抛体运动模型。
4. 建立烟幕云团起爆后的下沉模型。
5. 建立烟幕对真目标的有效遮蔽判定模型。
6. 针对题目中的多个问题进行数值求解。
7. 输出指定格式的 Excel 结果文件。

本项目使用 Python 编写，主要依赖 `numpy`、`scipy` 和 `openpyxl`。

## 2. 环境要求

建议使用以下环境运行本项目：

```bash
Python 3.11.15
conda
pip
```

主要第三方库：

```text
numpy
scipy
openpyxl
```

## 3. 拉取项目代码

在本地选择一个用于存放项目的目录，然后在cmd执行：

```bash
git clone https://github.com/YYYYYYYYXL/Deployment-strategy-of-smoke-screen-grenades.git
```

进入项目目录：

```bash
cd 你的目录名
```

## 4. 创建 Conda 虚拟环境

创建 Python 3.11.15 虚拟环境：

```bash
conda create -n smoke-model python=3.11.15
```

激活虚拟环境：

```bash
conda activate smoke-model
```

如果需要退出虚拟环境，执行：

```bash
conda deactivate
```

## 5. 安装第三方依赖

项目根目录下应包含 `requirements.txt` 文件。

在项目根目录中执行：

```bash
pip install -r requirements.txt
```


## 6. 项目目录结构

项目结构示例：

```text
.
├── src/
│   ├── 1.py
│   ├── 2.py
│   ├── 3.py
│   ├── 4.py
│   └── 5.py
├── output/
│   └── data/
│       ├── result1.xlsx
│       ├── result2.xlsx
│       └── result3.xlsx
├── requirements.txt
└── README.md
```

各文件说明：

```text
src/1.py    求解问题 1
src/2.py    求解问题 2
src/3.py    求解问题 3
src/4.py    求解问题 4
src/5.py    求解问题 5
```

结果文件说明：

```text
output/data/result1.xlsx    问题 3 的结果文件
output/data/result2.xlsx    问题 4 的结果文件
output/data/result3.xlsx    问题 5 的结果文件
```

## 7. 运行项目

进入项目根目录后，先激活虚拟环境：

```bash
conda activate smoke-model
```

然后在src目录下运行对应问题的 Python 文件。

运行问题 1：

```bash
python src/1.py
```

运行问题 2：

```bash
python src/2.py
```

运行问题 3：

```bash
python src/3.py
```

运行问题 4：

```bash
python src/4.py
```

运行问题 5：

```bash
python src/5.py
```

## 8. 输出结果

运行代码后，结果文件会输出到：

```text
output/data/
```

主要输出文件为：

```text
result1.xlsx
result2.xlsx
result3.xlsx
```

其中：

```text
result1.xlsx    对应问题 3
result2.xlsx    对应问题 4
result3.xlsx    对应问题 5
```



## 9. 模型说明

本项目采用三维空间坐标系建模。

导弹按照题目给定初始位置，以固定速度飞向假目标。

无人机在接收到任务后，可以瞬时调整航向，然后以固定速度、固定高度做匀速直线飞行。

烟幕干扰弹从无人机上投放后，水平方向保持无人机投放时的速度，竖直方向受重力作用做自由落体运动。

烟幕弹起爆后，瞬时形成球状烟幕云团。烟幕云团中心以固定速度竖直下沉，在起爆后一定时间内具有有效遮蔽作用。

项目通过计算烟幕云团到“导弹—真目标”视线段的距离，判断烟幕是否能够有效遮蔽真目标。

## 10. 注意事项

1. 请确保 Python 版本为 `3.11.15`。
2. 请确保已经安装 `numpy`、`scipy` 和 `openpyxl`。
3. 运行代码前，请确认当前目录是否为src目录。
4. 如果输出目录不存在，请手动创建，或确保代码中会自动创建。
5. 如果使用 Excel 模板文件，请将模板文件放在代码指定的位置。
6. 部分问题使用数值优化方法，重新运行时结果可能会因随机种子、优化参数或采样精度不同而略有变化。
7. 若只需要复现当前结果，可以直接运行默认代码。
8. 若需要重新优化，请根据代码中的开关参数修改后再运行。

## 11. 常见问题

### 11.1 提示找不到 numpy、scipy 或 openpyxl

重新安装依赖：

```bash
pip install -r requirements.txt
```

或者手动安装：

```bash
pip install numpy scipy openpyxl
```

### 11.2 提示找不到输出目录

Linux 或 macOS 下执行：

```bash
mkdir -p output/data
```

Windows PowerShell 下执行：

```powershell
mkdir output\data
```

### 11.3 运行后没有生成结果文件

请检查：

1. 是否已经激活 Conda 虚拟环境。
2. 是否已经安装所有依赖库。
3. 是否在src目录下运行代码。
4. 代码中的输出路径是否正确。
5. 是否有权限在输出目录中创建文件。

## 12. 许可证

本项目仅用于数学建模学习、研究与竞赛实践。