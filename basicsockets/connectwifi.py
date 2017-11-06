import network

si = network.WLAN(network.STA_IF)
macaddress = "".join("{:02x}".format(x)  for x in si.config("mac"))
si.active(True)

knownwifis = dict(k.split(b":")[:2]  for k in open("wificodes.txt", "rb"))
print("Scanning wifis:", ", ".join(s.decode()  for s in knownwifis))

# X[3]=RSSI (received signal strength)
wifiname = max((sc  for sc in si.scan()  if sc[0] in knownwifis), key=lambda X: X[3])[0]  

print("Connecting to strongest known wifi signal", wifiname.decode())
si.connect(wifiname, knownwifis[wifiname])
del knownwifis

while not si.isconnected():
    pass

ipnumber = si.ifconfig()[0]
print("Device has ipnumber", ipnumber)
