import ustruct, math, array

from OLED_driver import i2c   # just get it from this common library

# check device is plugged in
# EEPROM is on device 0x50 and actual sensor is on 0x60
assert set(i2c.scan()).issuperset([0x50, 0x60])

# fetch  16 bit register [0x02:readcommand, reg, addressstep=0, numberofreads=1]
# (the interface to the MLX90621 is so you can request a row or column
#  of pixels with one command call)
def readreg16(reg, signed=False):
    i2c.writeto(0x60, bytearray([0x02, reg, 0x00, 0x01]), False)
    return ustruct.unpack("<h" if signed else "<H", i2c.readfrom(0x60, 2))[0]

# read signed/unsigned 1 or 2 byte number
def readEEprom(reg, nc):
    return ustruct.unpack(nc[1], i2c.readfrom_mem(0x50, reg, nc[0]))[0]
s16 = (2, "<h")
u16 = (2, "<H")
s8 = (1, "b")
u8 = (1, "B")

# read config
config = readreg16(0x92, signed=False)
needs_initializing = not (readreg16(0x92, signed=False) & 0x0400)  # also when power on

# Read the EEPROM table (see 8.2.3, 9.5)
#    deltaAi = i2c.readfrom_mem(0x50, 0x00, 0x40)
#    Bi = i2c.readfrom_mem(0x50, 0x40, 0x40)
#    deltaalphai = i2c.readfrom_mem(0x50, 0x80, 0x40)

def initialize_settings():
    print("Initializing settings")
    # Write the oscillator trim value into the IO at address 0x93 (see 7.1, 8.2.2.2, 9.4.4) (no idea what this is)
    OSC_trim = readEEprom(0xF7, u8)
    i2c.writeto_mem(0x60, 0x04, bytearray([OSC_trim - 0xAA, OSC_trim, 0x56, 0x00]));
    
    # Write the configuration value (IO address 0x92) (see 8.2.2.1, 9.4.3)
    #   The value is either read from the EEPROM or hard coded externally
    #   Set the POR/ Brown Out (!needs_initializing) flag to “1” (bit 10 at address 0x92)
    Hz_LSB = 0b00111010  # 18bit resolution, 16 frames/second
    defaultConfig_H = 0b01000100  # bit 2 resets the Brown Out flag  
    i2c.writeto_mem(0x60, 0x03, bytearray([Hz_LSB - 0x55, Hz_LSB, defaultConfig_H - 0x55, defaultConfig_H]))

    # prove ConfigReg[5:3] == 3, which is part of a scaling factor
    assert ((readreg16(0x92, signed=False)>>4)&3) == 3

    
# Read measurement data (PTAT + desired IR data)
# (see 7.2.1, 7.2.2, 8.2.1, 9.4.2)
# assuming resolution = ConfigReg[5:4] = 3 
KTscale = readEEprom(0xD2, u8)
VTH = readEEprom(0xDA, s16)
KT1 = readEEprom(0xDC, s16)/2**((KTscale>>4)&0x0F)
KT2 = readEEprom(0xDE, s16)/2**((KTscale&0x0F)+10)

Bscale = readEEprom(0xD9, u8)&0x0f
ACP = readEEprom(0xD3, s16)
BCP = readEEprom(0xD5, u8)/(2**Bscale)

# Tambient calculation (of the die)
Ta = (-KT1 + math.sqrt(KT1**2 - 4*KT2*(VTH - readreg16(0x40))))/(2*KT2) + 25

VCP = readreg16(0x41, signed=True)
VIRCPoffsetcompensated = VCP - (ACP + BCP*(Ta-25))
print(Ta, VIRCPoffsetcompensated)
TaK4 = (Ta+273.15)**4

irData = bytearray(128)
def ReadirData():
    i2c.writeto(0x60, b"\x02\x00\x01\x80", False)
    i2c.readfrom_into(0x60, irData)

