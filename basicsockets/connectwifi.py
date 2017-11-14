import network
from syslog import log

si = network.WLAN(network.STA_IF)
macaddress = "".join("{:02x}".format(x)  for x in si.config("mac"))
si.active(True)

knownwifis = dict(k.split(b":")[:2]  for k in open("wificodes.txt", "rb"))
print("Scanning wifis:", ", ".join(s.decode()  for s in knownwifis))

# X[3]=RSSI (received signal strength)
wifiname = max((sc  for sc in si.scan()  if sc[0] in knownwifis), 
               key=lambda X: X[3], 
               default=[None])[0]  

if wifiname is not None:
    log("Strongest wifi", wifiname.decode())
    si.connect(wifiname, knownwifis[wifiname])
    del knownwifis

    while not si.isconnected():
        pass

    ipnumber = si.ifconfig()[0] 
    
else:
    log("No recognized wifi")
    si = network.WLAN(network.AP_IF) # create access-point interface
    si.active(True)         # activate the interface
    log("Creating access point ESP_{}".format(macaddress[-6:]))
    ipnumber = si.ifconfig()[0]

log("Device has ipnumber", ipnumber)
