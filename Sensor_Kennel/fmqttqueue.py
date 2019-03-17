from mqtt_as import MQTTClient, config
import uasyncio as asyncio
from collections import deque

def callback(topic, msg):
    print((topic, msg))

async def conn_han(client):
    await client.subscribe('foo_topic', 1)


class FMQTTQueue:
    def __init__(self, pled=None):
        self.fqueue = None
        self.rqueue = deque((), 3)
        self.sublist = [ ]
        self.nsublist = None
        self.client = None
        self.pled = pled
        self.npublish = 0
        
    def callback(self, topic, msg):
        self.rqueue.append((topic, msg))

    async def conn_han(self, client):
        #assert client == self.client
        print("DRunning conn_han", self.nsublist, len(self.sublist))
        if self.nsublist is None:
            self.nsublist = 0
        while self.nsublist < len(self.sublist):
            await self.client.subscribe(self.sublist[self.nsublist], 1)
            self.nsublist += 1
            
    def addsubscription(self, topic):
        self.sublist.append(topic)
        if self.nsublist is not None:
            print("DRerunning conn_han", topic)
            asyncio.get_event_loop().create_task(self.conn_han(self.client))
            
    def setupmqttas(self, wifiname, wifipassword, mqttbroker):
        config['ssid'] = wifiname
        config['wifi_pw'] = wifipassword
        config['server'] = mqttbroker
        config['subs_cb'] = self.callback
        config['connect_coro'] = self.conn_han
        MQTTClient.DEBUG = True
        self.client = MQTTClient(config)

    def fput(self, topic, msg):
        if self.fqueue is not None:
            self.fqueue.append((topic, msg))
        
    async def fstreamtask(self):
        if self.pled is not None:  
            self.pled.value(1)
            
        print("DConnecting.")
        await self.client.connect()
        print("DConnected.")
        if self.pled is not None:  
            for i in range(11):
                self.pled.value(i%2)
                await asyncio.sleep_ms(50 if (i%4) else 250)
                
        self.fqueue = deque((), 3)
        while True:
            while not self.fqueue:
                await asyncio.sleep_ms(50)
            topic, msg = self.fqueue.popleft()
            await self.client.publish(topic, msg, qos=1)
            self.npublish += 1
            
