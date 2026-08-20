# -*- coding: utf-8 -*-
"""Re-export paper figures with English annotation.

Panels are rasterized from the project figures in figures/cadx/ at high
resolution, cropped, and recomposed with English labels so that the
manuscript contains no non-English text.  The power figure is redrawn
directly from the measurement log in source-material/board_data/.
"""
import csv, json, math, os, subprocess, sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import (Circle, FancyArrowPatch, FancyBboxPatch,
                                Rectangle, Wedge)
from matplotlib.lines import Line2D
from matplotlib.path import Path
from matplotlib.patches import PathPatch
from matplotlib.transforms import Affine2D
from PIL import Image, ImageEnhance, ImageFilter
import matplotlib.patheffects as pe

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
    "mathtext.fontset": "stix",
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
               label="component instance"),
        Line2D([], [], color="#555555", lw=1.0, label="terminal association"),
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
# Both panels are generated from one pipeline run stored under
# source-material/board_run/, so the photograph overlay, the net colouring and
# the graph cannot drift apart from the reconstruction they illustrate.
RUN_JSON = os.path.join(ROOT, "source-material", "board_run",
                        "inverting_amp_pipeline_result.json")
RUN_IMG = os.path.join(ROOT, "source-material", "board_run",
                       "inverting_amp_board.jpg")
CROP = (470, 620, 2230, 1870)      # board region of the 4032x3024 photograph

NET_PALETTE = ["#3B6FB6", "#C47A1C", "#3E8E72", "#8A6FA8", "#A77B24",
               "#4E8F98", "#B85450", "#7B6B62", "#526A78", "#6E8B5B"]
TYPE_COL = {"Resistor": "#263238", "Wire": "#263238", "IC": "#263238"}
PART = "#263238"
INK, WIRE, BODY = "#202428", "#7B8288", "#F7F8F8"
WIRE_LW, PIN_LW = 1.35, 1.05
NET_R = 0.39                       # net node radius
RES_L, RES_W = 0.70, 0.27          # resistor body along / across an edge
IC_W, IC_H = 2.2, 1.05             # half-width / half-height of the package
CORNER_R = 0.38                    # fillet radius at a direction change

# Hand-placed positions keyed to the net ids emitted by the run.  Package
# neighbours follow pin order, which keeps the drawing planar; only the second
# link of the supply net runs on the outer face.
NETS = {                           # net_id: (x, y, label)
    "NET_009": (-2.3, -2.5, "N9"), "NET_006": (-4.2, -3.2, "N6"),
    "NET_007": (-2.2, -4.4, "N7"), "NET_004": (0.5, -5.4, "N4"),
    "NET_012": (2.6, -2.2, "N12"), "NET_005": (4.4, -3.4, "N5"),
    "NET_010": (1.4, 2.6, "N10"), "NET_008": (3.4, 3.4, "N8"),
    "NET_003": (3.0, -5.6, "N3"), "NET_002": (5.0, -5.6, "N2"),
}
STRAIGHT = [("R1", "NET_006", "NET_009"), ("R2", "NET_009", "NET_007"),
            ("R3", "NET_008", "NET_010"), ("R4", "NET_012", "NET_005"),
            ("R5", "NET_002", "NET_003"), ("R6", "NET_003", "NET_004")]
PIN_STRAIGHT = {2: "NET_009", 3: "NET_004", 4: "NET_012", 6: "NET_010"}
PIN_ROUTED = {7: ("NET_004", [(-0.5, 2.2), (-5.4, 2.2), (-5.4, -5.4)])}
PIN_NC = (1, 5, 8)
MERGE_TAGS = {"NET_004": ("W2, W3, W5", (1.35, 0.62)),
              "NET_010": ("W1, W4", (-1.25, 0.30))}
ROLE_OFFSET = {"NET_010": (-1.05, -0.04)}  # keep the tag off the pin-5 stub


def _load_run():
    r = json.load(open(RUN_JSON, encoding="utf-8"))
    nl = r["stages"]["topology"]["netlist_v2"]
    net_by_node = {nd: n["electrical_net_id"]
                   for n in nl["nets"] for nd in n["member_node_ids"]}
    roles = {n["electrical_net_id"]: (n.get("power_role") or "")
             for n in nl["nets"]}
    colour = {nid: NET_PALETTE[i % len(NET_PALETTE)]
              for i, nid in enumerate(sorted(roles))}
    return r, net_by_node, roles, colour


def _mst_edges(pts):
    """Minimum spanning tree over a net's pins, so links stay local."""
    if len(pts) < 2:
        return []
    used, rest, out = [0], list(range(1, len(pts))), []
    while rest:
        best = min(((i, j) for i in used for j in rest),
                   key=lambda e: math.dist(pts[e[0]], pts[e[1]]))
        out.append((pts[best[0]], pts[best[1]]))
        used.append(best[1]); rest.remove(best[1])
    return out


