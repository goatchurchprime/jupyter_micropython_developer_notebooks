import time, ustruct, ure, math, sys
import machine
import timefuncs

# Module containing the interfaces to all devices identifiable by scanning on startup with 
# the initdevices() function (to be called after things like pindallas has been set)

# Functions are as minimal as possible with i2c devices identified by their address codes
# RTC interface is via isodates and jsepoch (javascript time units) for compatibility with webpages

# GPIO0 and GPIO2 set what mode we boot up in.  If you use them they both need to be pulled up high
# GPIO15 needs a pull down (or it won't reboot properly).  Avoid using these pins anyway if you can.  
# (you can change the clock frequency with machine.freq(160000000) from 80000000)

# Wemos pins: GPIO12=D6, GPIO13=D7, GPIO5=D1, GPIO4=D2, GPIO15=D8

if sys.platform == "LoPy":
    # ESP32: Lopy means it goes scl=G17, sda=G16
    i2c = machine.I2C(baudrate=20000)
    p2 = None  # a bit hazy on getting pins right!
    readlightpin = None
    
else:
    i2c = machine.I2C(scl=machine.Pin(5), sda=machine.Pin(4))   # NodeMCU: (D1=SCL, D2=SDA)
    readlightpin = machine.Pin(13, machine.Pin.OUT)  # wired to the light resistor, read from adc pin

    p2 = machine.Pin(2, machine.Pin.OUT)
    p2.on()   # blue light off


readlightpause = 0   # pause delay in seconds after readlightpin set high; see also devices.enableloglightvalues
adc = machine.ADC(0)


# dallas wiring: flat face towards you, left is ground, right is live, middle is signal with a 4.7k pullup resistor onto the live
pindallas = None   # machine.Pin(12)  [would be good for pin0 as that one should be pulled up anyway]
dallasobj = None
dallasscanned = None

scannedi2c = None
bmp180consts = None
nlightson = set()

# these are off the string in Julian's house listed in order
#dallasqorder = { 3891110100093507112:8, 864691150498112552:1, 7926335366213288488:3, 17365880185180280616:5, 
#                 3891110100094395176:6, 2522015813366565160:4, 4179340476246253096:2, 5908722733156329256:7 }
dallasqorder = None

def initdevices():
    global scannedi2c, bmp180consts, nlightson, dallasobj, dallasscanned
    
    scannedi2c = i2c.scan()
    res = [ ]

    if pindallas:
        import ds18x20, onewire
        dallasobj = ds18x20.DS18X20(onewire.OneWire(pindallas))
        dallasscanned = dallasobj.scan()
        if dallasqorder:
            dallasscanned = sorted(dallasscanned, key=lambda X: dallasqorder.get(ustruct.unpack("<Q", X)[0], ustruct.unpack("<Q", X)[0]))
        res.append("Dallas sensors found: %d" % len(dallasscanned))
        for i in range(len(dallasscanned)):
            print(ustruct.unpack("<Q", dallasscanned[i])[0])
    
    if 0x68 in scannedi2c:
        res.append("0x68 is DS3231 real time clock set to %s" % timefuncs.jsepochtoisodate(timefuncs.rtctojsepoch()))
        timefuncs.RTCnotset = timefuncs.jsepochtoisodate(timefuncs.rtctojsepoch()) < '2017'
        timefuncs.i2c0x68 = i2c
    else:
        res.append("Internal RTC used currently set to %s" % timefuncs.jsepochtoisodate(timefuncs.rtctojsepoch()))
