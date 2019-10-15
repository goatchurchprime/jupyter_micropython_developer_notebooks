from BlueFly_funcs import uart, SetupGPS, BFVmakesettings, ParseNMEA
from machine import Pin, SPI, UART
import os, time, math

def ConnectBluefly(oledshowfattext, vol=3):
    for i in range(15, 0, -1):
        time.sleep_ms(300)
        if BFVmakesettings({ b"BOF":1, # Output frequency (factor of 20ms)
                          b"BHV":0, # height timeout
                          b"BHT":10000, # seconds to timeout
                          b"BVL":vol  # volume (out of 1000)
                        }) and SetupGPS():
            break
        if oledshowfattext:
            oledshowfattext(["Turn Blu", "eFly on", str(i)])
            time.sleep_ms(700)


mstampSI7021 = 0
bh = bytearray(2)
bt = bytearray(2)

def calchumidtemps():
    rh = (bh[0]<<8) + (bh[1]&0xFC)
    rt = (bt[0]<<8) + (bt[1]&0xFC)
    return ((125.0*rh)/65536)-6, ((175.25*rt)/65536)-46.85 

SI7021readfail = 0
def InitSI7021(i2c):
    global SI7021readfail
    try:
        i2c.writeto(0x40, b'\xFE')  # resets chip
    except OSError:
        return "bad"
    return "good"


def readlogSI7021(i2c, dwrite):
    global mstampSI7021, SI7021readfail
    if SI7021readfail == -1:
        return
    try:
        mstamp = time.ticks_ms()
        if mstampSI7021 == 0:
            i2c.writeto(0x40, b'\xE5')
            mstampSI7021 = mstamp + 20
        elif mstamp > mstampSI7021:
            i2c.readfrom_into(0x40, bh)
            i2c.readfrom_mem_into(0x40, 0xE0, bt)
            if dwrite:
                dwrite("Gt{:08X}r{:02X}{:02X}a{:02X}{:02X}\n".format(mstamp, bh[0], bh[1], bt[0], bt[1]))
            mstampSI7021 = 0
            
    except OSError:
        SI7021readfail += 1

        
prs = 0
def readlogbluefly(dwrite):
    try:
        global prs
        b = uart.readline()
        if not b:
            return None
        mstamp = time.ticks_ms()
        if b[:3] == b'PRS':
            prs = int(b[4:-2], 16)
            dwrite("Ft{:08X}p{:06X}\n".format(mstamp, prs))
            return prs
        if b[0] == ord(b'$') and b[-1] == ord(b'\n'):
            pnmea = ParseNMEA(b)
            if pnmea:
                if pnmea == b"D": # parsed but do not print
                    return None
                dwrite(pnmea)
                return pnmea
            return b
    except IndexError:
        pass
    except ValueError:
        pass
    return None


def displayEulerAngles(fbuff, pitch, roll, orient):
    fbuff.fill(0)
    fbuff.hline(0, max(0, min(63, int(roll+32))), 128, 1)
    fbuff.text("%.1f"%roll, 0, 32, 1)
    fbuff.vline(max(0, min(127, int(pitch*2+64))), 0, 64, 1)
    fbuff.text("%.1f"%pitch, 64, 0, 1)
    fbuff.line(64, 32, 64+int(math.sin(math.radians(orient))*30), 32+int(math.cos(math.radians(orient))*30), 1)

