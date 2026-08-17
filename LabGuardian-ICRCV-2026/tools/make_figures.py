# -*- coding: utf-8 -*-
"""Re-export paper figures with English annotation.

Panels are rasterized from the project figures in figures/cadx/ at high
resolution, cropped, and recomposed with English labels so that the
manuscript contains no non-English text.  The power figure is redrawn
directly from the measurement log in source-material/board_data/.
"""
import csv, json, os, subprocess, sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle
from matplotlib.lines import Line2D
from PIL import Image, ImageEnhance, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CADX = os.path.join(ROOT, "figures", "cadx")
OUT = os.path.join(ROOT, "figures", "en")
TMP = os.path.join(OUT, "_raster")
DATA = os.path.join(ROOT, "source-material", "board_data")
# Source pages are rasterized well above the final print resolution so that the
# vector overlays stay crisp, and figures are saved at 600 dpi: matplotlib
# resamples every image to axes_size x savefig_dpi, so the default 100 dpi would
# throw away almost all of the photographic detail.
RASTER_DPI = 800
SAVE_DPI = 600

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Nimbus Roman", "DejaVu Serif"],
    "font.size": 8,
    "axes.linewidth": 0.7,
    "axes.spines.right": False,
    "axes.spines.top": False,
    "pdf.fonttype": 42,
    "savefig.dpi": SAVE_DPI,
    "figure.dpi": SAVE_DPI,
})


def raster(name):
    os.makedirs(TMP, exist_ok=True)
    stem = os.path.join(TMP, name)
    png = stem + "-1.png"
    if not os.path.exists(png):
        subprocess.run(["pdftoppm", "-png", "-r", str(RASTER_DPI), "-f", "1", "-l", "1",
                        os.path.join(CADX, name + ".pdf"), stem], check=True)
    return Image.open(png).convert("RGB")


def crop(im, x0, x1, y0, y1):
    w, h = im.size
    return im.crop((int(x0 * w), int(y0 * h), int(x1 * w), int(y1 * h)))


def enhance(im, radius=1.6, percent=85, contrast=1.06):
    """Counteract the softness introduced by rasterizing and resampling."""
    im = im.filter(ImageFilter.UnsharpMask(radius=radius, percent=percent,
                                           threshold=3))
    return ImageEnhance.Contrast(im).enhance(contrast)


def panel(ax, im, label, sub=None):
    ax.imshow(im, interpolation="antialiased")
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(True); s.set_linewidth(0.5); s.set_color("#555555")
    title = label if sub is None else f"{label} {sub}"
    ax.set_title(title, fontsize=8, pad=3)


# ---------------------------------------------------------------- figure: e2e
def fig_reconstruction():
    im = raster("e2e_triptych")
    a = enhance(crop(im, 0.006, 0.492, 0.004, 0.452))
    b = enhance(crop(im, 0.508, 0.997, 0.004, 0.452))
    c = enhance(crop(im, 0.006, 0.492, 0.492, 0.950), percent=70)

    fig = plt.figure(figsize=(7.0, 2.55))
    gs = fig.add_gridspec(1, 4, width_ratios=[1, 1, 1, 0.62], wspace=0.06,
                          left=0.005, right=0.995, top=0.90, bottom=0.02)
    panel(fig.add_subplot(gs[0]), a, "(a)", "board observation")
    panel(fig.add_subplot(gs[1]), b, "(b)", "component instances")
    panel(fig.add_subplot(gs[2]), c, "(c)", "pin-level structure")

    lax = fig.add_subplot(gs[3]); lax.axis("off")
    handles = [
        Rectangle((0, 0), 1, 1, fc="none", ec="#7B4EA8", lw=1.2, label="integrated package"),
        Rectangle((0, 0), 1, 1, fc="none", ec="#E8890C", lw=1.2, label="jumper wire"),
        Rectangle((0, 0), 1, 1, fc="none", ec="#2E86C1", lw=1.2, label="resistor"),
        Line2D([], [], marker="o", ls="none", mfc="#FFD93B", mec="#333333", ms=5,
               label="terminal keypoint"),
        Line2D([], [], marker="o", ls="none", mfc="white", mec="#333333", ms=5,
               label="component node"),
        Line2D([], [], color="#555555", lw=1.0, label="component-to-pin link"),
    ]
    lax.legend(handles=handles, loc="center left", frameon=False, fontsize=7.2,
               handlelength=1.5, borderpad=0.2, labelspacing=0.75)
    fig.savefig(os.path.join(OUT, "reconstruction.pdf"))
    plt.close(fig)


