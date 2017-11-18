import time
time.sleep(1.0)

from syslog import log, elog, powid
import os, ustruct, uasyncio

from connectwifi import ipnumber
#from connecthotspot import ipnumber

from webserve_funcs import servestaticfile
from webserve_funcs import servefilelist
from webserve_funcs import readhttpheaders
from webserve_funcs import recpostsave
from webserve_funcs import servemessage
from webserve_funcs import convertsavepostfile


async def handleconnection(reader, writer):
    receivedrequest = await readhttpheaders(reader)
    
    if "POST" in receivedrequest:
        await recpostsave(receivedrequest, reader, "POSTUPLOAD.txt")
        await servemessage(writer, "done")
        await writer.aclose()
        convertsavepostfile("POSTUPLOAD.txt")
        return

    rpath = receivedrequest.get("GET")
    log(receivedrequest)
    
    bcallaclose = True
    if rpath == "":
        await servefilelist(writer)
    elif rpath:
        await servestaticfile(writer, rpath)
        
    if bcallaclose:
        await writer.aclose()


# enables rewriting handleconnection function without restarting
def handleconnection_indirect(reader, writer):
    try:
        return handleconnection(reader, writer)
    except OSError as e:
        print("handleconnection exception", str(e))

port = 80
loop = uasyncio.get_event_loop()
print("* Running on http://%s:%s/" % (ipnumber, port))
loop.create_task(uasyncio.start_server(handleconnection_indirect, ipnumber, port))

loop.run_forever()
