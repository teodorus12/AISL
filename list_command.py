import serial
import time

def list_command():
    ser = serial.Serial('COM5', 9600, timeout=4)
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

    # Print incoming data instead of saving to file
    while True:
        data = ser.read(1024)
        if not data:
            break

        # Option 1: raw bytes
        print(data)

        # Option 2 (cleaner): hex format
        # print(data.hex())

        # Option 3 (if it's text):
        # print(data.decode(errors="ignore"), end="")

    print("Prenos končan")

    ser.close()