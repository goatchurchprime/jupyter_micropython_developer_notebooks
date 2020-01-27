
def checkCRC(k, mask):  # mask (matching nibble) different in case
    inCrc = 0
    for inData in [k[0], k[1]]:
        data = inCrc ^ inData;
        data <<= 8 
        for i in range(8):
            if (( data & 0x8000 ) != 0 ):
                data = data ^ (0x1070 << 3)
            data = data << 1
        inCrc = data >> 8
    return (inCrc & mask) == (k[2]&mask)

def mlx90614temps(i2c, addr=0x5a):
    try:
        ka = i2c.readfrom_mem(addr, 0x06, 3)
        ki = i2c.readfrom_mem(addr, 0x07, 3)
        bcrcgood = (checkCRC(ka, 0x0F) and checkCRC(ki, 0xF0))
        if ki[0] == 0 and ki[1] == 0:
            bcrcgood = False
    except OSError:
        bcrcgood = False
    if bcrcgood:
        tempAmbient = (ka[0]+ka[1]*256)*0.02 - 273.15
        tempIR = (ki[0]+ki[1]*256)*0.02 - 273.15
        return tempAmbient, tempIR
    return None, None
    