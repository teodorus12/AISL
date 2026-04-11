import serial
import time

from errors import SerialConnectionError, TransferError

def list_command():
    try:
        with serial.Serial('COM5', 9600, timeout=4) as ser:
            time.sleep(2)

            command = "LIST" + '\n'
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
                raise TransferError("Device did not accept LIST command (unknown command).")

            read_any = False
            # Print incoming data instead of saving to file
            while True:
                data = ser.read(1024)
                if not data:
                    break
                read_any = True

                # Option 1: raw bytes
                print(data)

                # Option 2 (cleaner): hex format
                # print(data.hex())

                # Option 3 (if it's text):
                # print(data.decode(errors="ignore"), end="")

            if not read_any:
                raise TransferError("No data received (timeout).")

            print("Prenos končan")
    except serial.SerialException as e:
        raise SerialConnectionError(f"Failed to open serial port COM5: {e}") from e