def _panel_board(ax, run, net_by_node, colour):
    im = Image.open(RUN_IMG).convert("RGB").crop(CROP)
    im = enhance(im, radius=2.0, percent=70)
    im = ImageEnhance.Color(im).enhance(0.72)
    ax.imshow(im, interpolation="antialiased")
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(True); s.set_linewidth(0.5); s.set_color("#555555")
    ox, oy = CROP[0], CROP[1]

    pins, per_net, pin_xy = [], {}, {}
    for c in run["stages"]["mapping"]["components"]:
        for p in c["pins"]:
            k = next((o.get("keypoint") for o in p.get("observations", [])
                      if o.get("keypoint")), None)
            if not k:
                continue
            nid = net_by_node.get(p.get("electrical_node_id") or "")
            xy = (k[0] - ox, k[1] - oy)
            pins.append((xy, nid, bool(p.get("is_ambiguous"))))
            pin_xy[(c["component_id"], p["pin_name"])] = xy
            if nid:
                per_net.setdefault(nid, []).append(xy)

    for nid, pts in per_net.items():                   # net membership
        for a, b in _mst_edges(pts):
            ax.plot([a[0], b[0]], [a[1], b[1]], color=colour[nid], lw=0.8,
                    alpha=0.7, zorder=3, solid_capstyle="round")

    halo = [pe.withStroke(linewidth=1.6, foreground="white")]
    for c in run["stages"]["mapping"]["components"]:
        x0, y0, x1, y1 = c["bbox"]
        col = TYPE_COL.get(c["component_type"], "#263238")
        if c["component_type"] != "Wire":              # wire boxes only add noise
            ax.add_patch(Rectangle((x0 - ox, y0 - oy), x1 - x0, y1 - y0,
                                   fc="none", ec=col, lw=0.7, alpha=0.75,
                                   zorder=4))
            lx, ly = (x0 + x1) / 2 - ox, y0 - oy - 8
        else:
            continue                                   # omit wire IDs in print
        ax.text(lx, ly, c["component_id"], fontsize=5.2, color=col, zorder=7,
                ha="center", va="bottom", fontweight="bold", path_effects=halo)

    for xy, nid, amb in pins:
        ax.add_patch(Circle(xy, 7.0, fc=colour.get(nid, "#F2F2F2"),
                            ec="#333333" if nid is None else "white", lw=0.8,
                            zorder=5))
        if amb:
            ax.add_patch(Circle(xy, 14, fc="none", ec="#B3261E", lw=0.9,
                                ls=(0, (2.2, 1.8)), zorder=6))
    ax.set_title("(a) Image-space pin-to-hole assignments", fontsize=8,
                 fontweight="bold", loc="left", pad=4)


def _pin_xy(pin):
    """DIP anchor: pins 1-4 left to right along the bottom edge, 5-8 right to
    left along the top edge, as on a package straddling the trench."""
    if pin <= 4:
        return -1.5 + (pin - 1) * 1.0, -IC_H
    return 1.5 - (pin - 5) * 1.0, IC_H


def _resistor(ax, x, y, ang, label, side=1):
    body = Rectangle((-RES_L / 2, -RES_W / 2), RES_L, RES_W, fc="white",
                     ec=PART, lw=0.95, joinstyle="miter", zorder=6)
    body.set_transform(Affine2D().rotate(ang).translate(x, y) + ax.transData)
    ax.add_patch(body)
    nx, ny = -math.sin(ang), math.cos(ang)
    if (ny < 0) != (side < 0):
        nx, ny = -nx, -ny
    ax.text(x + nx * 0.52, y + ny * 0.52, f"${label[0]}_{{{label[1:]}}}$",
            ha="center", va="center", fontsize=6.7, color=PART, zorder=7)


def _link(ax, p0, p1, lw=WIRE_LW):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-", shrinkA=0, shrinkB=0,
                                 lw=lw, color=WIRE, capstyle="round", zorder=1))