# numbers that simplify the calculation by being zero
# (check if it's the case on your sensor)
KS4 = readEEprom(0xC4, s16)/2**(readEEprom(0xC0, u8)&0xF + 8)
assert KS4 == 0.0   # simplifies calculation
KsTa = readEEprom(0xE6, s16)/2**20
assert KsTa == 0.0
TGC = readEEprom(0xD8, s8)/32
assert TGC == 0
alpha0scale = readEEprom(0xE2, u8)
alpha0deltascale = readEEprom(0xE3, u8)
alpha0 = readEEprom(0xE0, u16)/(2**alpha0scale)
alphaCP = readEEprom(0xD6, u16)/(2**alpha0scale)
TGC = readEEprom(0xD8, s8)/32
Acommon = readEEprom(0xD0, s16)
deltaAscale = readEEprom(0xD9, u8)>>4

epsilon = readEEprom(0xE4, u16)/32768
assert epsilon == 1

# alpha values
i = 0
deltalpha = readEEprom(0x80+i, u8)
alpha = alpha0 + deltalpha/(2**alpha0deltascale)
alphacomp = (1+ KsTa*(Ta - 25))*(alpha - TGC*alphaCP)

# means alpha is constant (not depending on Ta)
assert TGC == 0 and KsTa == 0  # then alphacomp==alpha
# which means it's constant and doesn't change with Ta

alphacompI = array.array("f", 
     [ alpha0 + readEEprom(0x80+i, u8)/(2**alpha0deltascale)  for i in range(64) ])
                         
AI = array.array("i", 
     [ Acommon + readEEprom(0x00 + i, u8)*(2**deltaAscale)  for i in range(64) ])
                         
# this is documented as 2bytes numbers but doesn't seem to be
BI = array.array("f", 
     [ readEEprom(0x40 + i, s8)/(2**Bscale)  for i in range(64) ])   

# buffers with the data
temperatures = array.array("f", [0]*64)

def measure():
    needs_initializing = not (readreg16(0x92, signed=False) & 0x0400)  # also when power on
    if needs_initializing:
        initialize_settings()
    ReadirData()
    for i in range(64):
        # Section 7.3.3.1 
        VIR = ustruct.unpack("<h", irData[i*2:i*2+2])[0]  # <-- this is ridiculously slow
        VIRcompensated = VIR - (AI[i] + BI[i]*(Ta - 25))
        #VIRcompensated = VIRoffsetcompensated/epsilon   # epsilon=1
        temperatures[i] = (VIRcompensated/alphacompI[i] + TaK4)**0.25 - 273.15
    return temperatures
    


# Plotting array of pixels onto the OLED functions
def cellfillplot(fbuff, x, y, s):
    r = min(255, int(s*64))
    x = x*8
    y = y*8
    if r < 4:
        if r > 0:  fbuff.pixel(x+3, y+3, 1)
        if r > 1:  fbuff.pixel(x+4, y+3, 1)
        if r > 2:  fbuff.pixel(x+4, y+4, 1)
        return
    elif r < 16:
        n = 2
    elif r < 36:
        n = 4
    else:
        n = 6
        
    r -= n**2
    rx, ry = x+4-n//2, y+4-n//2
    if r <= n:
        fbuff.fill_rect(rx, ry, n, n, 1)
        fbuff.hline(rx, ry-1, r, 1)
    elif r <= 2*n + 1:
        fbuff.fill_rect(rx, ry-1, n, n+1, 1)
        fbuff.vline(rx+n, ry-1, r - n, 1)
    elif r <= 3*n + 2:
        fbuff.fill_rect(rx, ry-1, n+1, n+1, 1)
        w = r-(2*n + 1)
        fbuff.hline(rx+n+1-w, ry+n, w, 1)
    else:
        fbuff.fill_rect(rx, ry-1, n+1, n+2, 1)
        w = min(r-(3*n + 2), n+2)
        fbuff.vline(rx-1, ry+n+1-w, w, 1)

    