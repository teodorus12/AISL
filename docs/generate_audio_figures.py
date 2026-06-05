"""Generate figures for audio recognition Word document."""

import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

FIG_DIR = os.path.join(os.path.dirname(__file__), "figures_audio")
TEACHING_DIR = os.path.join(ROOT, "teaching_data")
TESTING_DIR = os.path.join(ROOT, "testing_data")


def _save(fig, name):
    os.makedirs(FIG_DIR, exist_ok=True)
    path = os.path.join(FIG_DIR, name)
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


def extract_features(path, proc):
    """Feature extraction; uses AudioProcessor with librosa compatibility fallback."""
    import librosa

    y, sr = librosa.load(path, sr=proc.sr)
    y, _ = librosa.effects.trim(y, top_db=20)
    if len(y) > proc.max_len:
        y = y[: proc.max_len]
    else:
        y = np.pad(y, (0, proc.max_len - len(y)))

    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=proc.n_mfcc)
    delta1 = librosa.feature.delta(mfcc)
    delta2 = librosa.feature.delta(mfcc, order=2)
    chroma = librosa.feature.chroma_stft(y=y, sr=sr)
    try:
        contrast = librosa.feature.spectral_contrast(y=y, sr=sr)
    except Exception:
        mel = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128, fmax=3800)
        contrast = librosa.feature.spectral_contrast(S=mel, sr=sr, n_bands=5, fmin=200.0)
        if contrast.shape[0] < 7:
            contrast = np.vstack([contrast, contrast[-1:]])
    zcr = librosa.feature.zero_crossing_rate(y)
    rms = librosa.feature.rms(y=y)

    parts = []
    for feat in (mfcc, delta1, delta2, chroma, contrast, zcr, rms):
        parts += [feat.mean(axis=1), feat.std(axis=1)]
    return np.concatenate(parts)


def load_teaching_dataset(proc):
    X, y = [], []
    for label in sorted(os.listdir(TEACHING_DIR)):
        folder = os.path.join(TEACHING_DIR, label)
        if not os.path.isdir(folder):
            continue
        for f in os.listdir(folder):
            if not f.endswith(".wav"):
                continue
            try:
                X.append(extract_features(os.path.join(folder, f), proc))
                y.append(label)
            except Exception as e:
                print(f"skip {f}: {e}")
    return np.array(X, dtype=np.float32), np.array(y)


def fig_pipeline():
    fig, ax = plt.subplots(figsize=(10, 7))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis("off")
    boxes = [
        (0.8, 8.0, "WAV datoteka\n(ali BIN → WAV)"),
        (0.8, 6.4, "librosa.load\nsr=8000 Hz, 1 s"),
        (0.8, 4.8, "trim + pad\nAudioProcessor"),
        (0.8, 3.2, "MFCC, Δ, chroma,\ncontrast, ZCR, RMS"),
        (0.8, 1.6, "Vektor 162 znač.\nmean + std"),
        (5.2, 3.2, "NeuralNetwork\nMLP + softmax"),
        (5.2, 1.6, "Beseda\n(npr. kava, čaj)"),
        (5.2, 5.0, "sign_videos.py\nčrke → videi"),
    ]
    colors = ["#FFF3E0", "#FFE0B2", "#FFCC80", "#FFB74D", "#FFA726", "#C8E6C9", "#A5D6A7", "#81C784"]
    for i, (x, y, text) in enumerate(boxes):
        box = FancyBboxPatch(
            (x, y), 3.4, 1.1, boxstyle="round,pad=0.05",
            facecolor=colors[i], edgecolor="#E65100", linewidth=1.5,
        )
        ax.add_patch(box)
        ax.text(x + 1.7, y + 0.55, text, ha="center", va="center", fontsize=9, fontweight="bold")
    ax.annotate("", xy=(5.2, 3.75), xytext=(4.2, 3.75), arrowprops=dict(arrowstyle="->", lw=2))
    ax.annotate("", xy=(6.9, 4.5), xytext=(6.9, 4.1), arrowprops=dict(arrowstyle="->", lw=2))
    ax.set_title("Arhitektura prepoznave govora — projekt AISL", fontsize=14, fontweight="bold")
    return _save(fig, "audio_01_pipeline.png")


