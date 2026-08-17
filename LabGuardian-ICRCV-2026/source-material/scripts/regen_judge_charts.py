# -*- coding: utf-8 -*-
"""LLM-Judge 自动评分图 —— 灰度专业学术风，无彩色，无重叠，紧凑布局。
   运行: python regen_judge_charts.py
   输出: board_data/p0_four_model_judge.png, p0_int4_quality_judge.png,
         p0_5_fp_vs_int4_judge.png, p0_dimension_panel.png"""

import json, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams.update({
    "font.sans-serif": ["SimHei", "Microsoft YaHei", "Songti SC"],
    "axes.unicode_minus": False,
    "font.size": 10,
    "axes.linewidth": 0.6,
    "axes.edgecolor": "#333333",
    "axes.spines.right": False,
    "axes.spines.top": False,
    "xtick.major.width": 0.6,
    "ytick.major.width": 0.6,
})

INK   = "#1a1a1a"
DARK  = "#404040"
MID   = "#7a7a7a"
LIGHT = "#b0b0b0"
PALE  = "#d8d8d8"
GRID  = "#e8e8e8"

BOARD = "board_data"

def jload(name):
    return json.load(open(f"{BOARD}/{name}", encoding="utf-8"))

def clean(ax):
    ax.set_axisbelow(True)
    ax.tick_params(colors=INK)

# ═══════ 图1: 四模型 LLM-Judge 横向对比 ═══════

def fig_four_model():
    base  = jload("base_eval_local_auto_scored.json")["summary"]
    fp    = jload("student_eval_fp_local_auto_scored.json")["summary"]
    int4  = jload("student_eval_final_auto_scored.json")["summary"]
    teach = jload("teacher_eval_local_auto_scored.json")["summary"]

    models = ["未蒸馏基座", "蒸馏FP", "蒸馏INT4", "教师上限"]
    x = np.arange(len(models))
    w = 0.28

    ov = [base["overall_mean"], fp["overall_mean"],
          int4["overall_mean"], teach["overall_mean"]]
    co = [base["correctness_mean"], fp["correctness_mean"],
          int4["correctness_mean"], teach["correctness_mean"]]
    pa = [base["pass_rate_pct"], fp["pass_rate_pct"],
          int4["pass_rate_pct"], teach["pass_rate_pct"]]

    fig, (a1, a2) = plt.subplots(2, 1, figsize=(7.2, 5.2), dpi=200,
                                  gridspec_kw={"height_ratios": [1, 0.75]})

    # 上图: 综合 + 正确性 (/5)
    b1 = a1.bar(x - w/2, ov, w, color=LIGHT, edgecolor=INK, linewidth=0.6,
                label="综合得分", zorder=3)
    b2 = a1.bar(x + w/2, co, w, color=DARK, edgecolor=INK, linewidth=0.6,
                label="正确性", zorder=3)
    a1.set_xticks(x)
    a1.set_xticklabels(models, fontsize=10.5)
    a1.set_ylim(0, 5.3)
    a1.set_ylabel("得分 /5", fontsize=10, color=INK)
    a1.grid(axis="y", color=GRID, linewidth=0.35)
    a1.set_axisbelow(True)
    a1.tick_params(colors=INK)
    a1.spines["top"].set_visible(False)
    a1.spines["right"].set_visible(False)
    a1.legend(frameon=False, fontsize=9.5, loc="upper left",
              handlelength=1.5, handleheight=0.8)
    for bars in [b1, b2]:
        for bar in bars:
            h = bar.get_height()
            a1.text(bar.get_x() + bar.get_width()/2., h + 0.07,
                    f"{h:.2f}", ha="center", va="bottom",
                    fontsize=9, color=INK, fontweight="bold")

    # 下图: 通过率 (%)
    pc = [DARK if i == 2 else LIGHT for i in range(4)]  # INT4 = dark
    a2.bar(x, pa, width=w * 1.6, color=pc, edgecolor=INK, linewidth=0.6, zorder=3)
    a2.set_xticks(x)
    a2.set_xticklabels(models, fontsize=10.5)
    a2.set_ylim(0, 112)
    a2.set_ylabel("通过率 %", fontsize=10, color=INK)
    a2.grid(axis="y", color=GRID, linewidth=0.35)
    a2.set_axisbelow(True)
    a2.tick_params(colors=INK)
    a2.spines["top"].set_visible(False)
    a2.spines["right"].set_visible(False)
    for i, v in enumerate(pa):
        a2.text(i, v + 2.5, f"{v:.0f}", ha="center", va="bottom",
                fontsize=9.5, color=INK, fontweight="bold")

    fig.suptitle("四模型 LLM-Judge 自动评分对比  |  30题  |  5维1-5分量表",
                 fontsize=11.5, fontweight="bold", color=INK, y=1.01)
    fig.tight_layout(h_pad=2.5)
    fig.savefig(f"{BOARD}/p0_four_model_judge.png", bbox_inches="tight",
                facecolor="white", dpi=200, pad_inches=0.12)
    plt.close(fig)
    print("ok four_model")