z    
    if 0x77 in scannedi2c:
        res.append("0x77 is BMP180 barometer")
        bcd = i2c.readfrom_mem(0x77, 0xAA, 22)
        bmp180consts = dict(zip(("AC1", "AC2", "AC3", "AC4", "AC5", "AC6", "B1", "B2", "MB", "MC", "MD"), ustruct.unpack(">hhhHHHhhhhh", bcd)))  # note the 3 unsigned constants

    if 0x32 in scannedi2c:
        res.append("0x32 is LED breakout board")
        i2c.writeto(0x32, b"\x00\x40")
        i2c.writeto(0x32, b"\x36\x53")
    nlightson = set()
        
    if 0x6B in scannedi2c:
        res.append("0x6B is Gyros/Accelerometer")
        
        # turn on gyros reg(0x10)0x20=(ODR_G,FS_G,0,BWG)=001 00 0 00 gives 65ms ~ 14.9Hz
        # turn on gyros reg(0x10)0x40=(ODR_G,FS_G,0,BWG)=010 00 0 00 gives 59.9Hz at 245deg/sec
        # turn on gyros reg(0x10)0x40=(ODR_G,FS_G,0,BWG)=010 11 0 00 gives 59.9Hz at 2000deg/sec
        i2c.writeto(0x6B, b'\x10\x40')  # these gyros don't seem to work anyway.  give constant values that respond to orienting (0x13), scaling(0x10), enabling(0x1e), but not any any measuring of the environment

        # turn on accelerometer reg(0x20)=(ODR_XL,FS_XL,BW_SCAL_ODR,BW_XL)=110 00 0 00 should give 952Hz, but is overridden by gyros ODR 
        # there are various further settings of FIFO and High and Low pass filters
        i2c.writeto(0x6B, b'\x20\xC0')  

    if 0x1E in scannedi2c:
        res.append("0x1E is Magnetometer(compass)")
        i2c.writeto(0x1E, b'\x22\x00')  

        # turn on magnetometer reg(0x20)=(TEMP_COMP,OM,DO,0,ST)=1 11 110 0 0 (Ultra High Performance, 40Hz)
        #i2c.writeto(0x1E, b'\x20\x58')  
        i2c.writeto(0x1E, b'\x20\x58')  
        
    if 0x69 in scannedi2c:
        res.append("0x69 is Figaro CO2 meter")
        i2c.writeto(0x69, b'\x01\x02')

    if 0x40 in scannedi2c:
        res.append("0x40 is SI7021 humidity sensor")
        i2c.writeto(0x40, b'\xFE')  # resets chip
        time.sleep(0.2)
        
    if 0x48 in scannedi2c:
        res.append("0x48 is TMP102 temperature sensor")

    if 0x70 in scannedi2c:
        res.append("0x70 is LED number panel")
        i2c.writeto(0x70, b"\x21")  # set up oscilator
        i2c.writeto(0x70, b"\x81")  # blink off
        i2c.writeto(0x70, b"\xE3")  # normal brightness 
        i2c.writeto_mem(0x70, 0x00, b"\xC0\x00\xC0\x00\xC0\x00\xC0\x00")
        
    if 0x28 in scannedi2c:
        k = i2c.readfrom_mem(0x28, 0x00, 6)
        res.append("BNO055 sensor SW_REV_ID: %s.%s" %(hex(k[4]), hex(k[5])))
        
        i2c.writeto_mem(0x28, 0x3D, b'\x00')     # config mode
        i2c.writeto_mem(0x28, 0x3E, b'\x00')     # PWR_MODE, normal
        i2c.writeto_mem(0x28, 0x3B, b'\x00')     # UNIT_SEL, celsius, UDegrees and m/s^2
        i2c.writeto_mem(0x28, 0x3D, b'\x0c')     # back to NDOF mode

    for a in scannedi2c:
        if a not in [0x68, 0x77, 0x32, 0x69, 0x6B, 0x1E, 0x48, 0x40, 0x70, 0x28]:
            res.append("%s: Unknown I2C device" % hex(a))
            
    return res


def LED4digitnumber(n):
    numcharled = b"\x3F\x06\xDB\xCF\xE6\xED\xFD\x07\xFF\xEF"
    bleadingzero = True
    sigfig = 1000
    for i in range(4):
        d = n//sigfig % 10
        if d == 0 and bleadingzero and i != 3:
            i2c.writeto_mem(0x70, i*2, b'\x00')
        else:
            i2c.writeto_mem(0x70, i*2, numcharled[d:d+1])
            bleadingzero = False
        sigfig = sigfig//10



