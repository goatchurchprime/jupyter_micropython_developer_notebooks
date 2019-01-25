import ustruct, time, machine

uart = machine.UART(1, baudrate=9600, rx=16, tx=17)  # labelled R/TX2

def sendNMEA(comm):
    s = 0
    for c in comm:
        s ^= c
    uart.write(b"${:s}*{:02x}\r\n".format(comm, s))

def appendchecksumUBX(comm):
    ca, cb = 0, 0
    for c in comm[2:]:
        ca = (ca + c) & 0xFF
        cb = (cb + ca) & 0xFF
    comm.append(ca)
    comm.append(cb)

def checkchecksum(comm):
    if comm[0] == ord(b"$"):
        s = 0
        for c in comm[1:-5]:
            s ^= c
        try:
            return s == int(comm[-4:-2], 16)
        except ValueError:
            return False

    ca, cb = 0, 0
    for c in comm[2:-2]:
        ca = (ca + c) & 0xFF
        cb = (cb + ca) & 0xFF
    return comm[-2] == ca and comm[-1] == cb
    
def sendUBX(clsID, msgID, payload):  # look up on p138
    comm = bytearray((0xb5, 0x62, clsID, msgID, len(payload) & 0xFF, (len(payload)>>8) & 0xFF))
    comm.extend(payload)
    appendchecksumUBX(comm)
    uart.write(comm)
    comm = bytearray((0xb5, 0x62, 0x05, 0x01, 0x02, 0x00, clsID, msgID))
    appendchecksumUBX(comm)
    print("expected_ack:", bytes(comm))

def setbaud(baudrate):
    sendNMEA(b"PUBX,41,1,0007,0003,%d,0" % baudrate)
    uart.init(baudrate=baudrate)

def msgoutputs(msgIDmap, measRate):
    for msgId, cycles in msgIDmap.items():
        sendNMEA(b"PUBX,40,{:s},0,{:d},0,0,0,0".format(msgId, cycles))
    if measRate:
        sendUBX(0x06, 0x08, ustruct.pack("<HHH", measRate, 1, 0))  # UBX-CFG-RATE

def reboot():
    sendUBX(0x06, 0x04, ustruct.pack("<Hbb", 0x0001, 0, 0)) # Hot reboot
    uart.init(baudrate=9600)
        
def readprint(n):
    for i in range(n):
        l = uart.read()
        if l:
            print(l)
        else:
            time.sleep_ms(10)
            
#
# This does the full base parsing and checksum checking
# (will in future be done with async)
#
#Dseqs = [ ]
def uartgen():
    xbufflen = 400
    x = memoryview(bytearray(xbufflen))
    nx = 0
    t0 = time.ticks_ms()
    while 1:
        inx = uart.readinto(x[nx:])
        if not inx:
            if time.ticks_ms() - t0 > 2000:
                yield b''
                t0 = time.ticks_ms()
            time.sleep_ms(10)
            continue
        nx += inx
        #while len(Dseqs) >= 10:
        #    Dseqs.pop(0)
        #Dseqs.append(bytes(x[nx-inx:nx]))
        
        while nx > 0:
            assert inx <= nx
            if x[0] == ord(b'$'):
                while inx > 0:
                    if x[nx-inx] == ord(b'\n'):
                        inx -= 1
                        lnx = nx-inx
                        if lnx >= 6:
                            s = 0
                            for c in x[1:lnx-5]:
                                s ^= c
                            try:
                                if s == int(bytes(x[lnx-4:lnx-2]), 16):
                                    yield x[:lnx]
                            except ValueError:
                                pass
                        t0 = time.ticks_ms()
                        x[:inx] = x[lnx:nx]
                        nx = inx
                        break
                    if x[nx-inx] == 0xb5:
                        x[:inx] = x[nx-inx:nx]
                        nx = inx
                        break
                    inx -= 1
                else:
                    break
            elif x[0] == 0xb5:  # should also check the 0x62
                if nx < 8:
                    break
                reclen = x[4]+x[5]*256+8
                if reclen > xbufflen:
                    print("too long", bytes(x[:nx]))
                    nx = 0
                    break
                if nx < reclen:
                    break
                ca, cb = 0, 0
                for c in x[2:reclen-2]:
                    ca = (ca + c) & 0xFF
                    cb = (cb + ca) & 0xFF
                if x[reclen-2] == ca and x[reclen-1] == cb:
                    yield x[:reclen]
                t0 = time.ticks_ms()
                x[:nx-reclen] = x[reclen:nx]
                nx = nx - reclen
                inx = nx
            else:
                while inx > 0:
                    if x[nx-inx] == ord(b'$') or x[nx-inx] == 0xb5:
                        x[:inx] = x[nx-inx:nx]
                        nx = inx
                        break
                    else:
                        inx -= 1
                else:
                    nx = 0

                    
                    
def parseNMEA(lbd):
    bd = lbd[:-5].split(b",")
    if len(bd) > 10 and bd[0] == b"$PUBX" and bd[1] == b"00":
        isotimestamp = bytearray("99:99:99.999")
        mstampmidnight = 0
        c1 = bd[2]
        ord0 = const(48) # ord('0')
        for c, i in zip(c1, [11, 12, 14, 15, 17, 18, 20, 20, 21, 22]):
            isotimestamp[i-11] = c
        mstampmidnight = sum((c-ord0)*f  for c, f in zip(c1, [10*60*60*1000, 60*60*1000, 10*60*1000, 60*1000, 10*1000, 1000, 0, 100, 10, 1]))
        res = { "isotimestamp":isotimestamp, "mstampmidnight":mstampmidnight }
        res["lat"] = (int(bd[3][:2]) + float(bd[3][2:])/60)*(1 if bd[4] == b'N' else -1)
        res["long"] = (int(bd[5][:3]) + float(bd[5][3:])/60)*(1 if bd[6] == b'E' else -1)
        res["altRef"] = float(bd[7])
        res["navStat"] = bd[8]  # G3=Stand alone 3D
        res["hAcc"], res["vAcc"] = float(bd[9]), float(bd[10])
        res["SOG"], res["COG"], res["vVel"] = float(bd[11]), float(bd[12]), float(bd[13]) # velocities
        res["HDOP"], res["VDOP"], res["TDOP"] = float(bd[15]), float(bd[16]), float(bd[17])
        res["numSvs"] = int(bd[18])
        return res
    return {"cmd":lbd} 
