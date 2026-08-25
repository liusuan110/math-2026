"""Render the cropped, paper-ready failure-case triptych.

Solid boxes come directly from the saved S1 API responses. Dashed red boxes are
manual visual callouts for expected objects that S1 missed; they are qualitative
annotations, not benchmark ground truth.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from PIL import Image


ROOT = Path(__file__).resolve().parent
RAW = ROOT / "raw"
IMAGES = ROOT / "images"
FIGURES = ROOT / "figures"
FIGURES.mkdir(parents=True, exist_ok=True)

COLORS = {
    "Resistor": "#2E6F9E",
    "Wire": "#D97706",
    "IC": "#68478D",
    "Potentiometer": "#C43C39",
}
FAILURE = "#C43C39"

CASES = [
    {
        "case_id": "board_1_summing",
        "image": "board_1_summing.jpg",
        "crop": (410, 350, 1070, 955),
        "panel": "(a)",
        "caption": "Standard view\ncomplete count; 8/28 ambiguous terminals",
    },
    {
        "case_id": "err_amp_cw",
        "image": "err_amp_cw.jpg",
        "crop": (365, 225, 965, 775),
        "panel": "(b)",
        "caption": "180° rotation\nIC and one jumper missed",
        "missed": [
            {"bbox": (615, 445, 738, 548), "label": "missed IC", "text_xy": (790, 535)},
            {"bbox": (590, 265, 630, 375), "label": "missed jumper", "text_xy": (760, 285)},
        ],
    },
    {
        "case_id": "err_amp2_portrait",
        "image": "err_amp2_portrait.jpg",
        "crop": (220, 800, 700, 1240),
        "panel": "(c)",
        "caption": "90° rotation\nresistor→potentiometer (0.30); jumper missed",
        "missed": [
            {"bbox": (255, 1018, 365, 1065), "label": "missed jumper", "text_xy": (240, 1100)},
        ],
    },
]


def load_detections(case_id: str) -> list[dict]:
    result = json.loads((RAW / f"{case_id}.json").read_text(encoding="utf-8"))
    return next(stage["data"]["detections"] for stage in result["stages"] if stage["stage"] == "detect")


def add_short_callout(ax, bbox, label: str, text_xy) -> None:
    x1, y1, x2, y2 = bbox
    ax.add_patch(
        Rectangle(
            (x1, y1),
            x2 - x1,
            y2 - y1,
            fill=False,
            ec=FAILURE,
            lw=1.25,
            ls=(0, (3, 2)),
            zorder=8,
        )
    )
    ax.annotate(
        label,
        xy=((x1 + x2) / 2, (y1 + y2) / 2),
        xytext=text_xy,
        fontsize=6.8,
        fontweight="bold",
        color=FAILURE,
        ha="left",
        va="center",
        arrowprops={"arrowstyle": "-", "color": FAILURE, "lw": 0.8},
        bbox={"boxstyle": "round,pad=0.18", "fc": "white", "ec": FAILURE, "lw": 0.55, "alpha": 0.94},
        zorder=9,
    )


plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 7.5,
        "axes.linewidth": 0.6,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    }
)

fig = plt.figure(figsize=(7.16, 3.02), dpi=220, facecolor="white")
grid = fig.add_gridspec(2, 3, height_ratios=(1.0, 0.17), hspace=0.03, wspace=0.055)

for idx, case in enumerate(CASES):
    ax = fig.add_subplot(grid[0, idx])
    image = Image.open(IMAGES / case["image"]).convert("RGB")
    ax.imshow(image, interpolation="lanczos")

    for item in load_detections(case["case_id"]):
        x1, y1, x2, y2 = item["bbox"]
        kind = item["component_type"]
        color = COLORS.get(kind, "#444444")
        critical_confusion = case["case_id"] == "err_amp2_portrait" and kind == "Potentiometer"
        ax.add_patch(
            Rectangle(
                (x1, y1),
                x2 - x1,
                y2 - y1,
                fill=False,
                ec=FAILURE if critical_confusion else color,
                lw=1.15 if critical_confusion else 0.85,
                zorder=6,
            )
        )
        if critical_confusion:
            ax.annotate(
                "R→Pot 0.30",
                xy=((x1 + x2) / 2, y1),
                xytext=(245, 955),
                fontsize=6.8,
                fontweight="bold",
                color=FAILURE,
                arrowprops={"arrowstyle": "-", "color": FAILURE, "lw": 0.8},
                bbox={"boxstyle": "round,pad=0.18", "fc": "white", "ec": FAILURE, "lw": 0.55, "alpha": 0.94},
                zorder=9,
            )

    for missed in case.get("missed", []):
        add_short_callout(ax, missed["bbox"], missed["label"], missed["text_xy"])

    left, top, right, bottom = case["crop"]
    ax.set_xlim(left, right)
    ax.set_ylim(bottom, top)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_color("#4A4A4A")
        spine.set_linewidth(0.65)

    ax.text(
        0.025,
        0.965,
        case["panel"],
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=8.5,
        fontweight="bold",
        color="#111111",
        bbox={"boxstyle": "square,pad=0.16", "fc": "white", "ec": "none", "alpha": 0.88},
        zorder=10,
    )

    caption_ax = fig.add_subplot(grid[1, idx])
    caption_ax.axis("off")
    caption_ax.text(0.5, 0.92, case["caption"], ha="center", va="top", fontsize=7.3, linespacing=1.18, color="#202020")

legend = [
    Line2D([0], [0], color=COLORS["Resistor"], lw=1.6, label="resistor"),
    Line2D([0], [0], color=COLORS["Wire"], lw=1.6, label="jumper"),
    Line2D([0], [0], color=COLORS["IC"], lw=1.6, label="IC"),
    Line2D([0], [0], color=FAILURE, lw=1.4, ls=(0, (3, 2)), label="missed / confused"),
]
fig.legend(
    handles=legend,
    loc="lower center",
    bbox_to_anchor=(0.5, -0.015),
    ncol=4,
    frameon=False,
    fontsize=7.2,
    handlelength=2.1,
    columnspacing=1.4,
)

fig.subplots_adjust(left=0.012, right=0.995, top=0.99, bottom=0.145)
png = FIGURES / "recognition_failure_triptych_v2.png"
pdf = FIGURES / "recognition_failure_triptych_v2.pdf"
fig.savefig(png, dpi=600, facecolor="white")
fig.savefig(pdf, dpi=600, facecolor="white")
plt.close(fig)
print(png)
print(pdf)
