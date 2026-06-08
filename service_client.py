"""TCP client for the local STM32 service (127.0.0.1:5000)."""

from __future__ import annotations

import socket
import threading
import time
from collections import deque
from queue import Empty, Queue

SERVICE_HOST = "127.0.0.1"
SERVICE_PORT = 5000
MAX_LOG_LINES = 200


class ServiceClient:
    def __init__(self, host: str = SERVICE_HOST, port: int = SERVICE_PORT):
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
