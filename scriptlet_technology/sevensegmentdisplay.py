import machine, time

sck = machine.Pin(14)
miso = machine.Pin(12)
mosi = machine.Pin(13) 
spi = machine.SPI(sck=sck, miso=miso, mosi=mosi, 
                  baudrate=1000000, polarity=0, phase=0, firstbit=machine.SPI.MSB)
cs = machine.Pin(2, machine.Pin.OUT)  # sets the pin to output
cs.value(1)

def swrite(s):
    cs.value(0)
    time.sleep_ms(5)
    spi.write(s)
    cs.value(1)
    time.sleep_ms(5)
         
swrite(b"\x0C\x00")
swrite(b"\x0F\x00")
swrite(b"\x0B\x07")
swrite(b"\x09\x00")
swrite(b"\x0C\x01")

nums = b"\x7E\x30\x6D\x79\x33\x5B\x5F\x70\x7F\x7B"
alpha = b"\x77\x1F\x0D\x3D\x4F\x47\x7B\x37\x44jk\x0E\x76\x15\x1D\x67\x73\x05\x5B\x0F\x1Cvwx\x3B\x6D"
ledstring = bytearray(50)
ledstringN = 0
ticksms0 = 0
def encodeledstring(s):
    global ledstringN, ticksms0
    ticksms0 = time.ticks_ms()
    ledstringPos = 0
    if type(s) == str:
        s = s.encode()
    ep = 0
    for ledstringN in range(len(ledstring)):
        if ep >= len(s):
            break
        ol = s[ep]
        c = 0x80
        if 48 <= ol <= 57:
            c = nums[ol - 48]
        elif 97 <= ol <= 122:
            c = alpha[ol - 97]
        elif ol == 46: # .
            c = 0x80
        elif ol == 45: # -
            c = 0x01
        elif ol == 95: # _
            c = 0x08
        elif ol == 32: # space
            c = 0x00
        if ep+1 < len(s) and s[ep+1] == 46:
            c += 0x80
            ep += 1
        ledstring[ledstringN] = c
        ep += 1


def writeledstringautoscroll(msstill=1000, mscrollletter=500):
    nscroll = max(0, ledstringN - 8)
    tperiodms = msstill*2 + nscroll*mscrollletter
    tphasems = (time.ticks_ms() - ticksms0) % tperiodms
    if tphasems < msstill:
        ledstringPos = 0
        br = tphasems*8//msstill
    elif tphasems < msstill+nscroll*mscrollletter:
        ledstringPos = min(max(0, ledstringN-8), int((tphasems-msstill)/mscrollletter))
        br = 7
    else:
        ledstringPos = max(0, ledstringN-8)
        br = (tperiodms-tphasems)*8//msstill
    for e in range(8):
        swrite(b"%c%c" % (8-e, ledstring[e+ledstringPos] if e+ledstringPos < ledstringN else 0x00))
    swrite(b"\x0A%c" % min(7, int(br)))  # pulse the brightness

