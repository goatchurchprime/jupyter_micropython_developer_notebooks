import ustruct, math

# I think PS1=Low is i2c and High is serial

# I2C interface (PS1=Low) (doesn't work from ESP32)
def BNO055init(li2c):
    global i2c
    i2c = li2c
    k = i2c.readfrom_mem(0x28, 0x00, 6)
    print("BNO055 sensor SW_REV_ID: %s.%s" %(hex(k[4]), hex(k[5])))
    i2c.writeto_mem(0x28, 0x3D, b'\x00')     # config mode
    i2c.writeto_mem(0x28, 0x3E, b'\x00')     # PWR_MODE, normal
    i2c.writeto_mem(0x28, 0x3B, b'\x00')     # UNIT_SEL, celsius, UDegrees and m/s^2
    i2c.writeto_mem(0x28, 0x3D, b'\x0c')     # back to NDOF mode

def BNO055calibstat():
    calibstat = i2c.readfrom_mem(0x28, 0x35, 1)[0]
    print("sys:", (calibstat>>6)&0x03, "gyr:", (calibstat>>4)&0x03, "acc:", (calibstat>>2)&0x03, "mag:", calibstat&0x03)
    return calibstat

def BNO055quat():  # returns qw, qx, qy, qz
    return ustruct.unpack("<hhhh", i2c.readfrom_mem(0x28, 0x20, 8))
    #accx, accy, accz = ustruct.unpack("<hhh", i2c.readfrom_mem(0x28, 0x28, 6))
    #gravx, gravy, gravz = ustruct.unpack("<hhh", i2c.readfrom_mem(0x28, 0x2E, 6))

def BNO055poletilt():
    q0, q1, q2, q3 = ustruct.unpack("<hhhh", i2c.readfrom_mem(0x28, 0x20, 8))
    riqsq = q0*q0 + q1*q1 + q2*q2 + q3*q3 
    iqsq = 1/max(1,riqsq)
    r31 = 2*(q1*q3 - q0*q2)*iqsq
    r32 = 2*(q0*q1 + q2*q3)*iqsq
    r33 = 1 - 2*(q1**2 + q2**2)*iqsq
    sidetilt = math.degrees(-math.atan2(r33, r32))
    foretilt = math.degrees(-math.atan2(r31, r32))
    return foretilt, sidetilt

def BNO055gacc():
    accx, accy, accz = ustruct.unpack("<hhh", i2c.readfrom_mem(0x28, 0x28, 6))
    gravx, gravy, gravz = ustruct.unpack("<hhh", i2c.readfrom_mem(0x28, 0x2E, 6))
    gdot = accx*gravx + accy*gravy + accz*gravz
    return int(gdot/981)

    