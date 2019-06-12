import socket, select, time, ustruct

def createmdnsrequestpacket(name):
    q = bytearray(b'\x00\x01\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00')
    for x in name.encode().split(b"."):
        q.append(len(x))
        q.extend(x)
    q.extend(b"\x00\x00\x01\x00\x01")
    return q

def extractpackedname(buf, o):
    names = [ ]
    while buf[o] != 0:
        if buf[o] & 0xc0:
            o = ustruct.unpack_from("!H", buf, o)[0] & 0x3FFF
        else:
            names.append(bytes(buf[o+1:o+1+buf[o]]))
            o += 1+buf[o]
    return b".".join(names).decode()

def lenpackedname(buf, o):
    i = 0
    while (buf[o+i] != 0) and ((buf[o+i] & 0xc0) != 0xc0):
        i += 1 + buf[o+i]
    return i + (1 if buf[o+i] == 0 else 2)

def decoderesponsepacket(name, buf):
    hostipnumber = ''
    try:
        pkt_id, flags, qst_count, ans_count = ustruct.unpack_from("!HHHH", buf)
        o = 12
        for i in range(qst_count):
            o += lenpackedname(buf, o) + 4
        for i in range(ans_count):
            l = lenpackedname(buf, o)
            if name == extractpackedname(buf, o):
                hostipnumber = ".".join(map(str, buf[o+l+10:o+l+14]))
            o += 10 + l + ustruct.unpack_from("!H", buf, o+l+8)[0]
    except IndexError:
        print("Index error processing packet; probably malformed data")
    return hostipnumber

def mdnshostnametoipnumber(si, name):
    MDNS_ADDR = '224.0.0.251'
    MDNS_PORT = const(5353)

    ipnumber = si.ifconfig()[0]
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    member_info = bytes(tuple(map(int, MDNS_ADDR.split("."))) + tuple(map(int, ipnumber.split("."))))
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, member_info)
    
    for i in range(9):
        q = createmdnsrequestpacket(name)
        try:
            sock.sendto(q, (MDNS_ADDR, MDNS_PORT))
        except OSError as e:
            print(e)
            time.sleep(1)
        rr = select.select([sock], [], [], 1)[0]
        while rr:
            buf, addr = sock.recvfrom(250)
            if addr[0] != ipnumber:
                hostipnumber = decoderesponsepacket(name, buf)
                if hostipnumber:
                    return hostipnumber
            rr = select.select([sock], [], [], 0)[0]
    return ''


# to use:
# import network, time
# si = network.WLAN(network.STA_IF) # create access-point interface
# si.active(True)         # activate the interface
# si.connect("ssid", "password")
# while not si.isconnected():
#     time.sleep(0.1)
#from minimalmdns import mdnshostnametoipnumber
#hostname = "mqtt.local"
#hostipnumber = mdnshostnametoipnumber(si, hostname)
#print(hostname, hostipnumber)

# example string sent to router:
#  'b\x00\x01\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x04mqtt\x05local\x00\x00\x01\x00\x01'
# example string received from router:
#  b'\x00\x01\x84\x00\x00\x01\x00\x01\x00\x00\x00\x00\x04mqtt\x05local\x00\x00\x01\x00\x01\xc0\x0c\x00\x01\x00\x01\x00\x00\x00\n\x00\x04\n\x00\x1e\xc2'