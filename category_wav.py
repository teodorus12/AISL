from __future__ import annotations

import re
from pathlib import Path

from convert_bin_to_wav import convert_file
from errors import UserInputError
from get_file import GET_FILE

BIN_FOLDER = "bin_folder"

CATEGORIES: tuple[tuple[str, str], ...] = (
    ("Kava", "kava"),
    ("Pivo", "pivo"),
    ("Čaj", "caj"),
    ("Sok", "sok"),
    ("viski", "viski"),
)


def _next_wav_stem(category_slug: str, category_dir: Path) -> str:
    pattern = re.compile(
        rf"^{re.escape(category_slug)} (\d{{3}})\.wav$",
        re.IGNORECASE,
    )
    max_n = 0
    if category_dir.is_dir():
        for wav_file in category_dir.glob("*.wav"):
            match = pattern.match(wav_file.name)
            if match:
                max_n = max(max_n, int(match.group(1)))
    return f"{category_slug} {max_n + 1:03d}"


def prompt_category() -> tuple[str, str]:
    print("Izberi kategorijo:")
    for i, (label, slug) in enumerate(CATEGORIES, start=1):
        print(f"  {i}. {label}  (-> mapa '{slug}/')")
    choice = input("Kategorija (1-5): ").strip()
    if not choice.isdigit():
        raise UserInputError("Vnesi številko kategorije (1-5).")
    idx = int(choice)
    if idx < 1 or idx > len(CATEGORIES):
        raise UserInputError(f"Neveljavna kategorija '{choice}'.")
    return CATEGORIES[idx - 1]


def download_bin_and_convert_by_category() -> Path:
    label, slug = prompt_category()
    filename = input("Ime BIN datoteke za prenos (npr. LOG004.BIN): ").strip()
    if not filename:
        raise UserInputError("Ime datoteke ne sme biti prazno.")

    GET_FILE(filename)

    bin_path = Path(BIN_FOLDER) / filename
    if not bin_path.is_file():
        raise FileNotFoundError(f"BIN datoteka ni bila shranjena: {bin_path}")

    category_dir = Path(slug)
    wav_stem = _next_wav_stem(slug, category_dir)
    out_path = convert_file(bin_path, category_dir, sample_rate=None, output_stem=wav_stem)

    print(f"Kategorija: {label}")
    print(f"Shranjeno: {out_path.resolve()}")
    return out_path
