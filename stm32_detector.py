from __future__ import annotations

import serial.tools.list_ports

STM32_VID = 0x0483
STM32_PID = 0x5740


def find_stm32_port() -> str | None:
    """Return serial device path for STM32 (VID/PID), else None."""
    for port in serial.tools.list_ports.comports():
        if port.vid == STM32_VID and port.pid == STM32_PID:
            return port.device
    return None
