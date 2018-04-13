def IdentifyI2CDevice(i2c):
    res = [ ]
    ads = i2c.scan()
    if 0x29 in ads:
        revid = i2c.readfrom_mem(0x29, 0xc2, 1)[0]
        devid = i2c.readfrom_mem(0x29, 0xc0, 1)[0]
        print("Revision ID:", hex(revid), "Device ID:", hex(devid))
        if devid == 0xee:
            res.append("VL53L0X") 
    if 0x40 in ads:
        i2c.writeto(0x40, b'\xFC\xC9')
        if i2c.readfrom(0x40, 1)[0] == 21:
            res.append("SI7021")
    return res