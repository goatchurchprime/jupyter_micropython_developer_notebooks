import machine, time

# First get the display up with its functions
sck = machine.Pin(14)
miso = machine.Pin(12)
mosi = machine.Pin(13) 
spi = machine.SPI(sck=sck, miso=miso, mosi=mosi, 
                  baudrate=1000000, polarity=0, phase=0, firstbit=machine.SPI.MSB)
cs = machine.Pin(2, machine.Pin.OUT)  # sets the pin to output
cs.value(1)

def swrite(s):
    cs.value(0)
    time.sleep_ms(5)
    spi.write(s)
    cs.value(1)
    time.sleep_ms(5)
         
swrite(b"\x0C\x00")
swrite(b"\x0F\x00")
swrite(b"\x0B\x07")
swrite(b"\x09\x00")
swrite(b"\x0C\x01")

nums = b"\x7E\x30\x6D\x79\x33\x5B\x5F\x70\x7F\x7B"
alpha = b"\x77\x1F\x0D\x3D\x4F\x47\x7B\x37\x44jk\x0Em\x15\x1D\x67\x73\x05\x5B\x0F\x1Cvwx\x3Bz"
def writestring(s):
    if type(s) == str:
        s = s.encode()
    ep = 0
    for e in range(8):
        ol = (s[ep]  if ep < len(s)  else 32)
        c = 0x80
        
        if ol == 32:
            c = 0x00
        elif 48 <= ol <= 57:
            c = nums[ol - 48]
        elif 97 <= ol <= 122:
            c = alpha[ol - 97]
        if ep+1 < len(s) and s[ep+1] == ".":
            c += 0x80
            ep += 1
        swrite(b"%c%c" % (8-e, c))
        ep += 1


# wifi situation
writestring("cnncting.")
import network

si = network.WLAN(network.STA_IF)
macaddress = "".join("{:02x}".format(x)  for x in si.config("mac"))
si.active(True)
si.connect(b"DoESLiverpool", b"decafbad00")
while not si.isconnected():
    pass
ipnumber = si.ifconfig()[0] 
print(ipnumber)
writestring("cnncted.")


# MQTT technology
from umqtt.robust import MQTTClient

c = MQTTClient("sevenseg", "10.0.29.167")
c.connect()
c.publish(b"sevenseg/on", b"now")

writestring("777  777")
dispmsg = "oooo"
def sub_cb(topic, msg):
    global dispmsg
    print(topic, msg)
    dispmsg = msg
c.set_callback(sub_cb)
c.connect()
c.subscribe(topic=b"sevenseg/show") 

# main loop
import time
currmsg = dispmsg
br = 1
while True:
    c.check_msg()
    if dispmsg != currmsg: 
        currmsg = dispmsg
        writestring(dispmsg)
        c.publish(b"sevenseg/on", b"now")

    time.sleep(0.1)
    swrite(b"\x0A%c" % ((br%8)+7))  # pulse the brightness
    br += 1