import ustruct, time

i2c = None

def crc8(b0, b1):
    crc = 0xFF
    crc ^= b0;
    for i in range(8):
        crc = (((crc << 1) ^ 0x31) if (crc & 0x80) else (crc << 1)) & 0xFF
    crc ^= b1
    for i in range(8):
        crc = (((crc << 1) ^ 0x31) if (crc & 0x80) else (crc << 1)) & 0xFF
    return crc


def SHT31Dsetup(li2c):
    global i2c
    i2c = li2c
    
    i2c.writeto(0x44, b'\xF3\x2D')    # SHT31_READSTATUS
    k = i2c.readfrom(0x44, 3)
    print(k, hex(crc8(k[0], k[1])))
    i2c.writeto(0x44, b'\x30\xA2')    # SHT31_SOFTRESET
    time.sleep(0.1)
    i2c.writeto(0x44, b'\x27\x37')    # read 10Hz?

    i2c.writeto(0x44, b'\xF3\x2D')    # SHT31_READSTATUS
    k = i2c.readfrom(0x44, 3)
    print(k, hex(crc8(k[0], k[1])))

def readSHT31D():
    i2c.writeto(0x44, b'\xE0\x00')
    k = i2c.readfrom(0x44, 6)
    if k[2] != crc8(k[0], k[1]) or k[5] != crc8(k[3], k[4]):
        return -1, -1
    rawtemp, b1, rawhumid, b2 = ustruct.unpack(">HbHb", k)
    stemp = (rawtemp * 175)/0xFFFF - 45
    shumid = (rawhumid*100)/0xFFFF
    return stemp, shumid



