# Windows 开发环境说明

本项目的**真正开发环境在 Windows 服务器上**，Mac 仅作为 VSCode Remote-SSH 瘦客户端。
这样可彻底规避跨平台环境差异，并直接使用 Windows 自带中文字体（论文排版不踩字体坑）。

## 机器与路径
- Windows 主机：`10.21.231.20`（用户 `lenovo`）
- 项目路径：`D:\math-2026`
- 虚拟环境：`D:\math-2026\.venv`（Python 3.12.9）
- Python 解释器：`D:\math-2026\.venv\Scripts\python.exe`

## Mac 端：用 VSCode 远程连接
1. 装扩展 **Remote - SSH**。
2. `Cmd+Shift+P` → **Remote-SSH: Connect to Host** → `10.21.231.20`（已在 `~/.ssh/config`，用户 lenovo）。
3. 输入密码 → **Open Folder** → `D:\math-2026`。
4. Windows 端装扩展 **Python**、**Jupyter**。
5. **Python: Select Interpreter** → 选 `D:\math-2026\.venv\Scripts\python.exe`。

## 常用命令（在 Windows 上，仓库根目录）
```bat
:: 环境自检（应输出 通过 10 / 失败 0）
D:\math-2026\.venv\Scripts\python.exe tools\verify_env.py

:: 跑某个模型演示
D:\math-2026\.venv\Scripts\python.exe code\evaluation\topsis.py

:: 装新依赖（用清华镜像，快）
D:\math-2026\.venv\Scripts\python.exe -m pip install 包名 -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## Git / 网络
- GitHub 在本机需走代理：git 已全局配置 `http(s).proxy = http://127.0.0.1:7897`（Clash 混合端口）。
  - 若换了代理端口：`git config --global http.proxy http://127.0.0.1:新端口`（https.proxy 同理）。
  - 代理没开时 push/pull 会失败，开代理即可。
- 同步流程：在 Windows 上 `git add/commit/push`；本仓库即真源。

## 注意
- `.venv` 已被 `.gitignore` 忽略，**不进版本库**（平台相关，换机器用 `pip install -r requirements.txt` 重建）。
- 控制台输出中文若乱码，是 SSH 终端编码问题，不影响程序正确性；脚本写文件用 UTF-8 不受影响。
- pulp 未装：其自带 CBC 求解器跨平台有坑，规划模板统一用 `scipy.optimize`（见 `code/optimization/`）。
