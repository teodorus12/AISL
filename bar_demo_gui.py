"""Combined bar demo: live hand tracking + audio order recognition."""

from __future__ import annotations

import subprocess
import sys
import threading
import time
import unicodedata
from pathlib import Path

import numpy as np

from audio_predict import DEFAULT_MODEL_PATH, load_model
from hand_tracking.HT_ai import SignRecogniser
from hand_tracking.HT_bar_window import BarDemoWindow
from hand_tracking.HT_camera_handler import CameraHandler
from hand_tracking.HT_dataset_recorder import DatasetRecorder
from hand_tracking.HT_frame_handler import FrameProcessor
from hand_tracking.HT_handler import HandTracker
from hand_tracking.HT_landmark_drawer import LandMarkDrawer
from hand_tracking.HT_serializer import Serializer
from sign_videos import (
    TESTING_DIR,
    list_testing_wavs,
    play_sign_videos,
    resolve_sign_videos,
    word_to_letters,
)
from service_client import SERVICE_HOST, SERVICE_PORT, ServiceClient

WORD_SIGNS_DIR = Path("SIGN_WORDS")
WAV_OUT_DIR = Path("wav_out")
VIDEO_EXTENSIONS = (".mov", ".mp4", ".avi", ".mkv")
LAST_AUDIO_RESULT: dict = {}


def _list_wav_names() -> list[str]:
    if not TESTING_DIR.is_dir():
        return []
    return [path.name for path in list_testing_wavs()]


def _safe_audio_filename(raw_name: str) -> str:
    filename = Path(raw_name).name
    if not filename.lower().endswith(".wav"):
        raise ValueError("Filename must be a .wav file.")
    return filename


def _normalize_word_key(word: str) -> str:
    normalized = unicodedata.normalize("NFKD", word).encode("ascii", "ignore").decode("ascii")
    return normalized.strip().upper()


def _resolve_word_sign_video_path(word: str) -> Path | None:
    if not WORD_SIGNS_DIR.is_dir():
        return None

    target = _normalize_word_key(word)
    for path in WORD_SIGNS_DIR.iterdir():
        if path.suffix.lower() not in VIDEO_EXTENSIONS:
            continue
        if _normalize_word_key(path.stem) == target:
            return path
    return None


def _latest_wav_in_out() -> Path | None:
    if not WAV_OUT_DIR.is_dir():
        return None
    wavs = sorted(WAV_OUT_DIR.glob("*.wav"), key=lambda p: p.stat().st_mtime, reverse=True)
    return wavs[0] if wavs else None


def _predict_wav_path(wav_path: Path) -> dict:
    if not wav_path.is_file():
        raise FileNotFoundError(f"WAV file not found: {wav_path}")

    nn, proc = load_model(DEFAULT_MODEL_PATH)
    vec = proc.wav_to_vector(wav_path)
    out = nn.forward(vec)[0]
    idx = int(np.argmax(out))
    word = nn.labels[idx]
    confidence = float(out[idx])
    word_video = _resolve_word_sign_video_path(word)

    letters = word_to_letters(word)
    letter_videos, missing = resolve_sign_videos(letters)

    return {
        "word": word,
        "confidence": round(confidence, 4),
        "word_video": word_video,
        "letter_videos": letter_videos,
        "missing_letters": missing,
        "wav_path": wav_path,
        "source_file": wav_path.name,
    }


def _predict_audio(filename: str) -> dict:
    return _predict_wav_path(TESTING_DIR / _safe_audio_filename(filename))


