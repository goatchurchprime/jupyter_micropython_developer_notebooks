import time
time.sleep(1.0)

from syslog import log, elog, powid
import os, ustruct, uasyncio

from webserve_funcs import servestaticfile
from webserve_funcs import servefilelist
from webserve_funcs import readhttpheaders

from webserve_funcs import recpostsave
from webserve_funcs import servemessage
from webserve_funcs import convertsavepostfile

from websocket_funcs import make_hybi07_header
from websocket_funcs import servewebsocket

from ms5611 import GetMS5611calibrations, MS5611convert, ams5611read
from ds3231 import rtctojsepoch, jsepochtoisodate

import machine, array 
i2c = machine.I2C(scl=machine.Pin(5), sda=machine.Pin(4))

greenpin = machine.PWM(machine.Pin(13), freq=1024, duty=40)
touchpin = machine.TouchPad(machine.Pin(33))


jsepochoffset = rtctojsepoch(i2c, busywaitsec=True) - time.ticks_ms()
log(jsepochtoisodate(jsepochoffset))


# enable the wifi only if entry is held down on startup
ipnumber = ""
for i in range(10):
    if touchpin.read() > 1100:
        break
    greenpin.duty(500 if ((i%2) == 0) else 0)
    time.sleep_ms(200)
    touchpin.read()
else:
    # this should be deferred or made on-off
    for i in range(20):
        greenpin.duty(500 if ((i%2) == 0) else 0)
        time.sleep_ms(50)
    
    #from connectwifi import ipnumber
    from connecthotspot import ipnumber
    
    for i in range(20):
        greenpin.duty(500 if ((i%2) == 0) else 0)
        time.sleep_ms(50)

        
import array, ustruct
from lsq_funcs import setpt0, addpt, copylq, mergelq, calcmc, calcrsq, dn

lqR = array.array("f", [0]*7)
lqA = array.array("f", [0]*7)
lqS = array.array("f", [0]*7)
nbatch = 32
rlimsq = 2.2**2

def nextpt(t, v, fout):
    if lqR[dn] == 0:
        setpt0(lqR, t, v)
        return
    addpt(lqR, t, v)
    if lqR[dn] < nbatch:
        return
    if lqA[dn] == 0:
        copylq(lqA, lqR)
        lqR[dn] = 0
        return
    copylq(lqS, lqA)
    mergelq(lqS, lqR)
    m, c = calcmc(lqS)
    rsq = calcrsq(lqS, m, c)
    if rsq > rlimsq:
        print("rsq", lqA[dn], rsq)
        if fout:
            fout.write(ustruct.pack("<fffffff", *lqA))
            fout.flush()
        copylq(lqA, lqR)
    else:
        copylq(lqA, lqS)
    lqR[dn] = 0
        
        
hook_ms5611 = [1, 0, 0, None]

async def ams5611():
    log("Entering ams5611")
    bdat = open("b%d_%d.dat"%(powid, time.ticks_ms()//1000), "wb")
    nbdat = 0
    try:
        dc = GetMS5611calibrations(i2c)
        readout = bytearray(3)
        while hook_ms5611[0]:
            await ams5611read(dc, readout, i2c, uasyncio)
            t = time.ticks_ms()
            hook_ms5611[2] = MS5611convert(dc)
            if bdat:
                nextpt(t, hook_ms5611[2]-100000, bdat)
                nbdat += 1
                if nbdat > 10000:
                    bdat.close()
                    bdat = None
            if hook_ms5611[3]:  # dump out to logfile here (if open)
                hook_ms5611[3].write(ustruct.pack("<II", hook_ms5611[1], hook_ms5611[2]))
                if (hook_ms5611[1]>>13) != (t>>13):   # 8 seconds
                    hook_ms5611[3].flush()
            hook_ms5611[1] = t
            greenpin.duty((t%500) if hook_ms5611[3] or (((t//500)%3) == 0) else 0)
    except Exception as e:
        elog(e)
    hook_ms5611[0] = -1
    log("Leaving ams5611")

async def createLogFile():
    ti = 0
    while hook_ms5611:
        ti = (ti + 1  if touchpin.read()<1100  else 0)
        if ti > 3:
            log("making datfile")
            hook_ms5611[3] = open("%d_%d.dat"%(powid, time.ticks_ms()//1000), "wb")
            for i in range(12*10):    # 10 minutes 
                await uasyncio.sleep_ms(5*1000)   # 5 second chunks
                if touchpin.read()<1100:
                    break   # break early
            hook_ms5611[3].close()
            hook_ms5611[3] = None
            await uasyncio.sleep_ms(5*1000)   # pause before activating again
        await uasyncio.sleep_ms(50)
    
    
# coroutine for handling the write loop (and closing when note comes through thr reader)
async def wswritesensorloop(rpath, writer, wscondition):
    rpath = rpath.split(",")
    
    delayms = int(rpath[1])
    hexbuff = bytearray(16)
    #if rpath[0] == "bme280":
    try:
        while wscondition[1]:
            while len(wscondition) > 2:
                incoming = wscondition.pop(2)
                log("[WS%d incoming] %s"%(wscondition[0], incoming))
                
            await writer.awrite(make_hybi07_header(16))
            ustruct.pack_into(">II", hexbuff, 8, hook_ms5611[1], hook_ms5611[2])
            for i in range(8):
                b = hexbuff[i+8]
                hexbuff[i*2] = (b>>4) + (48 if b < 160 else 55)  #ord('0')=48; ord('A')=65
                b &= 15
                hexbuff[i*2+1] = b + (48 if b < 10 else 55)
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
if ipnumber:
    print("Will listen on http://%s:%s/" % (ipnumber, port))
    loop.create_task(uasyncio.start_server(handleconnection_indirect, ipnumber, port))
loop.create_task(ams5611())
loop.create_task(createLogFile())


loop.run_forever()
