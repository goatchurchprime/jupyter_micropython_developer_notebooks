import ustruct
i2c = None

def writeData(reg, val):
    val = ustruct.pack("B", val)
    i2c.writeto_mem(0x29, reg, val)

def readData(Reg, num):
    return i2c.readfrom_mem(0x29, Reg, num)

#print("Revision ID:", hex(readData(0x00c2, 1)[0]))
#print("Device ID:", hex(readData(0x00c0, 1)[0]))

def VL53L0Xinit(li2c):
    global i2c
    i2c = li2c
    d = readData(0x0089, 1)
    d = (ord(d) & 0xFE) | 0x01
    writeData(0x0089, d)
    for r, v in [(0x88,0),(0x80,1),(0xff,1),(0,0),(0x91,0x3c),(0,1),(0xff,0),(0x80,0)]:
        writeData(r, v)
    for r, v in [(0x80,1),(0xff,1),(0,0),(0x91,0x3c),(0,1),(0xff,0),(0x80,0)]:
        writeData(r, v) 
    writeData(0x0000, 0x0002) # VL53L0X_REG_SYSRANGE_START, VL53L0X_REG_SYSRANGE_MODE_BACKTOBACK

def VL53L0Xdist():
    k = readData(0x0014, 12)
    b = ustruct.unpack(">HHH", k[6:])
    #b[0] ambientCount, b[1] signalCount
    status = k[0]>>3  # accurate when this is 11
    if status == 11:
        return b[2]
    return 0
