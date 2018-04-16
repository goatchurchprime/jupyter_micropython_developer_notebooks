import ustruct, time, math

i2c = None

def getgain16():
    return (i2c.readfrom_mem(0x39, 0x80 | 0x01, 1)[0] & 0x10) != 0 # _REGISTER_TIMING

def setgain16(b):
    x = i2c.readfrom_mem(0x39, 0x80 | 0x01, 1)[0]  # _REGISTER_TIMING
    i2c.writeto_mem(0x39, 0x80 | 0x01, chr((x & 0xEF) | (0x10 if b else 0x00)))

def getsamplewindow():
    # The integration time. 0:13.7ms, 1:101ms, 2:402ms, or 3:manual"""
    x = i2c.readfrom_mem(0x39, 0x80 | 0x01, 1)[0]  # _REGISTER_TIMING
    return x & 0x03

def setsamplewindow(c):
    # The integration time. 0:13.7ms, 1:101ms, 2:402ms, or 3:manual"""
    x = i2c.readfrom_mem(0x39, 0x80 | 0x01, 1)[0]  # _REGISTER_TIMING
    i2c.writeto_mem(0x39, 0x80 | 0x01, chr((x & 0xFC) | (c & 0x03)))

def setupTSL561(li2c):
    global i2c
    i2c = li2c
    i2c.writeto_mem(0x39, 0x80 | 0x00, b"\x03")  # _CONTROL_POWERON
    setgain16(False)
    setsamplewindow(2)
    
def luminosity():
    br = ustruct.unpack("<h", i2c.readfrom_mem(0x39, 0x80 | 0x0C, 2))[0]
    ir = ustruct.unpack("<h", i2c.readfrom_mem(0x39, 0x80 | 0x0E, 2))[0]
    return br, ir  # (can't fetch both with same read command)


_GAIN_SCALE = (16, 1)
_TIME_SCALE = (1 / 0.034, 1 / 0.252, 1)
_CLIP_THRESHOLD = (4900, 37000, 65000)

def _compute_lux(self):
    """Based on datasheet for FN package."""
    ch0, ch1 = self.luminosity
    if ch0 == 0:
        return None
    if ch0 > _CLIP_THRESHOLD[self.integration_time]:
        return None
    if ch1 > _CLIP_THRESHOLD[self.integration_time]:
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
                        # Pretty sure the floating point math formula on pg. 23 of datasheet
                        # is based on 16x gain and 402ms integration time. Need to scale
                        # result for other settings.
                        # Scale for gain.
                        lux *= _GAIN_SCALE[self.gain]
                        # Scale for integration time.
                        lux *= _TIME_SCALE[self.integration_time]
                        return lux
