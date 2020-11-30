import time, network, sys
from machine import Pin
from mqtt_as import config
import uasyncio as asyncio
from mqtt_as import config
    
fconfig = dict(x.strip().split(None, 1)  for x in open("config.txt"))
cdelimeter = fconfig.get("cdelimeter", ",")
if "connection0" in fconfig:
    config['ssid'], config['wifi_pw'], config['server'] = fconfig["connection0"].split(cdelimeter)
else:
    config['ssid'] = fconfig["wifiname"]
    config['wifi_pw'] = fconfig["wifipassword"]
    config['server'] = fconfig["mqttbroker"]

pinled = Pin(abs(int(fconfig["pinled"])), Pin.OUT)  if "pinled" in fconfig  else None
shortmac = "{:02X}{:02X}{:02X}".format(*network.WLAN().config('mac')[-3:])
topicstem = "%s/%s" % (sys.platform, shortmac)
network.WLAN().active(0)   # disable the connection at startup
config['ping_interval'] = 30

def flashpinled(n=5, sl0=300, sl1=300):
    if pinled:
        pinledOnvalue = 0 if (fconfig["pinled"][0] == "-") else 1
        for i in range(1, n*2+1):
            pinled.value((i%2)==pinledOnvalue)
            time.sleep_ms(sl0 if (i%2) else sl1)

async def flashledconnectedtask(client):
    pinledOnvalue = 0 if (fconfig["pinled"][0] == "-") else 1
    while True:
        pinled.value(pinledOnvalue)
        await asyncio.sleep_ms(50  if client.isconnected()  else 500)
        pinled.value(1-pinledOnvalue)
        await asyncio.sleep_ms(5000)

async def mqttconnecttask(client, cnumber=None):
    if cnumber is not None:
        if ("connection%d"%cnumber) not in fconfig:
            cnumber = 0
        y = fconfig.get("connection%d"%cnumber, \
            cdelimeter.join(fconfig.get(x, 'x') for x in ['wifiname', 'wifipassword', 'mqttbroker']))\
            .split(cdelimeter)
        print(y)
        client._ssid, client._wifi_pw, client.server = y

    else:
        cnumber = 0
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
    aloop.create_task(mqttconnecttask(client, cnumber+1))
    

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
    
    

