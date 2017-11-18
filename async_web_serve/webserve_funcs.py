import time, os
from syslog import log, elog, powid

# from webserve_static
import time
contenttypes = { "js":  "application/javascript; charset=utf-8", 
                 "css": "text/css; charset=utf-8", 
                 "jpg": "image/jpeg", 
                 "png": "image/png",
                 "bin": "application/octet-stream",
                 "html":"text/html; charset=utf-8" }

async def servestaticfile(w, lpath, fsize=0):
    try:
        if fsize == 0:
            try:
                fsize = os.stat(lpath)[6]
            except OSError:
                pass
        if fsize == 0:
            log("File '%s' not found"%(lpath))
            await w.awrite(b"HTTP/1.0 404 Not found\r\n\r\n")
            await w.awrite(b"File '%s' not found" % lpath.encode())
            return
        
        await w.awrite(b"HTTP/1.0 200 OK\r\n")
        lfext = lpath[lpath.rfind(".")+1:]
        await w.awrite(b"Content-Type: %s\r\n" % contenttypes.get(lfext, "text/plain; charset=utf-8"))
        if lfext == "js" and fsize > 20000:
            await w.awrite(b"Cache-Control: max-age=31536000\r\n")
        await w.awrite(b"Content-Length: %d\r\n" % fsize)
        await w.awrite(b"\r\n")

        #fsize = os.stat(lpath)[6]
        fin = open(lpath, "rb")
        
        t0 = time.ticks_ms()
        bs = bytearray(60)
        Dn = 0
        for i in range(int((fsize-1)/len(bs))):
            fin.readinto(bs)
            await w.awrite(bs)
            Dn += len(bs)
        nbs = fin.readinto(bs)
        Dn += nbs
        await w.awrite(bs, sz=nbs)
        td = time.ticks_ms() - t0
        log("File '%s' (%d bytes) served in %dms"%(lpath, fsize, td))
    except OSError as e:
        elog(e)
    
    
async def servefilelist(w, d=""):
    if not d:
        await w.awrite(b"HTTP/1.0 200 OK\r\n")
        await w.awrite(b"Content-Type: text/html\r\n\r\n")
        await w.awrite(b"<html><body>\n")
        await w.awrite(b"<table>\n")
        await w.awrite(b"<tr><th>Name</th><th>Size</th></tr>\n")
    for fname in os.listdir(d):
        if d:
            fname = "{}/{}".format(d, fname)
        st = os.stat(fname)
        if st[0] == 0x4000:
            await servefilelist(w, fname)
        else:
            fname = fname.encode()
            await w.awrite(b'<tr><td><a href="/')
            await w.awrite(fname)
            await w.awrite(b'">')
            await w.awrite(fname)
            await w.awrite(b'</a></td><td>%d</td></tr>\n' % st[6])
    if not d:
        await w.awrite(b"</table>\n")
        await w.awrite(b"</body></html>\n")
    else:
        pass  # return from recursion

async def servemessage(w, m):
    await w.awrite(b"HTTP/1.0 200 OK\r\n")
    await w.awrite(b"Content-Type: text/html\r\n\r\n")
    await w.awrite(b"<html><body>\n")
    await w.awrite(b'<div style="font-size:200%">\n')
    await w.awrite(m.encode())
    await w.awrite(b"</div>\n")
    await w.awrite(b"</body></html>\n")

    
async def readhttpheaders(r):
    h = await r.readline()
    h = h.decode().split()
    if len(h) != 3:
        return {}
    res = { h[0]:h[1][1:] }  # { "GET":path }
    
    # could skip large but non interesting headers
    headers = { }
    while True:
        h = await r.readline()
        if h == b"\r\n":
            break
        k, v = h.split(b":", 1)
        if k.find(b"Connection") != -1 or k.find(b"Upgrade") != -1 or k.find(b"WebSocket") != -1:
            headers[k.strip()] = v.strip()
        if k.find(b"Content-Length") != -1:
            res[k.strip().decode()] = int(v.strip())
        
    # check is websocket
    if b"Upgrade" in headers.get(b"Connection", b"") and headers.get(b"Upgrade").lower() == b"websocket":
        protocol = headers.get(b"WebSocket-Protocol") or headers.get(b"Sec-WebSocket-Protocol")
        assert protocol is None or protocol == b"base64", headers
        assert headers[b"Sec-WebSocket-Version"] == b"13", headers
        res["WebSocketKey"] = headers[b"Sec-WebSocket-Key"]
        
    return res

            
async def recpostsave(receivedrequest, reader, fname):
    rpath = receivedrequest["POST"]
    fsize = int(receivedrequest["Content-Length"])
    log("recpostsave", str(fsize))
    fout = open(fname, "wb")
    while fsize > 0:
        fb = await reader.read(min(fsize, 20))
        fout.write(fb)
        fsize -= len(fb)
    fout.close()


    
# extended code for handling post to files
# (doesn't work for binary files yet)
import uhashlib

def flinesplitgen(fname, n):
    fin = open(fname, "rb")
    rline = bytearray(n)
    mline = memoryview(rline)
    while True:
        i = 0
        while i < n:
            c = fin.read(1)
            if c == b'':
                break
            rline[i] = c[0]
            i += 1
            if c == b'\n':
                break
        yield mline[:i]    
        if c == b'':
            break

def convertsavepostfile(pname):
    lgen = flinesplitgen(pname, 80)
    linebreakhash = uhashlib.sha1(next(lgen)).digest()

    # get the headers
    for l in lgen:
        if l == b'\r\n':
            break
        k, v = bytes(l).split(b":")
        if k == b'Content-Disposition':
            for s in v.split(b";"):
                se = s.strip().split(b"=", 1)
                if len(se) == 2:
                    if se[0] == b"filename":
                        filename = se[1].strip(b'"').decode()

    log("convpostfile", filename)
    fout = open(filename, "wb")
    prelinebreak = b""  # used to handle the linebreak before the breakline
    for l in lgen:
        linehash = uhashlib.sha1(l).digest()
        if linehash == linebreakhash:
            if not prelinebreak:
                print("where the prelinebreak?")
            break
        if prelinebreak:
            fout.write(prelinebreak)
            prelinebreak = b""
        if len(l) == 2:
            prelinebreak = bytes(l)
            if prelinebreak != b"\r\n":
                prelinebreak = b""
        if not prelinebreak:
            fout.write(l)
            
    fout.close()
    os.remove(pname)
    