"""Generate figures for Prepoznavanje znakov Word document."""

import json
import os
import pickle
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from sklearn.metrics import confusion_matrix, classification_report
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

FIG_DIR = os.path.join(os.path.dirname(__file__), "figures")
CLIPS_DIR = os.path.join(ROOT, "Handtracking/clips")
MODEL_PATH = os.path.join(ROOT, "models", "sl_model.pkl")
CLASSES_PATH = os.path.join(ROOT, "models", "sl_classes.json")

HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (17, 18), (18, 19), (19, 20),
    (0, 17),
]

# Stylized 2D hand layout for diagram (not from camera)
HAND_XY = np.array([
    [0.0, 0.0],   # 0 wrist
    [-0.15, 0.35], [0.15, 0.35], [0.28, 0.35], [0.38, 0.35],  # thumb
    [-0.12, 0.55], [-0.12, 0.72], [-0.12, 0.88], [-0.12, 1.02],  # index
    [0.0, 0.58], [0.0, 0.75], [0.0, 0.91], [0.0, 1.05],  # middle
    [0.12, 0.55], [0.12, 0.70], [0.12, 0.84], [0.12, 0.96],  # ring
    [0.24, 0.50], [0.30, 0.62], [0.34, 0.72], [0.36, 0.80],  # pinky
])


def _save(fig, name):
    os.makedirs(FIG_DIR, exist_ok=True)
    path = os.path.join(FIG_DIR, name)
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


def fig_pipeline():
    fig, ax = plt.subplots(figsize=(10, 7))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis("off")
    boxes = [
        (1, 8.2, "Kamera\n(BGR frame)"),
        (1, 6.6, "MediaPipe\n21 landmarkov"),
        (1, 5.0, "Serializer\nnormalizacija"),
        (1, 3.4, "feature_vector\n126 dimenzij"),
        (1, 1.8, "MLPClassifier\nsoftmax"),
        (5.5, 1.8, "Majority vote\n10 okvirjev"),
        (5.5, 3.4, "Prag zaupanja\n≥ 60 %"),
        (5.5, 5.0, "GUI: AI: črka (%)"),
    ]
    colors = ["#E3F2FD", "#BBDEFB", "#90CAF9", "#64B5F6", "#42A5F5", "#FFE082", "#FFCC80", "#C8E6C9"]
    for i, (x, y, text) in enumerate(boxes):
        box = FancyBboxPatch(
            (x, y), 3.2, 1.1, boxstyle="round,pad=0.05",
            facecolor=colors[i % len(colors)], edgecolor="#1565C0", linewidth=1.5,
        )
        ax.add_patch(box)
        ax.text(x + 1.6, y + 0.55, text, ha="center", va="center", fontsize=9, fontweight="bold")

    arrows = [(2.6, 8.2, 2.6, 7.7), (2.6, 6.6, 2.6, 6.1), (2.6, 5.0, 2.6, 4.5),
              (2.6, 3.4, 2.6, 2.9), (4.2, 2.35, 5.5, 2.35), (7.1, 2.9, 7.1, 3.4),
              (7.1, 4.5, 7.1, 5.0)]
    for x1, y1, x2, y2 in arrows:
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="->", color="#37474F", lw=2))
    ax.set_title("Arhitektura sistema — potek podatkov", fontsize=14, fontweight="bold", pad=12)
    return _save(fig, "01_pipeline.png")


def fig_hand_skeleton():
    fig, ax = plt.subplots(figsize=(7, 8))
    for a, b in HAND_CONNECTIONS:
        ax.plot([HAND_XY[a, 0], HAND_XY[b, 0]], [HAND_XY[a, 1], HAND_XY[b, 1]], "b-", lw=2)
    ax.scatter(HAND_XY[:, 0], HAND_XY[:, 1], c="limegreen", s=120, zorder=5, edgecolors="darkgreen")
    for i, (x, y) in enumerate(HAND_XY):
        ax.annotate(str(i), (x, y), textcoords="offset points", xytext=(6, 6), fontsize=9, fontweight="bold")
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("MediaPipe: 21 landmarkov in povezave (skeleton)", fontsize=13, fontweight="bold")
    ax.text(0, -0.12, "0 = zapestje  |  9 = osnova srednjega prsta (referenca za skaliranje)",
            ha="center", transform=ax.transAxes, fontsize=10)
    return _save(fig, "02_hand_skeleton.png")


