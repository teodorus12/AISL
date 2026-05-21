"""Beseda -> črke -> videi znakov v signs_data/."""

from __future__ import annotations

import sys
import unicodedata
from pathlib import Path

from audio_predict import DEFAULT_MODEL_PATH, predict_word
from errors import UserInputError

SIGNS_DIR = Path("signs_data")
TESTING_DIR = Path("testing_data")
VIDEO_EXTENSIONS = (".mov", ".mp4", ".avi", ".mkv")


def _letter_key(char: str) -> str:
    return unicodedata.normalize("NFC", char).upper()


def word_to_letters(word: str) -> list[str]:
    word = word.strip()
    if not word:
        return []
    return [_letter_key(c) for c in word]


def build_sign_index(signs_dir: Path = SIGNS_DIR) -> dict[str, Path]:
    if not signs_dir.is_dir():
        raise FileNotFoundError(f"Mapa z videi ne obstaja: {signs_dir.resolve()}")

    index: dict[str, Path] = {}
    for path in signs_dir.iterdir():
        if path.suffix.lower() not in VIDEO_EXTENSIONS:
            continue
        key = _letter_key(path.stem)
        index[key] = path
    return index


def resolve_sign_videos(
    letters: list[str],
    signs_dir: Path = SIGNS_DIR,
) -> tuple[list[Path], list[str]]:
    index = build_sign_index(signs_dir)
    found: list[Path] = []
    missing: list[str] = []

    for letter in letters:
        path = index.get(letter)
        if path is None:
            missing.append(letter)
        else:
            found.append(path)

    return found, missing


def _play_with_opencv(video_path: Path, window_title: str) -> bool:
    try:
        import cv2
    except ImportError:
        return False

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return False

    cv2.namedWindow(window_title, cv2.WINDOW_NORMAL)

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        cv2.imshow(window_title, frame)
        key = cv2.waitKey(25) & 0xFF
        if key in (ord("q"), 27):
            cap.release()
            cv2.destroyAllWindows()
            return False

    cap.release()
    cv2.destroyAllWindows()
    return True


def play_sign_videos(
    video_paths: list[Path],
    letters: list[str] | None = None,
) -> None:
    if not video_paths:
        print("Ni videov za predvajanje.")
        return

    letters = letters or [p.stem for p in video_paths]
    use_opencv = True

    for letter, path in zip(letters, video_paths):
        title = f"Znak: {letter}"
        print(f"  Predvajam: {letter} ({path.name})")
        if use_opencv:
            ok = _play_with_opencv(path, title)
            if not ok:
                use_opencv = False
                print("  (OpenCV ni na voljo ali video ni bil odprt — nadaljujem z odprtjem v sistemu)")

        if not use_opencv:
            import subprocess

            if sys.platform == "darwin":
                subprocess.run(["open", str(path)], check=False)
                input(f"  Pritisni Enter po ogledu znaka {letter} ...")
            else:
                print(f"  Odpri ročno: {path.resolve()}")


def list_testing_wavs(testing_dir: Path = TESTING_DIR) -> list[Path]:
    if not testing_dir.is_dir():
        raise FileNotFoundError(f"Mapa testing_data ne obstaja: {testing_dir.resolve()}")
    return sorted(testing_dir.glob("*.wav"))


def pick_testing_wav() -> Path:
    files = list_testing_wavs()
    if not files:
        raise UserInputError("V testing_data ni WAV datotek.")

    print("\nTestne datoteke (testing_data/):")
    for i, path in enumerate(files, start=1):
        print(f"  {i:2}. {path.name}")

    choice = input("Izberi številko: ").strip()
    if not choice.isdigit():
        raise UserInputError("Vnesi številko iz seznama.")
    idx = int(choice)
    if idx < 1 or idx > len(files):
        raise UserInputError(f"Neveljavna izbira: {choice}")
    return files[idx - 1]


def recognize_and_play_signs(
    wav_path: Path | None = None,
    model_path: Path = DEFAULT_MODEL_PATH,
) -> None:
    if wav_path is None:
        wav_path = pick_testing_wav()
    else:
        wav_path = Path(wav_path)

    print(f"\nAnaliziram: {wav_path.name}")
    word = predict_word(wav_path, model_path)
    print(f"Prepoznana beseda: {word}")

    letters = word_to_letters(word)
    print(f"Znaki: {' '.join(letters)}")

    videos, missing = resolve_sign_videos(letters)
    if missing:
        raise UserInputError(
            f"Manjkajo videi za znake: {', '.join(missing)} "
            f"(pričakovano v {SIGNS_DIR}/ npr. Č.mov)"
        )

    print("\nPredvajanje znakov (q = prekini trenutni video, Ctrl+C = končaj):")
    play_sign_videos(videos, letters)