def fig_mfcc_spectrogram():
    import librosa
    import librosa.display

    sample = None
    for label in os.listdir(TEACHING_DIR):
        folder = os.path.join(TEACHING_DIR, label)
        if os.path.isdir(folder):
            for f in os.listdir(folder):
                if f.endswith(".wav"):
                    sample = os.path.join(folder, f)
                    break
        if sample:
            break
    if not sample:
        return None

    y, sr = librosa.load(sample, sr=8000)
    y, _ = librosa.effects.trim(y, top_db=20)
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=20)

    fig, axes = plt.subplots(2, 1, figsize=(10, 6))
    librosa.display.waveshow(y, sr=sr, ax=axes[0], color="#1565C0")
    axes[0].set_title("Valovna oblika (po obrezovanju tišine)")
    axes[0].set_xlabel("Čas (s)")

    img = librosa.display.specshow(mfcc, x_axis="time", sr=sr, ax=axes[1], cmap="magma")
    axes[1].set_title("MFCC spektrogram (20 koeficientov)")
    fig.colorbar(img, ax=axes[1], format="%+2.0f dB")
    fig.tight_layout()
    return _save(fig, "audio_02_mfcc_spectrogram.png")


def fig_feature_breakdown():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))
    labels = ["MFCC", "Δ MFCC", "Δ² MFCC", "Chroma", "Contrast", "ZCR", "RMS"]
    dims = [40, 40, 40, 24, 14, 2, 2]
    colors = plt.cm.YlOrBr(np.linspace(0.3, 0.9, len(labels)))
    ax1.barh(labels, dims, color=colors)
    ax1.set_xlabel("Število vrednosti v vektorju")
    ax1.set_title("Prispevek značilnosti (mean + std)")

    ax2.pie(dims, labels=labels, autopct="%1.0f%%", colors=colors, textprops={"fontsize": 8})
    ax2.set_title("Delež skupnega vektorja (162 dim.)")
    fig.suptitle("Sestava feature_vector — AudioProcessor", fontsize=13, fontweight="bold")
    fig.tight_layout()
    return _save(fig, "audio_03_feature_breakdown.png")


def fig_nn_architecture():
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 6)
    ax.axis("off")
    layers = [
        (0.3, "Vhod\n162 značilnosti\n(Z-score norm)"),
        (2.3, "Skriti 1\n128 nevronov\nReLU + dropout"),
        (4.3, "Skriti 2\n64 nevronov\nReLU + dropout"),
        (6.3, "Izhod\n5 razredov\nSoftmax"),
    ]
    for i, (x, text) in enumerate(layers):
        w = 1.7
        box = FancyBboxPatch(
            (x, 1.8), w, 2.2, boxstyle="round,pad=0.06",
            facecolor="#E8F5E9" if i % 2 == 0 else "#C8E6C9",
            edgecolor="#2E7D32", linewidth=2,
        )
        ax.add_patch(box)
        ax.text(x + w / 2, 2.9, text, ha="center", va="center", fontsize=10, fontweight="bold")
        if i < len(layers) - 1:
            ax.annotate("", xy=(layers[i + 1][0], 2.9), xytext=(x + w, 2.9),
                        arrowprops=dict(arrowstyle="->", color="#1B5E20", lw=2.5))
    ax.set_title("NeuralNetwork — lastna MLP implementacija (ai6.pkl)", fontsize=14, fontweight="bold")
    ax.text(6, 0.5, "Razredi: kava, pivo, sok, vino, čaj", ha="center", fontsize=10, style="italic")
    return _save(fig, "audio_04_nn_architecture.png")


def fig_dataset_distribution():
    counts = {}
    for label in sorted(os.listdir(TEACHING_DIR)):
        d = os.path.join(TEACHING_DIR, label)
        if os.path.isdir(d):
            n = len([f for f in os.listdir(d) if f.endswith(".wav")])
            if n:
                counts[label] = n
    if not counts:
        return None
    fig, ax = plt.subplots(figsize=(9, 5))
    labels = list(counts.keys())
    vals = [counts[l] for l in labels]
    bars = ax.bar(labels, vals, color="#FF9800", edgecolor="#E65100")
    ax.set_ylabel("Število WAV posnetkov")
    ax.set_title(f"Učna množica teaching_data/ — skupaj {sum(vals)} posnetkov")
    ax.grid(axis="y", alpha=0.3)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 3, str(v), ha="center", fontsize=10)
    return _save(fig, "audio_05_dataset.png")


