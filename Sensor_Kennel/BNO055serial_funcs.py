import time, ubinascii, ustruct, math

# This device needs calibration by being moved about.  
# if BNO055calibstat returns 0xff then everything is good, and 
# you should record ReadCalibration() and be able to feed 
# this value back in on startup

uart = None

def bno055write1(reg, val):
    uart.write(bytes((0xAA, 0x00, reg, 1, val)))
    time.sleep_ms(20)
    v = uart.read()
    if v != b'\xee\x01':
        raise Exception("bad bno055write %s" % str(v))

def bno055read(reg, n):
    uart.write(b"\xAA\x01")
    uart.write(chr(reg))
    uart.write(chr(n))
    time.sleep_ms(20)
    r = uart.read()
    if not ((r[0] == 0xBB) and (r[1] == n) and (len(r) == n + 2)):
        raise Exception("bad bno055read %s" % str(r))
    return r[2:]

def InitBNO055(luart):
    global uart
    uart = luart
    bno055write1(0x3D, 0x00)   # PWR_MODE
    bno055write1(0x3B, 0x00)   # UNIT_SEL, celsius, UDegrees and m/s^2
    bno055write1(0x3D, 0x0C)   # back to NDOF mode
    print("Temperature", bno055read(0x34, 1)[0])
    
def ReadCalibration():
    bno055write1(0x3D, 0x00)   # PWR_MODE
    calib = bno055read(0x55, 22)
    bno055write1(0x3D, 0x0C)   # back to NDOF mode
    return ubinascii.hexlify(calib).decode()
    
def SetCalibration(calib):
    calib = ubinascii.unhexlify(calib)
    uart.read()  # clear buffer
    bno055write1(0x3D, 0x00)   # PWR_MODE
    for i in range(10):          # tends to choke a few times before it gets it
        uart.write(b"\xAA\x00\x55\x16")
        uart.write(calib)
        time.sleep_ms(50)
        v = uart.read()
        if v == b'\xee\x01':
            break
    bno055write1(0x3D, 0x0C)   # back to NDOF mode
    return v == b'\xee\x01'


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

def BNO055absorientation():
    m = bno055read(0x20, 8)
    qw, qx, qy, qz = ustruct.unpack("<hhhh", m[0:8])
    #accx, accy, accz = ustruct.unpack("<hhh", m[8:14])
    #gx, gy, gz = ustruct.unpack("<hhh", m[14:22])
    return ConvertQuatToEuler(qw, qx, qy, qz)

def BNO055calibstat():
    calibstat = bno055read(0x35, 1)[0]
    #print("sys:", (calibstat>>6)&0x03, "gyr:", (calibstat>>4)&0x03, "acc:", (calibstat>>2)&0x03, "mag:", calibstat&0x03)
    return calibstat
