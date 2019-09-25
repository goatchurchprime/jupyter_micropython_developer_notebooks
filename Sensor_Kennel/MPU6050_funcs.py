# Conversion of the C++ code at: https://github.com/jrowberg/i2cdevlib Locally at: extrepositories/i2cdevlib/Arduino/MPU6050/
# Removed #defines that replace hex-codes that are in the documentation by text strings that are not there.

import ubinascii, ustruct, time, math

i2c = None

def writeBits(regAddr, bitStart, length, data):
    b = i2c.readfrom_mem(0x68, regAddr, 1)[0]
    mask = ((1 << length) - 1) << (bitStart - length + 1)
    b = (b & (mask ^ 0xFF)) | ((data << (bitStart - length + 1)) & mask)
    i2c.writeto_mem(0x68, regAddr, bytes([b]))

def writeBit(regAddr, bitNum, data):
    b = i2c.readfrom_mem(0x68, regAddr, 1)[0]
    b = (b | (1 << bitNum)) if (data != 0) else (b & ((1 << bitNum) ^ 0xFF))
    i2c.writeto_mem(0x68, regAddr, bytes([b]))

def writeByte(regAddr, data):
    i2c.writeto_mem(0x68, regAddr, bytes([data]))

def writeWord(regAddr, data):
    i2c.writeto_mem(0x68, regAddr, bytes([(data>>8), data&0xFF]))

def readUWord(regAddr):
    b = i2c.readfrom_mem(0x68, regAddr, 2)
    return (b[0]<<8)|b[1]
    
def readByte(regAddr):
    return i2c.readfrom_mem(0x68, regAddr, 1)[0]

def readBytes(regAddr, length):
    return i2c.readfrom_mem(0x68, regAddr, length)

def readBits(regAddr, bitStart, length):
    b = i2c.readfrom_mem(0x68, regAddr, 1)[0]
    mask = ((1 << length) - 1) << (bitStart - length + 1)
    return (b & mask) >> (bitStart - length + 1)

def writeMemoryBlockChunk(addr, data):
    writeByte(0x6D, ((addr>>8) & 0x1F))  # setMemoryBank(i>>8)
    writeByte(0x6E, (addr&0xFF))         # setMemoryStartAddress(address)
    i2c.writeto_mem(0x68, 0x6F, data)    # MPU6050_RA_MEM_R_W
    return len(data)
    
def writeMemoryBlockChunkHex(addr, hdata):
    return writeMemoryBlockChunk(addr, ubinascii.unhexlify(hdata.strip()))
    
def readMemoryBlockChunk(addr, length):
    # userBank: bank&0x20,  prefetchEnabled: bank&0x40
    writeByte(0x6D, (addr>>8))       # setMemoryBank(i>>8)
    writeByte(0x6E, (addr&0xFF))     # setMemoryStartAddress(address)
    return i2c.readfrom_mem(0x68, 0x6F, length)

def readMemoryBlockChunkHex(addr, length):
    return ubinascii.hexlify(readMemoryBlockChunk(addr, length)).decode().upper()
    
# calibrations get run several times until the numbers settle down
# (offsets are saved, then new offsets are measured and added in)
# must be lying still on its back
def calibacc(recvalues=None):
    if recvalues is not None:
        i2c.writeto_mem(0x68, 0x06, ustruct.pack(">hhh", recvalues[0], recvalues[1], recvalues[2]))
        return
    v0, v1, v2 = 0, 0, 0
    n = 200
    for i in range(n):
        m0, m1, m2 = ustruct.unpack(">hhh", i2c.readfrom_mem(0x68, 0x3B, 6))
        v0 += m0;  v1 += m1;  v2 += m2 - 16384
        time.sleep_ms(5)
    c0, c1, c2 = ustruct.unpack(">hhh", i2c.readfrom_mem(0x68, 0x06, 6))
    c0 += round(-v0/n/16)*2;  c1 += round(-v1/n/16)*2;  c2 += round(-v2/n/16)*2;  
    i2c.writeto_mem(0x68, 0x06, ustruct.pack(">hhh", c0, c1, c2))
    print(v0/n, v1/n, v2/n, c0, c1, c2)
    return c0, c1, c2

# must be lying still
def calibgyros(recvalues=None):
    if recvalues is not None:
        i2c.writeto_mem(0x68, 0x13, ustruct.pack(">hhh", recvalues[0], recvalues[1], recvalues[2]))
        return
    v0, v1, v2 = 0, 0, 0
    n = 100
    for i in range(n):
        m0, m1, m2 = ustruct.unpack(">hhh", i2c.readfrom_mem(0x68, 0x43, 6))
        v0 += m0;  v1 += m1;  v2 += m2
        time.sleep_ms(5)
    c0, c1, c2 = ustruct.unpack(">hhh", i2c.readfrom_mem(0x68, 0x13, 6))
    c0 += round(-v0/n*2);  c1 += round(-v1/n*2);  c2 += round(-v2/n*2);  
    i2c.writeto_mem(0x68, 0x13, ustruct.pack(">hhh", c0, c1, c2))
    print(v0/n, v1/n, v2/n, c0, c1, c2)
    return c0, c1, c2

