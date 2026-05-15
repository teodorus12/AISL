from pathlib import Path

from stream_command import STREAM
from list_command import list_command
from get_file import GET_FILE
from create_packets_final import CREATE_PACKETS
from create_file import save_chunks_to_file
from Signal_decode import sestavi_podatke
from Signal_decode import prikazi_signal
import os

from errors import AISLError, SerialConnectionError, TransferError, UserInputError

WAV_OUTPUT_DIR = "wav_out"

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
    print(f"8. pretvori vse BIN v WAV (izhod: {WAV_OUTPUT_DIR}/)")
    print("9. EXIT")

def convert_all_bin_in_cwd() -> None:
    bin_files = collect_inputs(["."])
    if not bin_files:
        print("Ni BIN datotek v trenutni mapi.")
        return

    output_dir = Path(WAV_OUTPUT_DIR)
    failures = 0
    for bin_file in bin_files:
        try:
            convert_file(bin_file, output_dir, sample_rate=None)
        except Exception as exc:
            failures += 1
            print(f"[ERR] {bin_file.name}: {exc}")

    if failures:
        print(f"Končano z {failures} napako/ami.")
    else:
        print(f"Vse BIN datoteke pretvorjene v {output_dir.resolve()}/")

if __name__ == "__main__":
    chunks = []
    Fvz = 0
    signal = []
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
                chunks = CREATE_PACKETS(filename)
                for c in chunks:
                    #print(c["id"])
                    print(c["data"])
                    print(c["timestamp"])
                
                save_chunks_to_file(chunks)
                print("Chunks saved to packets.txt")
            
            
            elif variable == "3":
                STREAM()
            
            elif variable == "4":
                list_command()

            elif variable == "5":
                chunks.clear()
                
            elif variable == "6":
                Fvz, signal = sestavi_podatke("packets.txt")
                
            elif variable == "7":
                prikazi_signal(
                    signal, naslov =
                    f"Signal z frekvenco {Fvz:.3f}Hz"
                )
                prikazi_signal(
                    signal, naslov =
                    f"Signal z frekvenco {Fvz:.3f}Hz",
                    startInd=1000,
                    endInd= int(Fvz * 200) + 100
                )
            elif variable == "8":
                convert_all_bin_in_cwd()
                
            elif variable == "9":
                break
            else:
                raise UserInputError(f"Unknown command '{variable}'. Choose 0-9.")
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
