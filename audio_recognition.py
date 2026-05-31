import sys
import numpy as np
import pickle
import librosa

sys.modules["__main__"] = sys.modules[__name__]


class NeuralNetwork:
    def __init__(
        self,
        input_size: int,
        hidden_size: int,
        output_size: int,
        lr: float = 0.003,
        hidden_size2: int | None = None,
        dropout_rate: float = 0.3,
        lr_decay: float = 0.995,
    ):
        self.lr = lr
        self.dropout_rate = dropout_rate
        self.lr_decay = lr_decay

        h2 = hidden_size2 if hidden_size2 is not None else hidden_size // 2

        self.W1 = np.random.randn(input_size, hidden_size) * np.sqrt(2.0 / input_size)
        self.b1 = np.zeros((1, hidden_size))

        self.W2 = np.random.randn(hidden_size, h2) * np.sqrt(2.0 / hidden_size)
        self.b2 = np.zeros((1, h2))

        self.W3 = np.random.randn(h2, output_size) * np.sqrt(2.0 / h2)
        self.b3 = np.zeros((1, output_size))

        self.mean: np.ndarray | None = None
        self.std:  np.ndarray | None = None
        self.labels: list[str] | None = None

    def _relu(self, x: np.ndarray) -> np.ndarray:
        return np.maximum(0, x)

    def _relu_grad(self, x: np.ndarray) -> np.ndarray:
        return (x > 0).astype(float)

    def _softmax(self, x: np.ndarray) -> np.ndarray:
        x = x - np.max(x, axis=1, keepdims=True)
        e = np.exp(x)
        return e / np.sum(e, axis=1, keepdims=True)

    def _norm(self, X: np.ndarray) -> np.ndarray:
        if self.mean is None:
            return X
        return (X - self.mean) / self.std


    def compute_loss(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        eps = 1e-9
        y_pred = np.clip(y_pred, eps, 1 - eps)
        return float(-np.mean(np.sum(y_true * np.log(y_pred), axis=1)))

    def compute_accuracy(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        return float(np.mean(np.argmax(y_pred, axis=1) == np.argmax(y_true, axis=1)))


    def forward(self, X: np.ndarray) -> np.ndarray:
        X = self._norm(X)
        a1 = self._relu(X  @ self.W1 + self.b1)
        a2 = self._relu(a1 @ self.W2 + self.b2)
        return self._softmax(a2 @ self.W3 + self.b3)


    def train_step(self, X: np.ndarray, y: np.ndarray) -> None:
        X = self._norm(X)

        z1 = X  @ self.W1 + self.b1
        a1 = self._relu(z1)
        mask1 = (np.random.rand(*a1.shape) > self.dropout_rate).astype(float)
        a1 *= mask1

        z2 = a1 @ self.W2 + self.b2
        a2 = self._relu(z2)
        mask2 = (np.random.rand(*a2.shape) > self.dropout_rate).astype(float)
        a2 *= mask2

        out = self._softmax(a2 @ self.W3 + self.b3)

        d3 = out - y

        dW3 = a2.T @ d3
        db3 = np.sum(d3, axis=0, keepdims=True)

        d2 = (d3 @ self.W3.T) * mask2 * self._relu_grad(z2)

        dW2 = a1.T @ d2
        db2 = np.sum(d2, axis=0, keepdims=True)

        d1 = (d2 @ self.W2.T) * mask1 * self._relu_grad(z1)

        dW1 = X.T @ d1
        db1 = np.sum(d1, axis=0, keepdims=True)

        self.W1 -= self.lr * dW1
        self.b1 -= self.lr * db1
        self.W2 -= self.lr * dW2
        self.b2 -= self.lr * db2
        self.W3 -= self.lr * dW3
        self.b3 -= self.lr * db3

    def decay_lr(self) -> None:
        self.lr *= self.lr_decay

    def save(self, path: str) -> None:
        with open(path, "wb") as f:
            pickle.dump(
                {
                    "W1": self.W1, "W2": self.W2, "W3": self.W3,
                    "b1": self.b1, "b2": self.b2, "b3": self.b3,
                    "mean": self.mean, "std": self.std,
                    "labels": self.labels,
                    "dropout_rate": self.dropout_rate,
                    "lr_decay": self.lr_decay,
                },
                f,
            )

    @staticmethod
    def load(path: str) -> "NeuralNetwork":
        with open(path, "rb") as f:
            d = pickle.load(f)

        nn = NeuralNetwork(
            input_size  = d["W1"].shape[0],
            hidden_size = d["W1"].shape[1],
            output_size = d["W3"].shape[1],
            hidden_size2= d["W2"].shape[1],
            dropout_rate= d.get("dropout_rate", 0.3),
            lr_decay    = d.get("lr_decay", 0.995),
        )
        nn.W1 = d["W1"]; nn.W2 = d["W2"]; nn.W3 = d["W3"]
        nn.b1 = d["b1"]; nn.b2 = d["b2"]; nn.b3 = d["b3"]
        nn.mean   = d["mean"]
        nn.std    = d["std"]
        nn.labels = d["labels"]
        return nn


class AudioProcessor:

    def __init__(self, n_mfcc: int = 20, sr: int = 8000, duration: float = 1.0):
        self.n_mfcc   = n_mfcc
        self.sr       = sr
        self.max_len  = int(sr * duration)

    def wav_to_vector(self, path) -> np.ndarray:
        y, sr = librosa.load(path, sr=self.sr)

        y, _ = librosa.effects.trim(y, top_db=20)
        if len(y) > self.max_len:
            y = y[: self.max_len]
        else:
            y = np.pad(y, (0, self.max_len - len(y)))

        mfcc    = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=self.n_mfcc)
        delta1  = librosa.feature.delta(mfcc)
        delta2  = librosa.feature.delta(mfcc, order=2)
        chroma  = librosa.feature.chroma_stft(y=y, sr=sr)
        contrast= librosa.feature.spectral_contrast(y=y, sr=sr)
        zcr     = librosa.feature.zero_crossing_rate(y)
        rms     = librosa.feature.rms(y=y)

        parts = []
        for feat in (mfcc, delta1, delta2, chroma, contrast, zcr, rms):
            parts += [feat.mean(axis=1), feat.std(axis=1)]

        return np.concatenate(parts).reshape(1, -1)