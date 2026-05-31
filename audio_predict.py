"""Predict a word from a WAV file using a saved model."""

from __future__ import annotations
from pathlib import Path

import numpy as np
from audio_recognition import NeuralNetwork, AudioProcessor

DEFAULT_MODEL_PATH = Path("ai6.pkl")

_model_cache: tuple[NeuralNetwork, AudioProcessor] | None = None


def load_model(
    model_path: str | Path = DEFAULT_MODEL_PATH,
) -> tuple[NeuralNetwork, AudioProcessor]:
    global _model_cache
    path = Path(model_path)
    if not path.is_file():
        raise FileNotFoundError(f"Model not found: {path.resolve()}")
    if _model_cache is None:
        nn = NeuralNetwork.load(path)         
        _model_cache = (nn, AudioProcessor())
    return _model_cache


def predict_word(
    wav_path: str | Path,
    model_path: str | Path = DEFAULT_MODEL_PATH,
) -> str:
    wav_path = Path(wav_path)
    if not wav_path.is_file():
        raise FileNotFoundError(f"WAV file not found: {wav_path}")

    nn, proc = load_model(model_path)
    vec = proc.wav_to_vector(wav_path)        
    out = nn.forward(vec)
    return nn.labels[int(np.argmax(out))]