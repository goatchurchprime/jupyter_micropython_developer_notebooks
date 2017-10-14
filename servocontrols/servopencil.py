from pca9685servo import setangspeed 
import math, time

class servopencil:
    def __init__(self, h, s, p, e, a0, b0, r0, t0):
        self.h = h  # height servo2 axle
        self.s = s  # servo1 to 2 axle dist
        self.p = p  # pencil length
        self.e = e  # servo3 to pencil centre dist

        self.hps1 = -h**2 + (p+s)**2
        self.hps2 = h**2 - (p-s)**2
        self.hps3 = (h-s)**2 - p**2

        self.minx = math.sqrt(p**2 - (h+s)**2)
        self.maxx = math.sqrt(self.hps1)
        print("xrange", self.minx, self.maxx)
        
        self.a0 = a0  # vertical
        self.b0 = b0  # horizontal
        self.r0 = r0  # zero rad
        self.t0 = t0  # zero theta

        self.xp = 0
        self.yp = 0
        setangspeed([b0,a0,t0])

    def solveab(self, x):
        x2 = x**2
        a = 2*math.atan((2*self.s*x - math.sqrt((self.hps1 - x2)*(self.hps2 + x2)))/(self.hps3 + x2))
        b = math.acos((-self.s*math.sin(a) + x)/self.p)
        return math.degrees(a), math.degrees(b)

    def xy(self, x, y, bplus=0):
        rlsq = (self.e+x)**2 + (self.r0+y)**2
        r = math.sqrt(rlsq - self.e**2)
        t = math.degrees(math.atan(r/self.e) - math.atan((self.r0+y)/(self.e+x)))
        a, b = self.solveab(r)
        setangspeed([self.b0-(b-a)+bplus, self.a0-a, self.t0-t], 0)

    def goxy(self, x, y, bplus=0, feedrate=100):
        n = max(abs(x-self.xp), abs(y-self.yp), 1)
        for i in range(0, n+1):
            l = i/n
            self.xy(self.xp*(1-l) + x*l, self.yp*(1-l) + y*l, bplus)
            time.sleep(1/feedrate)
        self.xp = x
        self.yp = y