# ----------------------------------------------------------- figure: ambiguity
def fig_ambiguity():
    im = raster("ambiguity")
    a = enhance(crop(im, 0.020, 0.470, 0.105, 0.965), radius=2.0, percent=110)
    b = enhance(crop(im, 0.526, 0.976, 0.105, 0.965), radius=2.0, percent=110)

    fig = plt.figure(figsize=(3.45, 1.62))
    gs = fig.add_gridspec(1, 2, wspace=0.05, left=0.005, right=0.995,
                          top=0.88, bottom=0.02)
    axa = fig.add_subplot(gs[0]); panel(axa, a, "(a)", "candidate holes")
    axb = fig.add_subplot(gs[1]); panel(axb, b, "(b)", "confirmed hole")

    # The project figure carries two non-English callouts; their positions were
    # measured on the rasterized panels and are masked and relabeled here.
    def relabel(ax, im, box, text):
        w, h = im.size
        x0, x1, y0, y1 = box
        ax.add_patch(Rectangle((x0 * w, y0 * h), (x1 - x0) * w, (y1 - y0) * h,
                               fc="white", ec="none", zorder=3))
        ax.text(0.5 * (x0 + x1) * w, 0.5 * (y0 + y1) * h, text, ha="center",
                va="center", fontsize=6.0, zorder=4)

    relabel(axa, a, (0.555, 0.990, 0.175, 0.285), "detected keypoint")
    relabel(axb, b, (0.425, 0.760, 0.460, 0.550), "locked")
    fig.savefig(os.path.join(OUT, "ambiguity.pdf"))
    plt.close(fig)


# ------------------------------------------------------------- figure: netlist
def fig_netlist():
    im = raster("netlist_info")
    a = enhance(crop(im, 0.052, 0.446, 0.078, 0.672))
    b = crop(im, 0.500, 0.985, 0.092, 0.665)

    fig = plt.figure(figsize=(7.0, 2.55))
    gs = fig.add_gridspec(1, 2, width_ratios=[1, 1.18], wspace=0.05,
                          left=0.005, right=0.995, top=0.90, bottom=0.02)
    panel(fig.add_subplot(gs[0]), a, "(a)", "hole-level assignment")
    panel(fig.add_subplot(gs[1]), b, "(b)", "component-net graph")
    fig.savefig(os.path.join(OUT, "netlist.pdf"))
    plt.close(fig)


# --------------------------------------------------------------- figure: power
LABELS = {"CPU_workload": "CPU INT8", "GPU_workload": "iGPU INT8",
          "NPU_workload": "NPU INT8"}


def fig_power():
    rows = list(csv.DictReader(open(os.path.join(DATA, "yolo_power_timeseries.csv"))))
    phases = json.load(open(os.path.join(DATA, "yolo_power_phases.json")))["phases"]
    # The sampler wrote a nominal 0.5 s step, whereas turbostat sampled every
    # 0.25 s; the time base is therefore rebuilt from the recorded phase log so
    # that the samples and the phase boundaries share one clock.
    itv = phases[-1]["end_s"] / len(rows)
    ts = [i * itv for i in range(len(rows))]
    pkg = [float(r["PkgWatt"]) for r in rows]
    cor = [float(r["CorWatt"]) for r in rows]
    gfx = [float(r["GFXWatt"]) for r in rows]

    fig, ax = plt.subplots(figsize=(3.45, 2.0))
    for ph in phases:
        if ph["name"] in LABELS:
            ax.axvspan(ph["start_s"], ph["end_s"], color="#efefef", zorder=0)
            seg = [(t, p) for t, p in zip(ts, pkg)
                   if ph["start_s"] <= t <= ph["end_s"]]
            pt, pw = max(seg, key=lambda x: x[1])
            ax.text(0.5 * (ph["start_s"] + ph["end_s"]), 36.4,
                    LABELS[ph["name"]], ha="center", fontsize=6.6, color="#222222")
            ax.annotate(f"{pw:.1f} W", xy=(pt, pw), xytext=(pt, pw + 2.2),
                        ha="center", fontsize=6.4, color="#111111",
                        arrowprops=dict(arrowstyle="-", lw=0.5, color="#666666"))
    ax.plot(ts, pkg, color="#111111", lw=0.9, label="package", zorder=3)
    ax.plot(ts, cor, color="#666666", lw=0.7, ls="--", label="CPU cores", zorder=2)
    ax.plot(ts, gfx, color="#999999", lw=0.7, ls=":", label="iGPU", zorder=2)
    ax.axhline(4.4, color="#aaaaaa", lw=0.6, ls="-.")
    ax.text(ts[-1], 5.0, "idle 4.4 W", ha="right", fontsize=6.2, color="#666666")
    ax.set_xlabel("Time (s)"); ax.set_ylabel("Package power (W)")
    ax.set_xlim(0, ts[-1]); ax.set_ylim(0, 40)
    ax.legend(frameon=False, fontsize=6.6, loc="center right",
              handlelength=1.6, borderaxespad=0.4)
    fig.tight_layout(pad=0.25)
    fig.savefig(os.path.join(OUT, "power.pdf"))
    plt.close(fig)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    fig_reconstruction(); fig_ambiguity(); fig_netlist(); fig_power()
    print("written to", OUT)
