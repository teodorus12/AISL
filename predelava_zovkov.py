import os
import numpy as np
import librosa
import soundfile as sf
import noisereduce as nr
from scipy.signal import butter, filtfilt

INPUT_DIR = "testing_data"
OUTPUT_DIR = "output_wav"

TARGET_PEAK = 0.98  # peak normalization

os.makedirs(OUTPUT_DIR, exist_ok=True)


def highpass_filter(y, sr, cutoff=80):
    b, a = butter(4, cutoff / (sr / 2), btype="high")
    return filtfilt(b, a, y)


def process(path, out_path):
    y, sr = librosa.load(path, sr=None, mono=True)

    # 1. high-pass filter (removes low rumble / DC noise)
    y = highpass_filter(y, sr)

    # 2. noise reduction without noise profile
    y = nr.reduce_noise(y=y, sr=sr, stationary=False)

    # 3. peak normalization (better for short clips than LUFS)
    peak = np.max(np.abs(y))
    if peak > 0:
        y = y / peak

    y = y * TARGET_PEAK

    sf.write(out_path, y, sr)


def batch():
    for f in os.listdir(INPUT_DIR):
        if f.lower().endswith(".wav"):
            print("Processing:", f)
            process(
                os.path.join(INPUT_DIR, f),
                os.path.join(OUTPUT_DIR, f)
            )


if __name__ == "__main__":
    batch()