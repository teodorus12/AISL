from stream_command import STREAM
from list_command import list_command
from get_file import GET_FILE
from create_packets_final import CREATE_PACKETS
import os

from errors import AISLError, SerialConnectionError, TransferError, UserInputError

def print_HELP():
    os.system('cls' if os.name == 'nt' else 'clear')
    print("0. HELP")
    print("1. get file")
    print("2. create packets")
    print("3. stream")
    print("4. list")
    print("5. clear chunks")
    print("6. sestavi podatke")
    print("7. prikazi podatke")
    print("8. EXIT")

if __name__ == "__main__":
    chunks = []
    print_HELP()
    while True:
        variable = input("chose command :")
        try:
            if variable == "0":
                print_HELP()
            elif variable == "1":
                filename = input("What file would you like to download?")
                GET_FILE(filename)

            elif variable == "2":
                filename = input("What file would you like to transofrm into packets?")
                if not isinstance(filename, str) or not filename.strip():
                    raise UserInputError("Filename must be a non-empty string.")
                chunks = CREATE_PACKETS(filename.strip())
                for c in chunks:
                    print(c["id"])
                    print(c["data"])
                    print(c["timestamp"])

            elif variable == "3":
                STREAM()

            elif variable == "4":
                list_command()

            elif variable == "5":
                chunks.clear()

            elif variable == "6":
                print("Not Implemented")
                input("Press any key to continue...")

            elif variable == "7":
                print("Not Implemented")
                input("Press any key to continue...")

            elif variable == "8":
                break
            else:
                raise UserInputError(f"Unknown command '{variable}'. Choose 0-8.")
        except UserInputError as e:
            print(f"Input error: {e}")
        except SerialConnectionError as e:
            print(f"Serial connection error: {e}")
        except TransferError as e:
            print(f"Transfer error: {e}")
        except AISLError as e:
            print(f"Error: {e}")
        except OSError as e:
            print(f"File error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")
