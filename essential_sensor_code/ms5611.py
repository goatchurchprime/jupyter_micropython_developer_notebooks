from syslog import log, elog, powid
import array, ustruct, time

# this can go down to 9 but then the variable heating effects in the sensor from such rapid readings 
# really muck things up and causes spikes
msreaddelay = const(20)

dC3 = const(0); dC4 = const(1); dC6 = const(2); dSENST1 = const(3); dOFFT1 = const(4); dTref = const(5); 
dD1 = const(6); dD2 = const(7);   # the readings

def GetMS5611calibrations(i2c):
    dc = array.array("I", range(8))
    i2c.writeto(0x77, b'\x1E')
    time.sleep_ms(20)
    C1 = ustruct.unpack(">H", i2c.readfrom_mem(0x77, 0xA2, 2))[0]
    C2 = ustruct.unpack(">H", i2c.readfrom_mem(0x77, 0xA4, 2))[0]
    dc[dC3] = ustruct.unpack(">H", i2c.readfrom_mem(0x77, 0xA6, 2))[0]
    dc[dC4] = ustruct.unpack(">H", i2c.readfrom_mem(0x77, 0xA8, 2))[0]
    C5 = ustruct.unpack(">H", i2c.readfrom_mem(0x77, 0xAA, 2))[0]
    dc[dC6] = ustruct.unpack(">H", i2c.readfrom_mem(0x77, 0xAC, 2))[0]
    dc[dSENST1] =  C1*0x8000
    dc[dOFFT1] = C2*0x10000
    dc[dTref] = C5*0x100
    return dc
    
# int(pressure*256) for consistency with bme280 
def MS5611convert(dc):
    dT = dc[dD2] - dc[dTref]
    TEMP = 2000 + dT*dc[dC6]/0x00800000 
    OFF = dc[dOFFT1] + dT*dc[dC4]/0x80 
    SENS = dc[dSENST1] + dT*dc[dC3] / 0x100
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
    return int((SENS * dc[dD1] / 0x200000 - OFF) / 0x80) 


def ms5611gen(i2c):
    dc = GetMS5611calibrations(i2c)
    readout = bytearray(3)
    while True:
        i2c.writeto(0x77, b'\x48')
        time.sleep_ms(msreaddelay)
        i2c.readfrom_mem_into(0x77, 0x00, readout)
        dc[dD1] = (readout[0]<<16) | (readout[1]<<8) | readout[2]

        i2c.writeto(0x77, b'\x58')
        time.sleep_ms(msreaddelay)
        i2c.readfrom_mem_into(0x77, 0x00, readout)
        dc[dD2] = (readout[0]<<16) | (readout[1]<<8) | readout[2]
        
        yield MS5611convert(dc)/256
        

async def ams5611read(dc, readout, i2c, uasyncio):
    i2c.writeto(0x77, b'\x48')
    await uasyncio.sleep_ms(20)
    i2c.readfrom_mem_into(0x77, 0x00, readout)
    dc[dD1] = (readout[0]<<16) | (readout[1]<<8) | readout[2]

    i2c.writeto(0x77, b'\x58')
    await uasyncio.sleep_ms(20)
    i2c.readfrom_mem_into(0x77, 0x00, readout)
    dc[dD2] = (readout[0]<<16) | (readout[1]<<8) | readout[2]
        
       
