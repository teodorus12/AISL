"""Figures for Wiremesh report (hand skeleton + serial data pipeline)."""

import os
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch

FIG_DIR = os.path.join(os.path.dirname(__file__), "figures_wiremesh")

HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (17, 18), (18, 19), (19, 20),
    (0, 17),
]
HAND_XY = np.array([
    [0.0, 0.0],
    [-0.15, 0.35], [0.15, 0.35], [0.28, 0.35], [0.38, 0.35],
    [-0.12, 0.55], [-0.12, 0.72], [-0.12, 0.88], [-0.12, 1.02],
    [0.0, 0.58], [0.0, 0.75], [0.0, 0.91], [0.0, 1.05],
    [0.12, 0.55], [0.12, 0.70], [0.12, 0.84], [0.12, 0.96],
    [0.24, 0.50], [0.30, 0.62], [0.34, 0.72], [0.36, 0.80],
])


def _save(fig, name):
    os.makedirs(FIG_DIR, exist_ok=True)
    path = os.path.join(FIG_DIR, name)
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


def fig_hand_wiremesh():
    fig, ax = plt.subplots(figsize=(8, 9))
    for a, b in HAND_CONNECTIONS:
        ax.plot([HAND_XY[a, 0], HAND_XY[b, 0]], [HAND_XY[a, 1], HAND_XY[b, 1]],
                color="#1565C0", lw=3, solid_capstyle="round", label="_")
    ax.scatter(HAND_XY[:, 0], HAND_XY[:, 1], c="#66BB6A", s=150, zorder=5, edgecolors="#1B5E20", linewidths=2)
    for i, (x, y) in enumerate(HAND_XY):
        ax.annotate(str(i), (x, y), xytext=(5, 5), textcoords="offset points", fontsize=9, fontweight="bold")
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("Wire mesh roke — 21 vozlišč, 21 robov\n(LandMarkDrawer / Serializer)", fontsize=13, fontweight="bold")
    ax.text(0.5, -0.08, "Zeleno = landmarki  |  Modro = wireframe povezave",
            transform=ax.transAxes, ha="center", fontsize=10)
    return _save(fig, "wm_01_hand_mesh.png")


def fig_mesh_vs_features():
    fig, axes = plt.subplots(1, 2, figsize=(11, 5))
    ax = axes[0]
    for a, b in HAND_CONNECTIONS:
        ax.plot([HAND_XY[a, 0], HAND_XY[b, 0]], [HAND_XY[a, 1], HAND_XY[b, 1]], "b-", lw=2)
    ax.scatter(HAND_XY[:, 0], HAND_XY[:, 1], c="limegreen", s=80)
    ax.set_title("Vizualizacija (2D wire mesh)")
    ax.axis("off")

    ax2 = axes[1]
    ax2.axis("off")
    text = (
        "Isti robovi v Serializer:\n\n"
        "• 21 kostnih vektorjev\n"
        "• normalizirana smer\n"
        "• + 21 × 3 koordinate\n"
        "• = 126-dim. vektor\n\n"
        "Mesh = topologija roke\n"
        "Feature = numerični opis"
    )
    ax2.text(0.1, 0.5, text, fontsize=12, va="center",
             bbox=dict(boxstyle="round", facecolor="#E3F2FD", edgecolor="#1565C0"))
    ax2.set_title("Povezava mesh → AI")
    fig.suptitle("Wire mesh in vektor značilnosti", fontsize=14, fontweight="bold")
    fig.tight_layout()
    return _save(fig, "wm_02_mesh_vs_features.png")


def fig_serial_pipeline():
    fig, ax = plt.subplots(figsize=(11, 6))
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 7)
    ax.axis("off")
    boxes = [
        (0.5, 5.5, "STM32\nsenzorji"),
        (2.8, 5.5, "UART\n9600 baud"),
        (5.1, 5.5, "Python\npyserial"),
        (7.4, 5.5, "BIN datoteka\nbin_folder/"),
        (0.5, 3.2, "CREATE_PACKETS\nstuffing + CRC"),
        (3.5, 3.2, "Chunk mesh\nid 1–4"),
        (6.5, 3.2, "Dekodiranje\nIMU / A-law"),
        (0.5, 0.8, "WAV (zvok)\nconvert_bin_to_wav"),
        (4.0, 0.8, "Grafi signalov\nSignal_decode"),
        (7.5, 0.8, "AI audio\naudio_predict"),
    ]
    colors = plt.cm.Blues(np.linspace(0.3, 0.85, len(boxes)))
    for i, (x, y, t) in enumerate(boxes):
        box = FancyBboxPatch((x, y), 2.0, 1.0, boxstyle="round,pad=0.04",
                             facecolor=colors[i], edgecolor="#0D47A1", lw=1.5)
        ax.add_patch(box)
        ax.text(x + 1.0, y + 0.5, t, ha="center", va="center", fontsize=8, fontweight="bold")
    arrows = [(2.5, 6.0, 2.8, 6.0), (4.8, 6.0, 5.1, 6.0), (7.1, 6.0, 7.4, 6.0),
              (8.4, 5.5, 2.0, 4.2), (4.5, 3.7, 6.5, 3.7), (2.0, 3.2, 1.5, 1.8),
              (5.5, 3.2, 5.0, 1.8), (8.0, 3.2, 8.0, 1.8)]
    for x1, y1, x2, y2 in arrows:
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle="->", lw=1.8))
    ax.set_title("Wire pipeline — podatki po serijski povezavi (STM32 → AISL)", fontsize=14, fontweight="bold")
    return _save(fig, "wm_03_serial_pipeline.png")


