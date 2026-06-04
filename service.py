#!/usr/bin/env python3
from __future__ import annotations

import socket
import threading
import time
from pathlib import Path

from convert_bin_to_wav import convert_file
from delete_command import delete_all_files
from errors import SerialConnectionError, TransferError, UserInputError
from get_file import GET_FILE
from list_command import list_files
from stm32_detector import find_stm32_port

HOST = "127.0.0.1"
PORT = 5000
MONITOR_INTERVAL_SEC = 1.0


class ClientChannel:
    def __init__(self, conn: socket.socket):
        self.conn = conn
        self._lock = threading.Lock()
        self._closed = False

    def send_line(self, message: str) -> None:
        with self._lock:
            if self._closed:
                return
            try:
                self.conn.sendall(f"{message}\n".encode())
            except OSError:
                self._closed = True

    def close(self) -> None:
        with self._lock:
            self._closed = True


def _require_port() -> str:
    port = find_stm32_port()
    if not port:
        raise SerialConnectionError("STM32 is not connected")
    return port


def _convert_bin_to_wav(filename: str) -> None:
    bin_path = Path("bin_folder") / filename
    if not bin_path.is_file():
        raise TransferError(f"Downloaded file was not found: {bin_path}")
    convert_file(bin_path, Path("wav_out"), sample_rate=None)


def _select_last_filename(filenames: list[str]) -> str:
    if not filenames:
        raise TransferError("No files found on STM32.")

    def sort_key(name: str) -> tuple[int, int, str]:
        digits = "".join(ch for ch in name if ch.isdigit())
        if digits:
            return (1, int(digits), name.lower())
        return (0, -1, name.lower())

    return max(filenames, key=sort_key)


def _handle_status() -> str:
    if find_stm32_port():
        return "STM32 is connected"
    return "STM32 is not connected"


def _handle_get_file(raw_filename: str) -> str:
    filename = raw_filename.strip()
    if not filename:
        raise UserInputError("Missing filename in GET_FILE command.")

    port = _require_port()
    GET_FILE(filename, port)
    _convert_bin_to_wav(filename)
    return f"File {filename} from STM32 has been processed"


def _handle_get_all() -> str:
    port = _require_port()
    filenames = list_files(port)

    for filename in filenames:
        GET_FILE(filename, port)
        _convert_bin_to_wav(filename)

    return "All files from STM32 are processed"


def _handle_get_last() -> str:
    port = _require_port()
    filenames = list_files(port)
    filename = _select_last_filename(filenames)
    GET_FILE(filename, port)
    _convert_bin_to_wav(filename)
    return "Last file from STM32 has been processed"


def _handle_delete() -> str:
    port = _require_port()
    delete_all_files(port)
    return "All files on STM32 are deleted"


def handle_command(command: str) -> str:
    if command == "STATUS":
        return _handle_status()
    if command == "GET_ALL":
        return _handle_get_all()
    if command == "GET_LAST":
        return _handle_get_last()
    if command == "DELETE":
        return _handle_delete()
    if command.startswith("GET_FILE|"):
        _, filename = command.split("|", 1)
        return _handle_get_file(filename)
    raise UserInputError("Unknown command")


def monitor_connection(channel: ClientChannel, stop_event: threading.Event) -> None:
    previous_port = find_stm32_port()
    while not stop_event.is_set():
        try:
            current_port = find_stm32_port()
            if current_port != previous_port:
                if current_port and not previous_port:
                    channel.send_line(f"STM32 detected at {current_port}")
                elif previous_port and not current_port:
                    channel.send_line("STM32 has disconnected")
                elif current_port:
                    channel.send_line(f"STM32 detected at {current_port}")
                previous_port = current_port
        except Exception:
            # Monitoring errors should never crash the service loop.
            pass
        stop_event.wait(MONITOR_INTERVAL_SEC)


def _connected_banner() -> str:
    port = find_stm32_port()
    if port:
        return f"Connected to SPO STM32 service - STM32 detected at {port}"
    return "Connected to SPO STM32 service - No STM32 detected"


def handle_client(conn: socket.socket, addr) -> None:
    channel = ClientChannel(conn)
    stop_event = threading.Event()
    monitor_thread = threading.Thread(
        target=monitor_connection, args=(channel, stop_event), daemon=True
    )

    with conn:
        channel.send_line(_connected_banner())
        monitor_thread.start()

        buffer = ""
        while True:
            try:
                data = conn.recv(1024)
                if not data:
                    break
                buffer += data.decode(errors="ignore")
                lines = buffer.splitlines(keepends=False)
                if not buffer.endswith("\n"):
                    buffer = lines.pop() if lines else buffer
                else:
                    buffer = ""

                for line in lines:
                    command = line.strip()
                    if not command:
                        continue
                    try:
                        response = handle_command(command)
                    except (SerialConnectionError, TransferError, UserInputError) as e:
                        response = f"FAIL: {e}"
                    except Exception as e:
                        response = f"FAIL: Unexpected error: {e}"
                    channel.send_line(response)
            except OSError:
                break

    stop_event.set()
    channel.close()
    try:
        monitor_thread.join(timeout=1.0)
    except RuntimeError:
        pass
    print(f"Client disconnected: {addr}")


def main() -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((HOST, PORT))
        server.listen()
        print(f"SPO STM32 service listening on {HOST}:{PORT}")

        while True:
            conn, addr = server.accept()
            print(f"Client connected: {addr}")
            thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            thread.start()


if __name__ == "__main__":
    main()
