import network

si = network.WLAN(network.AP_IF) # create access-point interface
macaddress = "".join("{:02x}".format(x)  for x in si.config("mac"))
si.active(True)         # activate the interface
print("Creating access point ESP_{}".format(macaddress[-6:]))

ipnumber = si.ifconfig()[0]
print("Device has ipnumber", ipnumber)