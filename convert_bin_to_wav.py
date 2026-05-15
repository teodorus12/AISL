#!/usr/bin/env python3
from __future__ import annotations

import argparse
import math
import wave
from pathlib import Path

import numpy as np

from create_packets_final import CREATE_PACKETS

DEFAULT_SAMPLE_RATE = 8000


def estimate_sample_rate(audio_packets: list[dict]) -> float:
    deltas: list[float] = []
    samples_per_packet: list[int] = []

    for i in range(len(audio_packets) - 1):
        dt = float(audio_packets[i + 1]["ts"]) - float(audio_packets[i]["ts"])
        if dt <= 0:
            continue
        deltas.append(dt)
        samples_per_packet.append(int(np.asarray(audio_packets[i]["data"]).size))

    if not deltas:
        return float("nan")
    return float(np.mean(samples_per_packet) / np.mean(deltas))


def convert_file(bin_path: Path, output_dir: Path, sample_rate: int | None) -> Path:
    packets = CREATE_PACKETS(str(bin_path))
    audio_packets = [p for p in packets if p.get("id") == 4]

    if not audio_packets:
        raise ValueError(f"No audio packets (id=4) found in {bin_path.name}")

    parts = [np.asarray(p["data"], dtype=np.int16).ravel() for p in audio_packets]
    audio = np.concatenate(parts) if parts else np.array([], dtype=np.int16)
    if audio.size == 0:
        raise ValueError(f"Audio packets are present but empty in {bin_path.name}")

    estimated_sr = estimate_sample_rate(audio_packets)
    if sample_rate is not None:
        wav_sr = int(sample_rate)
    elif math.isfinite(estimated_sr) and estimated_sr > 0:
        wav_sr = int(round(estimated_sr))
    else:
        wav_sr = DEFAULT_SAMPLE_RATE

    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"{bin_path.stem}.wav"

    with wave.open(str(out_path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)  # int16
        wav_file.setframerate(wav_sr)
        wav_file.writeframes(audio.astype("<i2", copy=False).tobytes())

    print(
        f"[OK] {bin_path.name} -> {out_path.name} | "
        f"samples={audio.size}, sr={wav_sr} Hz"
    )
    return out_path


def collect_inputs(paths: list[str]) -> list[Path]:
    files: list[Path] = []
    for raw in paths:
        p = Path(raw)
        if p.is_dir():
            files.extend(sorted(p.glob("*.BIN")))
            files.extend(sorted(p.glob("*.bin")))
        elif p.is_file():
            files.append(p)

    # remove duplicates while preserving order
    dedup: list[Path] = []
    seen: set[Path] = set()
    for f in files:
        r = f.resolve()
        if r in seen:
            continue
        seen.add(r)
        dedup.append(f)
    return dedup


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert SIS BIN logs to playable WAV files."
    )
    parser.add_argument(
        "inputs",
        nargs="+",
        help="BIN file(s) and/or folders containing BIN files.",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        default="wav_out",
        help="Output folder for WAV files (default: wav_out).",
    )
    parser.add_argument(
        "--sample-rate",
        type=int,
        default=None,
        help="Force sample rate in Hz (default: auto-estimate, fallback 8000).",
    )
    args = parser.parse_args()

    if args.sample_rate is not None and args.sample_rate <= 0:
        print("Sample rate must be a positive integer.")
        return 2

    input_files = collect_inputs(args.inputs)
    if not input_files:
        print("No BIN files found in provided input paths.")
        return 1

    output_dir = Path(args.output_dir)
    failures = 0
    for bin_file in input_files:
        try:
            convert_file(bin_file, output_dir, args.sample_rate)
        except Exception as exc:  # keep converting other files
            failures += 1
            print(f"[ERR] {bin_file.name}: {exc}")

    if failures:
        print(f"Done with {failures} error(s).")
        return 1

    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
