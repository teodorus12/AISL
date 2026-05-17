"""Prepoznava besede iz WAV z naloženim modelom ai1.0.pkl."""

from __future__ import annotations

import pickle
from pathlib import Path

import librosa
import numpy as np

DEFAULT_MODEL_PATH = Path("ai1.0.pkl")


class NeuralNetwork:
    def __init__(self, input_size, hidden_size, output_size, lr=0.01):
        self.lr = lr
        self.W1 = np.random.randn(input_size, hidden_size) * 0.1
        self.b1 = np.zeros((1, hidden_size))
        self.W2 = np.random.randn(hidden_size, output_size) * 0.1
        self.b2 = np.zeros((1, output_size))

    def sigmoid(self, x):
        return 1 / (1 + np.exp(-x))

    def softmax(self, x):
        x = x - np.max(x, axis=1, keepdims=True)
        exp = np.exp(x)
        return exp / np.sum(exp, axis=1, keepdims=True)

    def forward(self, X):
        z1 = X @ self.W1 + self.b1
        a1 = self.sigmoid(z1)
        z2 = a1 @ self.W2 + self.b2
        return self.softmax(z2)

    @staticmethod
    def load(path: str | Path, lr=0.01):
        with open(path, "rb") as f:
            data = pickle.load(f)

        nn = NeuralNetwork(
            input_size=data["W1"].shape[0],
            hidden_size=data["W1"].shape[1],
            output_size=data["W2"].shape[1],
            lr=lr,
        )
        nn.W1 = data["W1"]
        nn.b1 = data["b1"]
        nn.W2 = data["W2"]
        nn.b2 = data["b2"]
        return nn, data["labels"]


class AudioProcessor:
    def __init__(self, n_mfcc=20):
        self.n_mfcc = n_mfcc

    def wav_to_vector(self, path: str | Path):
        y, sr = librosa.load(path, sr=16000)
        y, _ = librosa.effects.trim(y)

        target = 16000
        if len(y) < target:
            y = np.pad(y, (0, target - len(y)))
        else:
            y = y[:target]

        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=self.n_mfcc)
        mean = np.mean(mfcc, axis=1)
        std = np.std(mfcc, axis=1)
        vec = np.concatenate([mean, std])
        return vec.reshape(1, -1)


_model_cache: tuple[NeuralNetwork, list[str], AudioProcessor] | None = None


def load_model(model_path: str | Path = DEFAULT_MODEL_PATH) -> tuple[NeuralNetwork, list[str], AudioProcessor]:
    global _model_cache
    path = Path(model_path)
    if not path.is_file():
        raise FileNotFoundError(f"Model ni najden: {path.resolve()}")

    if _model_cache is None:
        nn, labels = NeuralNetwork.load(path)
        _model_cache = (nn, labels, AudioProcessor())

    return _model_cache


def predict_word(
    wav_path: str | Path,
    model_path: str | Path = DEFAULT_MODEL_PATH,
) -> str:
    wav_path = Path(wav_path)
    if not wav_path.is_file():
        raise FileNotFoundError(f"WAV datoteka ne obstaja: {wav_path}")

    nn, labels, proc = load_model(model_path)
    vec = proc.wav_to_vector(wav_path)
    out = nn.forward(vec)
    idx = int(np.argmax(out))
    return labels[idx]
