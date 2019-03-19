import ustruct, time

C1, C2, C3, C4, C5, C6 = 0,0,0,0,0,0

def ms5611setup(li2c):
    global i2c, C1, C2, C3, C4, C5, C6
    i2c = li2c
    
    C1 =  ustruct.unpack('>H', i2c.readfrom_mem(0x77, 0xA2, 2))[0]
    C2 =  ustruct.unpack('>H', i2c.readfrom_mem(0x77, 0xA4, 2))[0]
    C3 =  ustruct.unpack('>H', i2c.readfrom_mem(0x77, 0xA6, 2))[0]
    C4 =  ustruct.unpack('>H', i2c.readfrom_mem(0x77, 0xA8, 2))[0]
    C5 =  ustruct.unpack('>H', i2c.readfrom_mem(0x77, 0xAA, 2))[0]
    C6 =  ustruct.unpack('>H', i2c.readfrom_mem(0x77, 0xAC, 2))[0]

def readMS5611():
    i2c.writeto(0x77, b'\x48')
    time.sleep_ms(9)
    D1 = i2c.readfrom_mem(0x77, 0x00, 3)
    D1 = D1[0]*0x10000 + D1[1]*0x100 + D1[2]
    i2c.writeto(0x77, b'\x58')
    time.sleep_ms(9)
    D2 = i2c.readfrom_mem(0x77, 0x00, 3)
    D2 = D2[0]*0x10000 + D2[1]*0x100 + D2[2]
    
    dT = D2 - C5 * 0x100
    TEMP = 2000 + dT*C6/0x00800000 
    OFF = C2*0x10000 + dT*C4/0x80 
    SENS = C1*0x8000 + dT*C3/0x100
    
    if (TEMP < 2000):
        T2 = dT*dT/0x80000000 
        ra = TEMP - 2000 
        ra = ra*ra 
        OFF -= 5*ra/2 
        SENS -= 5*ra / 4 
        if (TEMP < -1500):
            rb = TEMP - (-1500); 
            rb = rb*rb; 
            OFF -= 7*rb; 
            SENS -= 11*rb / 2; 
        TEMP -= T2; 
    
    Pr = (SENS * D1 / 0x200000 - OFF) / 0x8000; 
    return TEMP/100, Pr
    