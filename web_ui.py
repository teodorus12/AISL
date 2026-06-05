#!/usr/bin/env python3
from __future__ import annotations

import base64
import binascii
import socket
import threading
import time
import unicodedata
from collections import deque
from pathlib import Path
from queue import Empty, Queue

import numpy as np
from flask import Flask, jsonify, render_template, request, send_from_directory

from audio_predict import load_model
from sign_videos import SIGNS_DIR, TESTING_DIR, list_testing_wavs, resolve_sign_videos, word_to_letters

SERVICE_HOST = "127.0.0.1"
SERVICE_PORT = 5000
WEB_HOST = "127.0.0.1"
WEB_PORT = 8000
MAX_LOG_LINES = 200
WORD_SIGNS_DIR = Path("SIGN_WORDS")
VIDEO_EXTENSIONS = (".mov", ".mp4", ".avi", ".mkv")

app = Flask(__name__)


class ServiceClient:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self._sock: socket.socket | None = None
        self._reader: threading.Thread | None = None
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._response_queue: Queue[str] = Queue()
        self.logs: deque[str] = deque(maxlen=MAX_LOG_LINES)

    def _append_log(self, line: str) -> None:
        if line:
            self.logs.append(line)

    def _reader_loop(self) -> None:
        while not self._stop_event.is_set():
            with self._lock:
                sock = self._sock

            if sock is None:
                time.sleep(0.3)
                continue

            try:
                data = sock.recv(1024)
                if not data:
                    self._append_log("Service disconnected.")
                    with self._lock:
                        try:
                            sock.close()
                        except OSError:
                            pass
                        self._sock = None
                    continue

                for line in data.decode(errors="ignore").splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    self._append_log(line)
                    self._response_queue.put(line)
            except TimeoutError:
                # Keep connection alive on read timeout; just wait for more data.
                continue
            except OSError:
                with self._lock:
                    try:
                        sock.close()
                    except OSError:
                        pass
                    self._sock = None
                time.sleep(0.3)

    def connect(self) -> tuple[bool, str]:
        with self._lock:
            if self._sock is not None:
                return True, "Connected"
            try:
                self._sock = socket.create_connection((self.host, self.port), timeout=3)
                # create_connection timeout is for connect phase only;
                # keep socket in blocking mode afterwards to avoid false disconnects.
                self._sock.settimeout(None)
            except OSError:
                self._sock = None
                msg = f"Service is not reachable on {self.host}:{self.port}"
                self._append_log(msg)
                return False, msg

        if self._reader is None or not self._reader.is_alive():
            self._reader = threading.Thread(target=self._reader_loop, daemon=True)
            self._reader.start()
        return True, "Connected"

    def _is_monitor_line(self, line: str) -> bool:
        if line.startswith("Connected to SPO STM32 service"):
            return True
        if line.startswith("STM32 detected at "):
            return True
        if line == "STM32 has disconnected":
            return True
        return False

    def send_command(self, command: str, timeout_sec: float = 6.0) -> tuple[bool, str]:
        ok, message = self.connect()
        if not ok:
            return False, message

        with self._lock:
            if self._sock is None:
                msg = f"Service is not reachable on {self.host}:{self.port}"
                self._append_log(msg)
                return False, msg
            try:
                self._sock.sendall(f"{command}\n".encode())
            except OSError:
                self._sock = None
                msg = f"Service is not reachable on {self.host}:{self.port}"
                self._append_log(msg)
                return False, msg

        deadline = time.time() + timeout_sec
        while time.time() < deadline:
            try:
                line = self._response_queue.get(timeout=0.2)
            except Empty:
                continue
            if self._is_monitor_line(line):
                continue
            return not line.startswith("FAIL:"), line

        return False, "Timeout waiting for service response."

    def close(self) -> None:
        self._stop_event.set()
        with self._lock:
            if self._sock is not None:
                try:
                    self._sock.close()
                except OSError:
                    pass
                self._sock = None


service_client = ServiceClient(SERVICE_HOST, SERVICE_PORT)


class VideoRecognitionEngine:
    def __init__(self):
        self._lock = threading.Lock()
        self._ready = False
        self._error = ""
        self._tracker = None
        self._serializer = None
        self._recogniser = None
        self._cv2 = None
        self._init()

    def _init(self) -> None:
        with self._lock:
            if self._ready:
                return
            try:
                import cv2
                from hand_tracking.HT_ai import SignRecogniser
                from hand_tracking.HT_handler import HandTracker
                from hand_tracking.HT_serializer import Serializer
            except Exception as e:
                self._error = f"Video engine init failed: {e}"
                return

            try:
                self._tracker = HandTracker()
                self._serializer = Serializer()
                self._recogniser = SignRecogniser()
                self._cv2 = cv2
                self._ready = True
                self._error = ""
            except Exception as e:
                self._error = f"Video engine init failed: {e}"

    def predict_from_data_url(self, image_data_url: str) -> tuple[bool, dict]:
        if not self._ready:
            self._init()
        if not self._ready:
            return False, {"message": self._error or "Video engine is not ready."}

        if "," not in image_data_url:
            return False, {"message": "Invalid frame payload."}

        _, encoded = image_data_url.split(",", 1)
        try:
            raw_bytes = base64.b64decode(encoded, validate=True)
        except (binascii.Error, ValueError):
            return False, {"message": "Invalid base64 frame payload."}

        frame_array = np.frombuffer(raw_bytes, dtype=np.uint8)
        frame = self._cv2.imdecode(frame_array, self._cv2.IMREAD_COLOR)
        if frame is None:
            return False, {"message": "Failed to decode frame image."}

        detection = self._tracker.process(frame)
        if detection.hand_landmarks:
            feature_data = self._serializer.vektor_processor(detection.hand_landmarks[0])
            label, confidence = self._recogniser.predict(feature_data)
            return True, {
                "label": label,
                "confidence": round(float(confidence), 4),
            }

        self._recogniser.reset()
        return True, {
            "label": "?",
            "confidence": 0.0,
        }


