import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Polygon
import numpy as np, os

OUT = os.path.dirname(os.path.abspath(__file__))
os.makedirs(OUT, exist_ok=True)
INK, SOFT, BLUE, ORANGE, RED, GREY, PAPER, AMBER = "#1C2B2A", "#4A5654", "#1F6F8B", "#C2611F", "#B23A3A", "#8A9390", "#F6F4EE", "#B9770E"
plt.rcParams.update({"font.family": "Inter", "font.size": 11, "text.color": INK, "axes.edgecolor": GREY,
                     "axes.labelcolor": SOFT, "xtick.color": SOFT, "ytick.color": SOFT})

def canvas(w=9, h=4.2):
    fig, ax = plt.subplots(figsize=(w, h), dpi=200)
    ax.set_xlim(0, 100); ax.set_ylim(0, 100 * h / w); ax.axis("off")
    return fig, ax

def box(ax, cx, cy, w, h, title, sub=None, fc="white", ec=GREY, lw=1.5, ls="-", bold=True):
    ax.add_patch(FancyBboxPatch((cx - w/2, cy - h/2), w, h, boxstyle="round,pad=0,rounding_size=1.2",
                                fc=fc, ec=ec, lw=lw, ls=ls))
    if sub:
        ax.text(cx, cy + 1.3, title, ha="center", va="center", fontsize=11.5, weight="bold" if bold else "normal")
        ax.text(cx, cy - 2.2, sub, ha="center", va="center", fontsize=9, color=SOFT)
    else:
        ax.text(cx, cy, title, ha="center", va="center", fontsize=11.5, weight="bold" if bold else "normal")

def arrow(ax, p, q, color=GREY, lw=1.6, ls="-", rad=0.0):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=14, color=color, lw=lw, ls=ls,
                                 connectionstyle=f"arc3,rad={rad}", shrinkA=0, shrinkB=0))

def save(fig, name):
    fig.savefig(f"{OUT}/{name}.png", bbox_inches="tight", facecolor="white", pad_inches=0.15)
    plt.close(fig)

# ---------------------------------------------------------------- 00 layers
fig, ax = canvas(9, 4.2)
layers = [("Protected areas", "polygons + year", BLUE), ("Roads, population, elevation", "covariates", GREY),
          ("Forest loss", "one layer per year", ORANGE), ("Forest in 2000", "share of each cell", "#3E7D4F")]
for i, (t, s, c) in enumerate(layers):
    y = 8 + i * 8.5
    poly = Polygon([[2, y], [26, y], [33, y + 6], [9, y + 6]], closed=True, fc=c, alpha=0.18, ec=c, lw=1.5)
    ax.add_patch(poly)
    ax.text(35, y + 3, t, va="center", fontsize=10.5, weight="bold")
    ax.text(35, y - 0.2, s, va="center", fontsize=8.5, color=SOFT)
arrow(ax, (62, 21), (69, 21), INK, 2)
ax.text(65.5, 24, "1 km grid", ha="center", fontsize=8.5, color=SOFT)
cols = ["cell", "forest", "loss", "PA", "road"]
for j, c in enumerate(cols):
    ax.text(74 + j * 5.5, 34, c, ha="center", fontsize=8, weight="bold")
for r in range(5):
    y = 30 - r * 4.2
    ax.plot([71, 99], [y + 2, y + 2], color="#DDD9CF", lw=0.8)
    vals = [str(r + 1), f"{0.9 - r*0.05:.2f}", f"{0.02 + r*0.03:.2f}", "1" if r < 2 else "0", f"{3 + r*4}"]
    for j, v in enumerate(vals):
        ax.text(74 + j * 5.5, y, v, ha="center", fontsize=8, color=SOFT)
ax.text(85, 6, "one row per cell", ha="center", fontsize=9, color=SOFT)
save(fig, "00_layers")

# ---------------------------------------------------------------- 01 DAG
fig, ax = canvas(9, 4.2)
box(ax, 50, 35, 22, 7, "Remoteness", "far from roads & towns")
box(ax, 18, 14, 22, 7, "Protected area", fc="#E2EEF2", ec=BLUE, lw=2)
box(ax, 82, 14, 22, 7, "Forest loss", fc="#FBEADF", ec=ORANGE, lw=2)
box(ax, 50, 5, 26, 7.5, "Unobserved U", "e.g. land speculation", fc="#F7E4E1", ec=RED, ls="--")
arrow(ax, (40, 31.5), (24, 17.6), INK)
arrow(ax, (60, 31.5), (76, 17.6), INK)
arrow(ax, (29, 14), (71, 14), BLUE, 2.4)
ax.text(50, 16.3, "causal effect we want", ha="center", fontsize=9, color=BLUE, weight="bold")
arrow(ax, (37, 6), (23, 10.4), RED, 1.4, "--")
arrow(ax, (63, 6), (77, 10.4), RED, 1.4, "--")
ax.text(26, 26, "backdoor path:\nparks are placed\nin remote land…", ha="center", fontsize=8.5, color=SOFT)
ax.text(74, 26, "…which is cleared\nless anyway", ha="center", fontsize=8.5, color=SOFT)
save(fig, "01_dag")

