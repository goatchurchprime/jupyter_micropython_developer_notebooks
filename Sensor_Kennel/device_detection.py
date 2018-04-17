def IdentifyI2CDevice(i2c):
    res = [ ]
    ads = i2c.scan()
    if 0x29 in ads:
        revid = i2c.readfrom_mem(0x29, 0xc2, 1)[0]
        devid = i2c.readfrom_mem(0x29, 0xc0, 1)[0]
        print("Revision ID:", hex(revid), "Device ID:", hex(devid))
        if devid == 0xee:
            res.append("VL53L0X lidar")
            
    if 0x40 in ads:
        i2c.writeto(0x40, b'\xFC\xC9')
        if i2c.readfrom(0x40, 1)[0] == 21:
            res.append("SI7021 humidity")
            
    if 0x39 in ads:
        chip_id = i2c.readfrom_mem(0x39, 0x80 | 0x0A, 1)[0]
        partno = (chip_id >> 4) & 0x0f  # should be 5
        if partno == 5:
            res.append("TSL561 luminous")
            
    if 0x48 in scannedi2c:
        res.append("TMP102 temp")
            
    if not res:
        desc = " ".join("%02x"%c  for c in ads  if c != 0x3c)
        if desc:
            res.append("unknown %s" % desc)
        else:
            res.append("nothing nothing")
        
    return res