def fig_training_curves():
    """Train short model for illustrative loss/accuracy curves."""
    from audio_recognition import AudioProcessor, NeuralNetwork

    proc = AudioProcessor()
    X, y = load_teaching_dataset(proc)
    if len(X) < 10:
        return None

    labels = sorted(set(y))
    label_to_idx = {l: i for i, l in enumerate(labels)}
    y_oh = np.zeros((len(y), len(labels)))
    for i, lbl in enumerate(y):
        y_oh[i, label_to_idx[lbl]] = 1

    mean, std = X.mean(axis=0), X.std(axis=0) + 1e-9
    Xn = (X - mean) / std

    y_strat = np.array([label_to_idx[l] for l in y])
    X_train, X_val, y_train, y_val = train_test_split(
        Xn, y_oh, test_size=0.2, random_state=42, stratify=y_strat
    )

    nn = NeuralNetwork(162, 128, len(labels), hidden_size2=64, lr=0.003, dropout_rate=0.3)
    nn.labels = labels
    nn.mean, nn.std = mean, std

    epochs = 80
    batch = 32
    losses, accs = [], []
    n = len(X_train)

    for ep in range(epochs):
        idx = np.random.permutation(n)
        for i in range(0, n, batch):
            bi = idx[i : i + batch]
            nn.train_step(X_train[bi], y_train[bi])
        nn.decay_lr()
        out = nn.forward(X)
        y_full = np.zeros((len(y), len(labels)))
        for i, lbl in enumerate(y):
            y_full[i, label_to_idx[lbl]] = 1
        losses.append(nn.compute_loss(y_full, out))
        accs.append(nn.compute_accuracy(y_full, out))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
    ax1.plot(losses, color="#E65100", lw=2)
    ax1.set_title("Cross-entropy loss")
    ax1.set_xlabel("Epocha")
    ax1.grid(alpha=0.3)
    ax2.plot([a * 100 for a in accs], color="#2E7D32", lw=2)
    ax2.set_title("Natančnost na učni množici (%)")
    ax2.set_xlabel("Epocha")
    ax2.grid(alpha=0.3)
    fig.suptitle("Učenje (80 epoh, teaching_data) — ilustrativna krivulja", fontsize=12, fontweight="bold")
    fig.tight_layout()
    return _save(fig, "audio_06_training_curves.png")


def fig_confusion_and_f1():
    from audio_recognition import AudioProcessor, NeuralNetwork

    proc = AudioProcessor()
    X, y = load_teaching_dataset(proc)
    if len(X) < 20:
        return None, None

    labels = sorted(set(y))
    y_idx = np.array([labels.index(l) for l in y])
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_idx, test_size=0.2, random_state=42, stratify=y_idx
    )

    mean, std = X_train.mean(axis=0), X_train.std(axis=0) + 1e-9
    X_train_n = (X_train - mean) / std
    X_test_n = (X_test - mean) / std

    y_oh_train = np.zeros((len(y_train), len(labels)))
    for i, j in enumerate(y_train):
        y_oh_train[i, j] = 1

    nn = NeuralNetwork(X.shape[1], 128, len(labels), hidden_size2=64, lr=0.003, dropout_rate=0.3)
    nn.labels = labels
    nn.mean, nn.std = mean, std

    for ep in range(100):
        idx = np.random.permutation(len(X_train_n))
        for i in range(0, len(X_train_n), 32):
            bi = idx[i : i + 32]
            nn.train_step(X_train_n[bi], y_oh_train[bi])
        nn.decay_lr()

    out = nn.forward(X_test_n)
    y_pred = np.argmax(out, axis=1)

    cm = confusion_matrix(y_test, y_pred)
    fig, ax = plt.subplots(figsize=(8, 7))
    im = ax.imshow(cm, cmap="Oranges")
    ax.set_xticks(range(len(labels)))
    ax.set_yticks(range(len(labels)))
    ax.set_xticklabels(labels)
    ax.set_yticklabels(labels)
    ax.set_xlabel("Napoved")
    ax.set_ylabel("Dejanska beseda")
    ax.set_title("Matrika zamenjav (test 20 %, teaching_data)")
    plt.colorbar(im, ax=ax)
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, str(cm[i, j]), ha="center", va="center",
                    color="white" if cm[i, j] > cm.max() / 2 else "black")
    p1 = _save(fig, "audio_07_confusion_matrix.png")

    report = classification_report(y_test, y_pred, target_names=labels, output_dict=True, zero_division=0)
    names, f1s = [], []
    for lbl in labels:
        if lbl in report:
            names.append(lbl)
            f1s.append(report[lbl]["f1-score"])

    fig2, ax2 = plt.subplots(figsize=(9, 5))
    colors = ["#66BB6A" if f >= 0.85 else "#FFA726" if f >= 0.7 else "#EF5350" for f in f1s]
    ax2.bar(names, f1s, color=colors, edgecolor="#333")
    ax2.set_ylim(0, 1.05)
    ax2.set_ylabel("F1-score")
    ax2.set_title("F1-score po besedi (testna množica 20 %)")
    ax2.axhline(0.85, color="gray", linestyle="--", alpha=0.6)
    ax2.grid(axis="y", alpha=0.3)
    p2 = _save(fig2, "audio_08_f1_scores.png")
    return p1, p2