# ---------------------------------------------------------------- 02 DiD
fig, ax = plt.subplots(figsize=(9, 4.2), dpi=200)
t0, t1 = 0, 1
ax.plot([t0, t1], [0.6, 0.85], color=ORANGE, lw=3, marker="o", ms=8)
ax.plot([t0, t1], [0.3, 0.55], color=BLUE, lw=2, ls="--", marker="o", ms=8, mfc="white")
ax.plot([t0, t1], [0.3, 0.38], color=BLUE, lw=3, marker="o", ms=8)
ax.axvline(0.5, color=GREY, ls=":", lw=1.2)
ax.annotate("", xy=(1.06, 0.38), xytext=(1.06, 0.55), arrowprops=dict(arrowstyle="<->", color=INK, lw=1.6))
ax.text(1.09, 0.465, "DiD effect", va="center", fontsize=11, weight="bold")
ax.text(-0.04, 0.6, "Never protected", ha="right", va="center", fontsize=10.5, color=ORANGE, weight="bold")
ax.text(-0.04, 0.3, "Protected later", ha="right", va="center", fontsize=10.5, color=BLUE, weight="bold")
ax.text(1.03, 0.6, "if never protected\n(parallel trend)", va="center", fontsize=9, color=SOFT)
ax.text(0.5, 0.95, "designation", ha="center", fontsize=9, color=SOFT)
ax.set_xticks([0, 1], ["before\n2001–2005", "after\n2013–2023"]); ax.set_yticks([])
ax.set_ylabel("Forest loss per year")
ax.set_xlim(-0.45, 1.4); ax.set_ylim(0.2, 1.0)
for s in ["top", "right"]: ax.spines[s].set_visible(False)
save(fig, "04_did")

# ---------------------------------------------------------------- 03 RD
rng = np.random.default_rng(4)
fig, ax = plt.subplots(figsize=(9, 4.2), dpi=200)
xo = rng.uniform(-10, 0, 70); xi = rng.uniform(0, 10, 70)
yo = 0.55 + 0.012 * xo + rng.normal(0, 0.05, 70); yi = 0.30 - 0.008 * xi + rng.normal(0, 0.05, 70)
ax.scatter(xo, yo, s=18, color=ORANGE, alpha=0.55); ax.scatter(xi, yi, s=18, color=BLUE, alpha=0.55)
ax.plot([-10, 0], [0.43, 0.55], color=ORANGE, lw=3); ax.plot([0, 10], [0.30, 0.22], color=BLUE, lw=3)
ax.axvline(0, color=INK, ls="--", lw=1.4)
ax.annotate("", xy=(0.4, 0.30), xytext=(0.4, 0.55), arrowprops=dict(arrowstyle="<->", color=INK, lw=1.6))
ax.text(0.9, 0.44, "effect at\nthe boundary", fontsize=10.5, weight="bold", va="center")
ax.text(-9.5, 0.72, "outside the park", fontsize=10.5, color=ORANGE, weight="bold")
ax.text(5.5, 0.42, "inside the park", fontsize=10.5, color=BLUE, weight="bold")
ax.text(0, 0.8, "park boundary", ha="center", fontsize=9, color=SOFT)
ax.set_xlabel("Distance to the park boundary (km): − outside, + inside")
ax.set_ylabel("Forest loss 2006–2023"); ax.set_yticks([]); ax.set_ylim(0.05, 0.85)
for s in ["top", "right"]: ax.spines[s].set_visible(False)
save(fig, "02_rd")

# ---------------------------------------------------------------- 04 matching
fig, ax = canvas(9, 4.2)
ax.text(2, 33, "Protected cells", fontsize=11, weight="bold", color=BLUE)
ax.text(2, 17, "Unprotected cells", fontsize=11, weight="bold", color=ORANGE)
prot = [55, 63, 71, 79, 86]; used = [56, 62.5, 72, 78, 87.5]
near = [8, 13, 18, 23, 28, 33, 38, 43, 48]
for a, b in zip(prot, used):
    ax.plot([a, b], [27.5, 13.5], color=BLUE, ls=":", lw=1.4)
for a in prot: ax.add_patch(plt.Circle((a, 28.5), 1.5, color=BLUE))
ax.add_patch(plt.Circle((94, 28.5), 1.5, fc="white", ec=BLUE, lw=1.5))
ax.text(94, 32.5, "no match:\ndropped", ha="center", fontsize=8, color=SOFT)
for a in near: ax.add_patch(plt.Circle((a, 12.5), 1.5, color=ORANGE, alpha=0.22))
for a in used: ax.add_patch(plt.Circle((a, 12.5), 1.5, color=ORANGE))
arrow(ax, (4, 5), (97, 5), GREY, 1.4)
ax.text(4, 1.5, "near roads & cleared land", fontsize=8.5, color=SOFT)
ax.text(97, 1.5, "remote", fontsize=8.5, color=SOFT, ha="right")
ax.text(28, 8, "faded: no protected look-alike, left out", fontsize=8.5, color=SOFT, ha="center")
save(fig, "03_matching")
print(sorted(os.listdir(OUT)))
