import numpy as np

def save_chunks_to_file(chunks, output_file="packets.txt"):
    with open(output_file, "w", encoding="utf-8") as f:
        for chunk in chunks:
            data_str = ",".join(map(str, chunk["data"].flatten()))
            f.write(f"{chunk['ts']};{data_str}\n")