def fig_feature_breakdown():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.5))
    sizes = [63, 63]
    labels = ["Normalizirane koordinate\n(21 × 3)", "Normalizirani kostni vektorji\n(21 × 3)"]
    colors = ["#4A90D9", "#7CB342"]
    ax1.pie(sizes, labels=labels, colors=colors, autopct="%1.0f%%", startangle=90, textprops={"fontsize": 10})
    ax1.set_title("Sestava feature_vector (126 dim.)")

    parts = ["Landmark 0–4\n(prst 1)", "5–8\n(prst 2)", "9–12\n(prst 3)", "13–16\n(prst 4)", "17–20\n(prst 5)"]
    vals = [15, 15, 15, 15, 15]
    ax2.barh(parts, vals, color="#64B5F6")
    ax2.set_xlabel("Delež v koordinatnem delu (enakomerno po prstih)")
    ax2.set_title("Porazdelitev 21 točk po prstih")
    fig.suptitle("Vektorizacija — Serializer", fontsize=13, fontweight="bold")
    fig.tight_layout()
    return _save(fig, "03_feature_breakdown.png")


def fig_mlp_architecture():
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 6)
    ax.axis("off")
    layers = [
        (0.5, "Vhod\n126 značilnosti"),
        (2.5, "Skriti sloj 1\n256 nevronov\nReLU"),
        (4.5, "Skriti sloj 2\n128 nevronov\nReLU"),
        (6.5, "Skriti sloj 3\n64 nevronov\nReLU"),
        (8.5, "Izhod\nN razredov\nSoftmax"),
    ]
    for i, (x, text) in enumerate(layers):
        w = 1.6 if i == 0 or i == len(layers) - 1 else 1.8
        box = FancyBboxPatch(
            (x, 1.8), w, 2.2, boxstyle="round,pad=0.06",
            facecolor="#E8EAF6" if i % 2 == 0 else "#C5CAE9",
            edgecolor="#3949AB", linewidth=2,
        )
        ax.add_patch(box)
        ax.text(x + w / 2, 2.9, text, ha="center", va="center", fontsize=10, fontweight="bold")
        if i < len(layers) - 1:
            nx = layers[i + 1][0]
            ax.annotate("", xy=(nx, 2.9), xytext=(x + w, 2.9),
                        arrowprops=dict(arrowstyle="->", color="#1A237E", lw=2.5))
    ax.set_title("Arhitektura MLPClassifier (scikit-learn)", fontsize=14, fontweight="bold")
    ax.text(6, 0.6, "N = število učenih črk (npr. 25 razredov)", ha="center", fontsize=10, style="italic")
    return _save(fig, "04_mlp_architecture.png")


def fig_normalization_flow():
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.axis("off")
    steps = [
        "Surowi landmarki\n(x, y, z)",
        "− zapestje (0)\nrelativne koordinate",
        "÷ ||točka 9||\nskala roke",
        "Kostni vektorji\n21 × smer",
        "Normalizacija\nvektorjev na |v|=1",
        "Združitev\n126-dim. vektor",
    ]
    xpos = np.linspace(0.05, 0.95, len(steps))
    for i, (xp, txt) in enumerate(zip(xpos, steps)):
        ax.text(xp, 0.55, txt, ha="center", va="center", fontsize=9,
                bbox=dict(boxstyle="round", facecolor="#E1F5FE", edgecolor="#0277BD"))
        if i < len(steps) - 1:
            ax.annotate("→", xy=(xpos[i + 1] - 0.06, 0.55), xytext=(xp + 0.06, 0.55),
                        fontsize=16, ha="center", va="center")
    ax.set_title("Algoritem Serializer — zaporedje transformacij", fontsize=13, fontweight="bold", y=0.95)
    return _save(fig, "05_normalization_flow.png")


def fig_dataset_distribution():
    counts = {}
    if os.path.isdir(CLIPS_DIR):
        for label in sorted(os.listdir(CLIPS_DIR)):
            d = os.path.join(CLIPS_DIR, label)
            if os.path.isdir(d):
                n = len([f for f in os.listdir(d) if f.endswith(".json")])
                if n:
                    counts[label] = n
    if not counts:
        return None

    labels = list(counts.keys())
    vals = [counts[l] for l in labels]
    fig, ax = plt.subplots(figsize=(12, 5))
    bars = ax.bar(labels, vals, color="#4A90D9", edgecolor="#1565C0")
    ax.set_xlabel("Črka (razred)")
    ax.set_ylabel("Število posnetkov (clipov)")
    ax.set_title(f"Porazdelitev učne množice — skupaj {sum(vals)} posnetkov, {len(labels)} razredov")
    ax.grid(axis="y", alpha=0.3)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.5, str(v), ha="center", fontsize=8)
    fig.tight_layout()
    return _save(fig, "06_dataset_distribution.png")


def _load_training_data():
    from hand_tracking.HT_train_model import load_dataset
    return load_dataset(CLIPS_DIR)


