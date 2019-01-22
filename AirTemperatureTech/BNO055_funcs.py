import math, time, ustruct
from machine import UART

uart2 = UART(2, baudrate=115200, rx=2, tx=18)
bno055buffer = bytearray(24)
tbno055timeout = 0
bs = bytearray("Zt00000000x0000y0000z0000a0000b0000c0000w0000x0000y0000z0000s00\n")
mbs = memoryview(bs)

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
        return None
    return r[2:]

prevcalibvals = None
def writecalibstat():
    global prevcalibvals
    cl = None
    for lcl in open("calibfile.txt"):
        if len(lcl) == 54:
            cl = lcl
    print(lcl)
    if cl is None:
        raise OSError("bad calib line")
    calibs = bytearray((0xAA, 0x00, 0x55, 22))
    for i in range(22):
        calibs.append(int(cl[9+i*2:11+i*2], 16))
    prevcalibvals = calibs[4:]
    uart2.write(calibs)
    time.sleep_ms(20)
    v = uart2.read()
    print(v)
    return v == b'\xee\x01'

def InitBNO055():
    if not bno055write1(0x3D, 0x00):  raise OSError("BAD055_0")   # config_mode
    writecalibstat()
    if not bno055write1(0x3E, 0x00):  raise OSError("BAD055_1")   # PWR_MODE normal
    if not bno055write1(0x3B, 0x00):  raise OSError("BAD055_2")   # UNIT_SEL: C, Degs, m/s^2
    if not bno055write1(0x3D, 0x0C):  raise OSError("BAD055_3")   # NDOF mode
    temperatureval = bno055read(0x34, 1)
    if temperatureval is None:
        raise OSError("BADTEMP")
    return ("Temp%d" % temperatureval[0])

prevcalibstat = 0x00
def recordcalibifnecessary(calibstat):
    global prevcalibstat, prevcalibvals
    if calibstat == 0xFF and prevcalibstat != 0xFF:
        calibs = bno055read(0x55, 22)
        if calibs is None:
            return
        if calibs != prevcalibvals:
            print("recordingcalibs", calibs)
            fcalib = open("calibfile.txt", "a")
            fcalib.write(mbs[2:10])
            fcalib.write(" ")
            for c in calibs:
                fcalib.write("%02X" % c)
            fcalib.write("\n")
            fcalib.flush()
            fcalib.close()
            prevcalibvals = calibs
        else:
            print("calibvals unchanged")
    prevcalibstat = calibstat


hposlst = b').38\x0b\x10\x15\x1a\x1f$' # =[41, 46, 51, 56, 11, 16, 21, 26, 31, 36]
def readhexlifyBNO055(timeoutms=20):
    global tbno055timeout,qw,qx,qy,qz
    nr = uart2.readinto(bno055buffer)
    brec = ((bno055buffer[0] == 0xBB) and (bno055buffer[1] == 22) and (nr == 24))
    mstamp = time.ticks_ms()
    if brec:
        mbs[2:10] = b"%08X" % mstamp
        mbs[61:63] = b"%02X" % bno055buffer[23]  # CALIB_STAT in 0x35 
        for i, p in enumerate(hposlst):
            v = bno055buffer[i*2 + 2] + (bno055buffer[i*2 + 3]<<8)
            mbs[p:p+4] = b"%04X" % v
        tbno055timeout = 0  # immediately fire off the next request
        
        recordcalibifnecessary(bno055buffer[23])
    
    if mstamp > tbno055timeout:
        uart2.write(b"\xAA\x01\x20\x16")
        tbno055timeout = mstamp + timeoutms
    return bs if brec else None

#qw,qx,qy,qz = ustruct.unpack("<HHHH", bno055buffer[2:10])
#ax,ay,az = ustruct.unpack("<HHH", bno055buffer[10:16])
#gx,gy,gz = ustruct.unpack("<HHH", bno055buffer[16:22])
#"Zt{:08X}x{:04X}y{:04X}z{:04X}".format(mstamp, ax, ay, az)
#"a{:04X}b{:04X}c{:04X}".format(gx, gy, gz)
#"w{:04X}x{:04X}y{:04X}z{:04X}s{:02X}\n".format(qw, qx, qy, qz, calibstat)

def GetEulerAngles():
    # should take from bs-record (but don't forget signs)
    q0,q1,q2,q3 = ustruct.unpack("<hhhh", bno055buffer[2:10]) 
    
    #def ConvertQuatToEuler(q0, q1, q2, q3):
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

