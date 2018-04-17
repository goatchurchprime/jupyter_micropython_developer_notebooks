import ustruct
i2c = None

def SetupAccGyrMag(li2c):
    global i2c
    i2c = li2c
    
    # turn on gyros reg(0x10)0x20=(ODR_G,FS_G,0,BWG)=001 00 0 00 gives 65ms ~ 14.9Hz
    # turn on gyros reg(0x10)0x40=(ODR_G,FS_G,0,BWG)=010 00 0 00 gives 59.9Hz at 245deg/sec
    # turn on gyros reg(0x10)0x40=(ODR_G,FS_G,0,BWG)=010 11 0 00 gives 59.9Hz at 2000deg/sec
    i2c.writeto(0x6B, b'\x10\x40')  # these gyros don't seem to work anyway.  give constant values that respond to orienting (0x13), scaling(0x10), enabling(0x1e), but not any any measuring of the environment

    # turn on accelerometer reg(0x20)=(ODR_XL,FS_XL,BW_SCAL_ODR,BW_XL)=110 00 0 00 should give 952Hz, but is overridden by gyros ODR 
    # there are various further settings of FIFO and High and Low pass filters
    i2c.writeto(0x6B, b'\x20\xC0')  

    i2c.writeto(0x1E, b'\x22\x00')  

    # turn on magnetometer reg(0x20)=(TEMP_COMP,OM,DO,0,ST)=1 11 110 0 0 (Ultra High Performance, 40Hz)
    #i2c.writeto(0x1E, b'\x20\x58')  
    i2c.writeto(0x1E, b'\x20\x58')  

    
# reading the accelerometer/gyro/compass
Lcsd = { "a":(0x6B, 1, b"\x28"), "g":(0x6B, 2, b"\x18"), "c":(0x1E, 8, b"\x28") }
def readvectorsensor(vs):
    cs, stm, ds = Lcsd[vs] 
    while True:   # loop to wait for readings to be ready (at 60Hz)
        i2c.writeto(cs, b'\x27')
        st = ord(i2c.readfrom(cs, 1))  # (IG_XL,IG_G,INACT,BOOT_STATUS,TDA,GDA,XLDA) states whether a reading is ready
        if st & stm:
            break
    i2c.writeto(cs, ds)
    s = i2c.readfrom(cs, 6)
    sv = ustruct.unpack("<hhh", s)
    return sv
    
# rough temperature detector in the accelerometer
def readiacctemperature():
    k = i2c.readfrom_mem(0x6B, 0x15, 2)
    t = ustruct.unpack("<h", k)
    return t[0]/18.1 + 28.6  # worked out experimentally in fridge
