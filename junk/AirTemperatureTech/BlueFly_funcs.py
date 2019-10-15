import time
from machine import UART
uart = UART(1, baudrate=57600, rx=13, tx=17)

# get and set bluefly settings
def GetBFVsettings():
    uart.write(b"$BST*\r\n")
    for code in [b"BST", b"SET"]:
        for i in range(500):
            lbd = uart.readline()
            time.sleep_ms(1)
            if lbd and lbd[:3] == code:
                if lbd[-1] != ord(b"\n"):
                    time.sleep_ms(50)
                    lbd += uart.readline() or b""
                break
        else:
            return {}
        if code == b"BST":
            lbdkeys = lbd
    return dict(zip(lbdkeys.split(), map(int, lbd.split()[1:])))

def BFVmakesettings(lBFVsettings):
    bfvsettings = GetBFVsettings()
    if not bfvsettings:
        return False
    for k, v in lBFVsettings.items():
        if bfvsettings.get(k) != v:
            print("Setting", k, v)
            uart.write(b"${:s} {:d}*\r\n".format(k, v))
            time.sleep_ms(100)
        else:
            print(k, "already good")
    return True

def sendgpsack(comm):
    s = 0
    for c in comm:
        s ^= c
    uart.write(b"${:s}*{:02x}\r\n".format(comm, s))
    rcode = b"$PMTK001,%s,3"%(comm[4:].split(b",", 1)[0])
    for i in range(1000):
        k = uart.readline()
        if k and k[:len(rcode)] == rcode:
            return True
        #if k and k[:1] == b"$":  print("kk", k)
        time.sleep_ms(1)
    return False

def SetupGPS():
    uart.write(b"$BRB 34*\r\n")  # BFV read from GPS at baud 57600
    time.sleep_ms(50)
    if not sendgpsack(b"PMTK220,1000"):
        uart.write(b"$BRB 207*\r\n") # BFV read from GPS baud 9600
        time.sleep_ms(50)
        if sendgpsack(b"PMTK220,1000"):
            print("Change GPS to baud 57600")
            sendgpsack(b"PMTK251,57600") # set GPS baud 57600
            uart.write(b"$BRB 34*\r\n")  # BFV read from GPS at 57600
            time.sleep_ms(50)
            if not sendgpsack(b"PMTK220,1000"):
                print("GPS not seen at baud 57600")
                return False
        else:
            print("GPS not waking")
            return False
    else:
        print("GPS already baud 57600")

    # GPGLL=0,GPRMC=5,GPVTG=1,GPGGA=1,GPGSA=0,GPGSV=0 record multiples (RMC once a second, GGA 5 times a second)
    return sendgpsack(b"PMTK314,0,5,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0") \
           and sendgpsack(b"PMTK220,200") # 5 times a second
#while 1: x=uart.readline(); print(x.decode() if x and x[:1]==b"$" else "", end="")

isotimestamp = bytearray("2099-99-99T99:99:99.999")
mstampmidnight = 0
ord0 = const(48) # ord('0')
def SetIsoTimestampFromGps(c1):
    global mstampmidnight
    for c, i in zip(c1, [11, 12, 14, 15, 17, 18, 20, 20, 21, 22]):
        isotimestamp[i] = c
    mstampmidnight = sum((c-ord0)*f  for c, f in zip(c1, [10*60*60*1000, 60*60*1000, 10*60*1000, 60*1000, 10*1000, 1000, 0, 100, 10, 1]))  # multiplies out the parts of the timefield
    return True 

def ParseNMEA(lbd):
    mstamp = time.ticks_ms()
    bd = lbd.split(b",")
    if bd[0] == b"$GPRMC" and bd[2] == b"A":
        for c, i in zip(bd[9], [8, 9, 5, 6, 2, 3]):
            isotimestamp[i] = c
        SetIsoTimestampFromGps(bd[1])
        latminutes10000 = ((int(bd[3][:2])*60 + int(bd[3][2:4]))*10000 + int(bd[3][5:]))*(1 if bd[4] == b'N' else -1)
        lngminutes10000 = ((int(bd[5][:3])*60 + int(bd[5][3:5]))*10000 + int(bd[5][6:]))*(1 if bd[6] == b'E' else -1)
        veldegrees100 = int(bd[8].replace(b".", b""))
        #velknots100 = float100parse(recline + recblock[7]); 
        return b"D"  # says do not print
    
    if bd[0] == b"$GPGGA" and bd[6] != b"0":
        SetIsoTimestampFromGps(bd[1])
        latminutes10000 = ((int(bd[2][:2])*60 + int(bd[2][2:4]))*10000 + int(bd[2][5:]))*(1 if bd[3] == b'N' else -1)
        lngminutes10000 = ((int(bd[4][:3])*60 + int(bd[4][3:5]))*10000 + int(bd[4][6:]))*(1 if bd[5] == b'E' else -1)
        altitude10 = int(bd[9].replace(b".", b""))
        return "Qt{:08X}u{:08X}y{:08X}x{:08X}a{:04X}\n".format(mstamp, mstampmidnight, latminutes10000&0xFFFFFFFF, lngminutes10000&0xFFFFFFFF, altitude10).encode()

    if bd[0] == b"$GPVTG" and bd[9] != b"N":
        veldegrees100 = int(bd[1].replace(b".", b""))
        velkph100 = int(bd[7].replace(b".", b""))
        if veldegrees100 != 0 or velkph100 != 0:
            return "Vt{:08X}v{:04X}d{:06X}\n".format(mstamp, velkph100, veldegrees100).encode()
        return b"D"
        
    return b""  # says can printpreview
