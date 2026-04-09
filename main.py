from stream_command import STREAM
from  list_command import list_command
from get_file import GET_FILE
from create_packets_final import CREATE_PACKETS
import os

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
        if variable == "0":
            print_HELP()
        if variable == "1":
            filename = input("What file would you like to download?")
            GET_FILE(filename)

        elif variable == "2":
            filename = input("What file would you like to transofrm into packets?")
            chunks = CREATE_PACKETS(filename)
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