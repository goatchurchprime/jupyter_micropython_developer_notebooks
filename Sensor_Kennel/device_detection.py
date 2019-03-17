import time, ustruct

def IdentifyI2CDevice(i2c):
    res = [ ]
    ads = i2c.scan()
    
    if 0x29 in ads:
        revid = i2c.readfrom_mem(0x29, 0xc2, 1)[0]
        devid = i2c.readfrom_mem(0x29, 0xc0, 1)[0]
        print("Revision ID:", hex(revid), "Device ID:", hex(devid))
        if devid == 0xee:
            res.append("VL53L0X lidar")
    
    if 0x29 in ads:
        def get_reg8(address):
            i2c.writeto(0x29, ustruct.pack('>H', address))
            return i2c.readfrom(0x29, 1)[0]
        model = get_reg8(0x0000)
        revision = (get_reg8(0x0001), get_reg8(0x0002))
        module_revision = (get_reg8(0x0003), get_reg8(0x0004))
        if model == 180:
            print("revision", revision, "module_revision", module_revision)
            res.append("VL6180 lidar")
            
    if 0x40 in ads:
        i2c.writeto(0x40, b'\xFC\xC9')
        if i2c.readfrom(0x40, 1)[0] == 21:
            res.append("SI7021 humidity")
            
    if 0x39 in ads:
        chip_id = i2c.readfrom_mem(0x39, 0x80 | 0x0A, 1)[0]
        partno = (chip_id >> 4) & 0x0f  # should be 5
        if partno == 5:
            res.append("TSL561 luminous")
            
    if 0x48 in ads:
        res.append("TMP102 temp")
        
    if 0x69 in ads:
        res.append("CDM7160 CO2-gas")
        
    if 0x6B in ads and 0x1E in ads:
        res.append("SDOF GyAccMag")

    if 0x77 in ads:
        k = i2c.readfrom_mem(0x77, 0xD0, 1)[0]
        if k == 0x60:
            res.append("BME280 barhumid")
        if k == 0x55:
            res.append("BME180 barhumid")
            
    if 0x44 in ads:
        i2c.writeto(0x44, b'\xF3\x2D')
        k = i2c.readfrom(0x44, 3)   # status
        if len(k) == 3:
            res.append("SHT31D tmphumid")
            
    if 0x50 in ads and 0x60 in ads:
        k = i2c.readfrom_mem(0x50, 0xD2, 1)
        if k[0] == 0x8b:
            res.append("MLX90621 16x4-ir")
            
    if 0x28 in ads:
        res.append("PX4PITOT airspeed")

    if not res:
        desc = " ".join("%02x"%c  for c in ads  if c != 0x3c)
        if desc:
            res.append("unknown %s" % desc)
        
    return res

# UART(1, baudrate=9600, rx=13, tx=12)
def IdentifyUARTDevice(uart):
    res = [ ]
    uart.init(baudrate=115200)
    for i in range(3):
        uart.read()
        uart.write(b"\xAA\x01\x00\x06")  # request chip_id and firmware version
        time.sleep_ms(20)
        r = uart.read()
        if r is not None and len(r) == 8 and r[:3] == b'\xbb\x06\xa0':
            swversion = "%d.%d" % (r[6], r[7])  # 8.3
            res.append("BNO055 orient")
            break
        time.sleep(0.2)
            
    uart.init(baudrate=9600)
    for i in range(10):
        x = uart.readline()
        if x is not None and x[:3] == b"$GP":
            res.append("GPS NMEA")
            break
        time.sleep(0.1)
        
    return res
    
    