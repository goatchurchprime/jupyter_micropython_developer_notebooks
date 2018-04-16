import ustruct, time, math

i2c = None
def setupSI7021(li2c):
    global i2c
    i2c = li2c
    i2c.writeto(0x40, b'\xFE')  # resets chip
    time.sleep_ms(20)  # got to delay or you get an error if call next function too soon
    
def SI7021checkchip():
    i2c.writeto(0x40, b'\xFA\x0F')
    sna = i2c.readfrom(0x40, 8)
    i2c.writeto(0x40, b'\xFC\xC9')
    snb = i2c.readfrom(0x40, 6)
    i2c.writeto(0x40, b'\x84\xB8')
    firmr = i2c.readfrom(0x40, 1)
    print("SNA %s %s %s %s  SNB %s %s %s %s  firmware %s" % (hex(sna[0]), hex(sna[2]), hex(sna[4]), hex(sna[6]), hex(snb[0]), hex(snb[1]), hex(snb[3]), hex(snb[4]), hex(firmr[0])))
    return (snb[0] == 21) # identifies the Si7021 type chip

def SI7021printstatus():
    reg1 = i2c.readfrom_mem(0x40, 0xE7, 1)[0]
    heater = i2c.readfrom_mem(0x40, 0x11, 1)[0]
    print("MeasRes:%s VDD:%s heater-on:%s heater:%s" % (hex(reg1 & 0x81), hex(reg1 & 0x40), hex(reg1 & 0x04), hex(heater & 0x0F)))

def SI7021setheater(hheater):
    # hheater to be between 0 and 15
    reg1 = i2c.readfrom_mem(0x40, 0xE7, 1)[0]
    nreg1 = (reg1 & 0xFB) if (hheater == 0) else (reg1 | 0x04) 
    i2c.writeto_mem(0x40, 0xE6, bytes([nreg1]))
    
    heater = i2c.readfrom_mem(0x40, 0x11, 1)[0]
    nheater = ((heater & 0xF0) | hheater); 
    i2c.writeto_mem(0x40, 0x51, bytes([nheater]))

def SI7021humiditytempBin():
    i2c.writeto(0x40, b'\xE5')  
    time.sleep_ms(20)   # give it time to take a reading or it fails
    bh = i2c.readfrom(0x40, 2)
    bt = i2c.readfrom_mem(0x40, 0xE0, 2)
    return bh, bt

def SI7021humiditytempConv(bh, bt):
    rh = ustruct.unpack(">H", bh)[0] & 0xFFFC
    rt = ustruct.unpack(">H", bt)[0] & 0xFFFC
    return ((125.0*rh)/65536)-6, ((175.25*rt)/65536)-46.85 

def SI7021humiditytemp():
    bh, bt = SI7021humiditytempBin()
    return SI7021humiditytempConv(bh, bt)

def DewpointTemperature(humid, temp):
    A, B, C = 8.1332, 1762.39, 235.66
    svp = 10**(A - B/(temp + C))*133.322387415
    pvp = svp*humid/100
    return -C - B/(math.log10(pvp/133.322387415) - A)