# ═══════ 图2: INT4 五维剖面 + 意图细分 ═══════

def fig_int4_detail():
    int4 = jload("student_eval_final_auto_scored.json")["summary"]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.5, 2.8), dpi=200)

    dims_zh = ["正确性", "教学性", "简洁性", "格式结构", "接地安全"]
    dim_keys = ["correctness", "pedagogy", "conciseness", "format", "groundedness"]
    dv = [int4[f"{k}_mean"] for k in dim_keys]
    dx = range(len(dims_zh))

    a1.bar(dx, dv, color=[DARK, PALE, LIGHT, LIGHT, LIGHT],
           edgecolor=INK, linewidth=0.5, width=0.52)
    a1.set_xticks(list(dx))
    a1.set_xticklabels(dims_zh, fontsize=9)
    a1.set_ylim(0, 5.1)
    a1.grid(axis="y", color=GRID, linewidth=0.35)
    clean(a1)
    a1.set_title("五维质量剖面", fontsize=10, fontweight="bold", color=INK, pad=4)
    for xi, v in zip(dx, dv):
        a1.text(xi, v + 0.10, f"{v:.2f}", ha="center", va="bottom",
                fontsize=9, color=INK, fontweight="bold",
                    clip_on=False)

    # 右: 意图
    order = ["concept_tutor", "mixed", "lab_guidance", "diagnostic"]
    izh = {"concept_tutor": "概念讲解", "mixed": "混合问答",
           "lab_guidance": "实验指导", "diagnostic": "诊断排查"}
    ilabels = [izh[k] for k in order]
    ivals = [int4["by_intent"][k]["mean_overall"] for k in order]
    ix = range(len(ilabels))
    icolors = [LIGHT] * 4
    icolors[ivals.index(max(ivals))] = DARK
    icolors[ivals.index(min(ivals))] = PALE

    a2.bar(ix, ivals, color=icolors, edgecolor=INK, linewidth=0.5, width=0.52)
    a2.set_xticks(list(ix))
    a2.set_xticklabels(ilabels, fontsize=9)
    a2.set_ylim(0, 5.1)
    a2.grid(axis="y", color=GRID, linewidth=0.35)
    clean(a2)
    a2.set_title("按意图细分", fontsize=10, fontweight="bold", color=INK, pad=4)
    for xi, v in zip(ix, ivals):
        a2.text(xi, v + 0.10, f"{v:.2f}", ha="center", va="bottom",
                fontsize=9, color=INK, fontweight="bold",
                    clip_on=False)

    fig.suptitle("部署版 INT4 学生模型  |  LLM-Judge 质量剖面",
                 fontsize=10, fontweight="bold", color=INK, y=1.06)
    fig.tight_layout(w_pad=3.0)
    fig.savefig(f"{BOARD}/p0_int4_quality_judge.png", bbox_inches="tight",
                facecolor="white", dpi=200, pad_inches=0.15)
    plt.close(fig)
    print("ok int4_detail")


# ═══════ 图3: FP vs INT4 量化对比 ═══════

