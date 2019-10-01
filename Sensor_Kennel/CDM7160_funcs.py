# supplier for £40 https://www.soselectronic.com/products/figaro/cdm7160-c00-304480
# CDM7160_task()

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

    def getvalue(self):
        j = n-1 if (xybuffpos == 0) else xybuffpos-1
        return xybuff[j+n]; 
        


def readCO2sensor(i2c):
    try:
        k = i2c.readfrom_mem(0x69, 0x03, 2)
        v = (k[0]+k[1]*256)
    except OSError:
        v = 0
    return v

#
# code below to handle filtering out bad values/spike (based on simple exponential filter)
# and a noise filtering signal based on a butterworth AB filter
#

# The CO2 sensor has 50ppm noise element inherent in the sensor, 
# which this Butterworth filter is good at ironing out to get a good result
#b, a = scipy.signal.butter(3, 0.01, 'low')
b, a = [ 3.75683802e-06, 1.12705141e-05, 1.12705141e-05, 3.75683802e-06], \
       [ 1., -2.93717073,  2.87629972, -0.93909894]
butterworthfilter = ABfilter(b, a)

badreadings = (0, 274, 293)
expsmoothfactor, validrange = 1.0, 4000
co2ppmSmoothed = 0
def readCO2Filtered(n, i2c):  # n should iterate from 0
    global expsmoothfactor, validrange, co2ppmSmoothed
    co2ppm = readCO2sensor(i2c)
    if co2ppm not in badreadings:
        if n == 0:     expsmoothfactor, validrange = 1.0, 4000
        if n == 1:     expsmoothfactor, validrange = 0.8, 1000
        elif n == 5:   expsmoothfactor, validrange = 0.2, 200
        elif n == 50:  expsmoothfactor, validrange = 0.02, 60
        co2ppmSmoothed = co2ppm*expsmoothfactor + co2ppmSmoothed*(1.0-expsmoothfactor)
        if abs(co2ppmSmoothed - co2ppm) < validrange:
            bfiltco2ppm = butterworthfilter.addfiltvalue(co2ppm)
            return co2ppm, bfiltco2ppm
    return 0.0, 0.0

