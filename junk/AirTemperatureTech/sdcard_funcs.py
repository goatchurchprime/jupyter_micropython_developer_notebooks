import sdcard, os, time
from machine import Pin, SPI

# mosi should be mosi=Pin19 (to match Lora) but won't work as OUTPUT
# https://github.com/micropython/micropython-lib/blob/master/errno/errno.py
# errno=28(no space)
spi = None  
sd = None
sdfile = None

def ConnectSDcardFile():
    global spi, sdfile, sd
    spi = SPI(sck=Pin(5), mosi=Pin(22), miso=Pin(27))  
    
    try:
        sd = sdcard.SDCard(spi, Pin(23))
        os.mount(sd, '/sd')
    except OSError as e:
        return ("SD card", str(e.args[0]))
    
    if not sum((f[0]=="LOG")  for f in os.ilistdir("sd")):
        os.mkdir("sd/LOG")
    fnum = 1+max((int(f[0][:3])  for f in os.ilistdir("sd/LOG")  if f[3]>10), default=0)
    fname = "sd/LOG/{:03d}.TXT".format(fnum)
    print("Opening file", fname)
    sdfile = open(fname, "w")
    sdfile.write("Logfile: {}\n".format(fname))
    sdfile.write("Device number: 3\n")
    sdfile.write("Rt[ms]d\"[isodate]\"e[latdE]n[latdN]f[lngdE]o[lngdN] GPS cooeffs\n") 
    sdfile.write("Qt[ms]u[ms midnight]y[lat600000]x[lng600000]a[alt] GPS\n") 
    sdfile.write("Vt[ms]v[kph100]d[deg100] GPS velocity\n") 
    sdfile.write("Ft[ms]p[milibars] bluefly pressure\n") 
    sdfile.write("Gt[ms]r[rawhumid]a[rawtemp] si7021Humidity meter\n") 
    sdfile.write("Nt[ms]r[rawadc]s[resistance] nickel wire sensor\n") 
    sdfile.write("Zt[ms]xyz[linacc]abc[gravacc]wxyz[quat]s[calibstat] orient\n"); 
    sdfile.write("Yt[ms]s\"calibconsts\" orient calib\n"); 
    sdfile.write("\n")
    sdfile.flush()
    return (["SDfile", fname[:6], fname[6:]])
    
