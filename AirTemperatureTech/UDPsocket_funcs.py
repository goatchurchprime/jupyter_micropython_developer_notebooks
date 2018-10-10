import network, socket, time

# Create access point for the phone to log onto
si = network.WLAN(network.AP_IF) 
si.active(True)         
print(si.ifconfig())

espname = "ESP_%X%X%X" % tuple(si.config("mac")[-3:])
print("\nConnect to wifi {}".format(espname))
port = 9019

sockudp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sockudp.settimeout(0.1)
sockudp.bind(("192.168.4.1", port))

udpaddr = None
tudptimeout = 0

def dwrite(mess):
    global udpaddr
    if udpaddr is not None:
        try:
            sockudp.sendto(mess, udpaddr)
        except OSError as e:
            print(e)
            udpaddr = None

def dflush():
    global udpaddr
    if udpaddr is None:
        try:
            rmess, udpaddr = sockudp.recvfrom(100)
            print(rmess, udpaddr)
        except OSError as e:
            print(e)
            