def fig_preprocessing_steps():
    fig, ax = plt.subplots(figsize=(10, 3.5))
    ax.axis("off")
    steps = ["WAV", "Resample\n8 kHz", "Trim\ntišina", "Pad/truncate\n1 s", "Ekstrakcija\nznačilnosti", "Z-score\n(ob učenju)"]
    xpos = np.linspace(0.04, 0.96, len(steps))
    for xp, txt in zip(xpos, steps):
        ax.text(xp, 0.5, txt, ha="center", va="center", fontsize=10,
                bbox=dict(boxstyle="round", facecolor="#FFF8E1", edgecolor="#F9A825"))
    for i in range(len(steps) - 1):
        ax.annotate("→", xy=(xpos[i + 1] - 0.04, 0.5), xytext=(xpos[i] + 0.04, 0.5), fontsize=14, ha="center")
    ax.set_title("Predobdelava zvoka — AudioProcessor.wav_to_vector", fontsize=13, fontweight="bold", y=0.95)
    return _save(fig, "audio_09_preprocessing.png")


def fig_sign_videos_flow():
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.axis("off")
    ax.text(0.5, 0.75, "WAV → predict_word() → beseda (npr. čaj)", ha="center", fontsize=12,
            bbox=dict(boxstyle="round", facecolor="#E3F2FD"))
    ax.text(0.5, 0.45, "word_to_letters() → [Č, A, J]", ha="center", fontsize=12,
            bbox=dict(boxstyle="round", facecolor="#E8F5E9"))
    ax.text(0.5, 0.15, "signs_data/ → predvajanje videov po črkah", ha="center", fontsize=12,
            bbox=dict(boxstyle="round", facecolor="#F3E5F5"))
    ax.annotate("↓", xy=(0.5, 0.62), xytext=(0.5, 0.68), fontsize=16, ha="center")
    ax.annotate("↓", xy=(0.5, 0.32), xytext=(0.5, 0.38), fontsize=16, ha="center")
    ax.set_title("Integracija z znakovnim jezikom (main.py možnost 10)", fontsize=13, fontweight="bold")
    return _save(fig, "audio_10_sign_videos.png")


def fig_complexity():
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.axis("off")
    data = [
        ["Faza", "Zahtevnost", "Opomba"],
        ["librosa.load + MFCC", "O(T log T)", "T = vzorci, 1 s @ 8 kHz"],
        ["Agregacija mean/std", "O(F)", "F = frekvenčni okvirji"],
        ["Forward MLP", "O(162×128 + …)", "Zanemarljivo na CPU"],
        ["Učenje (200 epoh)", "O(epochs × N × dim)", "N ≈ 1600 posnetkov"],
    ]
    table = ax.table(cellText=data, loc="center", cellLoc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.2, 1.8)
    for (row, col), cell in table.get_celld().items():
        if row == 0:
            cell.set_facecolor("#E65100")
            cell.set_text_props(color="white", fontweight="bold")
    ax.set_title("Algoritmična analiza — audio modul", fontsize=13, fontweight="bold", y=0.95)
    return _save(fig, "audio_11_complexity.png")


def generate_all():
    os.makedirs(FIG_DIR, exist_ok=True)
    fig_pipeline()
    fig_mfcc_spectrogram()
    fig_feature_breakdown()
    fig_nn_architecture()
    fig_dataset_distribution()
    print("Training curves (may take ~30s)...")
    fig_training_curves()
    print("Confusion matrix + F1 (may take ~60s)...")
    fig_confusion_and_f1()
    fig_preprocessing_steps()
    fig_sign_videos_flow()
    fig_complexity()
    print(f"Done → {FIG_DIR}")


if __name__ == "__main__":
    generate_all()
