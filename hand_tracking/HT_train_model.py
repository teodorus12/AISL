import json
import os
import argparse
import numpy as np
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report
import pickle
import matplotlib.pyplot as plt
 
DEFAULT_CLIPS_DIR = "Handtracking/clips"
DEFAULT_OUT_DIR   = "models"
AGGREGATE = "mean"
 
 
def load_dataset(clips_dir: str):
    X, y = [], []
 
    for label in os.listdir(clips_dir):
        label_dir = os.path.join(clips_dir, label)
        if not os.path.isdir(label_dir):
            continue
 
        for fname in os.listdir(label_dir):
            if not fname.endswith(".json"):
                continue
 
            fpath = os.path.join(label_dir, fname)
            with open(fpath) as f:
                data = json.load(f)
 
            frames = data.get("frames", [])
            if not frames:
                continue
 
            # Collect all feature vectors from this clip
            vecs = [frame["feature_vector"] for frame in frames
                    if "feature_vector" in frame]
 
            if not vecs:
                continue
 
            arr = np.array(vecs, dtype=np.float32)
 
            # Aggregate frames → single feature vector per clip
            if AGGREGATE == "mean":
                clip_vec = arr.mean(axis=0)
            elif AGGREGATE == "first":
                clip_vec = arr[0]
            else:
                clip_vec = arr.mean(axis=0)
 
            X.append(clip_vec)
            y.append(label)
 
    return np.array(X, dtype=np.float32), np.array(y)
 
 
def train(clips_dir: str, out_dir: str):
    print(f"[TRAIN] Loading clips from: {clips_dir}")
    X, y = load_dataset(clips_dir)
 
    if len(X) == 0:
        print("[TRAIN] No data found — record some clips first (hold SPACE in the app).")
        return
 
    print(f"[TRAIN] Loaded {len(X)} samples across {len(set(y))} classes: {sorted(set(y))}")
 
    le = LabelEncoder()
    y_enc = le.fit_transform(y)
 
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_enc, test_size=0.2, random_state=42, stratify=y_enc
    )
 
    model = MLPClassifier(
        hidden_layer_sizes=(256, 128, 64),
        activation="relu",
        max_iter=500,
        random_state=42,
        verbose=True,
    )
 
    print("[TRAIN] Fitting model…")
    model.fit(X_train, y_train)
 
    y_pred = model.predict(X_test)
    print("\n[TRAIN] Evaluation on held-out test set:")
    print(classification_report(y_test, y_pred, target_names=le.classes_))
 
    os.makedirs(out_dir, exist_ok=True)
 
    model_path = os.path.join(out_dir, "sl_model.pkl")
    with open(model_path, "wb") as f:
        pickle.dump(model, f)
 
    classes_path = os.path.join(out_dir, "sl_classes.json")
    with open(classes_path, "w") as f:
        json.dump(list(le.classes_), f)
 
    print(f"\n[TRAIN] Model saved  →  {model_path}")
    print(f"[TRAIN] Classes saved →  {classes_path}")
 
    # ── Learning curve ────────────────────────────────────────────────────────
    plot_learning_curve(model, out_dir)
 
 
def plot_learning_curve(model: MLPClassifier, out_dir: str):
    losses = model.loss_curve_
 
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(losses, color="#4A90D9", linewidth=2, label="Training loss")
    ax.set_title("Learning Curve", fontsize=14, fontweight="bold")
    ax.set_xlabel("Iteration")
    ax.set_ylabel("Loss")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
 
    plot_path = os.path.join(out_dir, "learning_curve.png")
    fig.savefig(plot_path, dpi=150)
    print(f"[TRAIN] Learning curve saved → {plot_path}")
    plt.show()
 
 
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--clips_dir", default=DEFAULT_CLIPS_DIR)
    parser.add_argument("--out_dir",   default=DEFAULT_OUT_DIR)
    args = parser.parse_args()
 
    train(args.clips_dir, args.out_dir)