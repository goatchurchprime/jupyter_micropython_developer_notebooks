# do the connectionstuff (remember to put onto hotspot)

import network, socket
import time, machine

pled = machine.Pin(2, machine.Pin.OUT)
pboot = machine.Pin(0, machine.Pin.IN)

port = 9019
sockudp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sockudp.settimeout(0.1)

wconn, wpass = b'BV6000', b'beckaaaa'
si = network.WLAN(network.STA_IF) 
si.active(True)
bwconnexists = bool(l  for l in si.scan()  if l[0] == wconn)
si.connect(wconn, wpass)
while not si.isconnected():
    pled.value(1-pled.value())
    time.sleep_ms(100)
udpaddr = ("192.168.43.1", port)

print(si.ifconfig())
tudptimeout = 0

def dwrite(mess):
    try:
        sockudp.sendto(mess, udpaddr)
    except OSError as e:
        print("dwrite", e)

import machine, time
# Vin=Red, Gnd=Black, RX2=Green, TX2=Yellow
# https://randomnerdtutorials.com/esp32-pinout-reference-gpios/
uart = machine.UART(1, baudrate=9600, rx=16, tx=17)  # labelled R/TX2
time.sleep(1)
print(uart.read())




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
    if bd[0] == b"$GNRMC" and bd[2] == b"A":
        for c, i in zip(bd[9], [8, 9, 5, 6, 2, 3]):
            isotimestamp[i] = c
        SetIsoTimestampFromGps(bd[1])
        latminutes10000 = ((int(bd[3][:2])*60 + int(bd[3][2:4]))*10000 + int(bd[3][5:9]))*(1 if bd[4] == b'N' else -1)
        lngminutes10000 = ((int(bd[5][:3])*60 + int(bd[5][3:5]))*10000 + int(bd[5][6:10]))*(1 if bd[6] == b'E' else -1)
        if bd[8]:
            veldegrees100 = int(bd[8].replace(b".", b""))
        #velknots100 = float100parse(recline + recblock[7]); 
        return b"D"  # says do not print
    
    if bd[0] == b"$GNGGA" and bd[6] != b"0":
        SetIsoTimestampFromGps(bd[1])
        latminutes10000 = ((int(bd[2][:2])*60 + int(bd[2][2:4]))*10000 + int(bd[2][5:9]))*(1 if bd[3] == b'N' else -1)
        lngminutes10000 = ((int(bd[4][:3])*60 + int(bd[4][3:5]))*10000 + int(bd[4][6:10]))*(1 if bd[5] == b'E' else -1)
        altitude10 = int(bd[9].replace(b".", b""))
        return "Qt{:08X}u{:08X}y{:08X}x{:08X}a{:04X}\n".format(mstamp, mstampmidnight, latminutes10000&0xFFFFFFFF, lngminutes10000&0xFFFFFFFF, altitude10).encode()

    if bd[0] == b"$GNVTG" and bd[9] != b"N" and bd[1]:
        veldegrees100 = int(bd[1].replace(b".", b""))
        velkph100 = int(bd[7].replace(b".", b""))
        if veldegrees100 != 0 or velkph100 != 0:
            return "Vt{:08X}v{:04X}d{:06X}\n".format(mstamp, velkph100, veldegrees100).encode()
        return b"D"
        
    return b""  # says can printpreview

for j in uart:
    pass
sq = [ ]
while 1:
    j = uart.readline()
    if j:
        if j[0] == ord('$') or sq:
            sq.append(j)
        #print(j, sq)
        if j[-1] == ord('\n'):
            lbd = b"".join(sq)
            #print(lbd)
            x = ParseNMEA(lbd)
            if x and x != b"D":
                print(x)
                dwrite(x)
                pled.value(1 - pled.value())
            del sq[:]
