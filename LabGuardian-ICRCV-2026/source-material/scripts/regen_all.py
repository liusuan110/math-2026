# -*- coding: utf-8 -*-
"""统一重绘 5 张蒸馏/评测图 —— 灰度 + 中文 + 朴素学术风。
   运行: cd /tmp/lgx && python3 regen_all.py  (输出覆盖 board_data/*.png)"""
import json, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["Songti SC"]
plt.rcParams["font.serif"] = ["Songti SC"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["font.size"] = 11
plt.rcParams["axes.linewidth"] = 0.8
plt.rcParams["axes.edgecolor"] = "#000000"

LIGHT = "#d6d6d6"   # 普通
DARK = "#3a3a3a"    # 关键(部署版/最终)
REF = "#9a9a9a"     # 参考(教师)
EDGE = "#222222"
GRID = "#e8e8e8"

def clean(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.set_axisbelow(True)

def hbar(ax, labels, vals, colors, xlabel, fmt="{:.1f}", xpad=1.5, xmax=None):
    y = range(len(labels))
    ax.barh(y, vals, color=colors, edgecolor=EDGE, linewidth=0.8, height=0.62)
    ax.set_yticks(list(y)); ax.set_yticklabels(labels); ax.invert_yaxis()
    if xmax: ax.set_xlim(0, xmax)
    ax.set_xlabel(xlabel)
    for i, v in enumerate(vals):
        ax.text(v + xpad, i, fmt.format(v), va="center", ha="left", fontsize=9.5)
    ax.grid(axis="x", color=GRID, linewidth=0.6); clean(ax)

def vgroup(ax, groups, series, xlabel, ylabel, ymax=110, fmt="{:.1f}"):
    # series: list of (name,color,values)
    import numpy as np
    x = np.arange(len(groups)); n = len(series); w = 0.8 / n
    for k,(name,color,vals) in enumerate(series):
        xs = x - 0.4 + w*(k+0.5)
        ax.bar(xs, vals, width=w, color=color, edgecolor=EDGE, linewidth=0.8, label=name)
        for xi,v in zip(xs,vals):
            ax.text(xi, v+ymax*0.012, fmt.format(v), ha="center", va="bottom", fontsize=8.5)
    ax.set_xticks(x); ax.set_xticklabels(groups)
    ax.set_ylim(0, ymax); ax.set_ylabel(ylabel)
    ax.grid(axis="y", color=GRID, linewidth=0.6); clean(ax)
    ax.legend(frameon=False, fontsize=9, loc="upper right")

def vbar(ax, labels, vals, colors, ylabel, ymax=None, fmt="{:.1f}"):
    x = range(len(labels))
    m = ymax or max(vals)*1.18
    ax.bar(x, vals, color=colors, edgecolor=EDGE, linewidth=0.8, width=0.62)
    ax.set_xticks(list(x)); ax.set_xticklabels(labels)
    ax.set_ylim(0, m); ax.set_ylabel(ylabel)
    for xi,v in zip(x,vals):
        ax.text(xi, v+m*0.012, fmt.format(v), ha="center", va="bottom", fontsize=8.5)
    ax.grid(axis="y", color=GRID, linewidth=0.6); clean(ax)

def jload(p):
    return json.load(open("board_data/"+p, encoding="utf-8"))

def scene_zh(k):
    k=k.lower()
    if "rc" in k: return "一阶RC"
    if "emit" in k or "common" in k or "ce" in k: return "共射"
    if "invert" in k or "inv" in k: return "UA741反相"
    if "integ" in k: return "积分"
    if "sum" in k: return "加法"
    if "diff" in k: return "差分"
    return k
INTENT_ZH={"diagnostic":"诊断排查","lab_guidance":"实验指导","concept_tutor":"概念讲解","mixed":"混合"}
ERRTAG_ZH={"MISSING_COMPONENT":"缺失元件","FLOATING_CONNECTION":"悬空连接","WRONG_NODE_CONNECTION":"节点错接","INCOMPLETE_CIRCUIT":"回路不完整","SHORT_RISK":"短路风险"}

# ---------- 图1 四模型矩阵 ----------
def fig_four_model():
    models=["未蒸馏基座","蒸馏学生 FP","蒸馏学生 INT4","教师上限"]
    avg=[66.7,64.4,71.1,92.2]; lat=[4.26,5.80,7.73,1.32]
    colors=[LIGHT,LIGHT,DARK,REF]
    fig,(a1,a2)=plt.subplots(1,2,figsize=(8.2,3.1),dpi=200)
    hbar(a1,models,avg,colors,"平均得分率 (%)",xpad=1.5,xmax=100)
    hbar(a2,models,lat,colors,"单题平均生成时延 (s)",fmt="{:.2f}",xpad=max(lat)*0.02,xmax=max(lat)*1.25)
    fig.tight_layout(w_pad=2.5); fig.savefig("board_data/p0_four_model_matrix.png",bbox_inches="tight",facecolor="white"); plt.close(fig)

# ---------- 图2 P0.5 量化对比 ----------
def fig_p05():
    d=jload("p0_5_fp_vs_int4_quality_summary.json")
    fp=d["fp"]; it=d["int4"]
    fig,(a1,a2)=plt.subplots(1,2,figsize=(8.2,3.2),dpi=200)
    groups=["平均得分率","通过率","满分率"]
    vgroup(a1,groups,[("FP",LIGHT,[fp["avg_score_pct"],fp["pass_rate_pct"],fp["full_score_rate_pct"]]),
                      ("INT4",DARK,[it["avg_score_pct"],it["pass_rate_pct"],it["full_score_rate_pct"]])],
           "","百分比 (%)",ymax=110)
    vbar(a2,["FP","INT4"],[fp["avg_latency_s"],it["avg_latency_s"]],[LIGHT,DARK],"单题平均生成时延 (s)",fmt="{:.2f}")
    fig.tight_layout(w_pad=2.5); fig.savefig("board_data/p0_5_fp_vs_int4.png",bbox_inches="tight",facecolor="white"); plt.close(fig)

# ---------- 图3 P0 部署版 INT4 质量 ----------
def fig_p0_quality():
    d=jload("p0_student_eval_final_manual_summary.json")
    ov=d["overall"]; bi=d["by_intent"]
    fig,(a1,a2)=plt.subplots(1,2,figsize=(8.2,3.2),dpi=200)
    vbar(a1,["平均得分率","通过率","满分率"],
         [ov["avg_score_pct"],ov["pass_rate_pct"],ov["full_score_rate_pct"]],
         [DARK,DARK,DARK],"百分比 (%)",ymax=110)
    order=["concept_tutor","mixed","lab_guidance","diagnostic"]
    order=[k for k in order if k in bi]
    labels=[INTENT_ZH.get(k,k) for k in order]
    vals=[bi[k]["avg_score_pct"] for k in order]
    cols=[DARK if v==max(vals) else LIGHT for v in vals]
    vbar(a2,labels,vals,[LIGHT]*len(vals),"按意图平均得分率 (%)",ymax=110)
    fig.tight_layout(w_pad=2.5); fig.savefig("board_data/p0_quality_stats.png",bbox_inches="tight",facecolor="white"); plt.close(fig)

# ---------- 图4 双教师互补 ----------
def fig_dual():
    d=jload("dual_teacher_stats.json")["overlap"]
    fig,(a1,a2)=plt.subplots(1,2,figsize=(8.2,3.2),dpi=200)
    vbar(a1,["DeepSeek","Qwen","并行候选池"],
         [d["deepseek_usable_rate_pct"],d["qwen_usable_rate_pct"],d["pooled_usable_rate_pct"]],
         [LIGHT,LIGHT,DARK],"高纯可用覆盖率 (%)",ymax=100)
    vbar(a2,["双教师共有","仅DeepSeek","仅Qwen","均不可用"],
         [d["both_usable_rate_pct"],d["deepseek_only_rate_pct"],d["qwen_only_rate_pct"],d["neither_rate_pct"]],
         [DARK,LIGHT,LIGHT,REF],"候选池组成占比 (%)",ymax=55)
    fig.tight_layout(w_pad=2.5); fig.savefig("board_data/dual_teacher_stats.png",bbox_inches="tight",facecolor="white"); plt.close(fig)

# ---------- 图5 SFT 数据分布 ----------
def fig_dataset():
    d=jload("distill_dataset_stats.json")
    fig,axs=plt.subplots(2,2,figsize=(8.4,6.0),dpi=200)
    # 漏斗
    fn=d["funnel"]; fl=["候选","高纯教师","正式SFT"]; fv=[s["count"] for s in fn]
    vbar(axs[0,0],fl,fv,[LIGHT,LIGHT,DARK],"样本数",ymax=max(fv)*1.18,fmt="{:.0f}")
    axs[0,0].set_title("筛样漏斗",fontsize=11)
    # 意图
    it=d["intents"]; il=[INTENT_ZH.get(x["key"],x["key"]) for x in it]; iv=[x["count"] for x in it]
    vbar(axs[0,1],il,iv,[LIGHT]*len(iv),"样本数",ymax=max(iv)*1.18,fmt="{:.0f}")
    axs[0,1].set_title("意图分布",fontsize=11)
    # 场景
    sc=d["scenes"]; sl=[scene_zh(x.get("key",x.get("label",""))) for x in sc]; sv=[x["count"] for x in sc]
    vbar(axs[1,0],sl,sv,[LIGHT]*len(sv),"样本数",ymax=max(sv)*1.18,fmt="{:.0f}")
    axs[1,0].set_title("场景分布",fontsize=11)
    # 错误标签
    et=d["error_tags"]; el=[ERRTAG_ZH.get(x.get("label",""),x.get("label","")) for x in et]; ev=[x["count"] for x in et]
    vbar(axs[1,1],el,ev,[LIGHT]*len(ev),"样本数",ymax=max(ev)*1.18,fmt="{:.0f}")
    axs[1,1].set_title("主要错误标签",fontsize=11)
    for ax in axs.flat:
        ax.tick_params(axis="x",labelsize=9)
    fig.tight_layout(h_pad=2.0,w_pad=2.5); fig.savefig("board_data/distill_dataset_stats.png",bbox_inches="tight",facecolor="white"); plt.close(fig)

fig_four_model(); print("ok four_model")
fig_p05(); print("ok p0_5")
fig_p0_quality(); print("ok p0_quality")
fig_dual(); print("ok dual_teacher")
fig_dataset(); print("ok dataset")
print("ALL DONE")
