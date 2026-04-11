"""
Project-level exceptions for consistent error handling.

These are intended to be raised from command modules (e.g. `get_file.py`)
and handled centrally in `main.py` to produce user-friendly output.
"""


class AISLError(Exception):
    """Base class for all project-level errors."""


class UserInputError(AISLError):
    """Raised when user input is invalid (e.g., filename/command)."""


class SerialConnectionError(AISLError):
    """Raised when the serial port cannot be opened or configured."""


class TransferError(AISLError):
    """Raised when a transfer/stream fails, times out, or is incomplete."""

