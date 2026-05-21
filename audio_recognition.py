import sys
import numpy as np
import pickle
import librosa

sys.modules["__main__"] = sys.modules[__name__]


class NeuralNetwork:
    def __init__(self, input_size, hidden_size, output_size, lr=0.003):
        self.lr = lr

        self.W1 = np.random.randn(input_size, hidden_size) * 0.1
        self.b1 = np.zeros((1, hidden_size))

        self.W2 = np.random.randn(hidden_size, output_size) * 0.1
        self.b2 = np.zeros((1, output_size))

        self.mean = None
        self.std = None
        self.labels = None

    def sigmoid(self, x):
        return 1 / (1 + np.exp(-x))

    def softmax(self, x):
        x = x - np.max(x, axis=1, keepdims=True)
        e = np.exp(x)
        return e / np.sum(e, axis=1, keepdims=True)

    def norm(self, X):
        if self.mean is None:
            return X
        return (X - self.mean) / self.std

    def compute_loss(self, y_true, y_pred):
        eps = 1e-9
        y_pred = np.clip(y_pred, eps, 1 - eps)
        return -np.mean(np.sum(y_true * np.log(y_pred), axis=1))

    def compute_accuracy(self, y_true, y_pred):
        preds = np.argmax(y_pred, axis=1)
        truth = np.argmax(y_true, axis=1)
        return np.mean(preds == truth)

    def forward(self, X):
        X = self.norm(X)

        z1 = X @ self.W1 + self.b1
        a1 = self.sigmoid(z1)

        z2 = a1 @ self.W2 + self.b2
        return self.softmax(z2)

    def train_step(self, X, y):
        X = self.norm(X)

        z1 = X @ self.W1 + self.b1
        a1 = self.sigmoid(z1)

        z2 = a1 @ self.W2 + self.b2
        out = self.softmax(z2)

        d2 = out - y

        dW2 = a1.T @ d2
        db2 = np.sum(d2, axis=0, keepdims=True)

        d1 = (d2 @ self.W2.T) * (a1 * (1 - a1))

        self.W1 -= self.lr * (X.T @ d1)
        self.b1 -= self.lr * np.sum(d1, axis=0, keepdims=True)

        self.W2 -= self.lr * dW2
        self.b2 -= self.lr * db2

    def save(self, path):
        with open(path, "wb") as f:
            pickle.dump({
                "W1": self.W1,
                "W2": self.W2,
                "b1": self.b1,
                "b2": self.b2,
                "mean": self.mean,
                "std": self.std,
                "labels": self.labels
            }, f)

    @staticmethod
    def load(path):
        with open(path, "rb") as f:
            d = pickle.load(f)

        nn = NeuralNetwork(
            d["W1"].shape[0],
            d["W1"].shape[1],
            d["W2"].shape[1]
        )

        nn.W1 = d["W1"]
        nn.W2 = d["W2"]
        nn.b1 = d["b1"]
        nn.b2 = d["b2"]

        nn.mean = d["mean"]
        nn.std = d["std"]
        nn.labels = d["labels"]

        return nn


class AudioProcessor:
    def __init__(self, n_mfcc=20):
        self.n_mfcc = n_mfcc

    def wav_to_vector(self, path):
        y, sr = librosa.load(path, sr=16000)

        y, _ = librosa.effects.trim(y)

        y = y[:16000] if len(y) > 16000 else np.pad(
            y,
            (0, 16000 - len(y))
        )

        mfcc = librosa.feature.mfcc(
            y=y,
            sr=sr,
            n_mfcc=self.n_mfcc
        )

        delta = librosa.feature.delta(mfcc)

        return np.concatenate([
            mfcc.mean(axis=1),
            mfcc.std(axis=1),
            delta.mean(axis=1),
            delta.std(axis=1)
        ]).reshape(1, -1)