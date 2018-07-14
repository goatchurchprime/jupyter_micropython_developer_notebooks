from BlueFly_funcs import uart, SetupGPS, BFVmakesettings, ParseNMEA
from OLED_driver import i2c, fbuff, oledshow, doublepixels, fatntext, oledshowfattext
from machine import Pin, SPI, UART
import sdcard, os, time

def ConnectBluefly():
    for i in range(15, 0, -1):
        time.sleep_ms(300)
        if BFVmakesettings({ b"BOF":1, # Output frequency (factor of 20ms)
                          b"BHV":0, # height timeout
                          b"BHT":10000, # seconds to timeout
                          b"BVL":3  # volume (out of 1000)
                        }) and SetupGPS():
            break
        oledshowfattext(["Turn Blu", "eFly on", str(i)])
        time.sleep_ms(700)

        
# mosi should be mosi=Pin19 (to match Lora) but won't work as OUTPUT
# https://github.com/micropython/micropython-lib/blob/master/errno/errno.py
# errno=28(no space)
spi = SPI(sck=Pin(5), mosi=Pin(22), miso=Pin(27))  
sd = sdcard.SDCard(spi, Pin(23))
sdfile = None
def ConnectSDcardFile():       
    global sdfile
    try:
        os.mount(sd, '/sd')
    except OSError as e:
        oledshowfattext(["SD card", "failed"])
        time.sleep_ms(4000)
    
    if not sum((f[0]=="LOG")  for f in os.ilistdir("sd")):
        os.mkdir("sd/LOG")
    fnum = 1+max((int(f[0][:3])  for f in os.ilistdir("sd/LOG")  if f[3]>10), default=0)
    fname = "sd/LOG/{:03d}.TXT".format(fnum)
    oledshowfattext(["SDfile", fname[:6], fname[6:]])
    print("Opening file", fname)
    sdfile = open(fname, "w")
    sdfile.write("Logfile: {}\n".format(fname))
    sdfile.write("Device number: 3\n")
    sdfile.write("Rt[ms]d\"[isodate]\"e[latdE]n[latdN]f[lngdE]o[lngdN] GPS cooeffs\n") 
    sdfile.write("Qt[ms]u[ms midnight]y[lat600000]x[lng600000]a[alt] GPS\n") 
    sdfile.write("Vt[ms]v[kph100]d[deg100] GPS velocity\n") 
    sdfile.write("Ft[ms]p[milibars] bluefly pressure\n") 
    sdfile.write("Gt[ms]r[rawhumid]a[rawtemp] si7021Humidity meter\n") 
    sdfile.write("Nt[ms]r[rawadc]s[resistance] nickel wire sensor\n") 
    sdfile.write("Zt[ms]xyz[linacc]abc[gravacc]wxyz[quat]s[calibstat] orient\n"); 
    sdfile.write("Yt[ms]s\"calibconsts\" orient calib\n"); 
    sdfile.write("\n")
    sdfile.flush()
    return sdfile

mstampSI7021 = 0
bh = bytearray(2)
bt = bytearray(2)

def calchumidtemps():
    rh = (bh[0]<<8) + (bh[1]&0xFC)
    rt = (bt[0]<<8) + (bt[1]&0xFC)
    return ((125.0*rh)/65536)-6, ((175.25*rt)/65536)-46.85 

def readlogSI7021():
    global mstampSI7021
    mstamp = time.ticks_ms()
    if mstampSI7021 == 0:
        i2c.writeto(0x40, b'\xE5')
        mstampSI7021 = mstamp + 20
    elif mstamp > mstampSI7021:
        i2c.readfrom_into(0x40, bh)
        i2c.readfrom_mem_into(0x40, 0xE0, bt)
        if sdfile:
            sdfile.write("Gt{:08X}r{:02X}{:02X}a{:02X}{:02X}\n".format(mstamp, bh[0], bh[1], bt[0], bt[1]))
        mstampSI7021 = 0

prs = 0
def readlogbluefly():
    global prs
    b = uart.readline()
    if not b:
        return None
    mstamp = time.ticks_ms()
    if b[:3] == b'PRS':
        prs = int(b[4:-2], 16)
        sdfile.write("Ft{:08X}p{:06X}\n".format(mstamp, prs))
        return prs
    if b[0] == ord(b'$') and b[-1] == ord(b'\n'):
        try:
            pnmea = ParseNMEA(b)
        except IndexError:
            pnmea = None
        except ValueError:
            pnmea = None
        if pnmea:
            if pnmea == b"D": # parsed but do not print
                return None
            sdfile.write(pnmea)
            return pnmea
        return b
    return None


# BNO055 funcs
import math, time
uart2 = None
def bno055write1(reg, val):
    uart2.write(bytes((0xAA, 0x00, reg, 1, val)))
    time.sleep_ms(20)
    v = uart2.read()
    return v == b'\xee\x01'
   
def bno055read(reg, n):
    uart2.write(bytes((0xAA, 0x01, reg, n)))
    time.sleep_ms(20)
    r = uart2.read()
    if not ((r[0] == 0xBB) and (r[1] == n) and (len(r) == n + 2)):
        raise Exception("bad bno055read %s" % str(r))
    return r[2:]

def InitBNO055(luart2):
    global uart2
    uart2 = luart2
    if not bno055write1(0x3D, 0x00):  return "BAD055_1"   # PWR_MODE
    if not bno055write1(0x3B, 0x00):  return "BAD055_2"   # UNIT_SEL, celsius, UDegrees and m/s^2
    if not bno055write1(0x3D, 0x0C):  return "BAD055_3"   # back to NDOF mode
    return ("Temp%d" % bno055read(0x34, 1)[0])
    
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

