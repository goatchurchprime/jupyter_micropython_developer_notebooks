import time

epoch1970 = const(946684800000)   # micropython uses a yr 2000 epoch

def rhex(h):  
    return (h>>4)*10 + (h&0x0f)
def dhex(v):  
    return chr(((v//10)<<4) + (v%10))

def rtctojsepoch(i2c, busywaitsec=False):
    r = i2c.readfrom_mem(0x68, 0x00, 7)
    year, month, day = rhex(r[6])+2000, rhex(r[5]), rhex(r[4])
    hour, minute, second = rhex(r[2]), rhex(r[1]), rhex(r[0])
    micropythonepoch = time.mktime((year, month, day, hour, minute, second, -1, -1))
    if busywaitsec:   # this is to get the exact transition to next second tick (for calibration timings)
        micropythonepoch += 1000
        while (r[0] == i2c.readfrom_mem(0x68, 0x00, 1)[0]):
            pass
    return micropythonepoch*1000 + epoch1970

def jsepochtortc(jsepoch, i2c):
    micropythonepoch = (jsepoch - epoch1970)//1000
    microsecond = jsepoch % 1000
    year, month, day, hour, minute, second, d1, d2 = time.localtime(micropythonepoch)
    i2c.writeto(0x68, chr(0) + dhex(second) + dhex(minute) + dhex(hour))
    i2c.writeto(0x68, chr(4) + dhex(day) + dhex(month) + dhex(year-2000))
    
def isodatetojsepoch(isodate):  # 2017-11-19T16:05:45.413Z
    #mtime = ure.match("(\d\d\d\d)-(\d\d)-(\d\d)[T ](\d\d)[:c](\d\d)[:c](\d\d)[\.d](\d\d\d)", isodate)
    #year, month, day, hour, minute, second, microsecond = int(mtime.group(1)), int(mtime.group(2)), int(mtime.group(3)), int(mtime.group(4)), int(mtime.group(5)), int(mtime.group(6)), int(mtime.group(7)) 
    year, month, day = int(isodate[:4]), int(isodate[5:7]), int(isodate[8:10])
    hour, minute, second, microsecond = int(isodate[11:13]), int(isodate[14:16]), int(isodate[17:19]), int(isodate[20:23])
    micropythonepoch = time.mktime((year, month, day, hour, minute, second, -1, -1))
    return micropythonepoch*1000 + microsecond + epoch1970

def jsepochtoisodate(jsepoch):
    micropythonepoch = (jsepoch - epoch1970)//1000
    microsecond = jsepoch % 1000
    year, month, day, hour, minute, second, d1, d2 = time.localtime(micropythonepoch)
    return "{0:04d}-{1:02d}-{2:02d}T{3:02d}:{4:02d}:{5:02d}.{6:03d}".format(year, month, day, hour, minute, second, microsecond)
    
