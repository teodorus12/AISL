"""Prepoznava besede iz WAV z naloženim modelom ai1.0.pkl."""

from __future__ import annotations
from audio_recognition import NeuralNetwork, AudioProcessor

import pickle
from pathlib import Path

import librosa
import numpy as np

DEFAULT_MODEL_PATH = Path("ai4.pkl")

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
    model_path: str | Path = DEFAULT_MODEL_PATH,) -> str:
    wav_path = Path(wav_path)
    if not wav_path.is_file():
        raise FileNotFoundError(f"WAV datoteka ne obstaja: {wav_path}")

    nn, labels, proc = load_model(model_path)
    vec = proc.wav_to_vector(wav_path)
    out = nn.forward(vec)
    idx = int(np.argmax(out))
    return labels[idx]