def fig_confusion_matrix():
    if not os.path.exists(MODEL_PATH):
        return None
    X, y = _load_training_data()
    if len(X) == 0:
        return None

    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
    with open(CLASSES_PATH) as f:
        classes = json.load(f)

    le = LabelEncoder()
    le.classes_ = np.array(classes)
    # Only classes present in data
    present = sorted(set(y))
    y_enc = np.array([list(le.classes_).index(lbl) for lbl in y])

    X_train, X_test, y_train, y_test = train_test_split(
        X, y_enc, test_size=0.2, random_state=42, stratify=y_enc
    )
    y_pred = model.predict(X_test)

    # Map indices to present class names for readable matrix
    test_labels = [present[i] if i < len(present) else le.classes_[i] for i in sorted(set(y_test))]
    idx_to_name = {i: le.classes_[i] for i in range(len(le.classes_))}
    names = [idx_to_name[i] for i in sorted(set(y_test) | set(y_pred))]

    cm = confusion_matrix(y_test, y_pred, labels=sorted(set(y_test) | set(y_pred)))
    labels_sorted = [idx_to_name[i] for i in sorted(set(y_test) | set(y_pred))]

    fig, ax = plt.subplots(figsize=(14, 12))
    im = ax.imshow(cm, cmap="Blues")
    ax.set_xticks(range(len(labels_sorted)))
    ax.set_yticks(range(len(labels_sorted)))
    ax.set_xticklabels(labels_sorted, fontsize=8)
    ax.set_yticklabels(labels_sorted, fontsize=8)
    ax.set_xlabel("Napoved")
    ax.set_ylabel("Dejanska črka")
    ax.set_title("Matrika zamenjav (testna množica, 20 %)")
    plt.colorbar(im, ax=ax, fraction=0.046)
    thresh = cm.max() / 2.0 if cm.max() else 0
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, str(cm[i, j]), ha="center", va="center", fontsize=7,
                    color="white" if cm[i, j] > thresh else "black")
    fig.tight_layout()
    return _save(fig, "07_confusion_matrix.png")


def fig_metrics_bar():
    if not os.path.exists(MODEL_PATH):
        return None
    X, y = _load_training_data()
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
    with open(CLASSES_PATH) as f:
        classes = json.load(f)

    y_enc = np.array([classes.index(lbl) for lbl in y if lbl in classes])
    X_f = X[[i for i, lbl in enumerate(y) if lbl in classes]]
    X_train, X_test, y_train, y_test = train_test_split(
        X_f, y_enc, test_size=0.2, random_state=42, stratify=y_enc
    )
    y_pred = model.predict(X_test)
    present_classes = sorted(set(y_test) | set(y_pred))
    target_names = [classes[i] for i in present_classes]
    report = classification_report(
        y_test, y_pred, labels=present_classes, target_names=target_names, output_dict=True, zero_division=0
    )

    names, f1s = [], []
    for k, v in report.items():
        if k in target_names and isinstance(v, dict):
            names.append(k)
            f1s.append(v["f1-score"])

    fig, ax = plt.subplots(figsize=(12, 5))
    colors = ["#66BB6A" if f >= 0.9 else "#FFA726" if f >= 0.7 else "#EF5350" for f in f1s]
    ax.bar(names, f1s, color=colors, edgecolor="#333")
    ax.axhline(0.9, color="gray", linestyle="--", alpha=0.6, label="F1 = 0.9")
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("F1-score")
    ax.set_xlabel("Razred")
    ax.set_title("F1-score po razredu (testna množica 20 %)")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    return _save(fig, "08_f1_per_class.png")


def fig_learning_curve():
    lc = os.path.join(ROOT, "models", "learning_curve.png")
    if os.path.exists(lc):
        return lc
    if not os.path.exists(MODEL_PATH):
        return None
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
    if not hasattr(model, "loss_curve_"):
        return None
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(model.loss_curve_, color="#4A90D9", lw=2)
    ax.set_xlabel("Iteracija")
    ax.set_ylabel("Loss")
    ax.set_title("Učna krivulja (training loss)")
    ax.grid(alpha=0.3)
    return _save(fig, "09_learning_curve.png")


def fig_live_smoothing():
    fig, ax = plt.subplots(figsize=(10, 4))
    frames = list(range(1, 11))
    raw = ["A", "A", "?", "A", "B", "A", "A", "A", "A", "A"]
    colors = ["#EF5350" if r == "?" else "#42A5F5" if r == "B" else "#66BB6A" for r in raw]
    ax.bar(frames, [1] * 10, color=colors, edgecolor="#333")
    for i, r in enumerate(raw):
        ax.text(frames[i], 1.05, r, ha="center", fontweight="bold")
    ax.set_xlabel("Zaporedni okvir (frame)")
    ax.set_yticks([])
    ax.set_title("Glajenje napovedi: majority vote nad zadnjimi 10 okvirji → stabilna črka A")
    ax.text(5, -0.25, "Rdeče = nizko zaupanje (?), modro = napačna časovna napoved (B), zeleno = A",
            ha="center", transform=ax.transAxes, fontsize=9)
    fig.tight_layout()
    return _save(fig, "10_live_smoothing.png")


