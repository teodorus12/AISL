def crc16_update(crc, data_byte):
    crc ^= data_byte
    for _ in range(8):
        if crc & 1:
            crc = (crc >> 1) ^ 0xA001
            
        else:
            crc >>= 1
    return crc & 0xFFFF 

def crc16_compute(data):
    crc = 0xFFFF
    for b in data:
        crc = crc16_update(crc, b)
    return crc