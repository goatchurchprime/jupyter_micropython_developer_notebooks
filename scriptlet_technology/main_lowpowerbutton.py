# Needs: MicroPython_ESP32_psRAM_LoBo build

import time
import utime
from  machine import Pin, I2C
import machine
import ssd1306
import framebuf
import network
import ubinascii

# Definitions
ssid = 'DoESLiverpool'
password = 'decafbad00'

# Why did we wake up?
print(machine.wake_description())

# Setup OLED
rst = Pin(16, Pin.OUT)
rst.value(1)
scl = Pin(15, Pin.OUT, Pin.PULL_UP)
sda = Pin(4, Pin.OUT, Pin.PULL_UP)

i2c = I2C(scl=scl, sda=sda, freq=450000)

oled = ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3c)
 
# Gimme a welcome screen!
oled.fill(0)
oled.text('DoES Dash', 0, 0)
oled.show()
time.sleep(0.25)

# Set up networking
sta_if = network.WLAN(network.STA_IF)
 
oled.text('Wifi Connecting', 0, 10)
#oled.text(ssid, 0, 20)
oled.show()
 
if not sta_if.isconnected():
    print("Connecting to SSID", ssid)
    sta_if.active(True)
    sta_if.connect(ssid, password)
    while not sta_if.isconnected():
        pass
print("Connected! IP = ", sta_if.ifconfig()[0])

#oled.text("IP: " + sta_if.ifconfig()[0], 0, 30)
#oled.show()
#time.sleep(0.25)

rtc = machine.RTC()

# Sync RTC over NTP
if not rtc.synced():
    rtc.ntp_sync(server="hr.pool.ntp.org", tz="CET-1CEST")
    while not rtc.synced():
        pass
    print(utime.gmtime())
    print(utime.localtime())

# Send MQtt message
def conncb(task):
    print("[{}] Connected".format(task))

def disconncb(task):
    print("[{}] Disconnected".format(task))

def subscb(task):
    print("[{}] Subscribed".format(task))

def pubcb(pub):
    print("[{}] Published: {}".format(pub[0], pub[1]))

def datacb(msg):
    print("[{}] Data arrived from topic: {}, Message:\n".format(msg[0], msg[1]), msg[2])

mqtt = network.mqtt("does", "mqtt://10.0.29.187", user="user", password="pass", cleansession=True, connected_cb=conncb, disconnected_cb=disconncb, subscribed_cb=subscb, published_cb=pubcb, data_cb=datacb)

# secure connection requires more memory and may not work
#mqtts = network.mqtt("eclipse", "mqtts://iot.eclipse.org", cleansession=True, data_cb=datacb)

# mqtt over Websocket can also be used
# mqttws = network.mqtt("eclipse", "ws://iot.eclipse.org:80", cleansession=True, data_cb=datacb)
# mqttwss = network.mqtt("eclipse", "wss://iot.eclipse.org:80", cleansession=True, data_cb=datacb)

# Start the mqtt
print("Connecting to MQtt")
oled.text("Publishing Msg", 0, 20)
oled.show()

mqtt.start()

# Wait until status is: (1, 'Connected')
while mqtt.status()[0] < 2:
    print(mqtt.status())
    time.sleep(1)

#mqtt.subscribe('test')
mqtt.publish('button/' + ubinascii.hexlify(machine.unique_id()).decode('ascii'), 'woke up')

oled.text("Done. Sleeping", 0, 30)
oled.show()

i2c.deinit()

# Debug
time.sleep(1)

# Setup Sleep (wake on button press)
pin=machine.Pin(0)
pin.init(mode=pin.IN, pull=pin.PULL_UP)
rtc.wake_on_ext0(pin, 0)

print("Sleeping...")
machine.deepsleep()
