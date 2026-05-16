import tkinter as tk
from tkinter import filedialog, messagebox
import numpy as np
import librosa
import matplotlib.pyplot as plt
import threading
import pickle
import os


class NeuralNetwork:
    def __init__(self, input_size, hidden_size, output_size, lr=0.01):
        self.lr = lr

        self.W1 = np.random.randn(input_size, hidden_size) * 0.1
        self.b1 = np.zeros((1, hidden_size))

        self.W2 = np.random.randn(hidden_size, output_size) * 0.1
        self.b2 = np.zeros((1, output_size))

        self.loss_history = []

    def sigmoid(self, x):
        return 1 / (1 + np.exp(-x))

    def softmax(self, x):
        x = x - np.max(x, axis=1, keepdims=True)
        exp = np.exp(x)
        return exp / np.sum(exp, axis=1, keepdims=True)

    def forward(self, X):
        self.z1 = X @ self.W1 + self.b1
        self.a1 = self.sigmoid(self.z1)

        self.z2 = self.a1 @ self.W2 + self.b2
        self.a2 = self.softmax(self.z2)

        return self.a2

    def cross_entropy(self, y_true, y_pred):
        eps = 1e-9
        return -np.mean(np.sum(y_true * np.log(y_pred + eps), axis=1))

    def train_step(self, X, y):
        out = self.forward(X)

        loss = self.cross_entropy(y, out)
        self.loss_history.append(loss)

        d2 = (out - y)  # softmax + CE gradient

        dW2 = self.a1.T @ d2
        db2 = np.sum(d2, axis=0, keepdims=True)

        d1 = (d2 @ self.W2.T) * self.sigmoid(self.a1)

        dW1 = X.T @ d1
        db1 = np.sum(d1, axis=0, keepdims=True)

        self.W2 -= self.lr * dW2
        self.b2 -= self.lr * db2
        self.W1 -= self.lr * dW1
        self.b1 -= self.lr * db1

        return loss

    def save(self, path, labels):
        data = {
            "W1": self.W1,
            "b1": self.b1,
            "W2": self.W2,
            "b2": self.b2,
            "labels": labels
        }

        with open(path, "wb") as f:
            pickle.dump(data, f)

    @staticmethod
    def load(path, lr=0.01):
        with open(path, "rb") as f:
            data = pickle.load(f)

        nn = NeuralNetwork(
            input_size=data["W1"].shape[0],
            hidden_size=data["W1"].shape[1],
            output_size=data["W2"].shape[1],
            lr=lr
        )

        nn.W1 = data["W1"]
        nn.b1 = data["b1"]
        nn.W2 = data["W2"]
        nn.b2 = data["b2"]

        return nn, data["labels"]



class AudioProcessor:
    def __init__(self, n_mfcc=20):
        self.n_mfcc = n_mfcc

    def wav_to_vector(self, path):
        y, sr = librosa.load(path, sr=16000)

        y, _ = librosa.effects.trim(y)

        target = 16000
        if len(y) < target:
            y = np.pad(y, (0, target - len(y)))
        else:
            y = y[:target]

        mfcc = librosa.feature.mfcc(
            y=y,
            sr=sr,
            n_mfcc=self.n_mfcc
        )

        mean = np.mean(mfcc, axis=1)
        std = np.std(mfcc, axis=1)

        vec = np.concatenate([mean, std])

        return vec.reshape(1, -1)



class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Speech Recognizer (Improved)")

        self.dataset = []
        self.labels = []
        self.nn = None

        self.proc = AudioProcessor()

        tk.Label(root, text="Hidden neurons").grid(row=0, column=0)
        self.hidden_entry = tk.Entry(root)
        self.hidden_entry.insert(0, "64")
        self.hidden_entry.grid(row=0, column=1)

        tk.Label(root, text="LR").grid(row=1, column=0)
        self.lr_entry = tk.Entry(root)
        self.lr_entry.insert(0, "0.01")
        self.lr_entry.grid(row=1, column=1)

        tk.Button(root, text="Load teaching_data", command=self.load_data).grid(row=2, column=0, columnspan=2)
        tk.Button(root, text="Train", command=self.train).grid(row=3, column=0, columnspan=2)
        tk.Button(root, text="Test WAV", command=self.test).grid(row=4, column=0, columnspan=2)
        tk.Button(root, text="Save", command=self.save).grid(row=5, column=0, columnspan=2)
        tk.Button(root, text="Load", command=self.load).grid(row=6, column=0, columnspan=2)

    def encode(self, label):
        y = np.zeros((1, len(self.labels)))
        y[0, self.labels.index(label)] = 1
        return y

    def load_data(self):
        base = "teaching_data"

        if not os.path.exists(base):
            messagebox.showerror("Error", "No folder")
            return

        count = 0

        for label in os.listdir(base):
            folder = os.path.join(base, label)

            if not os.path.isdir(folder):
                continue

            for f in os.listdir(folder):
                if not f.endswith(".wav"):
                    continue

                path = os.path.join(folder, f)

                vec = self.proc.wav_to_vector(path)

                self.dataset.append((vec[0], label))
                count += 1

        messagebox.showinfo("Done", f"Loaded {count} samples")

    def train(self):
        self.labels = sorted(set(l for _, l in self.dataset))

        X = np.array([v for v, _ in self.dataset])
        y = np.array([self.encode(l)[0] for _, l in self.dataset])

        self.nn = NeuralNetwork(
            input_size=X.shape[1],
            hidden_size=int(self.hidden_entry.get()),
            output_size=len(self.labels),
            lr=float(self.lr_entry.get())
        )

        def loop():
            for i in range(200000):
                loss = self.nn.train_step(X, y)
                if i % 100 == 0:
                    print(i, loss)

            plt.plot(self.nn.loss_history)
            plt.show()

            messagebox.showinfo("Done", "Training finished")

        threading.Thread(target=loop).start()

    def test(self):
        if not self.nn:
            return

        path = filedialog.askopenfilename()

        vec = self.proc.wav_to_vector(path)

        out = self.nn.forward(vec)

        pred = np.argmax(out)

        messagebox.showinfo(
            "Result",
            self.labels[pred]
        )

    def save(self):
        path = filedialog.asksaveasfilename(defaultextension=".pkl")
        self.nn.save(path, self.labels)

    def load(self):
        path = filedialog.askopenfilename()
        self.nn, self.labels = NeuralNetwork.load(path)


root = tk.Tk()
App(root)
root.mainloop()