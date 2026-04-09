import struct
import numpy as np
from CRC16 import crc16_compute, crc16_update

def unstuff_bytes(stuffed):
    decoded = bytearray()
    i = 0
    while i < len(stuffed):
        if stuffed[i] == 0xFE:
            if i + 1 >= len(stuffed):
                print(f"Warning: 0xFE at end of payload, skipping")
                break
            decoded.append(0xFE ^ stuffed[i+1])
            i += 2
        else:
            decoded.append(stuffed[i])
            i += 1
    return decoded

def CREATE_PACKETS(file_path):
    with open(file_path, "rb") as f:
        data = f.read()

    packets = []
    i = 0

    while i < len(data) - 1:
        if data[i] == 0xFF and data[i+1] == 0xFF:
            i += 2 

            packet_counter = data[i]
            i += 1

            chunk = bytearray()
            while i < len(data) - 1 and not (data[i] == 0xFF and data[i+1] == 0xFF):
                chunk.append(data[i])
                i += 1
            payload = unstuff_bytes(chunk)
            payload = bytearray([packet_counter]) + payload
            packets.append(payload)
        else:
            i += 1
    chunks = []
    for payload in packets:
        packet_counter = payload[0]
        packet_data = payload[1:] 
        timestamp = struct.unpack_from("<I", packet_data, 0)[0]
        packet_size = struct.unpack_from("<H", packet_data, 4)[0] + 1
        chunks_data = packet_data[6:-2] 

        crc_received = struct.unpack_from("<H", packet_data, len(packet_data)-2)[0]
        crc_calculated = crc16_compute(packet_data[:-2])
        crc_ok = crc_calculated == crc_received
        

        if crc_ok:
            pos = 0
            while pos + 4 <= len(chunks_data):
                chunk_id = chunks_data[pos]
                if chunk_id == 4:
                    if pos + 3 >= len(chunks_data):
                        print(f"Warning: incomplete chunk header at pos {pos}")
                        break

                    chunk_size = struct.unpack_from("<H", chunks_data, pos+1)[0] + 1
                    reserved = chunks_data[pos+3]

                    if pos + 4 + chunk_size > len(chunks_data):
                        #print(f"Warning: incomplete chunk_data at pos {pos}")
                        break

                    signal = chunks_data[pos+4:pos+4+chunk_size]

                    if len(signal) % 2 != 0:
                        #print(f"Warning: odd-length signal for uint16 at chunk {chunk_id}")
                        signal = signal[:-1]

                    data_array = np.frombuffer(signal, dtype=np.int8).reshape(-1, 1)
                    chunks.append({
                        "timestamp": timestamp,
                        "data": data_array
                    })

                    pos += 4 + chunk_size

    return chunks



    
   