import struct
import numpy as np
import os
from CRC16 import crc16_compute, crc16_update

ALAW_TABLE = np.array([
     8, 24, 40, 56, 72, 88, 104, 120, 136, 152, 168, 184, 200, 216, 232, 248,
     264, 280, 296, 312, 328, 344, 360, 376, 392, 408, 424, 440, 456, 472, 488, 504,
     528, 560, 592, 624, 656, 688, 720, 752, 784, 816, 848, 880, 912, 944, 976, 1008,
     1056, 1120, 1184, 1248, 1312, 1376, 1440, 1504, 1568, 1632, 1696, 1760, 1824, 1888,
     1952, 2016, 2112, 2240, 2368, 2496, 2624, 2752, 2880, 3008, 3136, 3264, 3392, 3520,
     3648, 3776, 3904, 4032, 4224, 4480, 4736, 4992, 5248, 5504, 5760, 6016, 6272, 6528,
     6784, 7040, 7296, 7552, 7808, 8064, 8448, 8960, 9472, 9984, 10496, 11008, 11520, 12032,
     12544, 13056, 13568, 14080, 14592, 15104, 15616, 16128, 16896, 17920, 18944, 19968, 20992,
     22016, 23040, 24064, 25088, 26112, 27136, 28160, 29184, 30208, 31232, 32256
], dtype=np.int16)


def unstuff_bytes(stuffed):
    decoded = bytearray()
    i = 0
    while i < len(stuffed):
        if stuffed[i] == 0xFE:
            if i + 1 >= len(stuffed):
                break
            decoded.append(0xFE ^ stuffed[i + 1])
            i += 2
        else:
            decoded.append(stuffed[i])
            i += 1
    return decoded


def CREATE_PACKETS(file_path):
    file_path = os.path.join("bin_folder", file_path)

    with open(file_path, "rb") as f:
        data = f.read()

    packets = []
    i = 0

    while i < len(data) - 1:
        if data[i] == 0xFF and data[i + 1] == 0xFF:
            i += 2

            packet_counter = data[i]
            i += 1

            chunk = bytearray()

            while i < len(data) - 1 and not (data[i] == 0xFF and data[i + 1] == 0xFF):
                chunk.append(data[i])
                i += 1

            payload = unstuff_bytes(chunk)
            payload = bytearray([packet_counter]) + payload
            packets.append(payload)
        else:
            i += 1

    chunks = []

    for payload in packets:
        if len(payload) < 6:
            continue

        packet_counter = payload[0]
        packet_data = payload[1:]

        if len(packet_data) < 6:
            continue

        timestamp = struct.unpack_from("<I", packet_data, 0)[0]
        _packet_size = struct.unpack_from("<H", packet_data, 4)[0] + 1
        chunks_data = packet_data[6:-2]

        if len(packet_data) < 2:
            continue

        crc_received = struct.unpack_from("<H", packet_data, len(packet_data) - 2)[0]
        crc_calculated = crc16_compute(packet_data[:-2])

        if crc_calculated != crc_received:
            continue

        ts_sec = float(timestamp) / 1000.0
        pos = 0

        while pos + 4 <= len(chunks_data):
            chunk_id = chunks_data[pos]

            if pos + 3 >= len(chunks_data):
                break

            chunk_size = struct.unpack_from("<H", chunks_data, pos + 1)[0] + 1
            _reserved = chunks_data[pos + 3]

            if pos + 4 + chunk_size > len(chunks_data):
                break

            signal = chunks_data[pos + 4: pos + 4 + chunk_size]

            # IMU data (int16)
            if chunk_id in (1, 2, 3):
                if len(signal) % 2 != 0:
                    signal = signal[:-1]

                data_array = np.frombuffer(bytes(signal), dtype="<i2").copy()

                chunks.append({
                    "id": chunk_id,
                    "ts": ts_sec,
                    "data": data_array,
                })

                pos += 4 + chunk_size

            # A-law audio
            elif chunk_id == 4:
                if len(signal) % 2 != 0:
                    signal = signal[:-1]

                data_array = np.frombuffer(signal, dtype=np.int8).reshape(-1, 1)

                sign = np.sign(data_array)
                ipos = np.abs(data_array).astype(np.uint8)

                ipos = np.clip(ipos, 0, 127)

                decoded = ALAW_TABLE[ipos]
                decoded = (decoded * sign).astype(np.int16)

                chunks.append({
                    "id": 4,
                    "ts": ts_sec,
                    "data": decoded,
                })

                pos += 4 + chunk_size
            else:
                pos += 1

    return chunks