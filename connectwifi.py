import network

si = network.WLAN(network.STA_IF)
si.active(True)
#assert not si.isconnected()

knownwifis = dict(k.split(b":")[:2]  for k in open("wificodes.txt", "rb"))
wifiname = max((sc  for sc in si.scan()  if sc[0] in knownwifis), key=lambda X: X[3])[0]  # X[3]=RSSI (received signal strength)
print("strongest known DoESWifi signal", wifiname)
si.connect(wifiname, knownwifis[wifiname])
del knownwifis

while not si.isconnected():
    pass

ipnumber = si.ifconfig()[0]
print("Connect through wifi to", ipnumber)
