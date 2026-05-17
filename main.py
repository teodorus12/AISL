from stream_command import STREAM
from create_file import save_chunks_to_file
from Signal_decode import prikazi_signal
from list_command import list_command
from get_file import GET_FILE
from create_packets_final import CREATE_PACKETS
from convert_bin_to_wav import collect_inputs, convert_file
from Signal_decode import sestavi_podatke
from convert_all_in_cwd import convert_all_bin_in_cwd, WAV_OUTPUT_DIR
from category_wav import download_bin_and_convert_by_category
from sign_videos import recognize_and_play_signs
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
    print(f"8. pretvori vse BIN v WAV (izhod: {WAV_OUTPUT_DIR}/)")
    print("9. EXIT")
    print("10. prenesi BIN in pretvori v WAV")
    print("11. test - prepoznava glasovnih posnetkov + pretvarjanje v znake")

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

            elif variable == "10":
                download_bin_and_convert_by_category()

            elif variable == "11":
                recognize_and_play_signs()

            else:
                raise UserInputError(f"Unknown command '{variable}'. Choose 0-11.")
                
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
