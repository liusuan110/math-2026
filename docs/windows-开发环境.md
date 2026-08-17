# Windows 开发环境说明

本项目当前位于 Windows：

- 项目根目录：`D:\desktop\math-2026-main\math-2026-main`
- 独立 Python 环境：`D:\desktop\math-2026-main\math-2026-main\.venv`
- Python 解释器：`D:\desktop\math-2026-main\math-2026-main\.venv\Scripts\python.exe`
- Matlab：`D:\Matlab\bin\matlab.exe`（R2024a）

Windows 主要负责建模开发与跑程序；Mac 适合作为论文写作端，必要时通过 VS Code Remote-SSH 连到 Windows 同一个工作区。

## 首次配置

```bat
D:\Python312\python.exe -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
.venv\Scripts\python.exe -m ipykernel install --user --name math-2026 --display-name "Python (math-2026)"
```

项目已包含 `.vscode/settings.json`，用 VS Code 打开根目录时会自动优先选择 `.venv`。

## 常用命令

```bat
:: 环境自检：应输出 通过 25 / 失败 0
.venv\Scripts\python.exe tools\verify_env.py

:: 跑某个模型演示
.venv\Scripts\python.exe code\evaluation\topsis.py

:: 启动 JupyterLab
.venv\Scripts\python.exe -m jupyter lab

:: 安装新依赖
.venv\Scripts\python.exe -m pip install 包名 -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## Mac 写作协作

1. 在 Mac 上用 VS Code Remote-SSH 连接 Windows 主机。
2. 打开 `D:\desktop\math-2026-main\math-2026-main`。
3. 论文源文件优先放在具体赛题工程的 `paper/` 或 `docs/` 下，图表统一从 Windows 端生成到 `figures/`。
4. Windows 端跑模型产出数据和图片，Mac 端只编辑论文文本，减少跨平台依赖差异。

## 注意

- `.venv` 已被 `.gitignore` 忽略，不进入版本库，换机器时按 `requirements.txt` 重建。
- VS Code 终端会把 Matplotlib 缓存写到项目内 `.matplotlib-cache/`，该目录同样不进入版本库。
- `requirements.txt` 第一行保留了 UTF-8 编码声明，避免 Windows 下 `pip` 按 GBK 读取中文注释时报错。
- 控制台输出中文若乱码，多半是终端编码问题，不代表文件损坏；建议 PowerShell 使用 UTF-8 输出。