def fig_train_vs_live():
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.axis("off")
    ax.text(0.25, 0.85, "UČENJE (HT_train_model.py)", ha="center", fontsize=12, fontweight="bold", color="#1565C0")
    ax.text(0.75, 0.85, "LIVE (HT_hand_tracking.py)", ha="center", fontsize=12, fontweight="bold", color="#2E7D32")
    for x, items in [(0.25, ["Posnetek (1–2 s)", "↓", "N okvirjev", "↓", "mean(feature_vector)", "↓", "1 vzorec → MLP"]),
                     (0.75, ["1 okvir kamere", "↓", "feature_vector", "↓", "MLP + softmax", "↓", "majority vote (10)"])]:
        y = 0.72
        for item in items:
            if item == "↓":
                ax.text(x, y, item, ha="center", fontsize=14)
                y -= 0.08
            else:
                ax.text(x, y, item, ha="center", fontsize=10,
                        bbox=dict(boxstyle="round", facecolor="#E3F2FD" if x < 0.5 else "#E8F5E9"))
                y -= 0.12
    ax.annotate("", xy=(0.55, 0.45), xytext=(0.45, 0.45),
                arrowprops=dict(arrowstyle="<->", color="#F57C00", lw=2))
    ax.text(0.5, 0.38, "Morebitna\nneusklajenost", ha="center", fontsize=9, color="#E65100")
    ax.set_title("Primerjava: agregacija ob učenju vs. posamezen okvir v živo", fontsize=13, fontweight="bold", y=0.98)
    return _save(fig, "11_train_vs_live.png")


def fig_complexity_table():
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.axis("off")
    data = [
        ["Faza", "Časovna zahtevnost", "Prostorska zahtevnost"],
        ["MediaPipe detect", "O(1) na frame", "Fiksni TFLite model (~MB)"],
        ["Serializer", "O(21) = O(1)", "126 floatov na frame"],
        ["MLP inference", "O(126×256 + …)", "  model.pkl"],
        ["Majority vote", "O(10)", "10 znakov v deque"],
        ["Treniranje (celota)", "O(iter × N × dim)", "N = število posnetkov"],
    ]
    table = ax.table(cellText=data, loc="center", cellLoc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.2, 1.8)
    for (row, col), cell in table.get_celld().items():
        if row == 0:
            cell.set_facecolor("#1565C0")
            cell.set_text_props(color="white", fontweight="bold")
        else:
            cell.set_facecolor("#F5F5F5" if row % 2 == 0 else "white")
    ax.set_title("Analiza algoritmične zahtevnosti (asimptotično)", fontsize=13, fontweight="bold", y=0.95)
    return _save(fig, "12_complexity.png")


def fig_upgrade_roadmap():
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 7)
    ax.axis("off")
    items = [
        (0.5, 5.8, "Kratkoročno", "#C8E6C9", [
            "Uskladi live in učenje (mean vs frame)",
            "Več posnetkov / razred",
            "Popravek GUI panela",
        ]),
        (0.5, 3.2, "Srednjeročno", "#FFF9C4", [
            "Časovni model (LSTM/GRU)",
            "Augmentacija landmarkov",
            "Validacijski set + metrike",
        ]),
        (0.5, 0.6, "Dolgoročno", "#FFCCBC", [
            "Dinamični znaki (gesta)",
            "2 roki + 3D mesh",
            "Povezava s STM32 zvokom",
        ]),
    ]
    for x, y, title, color, bullets in items:
        ax.add_patch(FancyBboxPatch((x, y), 9, 2.0, boxstyle="round,pad=0.05",
                                    facecolor=color, edgecolor="#37474F", lw=1.5))
        ax.text(x + 0.3, y + 1.65, title, fontsize=12, fontweight="bold")
        for i, b in enumerate(bullets):
            ax.text(x + 0.4, y + 1.2 - i * 0.35, f"• {b}", fontsize=9)
    ax.set_title("Načrt nadgradnje prepoznavanja znakov", fontsize=14, fontweight="bold", y=0.98)
    return _save(fig, "13_upgrade_roadmap.png")


def generate_all():
    paths = {}
    for fn in [
        fig_pipeline, fig_hand_skeleton, fig_feature_breakdown, fig_mlp_architecture,
        fig_normalization_flow, fig_dataset_distribution, fig_confusion_matrix,
        fig_metrics_bar, fig_learning_curve, fig_live_smoothing, fig_train_vs_live,
        fig_complexity_table, fig_upgrade_roadmap,
    ]:
        try:
            p = fn()
            if p:
                paths[fn.__name__] = p
                print(f"OK {p}")
        except Exception as e:
            print(f"FAIL {fn.__name__}: {e}")
    return paths


if __name__ == "__main__":
    generate_all()
