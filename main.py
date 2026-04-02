from stream_command import STREAM
from  list_command import list_command
from get_file import GET_FILE
from create_packets_final import CREATE_PACKETS

if __name__ == "__main__":
    chunks = []
    while True:
        print("1. get file")
        print("2. create packets")
        print("3. stream")
        print("4. list")

        variable = input("chose command 1/2")

        if variable == "1":
            filename = input("What file would you like to download?")
            GET_FILE(filename)

        elif variable == "2":
            filename = input("What file would you like to transofrm into packets?")
            chunks = CREATE_PACKETS(filename)
            for c in chunks:
                print(c["data"])
        elif variable == "3":
            STREAM()
        
        elif variable == "4":
            list_command()