def fig_fp_vs_int4():
    fp   = jload("student_eval_fp_local_auto_scored.json")["summary"]
    int4 = jload("student_eval_final_auto_scored.json")["summary"]

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.0, 2.5), dpi=200)

    metrics = ["综合得分", "正确性", "通过率"]
    fp_v   = [fp["overall_mean"], fp["correctness_mean"], fp["pass_rate_pct"]]
    int4_v  = [int4["overall_mean"], int4["correctness_mean"], int4["pass_rate_pct"]]
    y = range(len(metrics))
    h = 0.26

    a1.barh([yi - h/2 for yi in y], fp_v, h, color=LIGHT, edgecolor=INK,
            linewidth=0.5, label="FP")
    a1.barh([yi + h/2 for yi in y], int4_v, h, color=DARK, edgecolor=INK,
            linewidth=0.5, label="INT4")
    a1.set_yticks(list(y))
    a1.set_yticklabels(metrics, fontsize=9)
    a1.invert_yaxis()
    a1.set_xlim(0, 108)
    a1.grid(axis="x", color=GRID, linewidth=0.35)
    clean(a1)
    a1.set_title("综合质量", fontsize=10, fontweight="bold", color=INK, pad=4)
    a1.legend(frameon=False, fontsize=8, loc="lower right")
    for i, (fv, iv) in enumerate(zip(fp_v, int4_v)):
        a1.text(fv + 4.0, i - h/2, f"{fv:.1f}", va="center", fontsize=7.5, color=MID,
                    clip_on=False, zorder=10)
        a1.text(iv + 4.0, i + h/2, f"{iv:.1f}", va="center", fontsize=7.5, color=INK,
                fontweight="bold",
                    clip_on=False, zorder=10)

    intent_order = ["concept_tutor", "diagnostic", "lab_guidance", "mixed"]
    izh = {"concept_tutor": "概念讲解", "diagnostic": "诊断排查",
           "lab_guidance": "实验指导", "mixed": "混合问答"}
    ilabels = [izh[k] for k in intent_order]
    fp_i   = [fp["by_intent"][k]["mean_overall"] for k in intent_order]
    int4_i  = [int4["by_intent"][k]["mean_overall"] for k in intent_order]
    yi = range(len(ilabels))

    a2.barh([yi_i - h/2 for yi_i in yi], fp_i, h, color=LIGHT, edgecolor=INK,
            linewidth=0.5, label="FP")
    a2.barh([yi_i + h/2 for yi_i in yi], int4_i, h, color=DARK, edgecolor=INK,
            linewidth=0.5, label="INT4")
    a2.set_yticks(list(yi))
    a2.set_yticklabels(ilabels, fontsize=9)
    a2.invert_yaxis()
    a2.set_xlim(0, 4.9)
    a2.grid(axis="x", color=GRID, linewidth=0.35)
    clean(a2)
    a2.set_title("按意图细分", fontsize=10, fontweight="bold", color=INK, pad=4)
    a2.legend(frameon=False, fontsize=8, loc="lower right")
    for i, (fv, iv) in enumerate(zip(fp_i, int4_i)):
        a2.text(fv + 0.15, i - h/2, f"{fv:.2f}", va="center", fontsize=7.5, color=MID,
                    clip_on=False, zorder=10)
        a2.text(iv + 0.15, i + h/2, f"{iv:.2f}", va="center", fontsize=7.5, color=INK,
                fontweight="bold",
                    clip_on=False, zorder=10)

    fig.suptitle("FP vs INT4 量化对比  |  同一题集 · 同一评委 · 同一约束",
                 fontsize=10, fontweight="bold", color=INK, y=1.07)
    fig.tight_layout(w_pad=3.5)
    fig.savefig(f"{BOARD}/p0_5_fp_vs_int4_judge.png", bbox_inches="tight",
                facecolor="white", dpi=200)
    plt.close(fig)
    print("ok fp_vs_int4")


# ═══════ 图4: 四模型五维剖面面板 ═══════

def fig_dimension_panel():
    base  = jload("base_eval_local_auto_scored.json")["summary"]
    fp    = jload("student_eval_fp_local_auto_scored.json")["summary"]
    int4  = jload("student_eval_final_auto_scored.json")["summary"]
    teach = jload("teacher_eval_local_auto_scored.json")["summary"]

    dims_zh = ["正确性", "教学性", "简洁性", "格式", "接地性"]
    dim_keys = ["correctness", "pedagogy", "conciseness", "format", "groundedness"]
    models_data = [
        ("基座", base,  LIGHT),
        ("FP",   fp,    LIGHT),
        ("INT4", int4,  DARK),
        ("教师", teach, PALE),
    ]

    fig, axes = plt.subplots(2, 2, figsize=(9.5, 5.5), dpi=200)
    for ax, (name, data, color) in zip(axes.flat, models_data):
        vals = [data[f"{k}_mean"] for k in dim_keys]
        x = range(len(dims_zh))
        ax.bar(x, vals, color=color, edgecolor=INK, linewidth=0.5, width=0.5)
        ax.set_xticks(list(x))
        ax.set_xticklabels(dims_zh, fontsize=8.5)
        ax.set_ylim(0, 5.1)
        ax.grid(axis="y", color=GRID, linewidth=0.35)
        clean(ax)
        ax.set_title(name, fontsize=10, fontweight="bold", color=INK, pad=3)
        for xi, v in zip(x, vals):
            ax.text(xi, v + 0.09, f"{v:.1f}", ha="center", va="bottom",
                    fontsize=8, color=INK, fontweight="bold",
                    clip_on=False)

    fig.suptitle("四模型五维评分剖面对比  |  LLM-Judge 1-5分量表",
                 fontsize=10, fontweight="bold", color=INK, y=1.02)
    fig.tight_layout(h_pad=2.2, w_pad=2.0)
    fig.savefig(f"{BOARD}/p0_dimension_panel.png", bbox_inches="tight",
                facecolor="white", dpi=200)
    plt.close(fig)
    print("ok dimension_panel")


if __name__ == "__main__":
    fig_four_model()
    fig_int4_detail()
    fig_fp_vs_int4()
    fig_dimension_panel()
    print("\nDONE — 4 charts")
