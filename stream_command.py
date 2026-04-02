import serial
import time
import sys

def STREAM():
    ser = serial.Serial('COM5', 9600, timeout=4)
    time.sleep(2)

    command = "STREAM" +'\n'
    print(command)
    max_retries = 4
    attempt = 0

    while attempt < max_retries:
        ser.write(command.encode())
        print("Ukaz poslan, poskus:", attempt + 1)

        response = ser.readline().decode().strip()
        print("Odgovor:", response)

        if "ERROR: Unknown command" not in response:
            break
        attempt += 1
        time.sleep(2)

    with open("stream.bin", "wb") as f:
        while True:
            data = ser.read(1024)
            if not data:
                break
            f.write(data)
    print("Prenos končan")

    ser.close()