def lightset(lightnumber, lightintensity):   # led lights
    if 0x32 in scannedi2c:
        i2c.writeto(0x32, chr(0x16+lightnumber) + chr(lightintensity))
    else:
        if lightintensity == 0:
            if lightnumber in nlightson:
                nlightson.remove(lightnumber)
        else:
            nlightson.add(lightnumber)
        if (len(nlightson) % 2) == 1:
            p2.off()
        else:
            p2.on()

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


def SI7021humiditytemp():
    i2c.writeto(0x40, b'\xF5')  # clock stretching hold type E5 seems not to work in micropython
    time.sleep_ms(20)   # give it time to take a reading or it fails
    bh = i2c.readfrom(0x40, 2)
    rh = ustruct.unpack(">H", bh)[0] & 0xFFFC
    bt = i2c.readfrom_mem(0x40, 0xE0, 2)
    rt = ustruct.unpack(">H", bt)[0] & 0xFFFC
    return ((125.0*rh)/65536)-6, ((175.25*rt)/65536)-46.85 

def DewpointTemperature(humid, temp):
    A, B, C = 8.1332, 1762.39, 235.66
    svp = 10**(A - B/(temp + C))*133.322387415
    pvp = svp*humid/100
    return -C - B/(math.log10(pvp/133.322387415) - A)


# figaro sensor
def readCO2():
    # pins are: 1 VDD [square pin], 2 GND, 3 ALARM, 4 PWM, 5 CAD0, 
    #           6 MSEL (Pulldown for I2C mode, checked only on startup), 7 CAL, 8 BUSY, 9 TX/SDA, 10 RC/SCL, 11 NC
    k = i2c.readfrom_mem(0x69, 0x03, 2)
    ppm = ustruct.unpack("<h", k)[0]
    return ppm


def readlight():
    if readlightpin:
        readlightpin.on()
    time.sleep(readlightpause)
    l = adc.read()
    if readlightpin:
        readlightpin.off()
    return l
    
def readtmp102():
    r = i2c.readfrom_mem(0x48, 0x00, 2)
    return r[0] + r[1]/256