def fig_packet_structure():
    fig, ax = plt.subplots(figsize=(10, 3.5))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 3)
    ax.axis("off")
    blocks = [
        (0.2, 1.2, 0.8, "0xFF\n0xFF", "#FFCDD2"),
        (1.1, 1.2, 0.7, "št.\npaketa", "#F8BBD9"),
        (1.9, 1.2, 4.5, "stuffing payload → unstuff", "#BBDEFB"),
        (6.5, 1.2, 1.2, "timestamp\npacket_size", "#C8E6C9"),
        (7.8, 1.2, 1.5, "chunks\n(id,size,data)", "#FFF9C4"),
        (9.4, 1.2, 0.5, "CRC16", "#E1BEE7"),
    ]
    for x, y, w, t, c in blocks:
        ax.add_patch(FancyBboxPatch((x, y), w, 0.9, boxstyle="square,pad=0.02",
                                    facecolor=c, edgecolor="#333"))
        ax.text(x + w / 2, y + 0.45, t, ha="center", va="center", fontsize=8, fontweight="bold")
    ax.annotate("", xy=(1.1, 1.65), xytext=(1.0, 1.65), arrowprops=dict(arrowstyle="->", lw=2))
    ax.annotate("", xy=(1.9, 1.65), xytext=(1.8, 1.65), arrowprops=dict(arrowstyle="->", lw=2))
    ax.set_title("Struktura paketa v BIN dnevniku (create_packets_final.py)", fontsize=12, fontweight="bold", y=0.92)
    return _save(fig, "wm_04_packet_structure.png")


def fig_chunk_mesh():
    fig, ax = plt.subplots(figsize=(9, 5))
    ids = ["1", "2", "3", "4"]
    names = ["Pospešek\n(IMU)", "Žiroskop\n(IMU)", "Magnetometer\n(IMU)", "Zvok\n(A-law)"]
    colors = ["#EF5350", "#42A5F5", "#66BB6A", "#FFA726"]
    ypos = [3, 2, 1, 0]
    for i, (cid, name, col, y) in enumerate(zip(ids, names, colors, ypos)):
        ax.barh(y, 3, left=1, height=0.6, color=col, edgecolor="#333")
        ax.text(0.3, y, f"id={cid}", va="center", fontweight="bold", fontsize=11)
        ax.text(2.5, y, name, va="center", ha="center", fontsize=10, color="white", fontweight="bold")
    ax.set_xlim(0, 5)
    ax.set_ylim(-0.5, 3.8)
    ax.axis("off")
    ax.set_title("Chunk mesh — več senzorskih tokov v enem paketu", fontsize=13, fontweight="bold")
    return _save(fig, "wm_05_chunk_mesh.png")


def fig_render_pipeline():
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.axis("off")
    steps = ["Frame\n(kamera)", "MediaPipe\nlandmarki", "LandMarkDrawer\nmesh 2D", "FrameProcessor\nflip + draw", "GUI\nHT_V2"]
    xpos = np.linspace(0.05, 0.95, len(steps))
    for xp, txt in zip(xpos, steps):
        ax.text(xp, 0.5, txt, ha="center", va="center", fontsize=10,
                bbox=dict(boxstyle="round", facecolor="#E8F5E9", edgecolor="#2E7D32"))
    for i in range(len(steps) - 1):
        ax.annotate("→", xy=(xpos[i + 1] - 0.06, 0.5), xytext=(xpos[i] + 0.06, 0.5), fontsize=14, ha="center")
    ax.set_title("Cevovod risanja wire mesha v aplikaciji", fontsize=13, fontweight="bold", y=0.9)
    return _save(fig, "wm_06_render_pipeline.png")


def generate_all():
    fig_hand_wiremesh()
    fig_mesh_vs_features()
    fig_serial_pipeline()
    fig_packet_structure()
    fig_chunk_mesh()
    fig_render_pipeline()
    print(f"Done → {FIG_DIR}")


if __name__ == "__main__":
    generate_all()
