import ustruct, time, math

i2c = None
bgain16 = False       # x16 gain
integration_time = 0  # 0:13.7ms, 1:101ms, 2:402ms, or 3:manual

def setregtimings(lbgain16, lintegration_time):
    global bgain16, integration_time
    bgain16, integration_time = lbgain16, lintegration_time
    x = i2c.readfrom_mem(0x39, 0x80 | 0x01, 1)[0]  # _REGISTER_TIMING
    x = (x & 0xEC) | (0x10 if bgain16 else 0x00) | (integration_time & 0x03)
    i2c.writeto_mem(0x39, 0x80 | 0x01, chr(x))

def setupTSL561(li2c):
    global i2c, bgain16, integration_time
    i2c = li2c
    i2c.writeto_mem(0x39, 0x80 | 0x00, b"\x03")    # _CONTROL_POWERON
    x = i2c.readfrom_mem(0x39, 0x80 | 0x01, 1)[0]  # _REGISTER_TIMING
    bgain16 = (x & 0x10) != 0
    integration_time = (x & 0x03)
    
def luminosity():
    br = ustruct.unpack("<h", i2c.readfrom_mem(0x39, 0x80 | 0x0C, 2))[0]
    ir = ustruct.unpack("<h", i2c.readfrom_mem(0x39, 0x80 | 0x0E, 2))[0]
    return br, ir  # (can't fetch both with same read command)

_CLIP_THRESHOLD = (4900, 37000, 65000)
def compute_lux(br, ir):
    ch0, ch1 = br, ir
    if ch0 == 0:
        return None
    if ch0 > _CLIP_THRESHOLD[integration_time]:
        return None
    if ch1 > _CLIP_THRESHOLD[integration_time]:
        return None
    ratio = ch1 / ch0
    if ratio >= 0 and ratio <= 0.50:
        lux = 0.0304 * ch0 - 0.062 * ch0 * ratio**1.4
    elif ratio <= 0.61:
        lux = 0.0224 * ch0 - 0.031 * ch1
    elif ratio <= 0.80:
        lux = 0.0128 * ch0 - 0.0153 * ch1
    elif ratio <= 1.30:
        lux = 0.00146 * ch0 - 0.00112 * ch1
    else:
        lux = 0
        
    if not bgain16:
        lux *= 16
    if integration_time == 0:
        lux /= 0.034
    elif integration_time == 1:
        lux /= 0.252
    return lux
