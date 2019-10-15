import array, ustruct

i2c = None

dcs = { }  # map addr to constants arrays of ints (to handle 2 sensors on one bus)
dT1 = const(0);  dT2 = const(1);  dT3 = const(2); # these are indexes into dc
dP1 = const(3);  dP2 = const(4);  dP3 = const(5);  dP4 = const(6); dP5 = const(7); 
dP6 = const(8);  dP7 = const(9);  dP8 = const(10); dP9 = const(11); 
dH1 = const(12); dH2 = const(13); dH3 = const(14); dH4 = const(15); dH5 = const(16); dH6 = const(17); 

def bme280init(li2c, addr=0x77):
    global i2c
    i2c = li2c
    dc = dcs[addr] = array.array("i", range(18))  # calibrations

    k = i2c.readfrom_mem(addr, 0xD0, 1)[0]
    assert k in [0x60, 0x55], ("chip not found", hex(k))
    
    i2c.writeto_mem(addr, 0xF2, b'\x01')  # switch on humidity (over)sampling=1
    i2c.writeto_mem(addr, 0xF4, b'\x27')  # switch on temp and pressure (over)sampling=1, mode=normal(continuous readings)
    i2c.writeto_mem(addr, 0xF5, b'\x00')  # 0.5ms standby, no filtering, no-SPI

    dc[dT1], dc[dT2], dc[dT3] = ustruct.unpack("<Hhh", i2c.readfrom_mem(addr, 0x88, 6))
    dc[dP1], dc[dP2], dc[dP3], dc[dP4], dc[dP5], dc[dP6], dc[dP7], dc[dP8], dc[dP9] = \
            ustruct.unpack("<Hhhhhhhhh", i2c.readfrom_mem(addr, 0x8E, 18))
        
    dc[dH1] = i2c.readfrom_mem(addr, 0xA1, 1)[0]
    dig_e1_e7 = i2c.readfrom_mem(addr, 0xE1, 7)
    dc[dH2], dc[dH3] = ustruct.unpack("<hB", dig_e1_e7)
    e4_sign = ustruct.unpack_from("<b", dig_e1_e7, 3)[0]
    dc[dH4] = (e4_sign << 4) | (dig_e1_e7[4] & 0xF)
    e6_sign = ustruct.unpack_from("<b", dig_e1_e7, 5)[0]
    dc[dH5] = (e6_sign << 4) | (dig_e1_e7[4] >> 4)
    dc[dH6] = ustruct.unpack_from("<b", dig_e1_e7, 6)[0]


readout = bytearray(8)
def readBME280(addr=0x77):
    # burst readout from 0xF7 to 0xFE, recommended by datasheet
    i2c.readfrom_mem_into(addr, 0xF7, readout)
    dc = dcs[addr]
    raw_press = ((readout[0] << 16) | (readout[1] << 8) | readout[2]) >> 4
    raw_temp = ((readout[3] << 16) | (readout[4] << 8) | readout[5]) >> 4
    raw_hum = (readout[6] << 8) | readout[7]

    # temperature
    var1 = ((raw_temp >> 3) - (dc[dT1] << 1)) * (dc[dT2] >> 11)
    var2 = (((((raw_temp >> 4) - dc[dT1]) * ((raw_temp >> 4) - dc[dT1])) >> 12) * dc[dT3]) >> 14
    t_fine = var1 + var2
    tempout = (t_fine * 5 + 128) >> 8
    
    # pressure
    var1 = t_fine - 128000
    var2 = var1 * var1 * dc[dP6]
    var2 = var2 + ((var1 * dc[dP5]) << 17)
    var2 = var2 + (dc[dP4] << 35)
    var1 = (((var1 * var1 * dc[dP3]) >> 8) + ((var1 * dc[dP2]) << 12))
    var1 = (((1 << 47) + var1) * dc[dP1]) >> 33
    if var1 == 0:
        pressureout = 0
    else:
        p = 1048576 - raw_press
        p = (((p << 31) - var2) * 3125) // var1
        var1 = (dc[dP9] * (p >> 13) * (p >> 13)) >> 25
        var2 = (dc[dP8] * p) >> 19
        pressureout = ((p + var1 + var2) >> 8) + (dc[dP7] << 4)
    
    # humidity
    h = t_fine - 76800
    h = (((((raw_hum << 14) - (dc[dH4] << 20) - (dc[dH5] * h)) + 16384) >> 15) * (((((((h * dc[dH6]) >> 10) * (((h * dc[dH3]) >> 11) + 32768)) >> 10) + 2097152) * dc[dH2] + 8192) >> 14))
    h = h - (((((h >> 15) * (h >> 15)) >> 7) * dc[dH1]) >> 4)
    h = 0 if h < 0 else h
    h = 419430400 if h > 419430400 else h
    humidityout = h >> 12
    return (tempout/100, pressureout/256, humidityout/1024)


        
        