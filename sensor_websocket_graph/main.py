import time
time.sleep(1.0)

from syslog import log, elog, powid
import os, ustruct, uasyncio

#from connectwifi import ipnumber
from connecthotspot import ipnumber

from webserve_funcs import servestaticfile
from webserve_funcs import servefilelist
from webserve_funcs import readhttpheaders

from webserve_funcs import recpostsave
from webserve_funcs import servemessage
from webserve_funcs import convertsavepostfile

from websocket_funcs import make_hybi07_header
from websocket_funcs import servewebsocket

from bme280 import bme280init, GetBME280calibrations, readBME280
from ms5611 import GetMS5611calibrations, MS5611convert, ams5611read

# hook = [ go=1/exit=0, time, t, p, h ]
async def abme280(i2c, hook):
    log("Entering abme280")
    try:
        if not bme280init(i2c):
            raise Exception("bme280 not found")
        dc = GetBME280calibrations(i2c)
        readout = bytearray(8)
        tph = array.array("i", range(3))
        while hook[0]:
            hook[1] = time.ticks_ms()
            readBME280(tph, dc, readout, i2c)
            hook[2] = tph[0]; hook[3] = tph[1]; hook[4] = tph[2]; 
            await uasyncio.sleep_ms(12)
    except Exception as e:
        elog(e)
    hook[0] = -1
    log("Leaving abme280")

def ams5611(i2c, hook):
    log("Entering ams5611")
    try:
        dc = GetMS5611calibrations(i2c)
        readout = bytearray(3)
        while hook[0]:
            await ams5611read(dc, readout, i2c, uasyncio)
            hook[1] = time.ticks_ms()
            hook[3] = MS5611convert(dc)

    except Exception as e:
        elog(e)
    hook[0] = -1
    log("Leaving ams5611")
        
def conv4inttoHex(hexbuff, i1, i2, i3, i4):
    ustruct.pack_into(">IIII", hexbuff, 16, i1, i2, i3, i4)
    for i in range(16):
        b = hexbuff[i+16]
        hexbuff[i*2] = (b>>4) + (48 if b < 160 else 55)  #ord('0')=48; ord('A')=65
        b &= 15
        hexbuff[i*2+1] = b + (48 if b < 10 else 55)

import machine, array 

i2c = machine.I2C(scl=machine.Pin(5), sda=machine.Pin(4))
hook_bme280 = array.array("i", [1,0,0,0,0])
hook_ms5611 = array.array("i", [1,0,0,0,0])

# coroutine for handling the write loop (and closing when note comes through thr reader)
async def wswritesensorloop(rpath, writer, wscondition):
    rpath = rpath.split(",")
    
    #hook = hook_bme280
    hook = hook_ms5611
    
    delayms = int(rpath[1])
    hexbuff = bytearray(32)
    #if rpath[0] == "bme280":
    try:
        while wscondition[1]:
            while len(wscondition) > 2:
                incoming = wscondition.pop(2)
                log("[WS%d incoming] %s"%(wscondition[0], incoming))
            await writer.awrite(make_hybi07_header(32))
            conv4inttoHex(hexbuff, hook[1], hook[2], hook[3], hook[4])
            await writer.awrite(hexbuff)
            await uasyncio.sleep_ms(delayms)
            
    except OSError as e:
        elog(e)
        wscondition[1] = 1
    log("[WS%d wpleave]"%wscondition[0])

async def handleconnection(reader, writer):
    receivedrequest = await readhttpheaders(reader)
    log(receivedrequest)
    
    if "POST" in receivedrequest:   # this is causing the str and binary comparison warning
        await recpostsave(receivedrequest, reader, "POSTUPLOAD.txt")
        await servemessage(writer, "done")
        await writer.aclose()
        #await reader.aclose()  # this gets a keyerror
        convertsavepostfile("POSTUPLOAD.txt")
        return
    
    rpath = receivedrequest.get("GET")
    
    bcallaclose = True
    if "WebSocketKey" in receivedrequest:
        bcallaclose = await servewebsocket(rpath, reader, writer, receivedrequest["WebSocketKey"], wswritesensorloop)
    elif rpath is None:
        pass
    elif rpath == "":
        await servefilelist(writer)
    else:
        await servestaticfile(writer, rpath)
        
    if bcallaclose:
        await writer.aclose()


import gc
async def garbagecollect():
    while True:
        gc.collect()
        await uasyncio.sleep_ms(20000)


# enables rewriting handleconnection function without restarting
def handleconnection_indirect(reader, writer):
    try:
        return handleconnection(reader, writer)
    except OSError as e:
        print("handleconnection exception", str(e))
    

port = 80
loop = uasyncio.get_event_loop()
loop.create_task(garbagecollect())
print("Will listen on http://%s:%s/" % (ipnumber, port))
loop.create_task(uasyncio.start_server(handleconnection_indirect, ipnumber, port))
#loop.create_task(abme280(i2c, hook_bme280))
loop.create_task(ams5611(i2c, hook_ms5611))

loop.run_forever()
