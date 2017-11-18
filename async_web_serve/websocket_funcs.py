import time, ustruct, uhashlib, ubinascii
from syslog import log, elog, powid
import uasyncio

async def initiatewebsocket(w, secwebsocketkey):
    guid = b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
    acc = uhashlib.sha1(secwebsocketkey + guid).digest()
    acc = ubinascii.b2a_base64(acc).strip()
    await w.awrite(b"HTTP/1.1 101 Switching Protocols\r\n")
    await w.awrite(b"Upgrade: websocket\r\nConnection: Upgrade\r\n")
    await w.awrite(b"Sec-WebSocket-Accept: %s\r\n\r\n" % acc)
    

def make_hybi07_header(length, opcode=0x81):   # 0x82 means binary
    # high bit of opcode says there is no continuation of this frame; opcode of 0x82 means binary
    if length > 0xffff:
        return ustruct.pack(">bbQ", opcode, 0x7f, length)
    if length > 0x7d:
        return ustruct.pack(">bbH", opcode, 0x7e, length)
    return ustruct.pack("bb", opcode, length)

async def wswrite(w, k, opcode=0x81):
    await w.awrite(make_hybi07_header(len(k), opcode))
    await w.awrite(k)

async def wsread(reader, wsid):
    while True:
        rex = await reader.readexactly(1)
        if len(rex) != 0:
            break
        log("[WS%d readexactly]"%wsid, [rex])
    opcode = (rex)[0] & 0x0F  # 8 means close
    if opcode == 8:
        log("[WS%d close]"%wsid)
        return None
    
    v = (await reader.readexactly(1))[0]
    masked = (v & 0x80)
    length = v & 0x7F
    if length == 0x7E:
        length = ustruct.unpack(">H", await reader.readexactly(2))[0]
    if length == 0x7F:
        length = ustruct.unpack(">Q", await reader.readexactly(8))[0]
    if masked:
        masked = await reader.readexactly(4)
    else:
        masked = b"\x00\x00\x00\x00"
        
    v = await reader.readexactly(length)
    v = bytes(k^masked[i%4]  for i, k in enumerate(v))
    return v
    
    
# coroutine for handling incoming stream which shares its state with wscondition=[wsid, state={1:good,0:dead}] object
async def wsreadprintloop(reader, wscondition):
    while wscondition[1]:
        try:
            res = await wsread(reader, wscondition[0])
        except OSError as e:
            print("[WS%d wsreadexception] %s"%(wscondition[0], str(e)))
            res = None
            
        if res is None:
            wscondition[1] = 0   # closed condition
            break
        log("[WS%d]"%wscondition[0], res)
        
        # pass any important messages through into this sequence! 
        # (not seen as a signal, but picked up next time that task wakes up)
        wscondition.append(res)  
        
    log("[WS%d rlleave]"%wscondition[0])

# this creates the wscondition structure that links the reader and the writer
WScount = 0
async def servewebsocket(rpath, reader, writer, secwebsocketkey, wswriteloop):
    global WScount
    await initiatewebsocket(writer, secwebsocketkey)
    await wswrite(writer, "HITHEREws(%d)"%WScount)
    wscondition = [WScount, 1]  # WSnumber, go/stop
    WScount += 1
    loop = uasyncio.get_event_loop()
    loop.create_task(wsreadprintloop(reader, wscondition))
    loop.create_task(wswriteloop(rpath, writer, wscondition))
    return False
    