def setupDMP(li2c, dmpMemoryFile="MPU6050_dmpMemoryv6.hex"):
    global i2c
    i2c = li2c
    
    writeBit(0x6B, 7, 1)         # PWR_MGMT_1: reset with 100ms delay
    time.sleep_ms(100)
    writeBits(0x6A, 2, 3, 0x07)  # full SIGNAL_PATH_RESET: with another 100ms delay
    time.sleep_ms(100)

    writeByte(0x6B, 0x03) # 0000 0011 PWR_MGMT_1: unsleep, Clock Source Select PLL_Z_gyro
    time.sleep_ms(100)
    
    Drev = readMemoryBlockChunk(0x7006, 1)[0]
    DOTPValid = readBits(0x00, 0, 1)
    DdeviceID = readBits(0x75, 6, 6)
    assert Drev == 0xA5, "revision bad %x"%Drev
    assert DdeviceID == 0x34, "deviceID bad %x"%DdeviceID
    assert DOTPValid

    writeByte(0x38, 0x00) # 0000 0000 INT_ENABLE: no Interrupt
    writeByte(0x23, 0x00) # 0000 0000 MPU FIFO_EN: (all off) Using DMP's FIFO instead
    writeByte(0x1C, 0x00) # 0000 0000 ACCEL_CONFIG: 0 =  Accel Full Scale Select: 2g
    writeByte(0x37, 0x80) # 1001 0000 INT_PIN_CFG: ACTL The logic level for int pin is active low. and interrupt status bits are cleared on any read
    writeByte(0x6B, 0x01) # 0000 0001 PWR_MGMT_1: Clock Source Select PLL_X_gyro
    writeByte(0x19, 0x04) # 0000 0100 SMPLRT_DIV: Divides the internal sample rate 400Hz ( Sample Rate = Gyroscope Output Rate / (1 + SMPLRT_DIV))
    writeByte(0x1A, 0x01) # 0000 0001 CONFIG: Digital Low Pass Filter (DLPF) Configuration 188HZ
    
    addr = 0
    for hdata in open(dmpMemoryFile):
        addr += writeMemoryBlockChunkHex(addr, hdata)
    assert addr == 3062
    assert readMemoryBlockChunkHex(0, 16) == "00F8F62A3F68F57A0006FFFE00030000"
    assert readMemoryBlockChunkHex(addr&0xFFF0, addr%0x10) == "A6D900D8F1FF"

    writeWord(0x70, 0x0400) # DMP Program Start Address
    writeByte(0x1B, 0x18) # 0001 1000 GYRO_CONFIG: 3 = +2000 Deg/sec

    writeByte(0x6A, 0xC0) # 1100 1100 USER_CTRL: Enable Fifo and Reset Fifo
    writeByte(0x38, 0x12) # 0000 0010 INT_ENABLE: RAW_DMP_INT_EN on

    writeBit(0x6A, 2, 1)  # Reset FIFO one last time.
    writeBit(0x6A, 7, 0)  # setDMPEnabled(false);   
    dmpPacketSize = 28;

    # calibrations of gyros and accelerometer (in case it's forgotten outside)
    calibgyros((80, -14, 30))
    calibacc((582, 951, 1692))

def getFIFOCount():
    b = i2c.readfrom_mem(0x68, 0x72, 2)   # getFIFOCount() # readBytes(devAddr, MPU6050_RA_FIFO_COUNTH, 2, buffer);
    return (b[0]<<8) + b[1]
def setDMPEnabled(v):
    writeByte(0x6A, 0xC4 if v else 0x44)  # DMP=Enabled, FIFO=enabled, FIFOreset
def getIntStatus():
    return readByte(0x3A)
def readfifoBuffer(n):
    return i2c.readfrom_mem(0x68, 0x74, n)


def ConvertQuatToEuler(q0, q1, q2, q3):
    riqsq = q0*q0 + q1*q1 + q2*q2 + q3*q3 
    iqsq = 1/riqsq 
    
    r02 = q0*q2*2 * iqsq
    r13 = q1*q3*2 * iqsq
    sinpitch = r13 - r02

    r01 = q0*q1*2 * iqsq
    r23 = q2*q3*2 * iqsq 
    sinroll = r23 + r01 
     
    r00 = q0*q0*2 * iqsq
    r11 = q1*q1*2 * iqsq
    r03 = q0*q3*2 * iqsq
    r12 = q1*q2*2 * iqsq
    a00=r00 - 1 + r11   
    a01=r12 + r03  
    rads = math.atan2(a00, -a01) 
    northorient = 180 - math.degrees(rads) 
    return math.degrees(math.asin(sinpitch)), math.degrees(math.asin(sinroll)), northorient