def _route(ax, pts, lw=PIN_LW):
    """Straight runs joined by small fillets: no free-form arcs."""
    verts, codes = [pts[0]], [Path.MOVETO]
    for i in range(1, len(pts) - 1):
        (px, py), (vx, vy), (nx_, ny_) = pts[i - 1], pts[i], pts[i + 1]
        d1, d2 = math.dist(pts[i - 1], pts[i]), math.dist(pts[i], pts[i + 1])
        r = min(CORNER_R, 0.45 * d1, 0.45 * d2)
        verts += [(vx - (vx - px) / d1 * r, vy - (vy - py) / d1 * r),
                  (vx, vy),
                  (vx + (nx_ - vx) / d2 * r, vy + (ny_ - vy) / d2 * r)]
        codes += [Path.LINETO, Path.CURVE3, Path.CURVE3]
    verts.append(pts[-1]); codes.append(Path.LINETO)
    ax.add_patch(PathPatch(Path(verts, codes), fc="none", ec=WIRE, lw=lw,
                           capstyle="round", joinstyle="round", zorder=1))


def _panel_graph(ax, roles, colour):
    ax.set_xlim(-6.1, 5.9); ax.set_ylim(-6.6, 4.1)
    ax.set_aspect("equal"); ax.axis("off")
    ax.set_title("(b) Derived component-net graph", fontsize=8,
                 fontweight="bold", loc="left", pad=4)

    for label, u, v in STRAIGHT:                       # two-terminal parts
        (x0, y0, _), (x1, y1, _) = NETS[u], NETS[v]
        _link(ax, (x0, y0), (x1, y1))
        _resistor(ax, (x0 + x1) / 2, (y0 + y1) / 2,
                  math.atan2(y1 - y0, x1 - x0), label)

    for pin, nid in PIN_STRAIGHT.items():              # package fan-out
        px, py = _pin_xy(pin)
        side = -1 if pin <= 4 else 1
        _link(ax, (px, py + side * 0.22), NETS[nid][:2], lw=PIN_LW)
    for pin, (nid, way) in PIN_ROUTED.items():
        px, py = _pin_xy(pin)
        _route(ax, [(px, py + 0.22)] + way + [NETS[nid][:2]])

    ax.add_patch(FancyBboxPatch((-IC_W, -IC_H), 2 * IC_W, 2 * IC_H,
                                boxstyle="round,pad=0.02,rounding_size=0.08",
                                fc=BODY, ec=PART, lw=1.1, zorder=3))
    ax.add_patch(Wedge((-IC_W, 0), 0.26, 270, 90, fc="white", ec=PART, lw=1.0,
                       zorder=4))
    ax.text(0.0, 0.22, "IC1", ha="center", va="center", fontsize=8.2,
            fontweight="bold", color=PART, zorder=5)
    ax.text(0.0, -0.30, "DIP-8", ha="center", va="center", fontsize=6.4,
            color="#5A5A5A", zorder=5)

    for pin in range(1, 9):
        px, py = _pin_xy(pin)
        side = -1 if pin <= 4 else 1
        ax.add_patch(Rectangle((px - 0.075, py + (0.0 if side > 0 else -0.22)),
                               0.15, 0.22, fc=PART, ec="none", zorder=4))
        ax.text(px, py - side * 0.24, str(pin), ha="center", va="center",
                fontsize=6.0, color="#5A5A5A", zorder=5)
        if pin in PIN_NC:
            ax.plot([px, px], [py + side * 0.22, py + side * 0.72], color=WIRE,
                    lw=PIN_LW, ls=(0, (1.6, 1.4)), zorder=1)
            lx = px - 0.46 if pin == 1 else px
            ax.text(lx, py + side * 0.92, "n.c.", ha="center", va="center",
                    fontsize=6.2, color="#5A5A5A", zorder=5)

    for nid, (x, y, label) in NETS.items():            # nets
        ax.add_patch(Circle((x, y), NET_R, fc="white", ec=colour[nid], lw=1.55,
                            zorder=4))
        ax.text(x, y, f"${label[0]}_{{{label[1:]}}}$", ha="center", va="center",
                fontsize=6.7, color=INK, zorder=5)
        if roles.get(nid):
            dx, dy = ROLE_OFFSET.get(nid, (0.0, -NET_R - 0.30))
            ax.text(x + dx, y + dy, roles[nid], ha="center", va="center",
                    fontsize=6.0, color="#3A4750", zorder=5)
        if nid in MERGE_TAGS:
            txt, (dx, dy) = MERGE_TAGS[nid]
            ax.text(x + dx, y + dy + NET_R, f"wire merge: {txt}",
                    ha="center", va="center", fontsize=5.6, style="italic",
                    color="#6A6A6A", zorder=5)


def fig_netlist():
    run, net_by_node, roles, colour = _load_run()
    fig = plt.figure(figsize=(7.0, 2.76))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.46, 1.00], wspace=0.055,
                          left=0.006, right=0.994, top=0.905, bottom=0.025)
    _panel_board(fig.add_subplot(gs[0]), run, net_by_node, colour)
    _panel_graph(fig.add_subplot(gs[1]), roles, colour)
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
