import network, socket, time, machine

# delay for reset
pled = machine.Pin(2, machine.Pin.OUT)
for i in range(10):
    time.sleep_ms(200)
    pled.value(i%2)

# Connect to Blackview (Android) phone
wconn, wpass = b'BV6000', b'beckaaaa'
si = network.WLAN(network.STA_IF) 
si.active(True)
bwconnexists = bool(l  for l in si.scan()  if l[0] == wconn)
si.connect(wconn, wpass)
while not si.isconnected():
    pled.value(1-pled.value())
    time.sleep_ms(100)

# set up UDP networking to the phone
udpaddr = ("192.168.43.1", 9019)  # ip default for android
sockudp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sockudp.settimeout(0.1)

udpaddrUBX = ("192.168.43.1", 9020)  # ip default for android
sockudpUBX = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sockudpUBX.settimeout(0.1)

def dwrite(mess):
    try:
        sockudp.sendto(mess, udpaddr)
    except OSError as e:
        print("dwrite", e)

def dwriteUBX(mess):
    try:
        sockudpUBX.sendto(mess, udpaddrUBX)
    except OSError as e:
        print("dwrite", e)
