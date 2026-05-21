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
        self.labels = []

        self.nn = None
        self.proc = AudioProcessor()

        tk.Button(
            root,
            text="Load Training Data",
            command=self.load_data
        ).grid(row=0, column=0, columnspan=2)

        tk.Button(
            root,
            text="Train",
            command=self.train
        ).grid(row=1, column=0, columnspan=2)

        tk.Button(
            root,
            text="Test WAV",
            command=self.test
        ).grid(row=2, column=0, columnspan=2)

        tk.Button(
            root,
            text="Save Model",
            command=self.save
        ).grid(row=3, column=0, columnspan=2)

        tk.Button(
            root,
            text="Load Model",
            command=self.load
        ).grid(row=4, column=0, columnspan=2)

        tk.Label(root, text="Hidden neurons").grid(row=5, column=0)

        self.hidden_entry = tk.Entry(root)
        self.hidden_entry.insert(0, "64")
        self.hidden_entry.grid(row=5, column=1)

        tk.Label(root, text="LR").grid(row=6, column=0)

        self.lr_entry = tk.Entry(root)
        self.lr_entry.insert(0, "0.003")
        self.lr_entry.grid(row=6, column=1)

        tk.Label(root, text="Epochs").grid(row=7, column=0)

        self.epoch_entry = tk.Entry(root)
        self.epoch_entry.insert(0, "120")
        self.epoch_entry.grid(row=7, column=1)

        tk.Label(root, text="Batch size").grid(row=8, column=0)

        self.batch_entry = tk.Entry(root)
        self.batch_entry.insert(0, "32")
        self.batch_entry.grid(row=8, column=1)

    def encode(self, label):
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
                    path = os.path.join(folder, f)

                    vec = self.proc.wav_to_vector(path)

                    self.dataset.append((vec[0], label))

        messagebox.showinfo(
            "Done",
            f"Loaded {len(self.dataset)} samples"
        )

    def train(self):
        self.labels = sorted(set(l for _, l in self.dataset))

        X = np.array([v for v, _ in self.dataset])

        y = np.array([
            self.encode(l)[0]
            for _, l in self.dataset
        ])

        self.mean = X.mean(axis=0)
        self.std = X.std(axis=0) + 1e-9

        X = (X - self.mean) / self.std

        self.nn = NeuralNetwork(
            input_size=X.shape[1],
            hidden_size=int(self.hidden_entry.get()),
            output_size=len(self.labels),
            lr=float(self.lr_entry.get())
        )

        self.nn.labels = self.labels
        self.nn.mean = self.mean
        self.nn.std = self.std

        epochs = int(self.epoch_entry.get())
        batch_size = int(self.batch_entry.get())

        def loop():
            n = len(X)

            losses = []
            accuracies = []

            for epoch in range(epochs):
                idx = np.random.permutation(n)

                Xs = X[idx]
                ys = y[idx]

                for i in range(0, n, batch_size):
                    xb = Xs[i:i + batch_size]
                    yb = ys[i:i + batch_size]

                    self.nn.train_step(xb, yb)

                out = self.nn.forward(X)

                loss = self.nn.compute_loss(y, out)
                acc = self.nn.compute_accuracy(y, out)

                losses.append(loss)
                accuracies.append(acc)

                print(
                    f"epoch {epoch} "
                    f"loss={loss:.4f} "
                    f"acc={acc:.4f}"
                )

            plt.figure()
            plt.plot(losses)
            plt.xlabel("Epoch")
            plt.ylabel("Loss")
            plt.title("Training Loss")
            plt.grid(True)

            plt.figure()
            plt.plot(accuracies)
            plt.xlabel("Epoch")
            plt.ylabel("Accuracy")
            plt.title("Training Accuracy")
            plt.grid(True)

            plt.show()

            messagebox.showinfo(
                "Done",
                "Training finished"
            )

        threading.Thread(target=loop).start()

    def test(self):
        if self.nn is None:
            return

        path = filedialog.askopenfilename()

        vec = self.proc.wav_to_vector(path)

        vec = (vec - self.nn.mean) / self.nn.std

        out = self.nn.forward(vec)

        pred = np.argmax(out)

        messagebox.showinfo(
            "Result",
            self.nn.labels[pred]
        )

    def save(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".pkl"
        )

        self.nn.save(path)

    def load(self):
        path = filedialog.askopenfilename()

        self.nn = NeuralNetwork.load(path)


if __name__ == "__main__":
    root = tk.Tk()

    App(root)

    root.mainloop()