video_engine = VideoRecognitionEngine()


def _safe_audio_filename(raw_name: str) -> str:
    filename = Path(raw_name).name
    if not filename.lower().endswith(".wav"):
        raise ValueError("Filename must be a .wav file.")
    return filename


def _normalize_word_key(word: str) -> str:
    normalized = unicodedata.normalize("NFKD", word).encode("ascii", "ignore").decode("ascii")
    return normalized.strip().upper()


def _resolve_word_sign_video(word: str) -> str | None:
    if not WORD_SIGNS_DIR.is_dir():
        return None

    target = _normalize_word_key(word)
    for path in WORD_SIGNS_DIR.iterdir():
        if path.suffix.lower() not in VIDEO_EXTENSIONS:
            continue
        stem_key = _normalize_word_key(path.stem)
        if stem_key == target:
            return f"/sign_words/{path.name}"
    return None


def _predict_audio(filename: str) -> dict:
    wav_path = TESTING_DIR / _safe_audio_filename(filename)
    if not wav_path.is_file():
        raise FileNotFoundError(f"WAV file not found: {wav_path}")

    nn, proc = load_model()
    vec = proc.wav_to_vector(wav_path)
    out = nn.forward(vec)[0]
    idx = int(np.argmax(out))
    word = nn.labels[idx]
    confidence = float(out[idx])
    word_video = _resolve_word_sign_video(word)

    letters = word_to_letters(word)
    videos, missing = resolve_sign_videos(letters)
    video_urls = [f"/signs/{path.name}" for path in videos]

    return {
        "word": word,
        "confidence": round(confidence, 4),
        "word_video": word_video,
        "letters": letters,
        "videos": video_urls,
        "missing_letters": missing,
    }


@app.get("/")
def index():
    service_client.connect()
    return render_template("index.html")


@app.get("/api/log")
def get_log():
    return jsonify(
        {
            "ok": True,
            "lines": list(service_client.logs),
        }
    )


@app.get("/api/audio/files")
def get_audio_files():
    try:
        files = [path.name for path in list_testing_wavs()]
        return jsonify({"ok": True, "files": files})
    except Exception as e:
        return jsonify({"ok": False, "message": str(e), "files": []})


@app.post("/api/audio/predict")
def post_audio_predict():
    payload = request.get_json(silent=True) or {}
    filename = str(payload.get("filename", "")).strip()
    if not filename:
        return jsonify({"ok": False, "message": "Filename is required."})

    try:
        result = _predict_audio(filename)
        return jsonify({"ok": True, **result})
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)})


@app.post("/api/video/predict")
def post_video_predict():
    payload = request.get_json(silent=True) or {}
    image_data = str(payload.get("imageData", "")).strip()
    if not image_data:
        return jsonify({"ok": False, "message": "Frame imageData is required."})

    ok, result = video_engine.predict_from_data_url(image_data)
    if not ok:
        return jsonify({"ok": False, **result})
    return jsonify({"ok": True, **result})


@app.get("/signs/<path:filename>")
def serve_sign_video(filename: str):
    return send_from_directory(SIGNS_DIR, filename)


@app.get("/sign_words/<path:filename>")
def serve_word_sign_video(filename: str):
    return send_from_directory(WORD_SIGNS_DIR, filename)


@app.post("/api/command")
def post_command():
    payload = request.get_json(silent=True) or {}
    action = str(payload.get("action", "")).strip().upper()
    filename = str(payload.get("filename", "")).strip()

    if action == "GET_FILE":
        if not filename:
            return jsonify({"ok": False, "message": "Filename is required for GET_FILE."})
        command = f"GET_FILE|{filename}"
    elif action in {"STATUS", "GET_ALL", "GET_LAST", "DELETE"}:
        command = action
    else:
        return jsonify({"ok": False, "message": "Unknown action."})

    ok, message = service_client.send_command(command)
    return jsonify({"ok": ok, "message": message})


if __name__ == "__main__":
    service_client.connect()
    app.run(host=WEB_HOST, port=WEB_PORT, debug=False)
