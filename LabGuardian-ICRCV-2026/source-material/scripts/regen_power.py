# -*- coding: utf-8 -*-
"""把两张功率时序图重绘为黑白统一风格(灰度+中文)。
   YOLO 源: 代码仓 scripts/openvino_export/results/{power_timeseries.csv,power_phases.json}
   student 源: board_data/llm_power_ts.csv
   输出: pictures/cadx/power_timeseries.pdf, board_data/llm_power_ts.png"""
import csv, json, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams.update({
    "font.sans-serif": ["Songti SC"], "font.serif": ["Songti SC"],
    "axes.unicode_minus": False, "font.size": 10,
    "axes.linewidth": 0.8, "axes.spines.right": False, "axes.spines.top": False,
})
INK = "#000000"; G1 = "#555555"; G2 = "#9a9a9a"; BAND = "#ededed"; BASE = "#777777"

YOLO_DIR = "board_data"  # 源 CSV/JSON 已随仓提交(yolo_power_*),可独立复现

def spans(ts, phases):
    """从 phase 列求连续区间 [(name,t0,t1)]"""
    out = []
    cur = None
    for t, p in zip(ts, phases):
        if cur is None or p != cur[0]:
            if cur: out.append((cur[0], cur[1], prev_t))
            cur = (p, t)
        prev_t = t
    if cur: out.append((cur[0], cur[1], prev_t))
    return out

# ---------------- 图A: YOLO 三单元功率 ----------------
def yolo():
    rows = list(csv.DictReader(open(YOLO_DIR + "/yolo_power_timeseries.csv")))
    meta = json.load(open(YOLO_DIR + "/yolo_power_phases.json"))
    n = len(rows); last_end = meta["phases"][-1]["end_s"]; itv = last_end / n
    t = [i * itv for i in range(n)]
    pkg = [float(r["PkgWatt"]) for r in rows]
    cor = [float(r["CorWatt"]) for r in rows]
    gfx = [float(r["GFXWatt"]) for r in rows]

    fig, ax = plt.subplots(figsize=(8.5, 4.2), dpi=200)
    lab = {"CPU_workload": "CPU INT8", "GPU_workload": "iGPU INT8", "NPU_workload": "NPU INT8"}
    ymax = max(pkg) * 1.15
    ax.plot(t, pkg, label="整封装(总)", color=INK, linewidth=2.0, zorder=3)
    ax.plot(t, cor, label="CPU 核心", color=G1, linewidth=1.3, linestyle="--", zorder=2)
    ax.plot(t, gfx, label="iGPU", color=G2, linewidth=1.5, linestyle=":", zorder=2)
    ax.axhline(y=4.42, color=BASE, linestyle="--", linewidth=0.8, alpha=0.8, zorder=1)
    ax.text(t[-1] * 0.985, 4.42 + 0.4, "空载 4.4W", fontsize=8, color=BASE, ha="right", va="bottom")
    for ph in meta["phases"]:
        if "workload" not in ph["name"]: continue
        mask = [ph["start_s"] <= ti <= ph["end_s"] for ti in t]
        seg = [(ti, p) for ti, p, m in zip(t, pkg, mask) if m]
        if not seg: continue
        pt, pw = max(seg, key=lambda x: x[1])
        ax.annotate(f"{pw:.1f}W", xy=(pt, pw), xytext=(pt, pw + 2.5), fontsize=9, fontweight="bold",
                    color=INK, ha="center", arrowprops=dict(arrowstyle="-", color=INK, alpha=0.6, lw=0.8))
        mid = (ph["start_s"] + ph["end_s"]) / 2
        ax.text(mid, ymax * 0.96, lab[ph["name"]], ha="center", va="top", fontsize=9, fontweight="bold", color="#333333")
    ax.set_xlabel("时间 (s)", fontsize=11); ax.set_ylabel("功率 (W)", fontsize=11)
    ax.set_title("YOLOv8s-pose INT8 在 DK-2500 上的 RAPL 功率时序\nIntel Core Ultra 5 225U", fontsize=11, pad=10)
    ax.legend(loc="upper right", fontsize=9, framealpha=0.95)
    ax.set_xlim(0, t[-1]); ax.set_ylim(0, ymax)
    ax.grid(True, alpha=0.3, linestyle=":", zorder=0)
    fig.tight_layout()
    fig.savefig("pictures/cadx/power_timeseries.pdf", bbox_inches="tight")
    plt.close(fig); print("ok YOLO power_timeseries.pdf")

# ---------------- 图B: student 功率 ----------------
def student():
    rows = [r for r in csv.DictReader(open("board_data/llm_power_ts.csv")) if r["phase"] != "phase"]
    t = [float(r["t_s"]) for r in rows]
    pkg = [float(r["PkgWatt"]) for r in rows]
    gfx = [float(r["GFXWatt"]) for r in rows]
    ph = [r["phase"] for r in rows]
    sp = spans(t, ph)
    fig, ax = plt.subplots(figsize=(8.5, 3.8), dpi=200)
    ymax = max(pkg) * 1.12
    zh = {"idle": "空载", "inference": "推理", "cooldown": "冷却"}
    for name, t0, t1 in sp:
        if name in zh and (t1 - t0) > 1:
            ax.text((t0 + t1) / 2, ymax * 0.05, zh[name], ha="center", va="bottom", fontsize=9, color="#444444")
    ax.plot(t, pkg, label="整封装功率", color=INK, linewidth=1.8, zorder=3)
    ax.plot(t, gfx, label="核显(iGPU)功率", color=G1, linewidth=1.5, linestyle="--", zorder=2)
    ax.set_xlabel("时间 (s)", fontsize=11); ax.set_ylabel("功率 (W)", fontsize=11)
    ax.set_title("端侧学生模型(Qwen2.5-1.5B-INT4)在 DK-2500 iGPU 上的功率时序", fontsize=11, pad=10)
    ax.legend(loc="center right", fontsize=9, framealpha=0.95)
    ax.set_xlim(min(t), max(t)); ax.set_ylim(0, ymax)
    ax.grid(True, alpha=0.3, linestyle=":", zorder=0)
    fig.tight_layout()
    fig.savefig("board_data/llm_power_ts.png", bbox_inches="tight", facecolor="white")
    plt.close(fig); print("ok student llm_power_ts.png")

yolo(); student(); print("DONE")