# complex calculations to convert from the raw readings
def readbmp180():
    oversamplesetting = 3
    ossdelay = (5, 8, 14, 25)[oversamplesetting]
    
    i2c.writeto_mem(0x77, 0xF4, b"\x2E")
    time.sleep_ms(5)
    UT = ustruct.unpack(">h", i2c.readfrom_mem(0x77, 0xF6, 2))[0]
    i2c.writeto_mem(0x77, 0xF4, bytearray([0x34+(oversamplesetting << 6)]))
    time.sleep_ms(ossdelay)
    MSB, LSB, XLSB = ustruct.unpack("BBB", i2c.readfrom_mem(0x77, 0xF6, 3))
    
    b = bmp180consts
    X1 = (UT - b["AC6"])*b["AC5"]//2**15
    X2 = b["MC"]*2**11//(X1+b["MD"])
    B5 = X1+X2

    UP = ((MSB << 16)+(LSB << 8)+XLSB) >> (8-oversamplesetting)
    B6 = B5-4000
    X1 = (b["B2"]*(B6**2//2**12))//2**11
    X2 = b["AC2"]*B6//2**11
    X3 = X1+X2
    B3 = ((int((b["AC1"]*4+X3)) << oversamplesetting)+2)//4
    X1 = b["AC3"]*B6//2**13
    X2 = (b["B1"]*(B6**2//2**12))//2**16
    X3 = ((X1+X2)+2)//2**2
    B4 = abs(b["AC4"])*(X3+32768)//2**15
    B7 = (abs(UP)-B3) * (50000 >> oversamplesetting)
    if B7 < 0x80000000:
        p = (B7*2)//B4
    else:
        p = (B7//B4)*2
    X1 = (p//2**8)**2
    X1 = (X1*3038)//2**16
    X2 = (-7357*p)//2**16
    
    temperature10 = ((B5+8)//2**4)
    pressure = p+(X1+X2+3791)//2**4
    
    #altitude = -7990.0*math.log(pressure/101325.0)

    return temperature10, pressure
    

# reading the accelerometer/gyro/compass
Lcsd = { "a":(0x6B, 1, b"\x28"), "g":(0x6B, 2, b"\x18"), "c":(0x1E, 8, b"\x28") }
def readvectorsensor(vs):
    cs, stm, ds = Lcsd[vs] 
    if cs not in scannedi2c:
        return (0,0,0)
    while True:   # loop to wait for readings to be ready (at 60Hz)
        i2c.writeto(cs, b'\x27')
        st = ord(i2c.readfrom(cs, 1))  # (IG_XL,IG_G,INACT,BOOT_STATUS,TDA,GDA,XLDA) states whether a reading is ready
        if st & stm:
            break
    i2c.writeto(cs, ds)
    s = i2c.readfrom(cs, 6)
    sv = ustruct.unpack("<hhh", s)
    return sv

# very rough temperature detector in the accelerometer (shouldn't even bother with it)
def readiacctemperatureraw():
    if 0x6B in scannedi2c:
        i2c.writeto(0x6B, b'\x15')
        k = i2c.readfrom(0x6B, 2)
        t = ustruct.unpack("<h", k)
        return t[0]
    return 0
    
def readiacctemperature():
    return readiacctemperatureraw()/18.1 + 28.6  # worked out experimentally in fridge



        
        
# butterworth filtering code (useful to apply to random noise sensors, like CO2sensor)
class ABfilter:
    def __init__(self, b, a):
        self.b = b
        self.a = a
        assert len(self.b) == len(self.a)
        self.xybuff = None
        self.xybuffpos = 0

    def addfiltvalue(self, x):
        n = len(self.b)
        if self.xybuff is None:
            self.xybuff = [x]*(n*2)
        self.xybuff[self.xybuffpos] = x 
        j = self.xybuffpos 
        y = 0 
        for i in range(n):
            y += self.xybuff[j]*self.b[i] 
            if i != 0:
                y -= self.xybuff[j+n]*self.a[i] 
            j = j-1 if j!=0 else n-1
        if self.a[0] != 1:
            y /= self.a[0]
        self.xybuff[self.xybuffpos+n] = y 
        self.xybuffpos = self.xybuffpos+1 if self.xybuffpos!=n-1 else 0
        Dj = (n-1 if (self.xybuffpos == 0) else self.xybuffpos-1)
        assert self.xybuff[Dj+n] == y
        return y 

        

# The CO2 sensor has 50ppm noise element inherent in the sensor, which this Butterworth filter is good at ironing out to get a good result
CO2smoother = None
def readCO2smooth():
    global CO2smoother
    x = readCO2()
    if x == 0 or CO2smoother == "disable":
        return x  # bad result anyway
    if CO2smoother is None:
        #b, a = scipy.signal.butter(3, 0.01, 'low')
        b, a = [ 3.75683802e-06, 1.12705141e-05, 1.12705141e-05, 3.75683802e-06], [ 1., -2.93717073,  2.87629972, -0.93909894]
        CO2smoother = ABfilter(b, a)
        return 0  # first reading usually bad
    return int(CO2smoother.addfiltvalue(x)+1)
    
def BNO055calibstat():
    calibstat = i2c.readfrom_mem(0x28, 0x35, 1)[0]
    print("sys:", (calibstat>>6)&0x03, "gyr:", (calibstat>>4)&0x03, "acc:", (calibstat>>2)&0x03, "mag:", calibstat&0x03)
    return calibstat

def BNO055quat():  # returns qw, qx, qy, qz
    return ustruct.unpack("<hhhh", i2c.readfrom_mem(0x28, 0x20, 8))
    #accx, accy, accz = ustruct.unpack("<hhh", i2c.readfrom_mem(0x28, 0x28, 6))
    #gravx, gravy, gravz = ustruct.unpack("<hhh", i2c.readfrom_mem(0x28, 0x2E, 6))
    
def BNO055pitchrollorient():  
    q0, q1, q2, q3 = ustruct.unpack("<hhhh", i2c.readfrom_mem(0x28, 0x20, 8))
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


