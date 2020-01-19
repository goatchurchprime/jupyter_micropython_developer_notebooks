import time
from machine import Pin
from mqtt_as import config
import uasyncio as asyncio
from mqtt_as import config
    
fconfig = dict(x.split()  for x in open("config.txt"))
config['server'] = fconfig["mqttbroker"]
config['ssid'] = fconfig["wifiname"]
config['wifi_pw'] = fconfig["wifipassword"]
config['mqttchannel'] = fconfig["boardname"]

if "pinled" in fconfig:
    pinled = Pin(int(fconfig["pinled"]), Pin.OUT)
    for i in range(10):
        pinled.value(i%2)
        time.sleep_ms(300)

async def mqttconnecttask(client, bflip=False):
    if bflip and "wifialt" in fconfig:
        assid, awifi_pw, aserver = fconfig["wifialt"].split(",")
        if client._ssid == assid:
            assid, awifi_pw, aserver = fconfig["wifiname"], fconfig["wifipassword"], fconfig["mqttbroker"]
        client._ssid, client._wifi_pw, client.server = assid, awifi_pw, aserver
    try:
        print("connecting to:", client._ssid)
        await client.connect()
        return
    except OSError as e:
        print("client connect", [e])
        
    aloop = asyncio.get_event_loop()
    aloop.create_task(mqtttask(client, not bflip))
