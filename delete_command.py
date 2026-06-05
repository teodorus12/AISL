from __future__ import annotations

import serial
import time

from errors import SerialConnectionError, TransferError


def delete_all_files(port: str | None) -> None:
    if not port:
        raise SerialConnectionError("STM32 is not connected.")

    try:
        with serial.Serial(port, 9600, timeout=4) as ser:
            time.sleep(2)

            command = "DELETE\n"
            max_retries = 4
            attempt = 0

            while attempt < max_retries:
                ser.write(command.encode())
                response = ser.readline().decode(errors="ignore").strip()

                if "ERROR: Unknown command" not in response:
                    return

                attempt += 1
                time.sleep(2)

            raise TransferError("Device did not accept DELETE command (unknown command).")
    except serial.SerialException as e:
        raise SerialConnectionError(f"Failed to open serial port {port}: {e}") from e
