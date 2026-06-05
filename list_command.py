from __future__ import annotations

import re
import serial
import time

from errors import SerialConnectionError, TransferError


def list_files(port: str | None) -> list[str]:
    if not port:
        raise SerialConnectionError("STM32 is not connected.")

    try:
        with serial.Serial(port, 9600, timeout=4) as ser:
            time.sleep(2)

            command = "LIST\n"
            print(command.strip())

            max_retries = 4
            attempt = 0

            while attempt < max_retries:
                ser.write(command.encode())
                print("Ukaz poslan, poskus:", attempt + 1)

                response = ser.readline().decode(errors="ignore").strip()
                print("Odgovor:", response)

                if "ERROR: Unknown command" not in response:
                    break

                attempt += 1
                time.sleep(2)

            if attempt >= max_retries:
                raise TransferError("Device did not accept LIST command (unknown command).")

            payload = bytearray()
            while True:
                data = ser.read(1024)
                if not data:
                    break
                payload.extend(data)

            if not payload:
                return []

            text = payload.decode(errors="ignore")
            names = re.findall(r"[A-Za-z0-9_.-]+\.BIN", text, flags=re.IGNORECASE)
            unique_names: list[str] = []
            seen: set[str] = set()
            for name in names:
                normalized = name.strip()
                key = normalized.lower()
                if key in seen:
                    continue
                seen.add(key)
                unique_names.append(normalized)

            return unique_names
    except serial.SerialException as e:
        raise SerialConnectionError(f"Failed to open serial port {port}: {e}") from e


def list_command(port: str | None):
    names = list_files(port)
    if not names:
        print("No files found on STM32.")
        return

    for name in names:
        print(name)

    print("Prenos končan")