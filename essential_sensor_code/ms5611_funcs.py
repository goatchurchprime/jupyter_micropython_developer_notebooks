from i2cmodule import i2c

import ustruct, time

C3, C4, C6, SENST1, OFFT1, Tref = 0,0,0,0,0,0
def setupms5611():
    global C3, C4, C6, SENST1, OFFT1, Tref
    i2c.writeto(0x77, b'\x1E')
    time.sleep_ms(20)
    C1 = ustruct.unpack(">H", i2c.readfrom_mem(0x77, 0xA2, 2))[0]
    C2 = ustruct.unpack(">H", i2c.readfrom_mem(0x77, 0xA4, 2))[0]
    C3 = ustruct.unpack(">H", i2c.readfrom_mem(0x77, 0xA6, 2))[0]
    C4 = ustruct.unpack(">H", i2c.readfrom_mem(0x77, 0xA8, 2))[0]
    C5 = ustruct.unpack(">H", i2c.readfrom_mem(0x77, 0xAA, 2))[0]
    C6 = ustruct.unpack(">H", i2c.readfrom_mem(0x77, 0xAC, 2))[0]
    SENST1 =  C1*0x8000
    OFFT1 = C2*0x10000
    Tref = C5*0x100
    
def MS5611readD():
    i2c.writeto(0x77, b'\x48')
    time.sleep_ms(20)
    r = i2c.readfrom_mem(0x77, 0x00, 3)
    D1 = r[0]*0x10000 + r[1]*0x100 + r[2]
    
    i2c.writeto(0x77, b'\x58')
    time.sleep_ms(20)
    r = i2c.readfrom_mem(0x77, 0x00, 3)
    D2 = r[0]*0x10000 + r[1]*0x100 + r[2]
    return D1, D2

def MS5611convert(D1, D2):
    dT = D2 - Tref
    TEMP = 2000 + dT*C6/0x00800000 
    OFF = OFFT1 + dT*C4/0x80 
    SENS = SENST1 + dT*C3 / 0x100
    if TEMP < 2000:
        T2 = dT*dT/0x80000000; 
        ra = TEMP - 2000; 
        ra = ra*ra; 
        OFF -= 5*ra/2; 
        SENS -= 5*ra / 4; 
        if TEMP < -1500:
            rb = TEMP - (-1500) 
            rb = rb*rb 
            OFF -= 7*rb 
            SENS -= 11*rb / 2 
        TEMP -= T2; 
    return (SENS * D1 / 0x200000 - OFF) / 0x8000 


# takes the library module as an argument to save importing it here
async def aMS5611read(uasyncio):
    i2c.writeto(0x77, b'\x48')
    await uasyncio.sleep_ms(20)
    r = i2c.readfrom_mem(0x77, 0x00, 3)
    D1 = r[0]*0x10000 + r[1]*0x100 + r[2]
    
    i2c.writeto(0x77, b'\x58')
    await uasyncio.sleep_ms(20)
    r = i2c.readfrom_mem(0x77, 0x00, 3)
    D2 = r[0]*0x10000 + r[1]*0x100 + r[2]
    
    return MS5611convert(D1, D2)

