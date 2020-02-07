import time, network
from machine import Pin
from mqtt_as import config
import uasyncio as asyncio
from mqtt_as import config
    
fconfig = dict(x.strip().split(None, 1)  for x in open("config.txt"))
config['server'] = fconfig["mqttbroker"]
config['ssid'] = fconfig["wifiname"]
config['wifi_pw'] = fconfig["wifipassword"]
pinled = Pin(int(fconfig["pinled"]), Pin.OUT)  if "pinled" in fconfig  else None
shortmac = "{:02X}{:02X}{:02X}".format(*network.WLAN().config('mac')[-3:])
#network.WLAN().active(0)  # disable the connection at startup

def flashpinled(n=5, sl0=300, sl1=300):
    if pinled:
        for i in range(n*2):
            pinled.value(i%2)
            time.sleep_ms(sl0 if (i%2) else sl1)

async def mqttconnecttask(client, bflip=False):
    if bflip and "wifialt" in fconfig:
        assid, awifi_pw, aserver = fconfig["wifialt"].split(",")
        if client._ssid == assid:
            assid, awifi_pw, aserver = fconfig["wifiname"], fconfig["wifipassword"], fconfig["mqttbroker"]
        client._ssid, client._wifi_pw, client.server = assid, awifi_pw, aserver
    try:
        print("await connecting to:", client._ssid, client.server)
        await client.connect()
        print("*** connected:")
        flashpinled(10, 100, 100)
        return
    except OSError as e:
        print("client connect error", [e], "retasking...")
        
    flashpinled(5, 300, 50)
    aloop = asyncio.get_event_loop()
    aloop.create_task(mqttconnecttask(client, not bflip))

# mosquitto_pub -h mqtt.local -t "esp8266maggas1/cmd" -m "print('hi there')"   
async def callbackcmdtask(client, topicreply, codemsg):
    print("executing", [codemsg])
    try:
        exec(codemsg)
        await client.publish(topicreply, "1")
    except Exception as e:
        print(e)
        await client.publish(topicreply+'/exception', str(e))
    return
    
    

