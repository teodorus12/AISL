#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert all BIN files in a folder to WAV."
    )
    parser.add_argument(
        "folder",
        nargs="?",
        default=".",
        help="Folder with BIN files (default: current folder).",
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
        help="Force sample rate in Hz (optional).",
    )
    args = parser.parse_args()

    folder = Path(args.folder)
    if not folder.is_dir():
        print(f"Folder does not exist: {folder}")
        return 1

    cmd = [
        sys.executable,
        str(Path(__file__).with_name("convert_bin_to_wav.py")),
        str(folder),
        "-o",
        args.output_dir,
    ]
    if args.sample_rate is not None:
        cmd.extend(["--sample-rate", str(args.sample_rate)])

    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
