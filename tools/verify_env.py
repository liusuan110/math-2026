"""环境自检：依次运行 code/ 下各模块的演示，报告 PASS/FAIL。

用法（在仓库根目录）：
    .venv/bin/python tools/verify_env.py          # macOS/Linux
    .venv\\Scripts\\python.exe tools\\verify_env.py  # Windows
"""
import os
import io
import sys
import runpy
import contextlib

# 无界面环境用 Agg 后端，避免 matplotlib 弹窗/报错
os.environ.setdefault("MPLBACKEND", "Agg")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CODE = os.path.join(REPO, "code")

TESTS = [
    ("evaluation", "ahp.py"),
    ("evaluation", "entropy_weight.py"),
    ("evaluation", "topsis.py"),
    ("evaluation", "fuzzy_grey.py"),
    ("optimization", "linear_programming.py"),
    ("optimization", "nonlinear_programming.py"),
    ("optimization", "heuristic.py"),
    ("prediction", "regression.py"),
    ("prediction", "arima_forecast.py"),
    ("prediction", "grey_model.py"),
    ("prediction", "ml_models.py"),
    ("clustering", "cluster_pca.py"),
    ("mechanism", "ode_models.py"),
    ("preprocessing", "data_prep.py"),
    ("graph", "graph_models.py"),
    ("simulation", "monte_carlo.py"),
    ("common", "sensitivity.py"),
    ("common", "plotting.py"),
]


def main():
    passed = failed = 0
    for d, f in TESTS:
        path = os.path.join(CODE, d, f)
        d_abs = os.path.join(CODE, d)
        os.chdir(d_abs)                   # 保证相对路径正常
        if d_abs not in sys.path:
            sys.path.insert(0, d_abs)     # 保证同级模块 import 正常
        try:
            with contextlib.redirect_stdout(io.StringIO()), \
                 contextlib.redirect_stderr(io.StringIO()):
                runpy.run_path(path, run_name="__main__")
            print(f"PASS  {d}/{f}")
            passed += 1
        except Exception as e:
            print(f"FAIL  {d}/{f}  ->  {type(e).__name__}: {str(e)[:120]}")
            failed += 1
    print(f"\n==== 通过 {passed} / 失败 {failed} ====")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
