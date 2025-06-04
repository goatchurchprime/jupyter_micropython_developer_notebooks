import time, network, sys
from machine import Pin, WDT
from mqtt_as import config, MQTTClient
import uasyncio as asyncio
    
fconfig = dict(x.strip().split(None, 1)  for x in open("config.txt"))
cdelimeter = fconfig.get("cdelimeter", ",")
if "connection0" in fconfig:
    config['ssid'], config['wifi_pw'], config['server'] = fconfig["connection0"].split(cdelimeter)
else:
    config['ssid'] = fconfig["wifiname"]
    config['wifi_pw'] = fconfig["wifipassword"]
    config['server'] = fconfig["mqttbroker"]
clientsingleton = [ ]


def sclient():
    return clientsingleton[0] if clientsingleton else None

pinled = Pin(abs(int(fconfig["pinled"])), Pin.OUT)  if "pinled" in fconfig  else None
pinledOnvalue = 0 if (fconfig.get("pinled", "+")[0] == "-") else 1

shortmac = "{:02X}{:02X}{:02X}".format(*network.WLAN().config('mac')[-3:])
topicstem = "%s/%s" % (sys.platform, shortmac)
topicstatus = topicstem+"/status"
network.WLAN().active(0)   # disable the connection at startup
config['will'] = (topicstatus, "offline", True)
config['ping_interval'] = 30

def flashpinled(n=5, sl0=300, sl1=300):
    if pinled:
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

async def mqttconnecttask(client):
    try:
        print("await connect")
        await client.connect()
        print("*** connected")
        flashpinled(10, 100, 100)
        clientsingleton.append(client)
        return
    except OSError as e:
        print("client connect error", [e], "retasking...")
    flashpinled(5, 300, 50)
    aloop = asyncio.get_event_loop()
    aloop.create_task(mqttconnecttask(cnumber+1))
    
def itertools_count():
    n = 0
    while True:
        yield n
        n += 1

async def WatchDogtask(wdtsecs):
    await asyncio.sleep_ms(20*1000)
    print("Starting Watchdog timer for", wdtsecs, "seconds")
    wd = WDT(timeout=int(wdtsecs*1000))
    while True:
        await asyncio.sleep_ms(1*1000)
        if clientsingleton and clientsingleton[0].isconnected():
            wd.feed()
            await asyncio.sleep_ms(9*1000)
        elif pinled:
            pinled.value(pinledOnvalue)
            await asyncio.sleep_ms(1*1000)
            pinled.value(not pinledOnvalue)


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


