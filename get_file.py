import serial
import time
import sys

from errors import SerialConnectionError, TransferError, UserInputError

def GET_FILE(file_name):
    if not isinstance(file_name, str) or not file_name.strip():
        raise UserInputError("Filename must be a non-empty string.")

    file_name = file_name.strip()

    try:
        with serial.Serial('COM5', 9600, timeout=4) as ser:
            time.sleep(2)

            command = 'GET ' + file_name + '\n'
            print(command)
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
                raise TransferError("Device did not accept GET command (unknown command).")

            wrote_any = False
            try:
                with open(file_name, "wb") as f:
                    while True:
                        data = ser.read(1024)
                        if not data:
                            break
                        wrote_any = True
                        f.write(data)
            except OSError as e:
                raise TransferError(f"Failed to write output file '{file_name}': {e}") from e

            if not wrote_any:
                raise TransferError("No data received (timeout).")

            print("Prenos končan")
    except serial.SerialException as e:
        raise SerialConnectionError(f"Failed to open serial port COM5: {e}") from e