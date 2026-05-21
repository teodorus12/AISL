from stream_command import STREAM
from create_file import save_chunks_to_file
from Signal_decode import prikazi_signal, sestavi_podatke
from list_command import list_command
from get_file import GET_FILE
from create_packets_final import CREATE_PACKETS
from convert_all_in_cwd import convert_all_bin_in_cwd, WAV_OUTPUT_DIR
from category_wav import download_bin_and_convert_by_category
from sign_videos import recognize_and_play_signs
from tests_for_ai import test_audio_ai

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
    print("11. test sign recognition")
    print("12. test audio neural network")


if __name__ == "__main__":
    print_HELP()

    while True:
        try:
            variable = input("choose command: ")

            if variable == "0":
                print_HELP()

            elif variable == "1":
                GET_FILE(input("file: "))

            elif variable == "2":
                fname = input("file: ")
                chunks = CREATE_PACKETS(fname)
                save_chunks_to_file(chunks)

            elif variable == "3":
                STREAM()

            elif variable == "4":
                list_command()

            elif variable == "5":
                pass

            elif variable == "6":
                sestavi_podatke("packets.txt")

            elif variable == "7":
                prikazi_signal([], naslov="signal")

            elif variable == "8":
                convert_all_bin_in_cwd()

            elif variable == "9":
                break

            elif variable == "10":
                download_bin_and_convert_by_category()

            elif variable == "11":
                recognize_and_play_signs()

            elif variable == "12":
                test_audio_ai()

            else:
                raise UserInputError("invalid command")

        except Exception as e:
            print("Unexpected error:", e)