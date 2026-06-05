import tkinter as tk
from tkinter import filedialog, messagebox

import numpy as np
import threading
import os
import matplotlib.pyplot as plt

from audio_recognition import NeuralNetwork, AudioProcessor


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Speech Recognizer")

        self.dataset = []
        self.labels  = []
        self.nn      = None
        self.proc    = AudioProcessor()

        btn_cfg = dict(width=22)
        tk.Button(root, text="Load Training Data", command=self.load_data,  **btn_cfg).grid(row=0, column=0, columnspan=2, pady=2)
        tk.Button(root, text="Train",              command=self.train,       **btn_cfg).grid(row=1, column=0, columnspan=2, pady=2)
        tk.Button(root, text="Test WAV",           command=self.test,        **btn_cfg).grid(row=2, column=0, columnspan=2, pady=2)
        tk.Button(root, text="Save Model",         command=self.save,        **btn_cfg).grid(row=3, column=0, columnspan=2, pady=2)
        tk.Button(root, text="Load Model",         command=self.load,        **btn_cfg).grid(row=4, column=0, columnspan=2, pady=2)

        params = [
            ("Hidden neurons (layer 1)", "64"),
            ("Hidden neurons (layer 2)", "32"),
            ("Learning rate",            "0.001"),
            ("LR decay (per epoch)",     "0.990"),
            ("Dropout rate",             "0.45"),
            ("Epochs",                   "150"),
            ("Batch size",               "16"),
        ]
        self.entries: dict[str, tk.Entry] = {}
        for i, (label, default) in enumerate(params):
            row = 5 + i
            tk.Label(root, text=label, anchor="w").grid(row=row, column=0, sticky="w", padx=4)
            e = tk.Entry(root)
            e.insert(0, default)
            e.grid(row=row, column=1, padx=4)
            self.entries[label] = e

    def _get(self, key: str):
        return self.entries[key].get()

    def _encode(self, label: str) -> np.ndarray:
        y = np.zeros((1, len(self.labels)))
        y[0, self.labels.index(label)] = 1
        return y

    def load_data(self):
        base = "teaching_data"
        self.dataset = []

        for label in os.listdir(base):
            folder = os.path.join(base, label)
            if not os.path.isdir(folder):
                continue
            for f in os.listdir(folder):
                if f.endswith(".wav"):
                    vec = self.proc.wav_to_vector(os.path.join(folder, f))
                    self.dataset.append((vec[0], label))

        messagebox.showinfo("Done", f"Loaded {len(self.dataset)} samples")

    def train(self):
        if not self.dataset:
            messagebox.showwarning("No data", "Load training data first.")
            return

        self.labels = sorted(set(l for _, l in self.dataset))

        X = np.array([v for v, _ in self.dataset])
        y = np.array([self._encode(l)[0] for _, l in self.dataset])

        mean = X.mean(axis=0)
        std  = X.std(axis=0) + 1e-9

        self.nn = NeuralNetwork(
            input_size   = X.shape[1],
            hidden_size  = int(self._get("Hidden neurons (layer 1)")),
            hidden_size2 = int(self._get("Hidden neurons (layer 2)")),
            output_size  = len(self.labels),
            lr           = float(self._get("Learning rate")),
            lr_decay     = float(self._get("LR decay (per epoch)")),
            dropout_rate = float(self._get("Dropout rate")),
        )
        self.nn.labels = self.labels
        self.nn.mean   = mean
        self.nn.std    = std

        epochs     = int(self._get("Epochs"))
        batch_size = int(self._get("Batch size"))

        def loop():
            n = len(X)
            losses, accuracies = [], []

            for epoch in range(epochs):
                idx = np.random.permutation(n)
                Xs, ys = X[idx], y[idx]

                for i in range(0, n, batch_size):
                    self.nn.train_step(Xs[i:i+batch_size], ys[i:i+batch_size])

                self.nn.decay_lr()

                out  = self.nn.forward(X)
                loss = self.nn.compute_loss(y, out)
                acc  = self.nn.compute_accuracy(y, out)
                losses.append(loss)
                accuracies.append(acc)

                if epoch % 10 == 0 or epoch == epochs - 1:
                    print(f"epoch {epoch:>4}  loss={loss:.4f}  acc={acc:.4f}  lr={self.nn.lr:.6f}")

            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
            ax1.plot(losses);     ax1.set_title("Loss");     ax1.set_xlabel("Epoch"); ax1.grid(True)
            ax2.plot(accuracies); ax2.set_title("Accuracy"); ax2.set_xlabel("Epoch"); ax2.grid(True)
            plt.tight_layout()
            plt.show()

            messagebox.showinfo("Done", f"Training finished  —  final acc: {accuracies[-1]*100:.1f} %")

        threading.Thread(target=loop, daemon=True).start()

    def test(self):
        if self.nn is None:
            messagebox.showwarning("No model", "Train or load a model first.")
            return

        path = filedialog.askopenfilename(filetypes=[("WAV files", "*.wav")])
        if not path:
            return

        vec  = self.proc.wav_to_vector(path)
        out  = self.nn.forward(vec)
        pred = self.nn.labels[np.argmax(out)]
        conf = float(np.max(out)) * 100

        messagebox.showinfo("Result", f"{pred}  ({conf:.1f} % confidence)")

    def save(self):
        if self.nn is None:
            messagebox.showwarning("No model", "Nothing to save.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".pkl")
        if path:
            self.nn.save(path)

    def load(self):
        path = filedialog.askopenfilename(filetypes=[("Model files", "*.pkl")])
        if path:
            self.nn = NeuralNetwork.load(path)
            messagebox.showinfo("Loaded", f"Labels: {', '.join(self.nn.labels)}")


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()