def _play_wav_file(wav_path: Path) -> None:
    if not wav_path.is_file():
        raise FileNotFoundError(f"WAV file not found: {wav_path}")

    if sys.platform == "darwin":
        subprocess.Popen(["afplay", str(wav_path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return

    if sys.platform == "win32":
        import winsound

        winsound.PlaySound(str(wav_path), winsound.SND_FILENAME | winsound.SND_ASYNC)
        return

    subprocess.Popen(["xdg-open", str(wav_path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _play_prediction_videos(result: dict) -> None:
    word = result["word"]
    word_video = result.get("word_video")
    if word_video is not None and Path(word_video).is_file():
        play_sign_videos([Path(word_video)], [word.upper()])
        return

    letter_videos = result.get("letter_videos") or []
    letters = word_to_letters(word)
    if letter_videos:
        play_sign_videos(letter_videos, letters)


class BarDemoApp:
    def __init__(self):
        self.camera_handler = CameraHandler()
        self.hand_tracker = HandTracker()
        self.landmark_drawer = LandMarkDrawer()
        self.frame_processor = FrameProcessor(self.hand_tracker, self.landmark_drawer)
        self.serializer = Serializer()
        self.recorder = DatasetRecorder()
        self.recogniser = SignRecogniser()
        self.current_label = "A"
        self.running = False
        self._playback_thread: threading.Thread | None = None
        self._stm32_thread: threading.Thread | None = None
        self.service_client = ServiceClient(SERVICE_HOST, SERVICE_PORT)

        self.window = BarDemoWindow(
            wav_files=_list_wav_names(),
            on_refresh=self.on_refresh_files,
            on_predict=self.on_predict_audio,
            on_play_wav=self.on_play_wav,
            on_play_signs=self.on_play_signs,
            on_fetch_stm32=self.on_fetch_stm32_last,
        )
        self.setup_keybinds()

    def setup_keybinds(self) -> None:
        self.window.root.bind("<KeyPress>", self.on_key_press)
        self.window.root.bind("<KeyRelease-Return>", self.on_enter_release)

    def on_key_press(self, event) -> None:
        key = event.keysym.upper()

        if key == "RETURN":
            if not self.recorder.rec:
                self.recorder.start_recording(self.current_label)
            return

        if key == "SPACE":
            self.current_label = "SPACE"
            self.window.set_lbl(self.current_label)
            return

        if len(key) == 1 and key.isalpha():
            self.current_label = key
            self.window.set_lbl(self.current_label)

    def on_enter_release(self, event) -> None:
        self.recorder.stop_recording()

    def on_refresh_files(self) -> None:
        files = _list_wav_names()
        self.window.set_wav_files(files)
        if files:
            self.window.set_audio_result(f"pripravljeno · {len(files)} testnih posnetkov")
        else:
            self.window.set_audio_result("ni testnih posnetkov v testing_data/")

    def on_play_wav(self) -> None:
        filename = self.window.get_selected_wav()
        if not filename:
            self.window.set_audio_result("izberi posnetek s seznama")
            return

        wav_path = TESTING_DIR / filename
        try:
            _play_wav_file(wav_path)
            self.window.set_audio_result(f"predvajanje · {filename}")
        except Exception as e:
            self.window.set_audio_result(f"Napaka pri predvajanju WAV: {e}")

    def _apply_audio_result(self, result: dict, *, source_prefix: str = "") -> None:
        global LAST_AUDIO_RESULT
        LAST_AUDIO_RESULT = result

        pct = int(result["confidence"] * 100)
        missing = result.get("missing_letters") or []
        suffix = f" | Manjka: {', '.join(missing)}" if missing else ""
        prefix = f"{source_prefix} · " if source_prefix else ""
        self.window.set_highlighted_product(result["word"])
        self.window.set_audio_result(f"{prefix}{result['word'].upper()} ({pct}%){suffix}")
        self._start_video_playback(result)

    def on_predict_audio(self) -> None:
        filename = self.window.get_selected_wav()
        if not filename:
            self.window.set_audio_result("izberi posnetek s seznama")
            return

        try:
            result = _predict_audio(filename)
        except Exception as e:
            self.window.set_audio_result(f"Napaka: {e}")
            return

        self._apply_audio_result(result)

    def on_fetch_stm32_last(self) -> None:
        if self._stm32_thread and self._stm32_thread.is_alive():
            return

        self.window.set_stm32_busy(True)
        self.window.set_stm32_status("Prenašam zadnjo datoteko s STM32…")
        self._stm32_thread = threading.Thread(target=self._fetch_stm32_worker, daemon=True)
        self._stm32_thread.start()

    def _fetch_stm32_worker(self) -> None:
        try:
            ok, message = self.service_client.send_command("GET_LAST", timeout_sec=30.0)
            if not ok:
                self._schedule_stm32_status(f"Napaka: {message}")
                return

            time.sleep(0.5)
            wav = _latest_wav_in_out()
            if wav is None:
                self._schedule_stm32_status("Ni WAV datoteke v wav_out/ po prenosu.")
                return

            result = _predict_wav_path(wav)
            self.window.root.after(
                0,
                lambda: self._on_stm32_success(result, wav.name),
            )
        except Exception as e:
            self._schedule_stm32_status(f"Napaka: {e}")
        finally:
            self.window.root.after(0, lambda: self.window.set_stm32_busy(False))

    def _schedule_stm32_status(self, text: str) -> None:
        self.window.root.after(0, lambda: self.window.set_stm32_status(text))

    def _on_stm32_success(self, result: dict, wav_name: str) -> None:
        self.window.set_stm32_status(f"Datoteka: {wav_name}")
        self._apply_audio_result(result, source_prefix=f"STM32 · {wav_name}")

    def on_play_signs(self) -> None:
        if not LAST_AUDIO_RESULT:
            self.window.set_audio_result("najprej pritisni Prepoznaj naročilo")
            return
        self._start_video_playback(LAST_AUDIO_RESULT)

    def _start_video_playback(self, result: dict) -> None:
        if self._playback_thread and self._playback_thread.is_alive():
            return

        missing = result.get("missing_letters") or []
        if missing and not result.get("word_video"):
            self.window.set_audio_result(
                f'{result["word"].upper()} | manjkajo videi: {", ".join(missing)}'
            )
            return

        self._playback_thread = threading.Thread(
            target=_play_prediction_videos,
            args=(result,),
            daemon=True,
        )
        self._playback_thread.start()

    def start(self) -> None:
        self.service_client.connect()
        self.camera_handler.open_camera()
        self.running = True
        self.recorder = DatasetRecorder()
        self.current_label = "A"
        self.window.set_close_callback(self.stop)
        self.update_loop()
        self.window.start()

    def update_loop(self) -> None:
        if not self.running:
            return

        succ, frame = self.camera_handler.read_frame()
        if succ:
            processed_frame = self.frame_processor.process(frame)
            detection_rez = self.hand_tracker.process(frame)

            if detection_rez.hand_landmarks:
                hand_landmarks = detection_rez.hand_landmarks[0]
                f_data = self.serializer.vektor_processor(hand_landmarks)
                label, conf = self.recogniser.predict(f_data)
                self.window.set_prediction(label, conf)
                self.recorder.add_frame_data(f_data)
            else:
                self.recogniser.reset()
                self.window.set_prediction("—", 0.0)

            self.window.update_video(processed_frame)

        self.window.after(10, self.update_loop)

    def stop(self) -> None:
        self.running = False
        self.service_client.close()
        self.camera_handler.release_camera()
        self.hand_tracker.close()
        self.window.destroy()


def bar_demo_startup() -> None:
    app = BarDemoApp()
    app.start()


if __name__ == "__main__":
    bar_demo_startup()
