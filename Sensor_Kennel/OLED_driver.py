from machine import I2C, Pin
import framebuf

i2c = I2C(scl=Pin(15, Pin.OUT, Pin.PULL_UP), sda=Pin(4, Pin.OUT, Pin.PULL_UP), freq=450000)
buffer = None

cmdforshow = bytes((0x80, 0x21, # SET_COL_ADDR
                    0x80, 0,    # 0
                    0x80, 127,  # width-1
                    0x80, 0x22, # SET_PAGE_ADDR
                    0x80, 0,    # 0
                    0x80, 7     # height//8 - 1
                  ))   

def oledshow():
    if buffer is not None:
        try:
            i2c.writeto(0x3c, cmdforshow)
            i2c.writeto(0x3c, buffer)
        except OSError as e:
            print(e)
        
def oledcontrast(contrast):
    if buffer is not None:
        try:
            i2c.writeto(0x3c, bytes((0x80, 0x81, 0x80, contrast)))
        except OSError as e:
            print(e)

def oledinvert(invert=True):
    if buffer is not None:
        try:
            i2c.writeto(0x3c, bytes((0x80, 0xa6 | (invert & 1))))
        except OSError as e:
            print(e)

# Initialize OLED screen if it is there
rst = Pin(16, Pin.OUT)
rst.value(1)
if 0x3c in i2c.scan():
    
    # There is an extra byte to the data buffer to hold an I2C data/command byte
    # to use hardware-compatible I2C transactions.
    buffer = bytearray(((64 // 8) * 128) + 1)
    buffer[0] = 0x40  # Set first byte of data buffer to Co=0, D/C=1
    fbuff = framebuf.FrameBuffer1(memoryview(buffer)[1:], 128, 64)

    cmdforinit = bytes((0xae,        # CMD_DISP=off
                        0x20, 0x00,  # SET_MEM_ADDR  horizontal
                        0x40,        # SET_DISP_START_LINE
                        0xa0 | 0x01, # column addr 127 mapped to SEG0
                        0xa8, 63,    # SET_MUX_RATIO, height-1
                        0xc0 | 0x08, # SET_COM_OUT_DIR scan from COM[N] to COM0
                        0xd3, 0x00,  # SET_DISP_OFFSET
                        0xda, 0x12,  # SET_COM_PIN_CFG
                        0xd5, 0x80,  # SET_DISP_CLK_DIV
                        0xd9, 0xf1,  # SET_PRECHARGE
                        0xdb, 0x30,  # SET_VCOM_DESEL 0.83*Vcc
                        0x81, 0xff,  # SET_CONTRAST maximum
                        0xa4,        # SET_ENTIRE_ON output follows RAM contents
                        0xa6,        # SET_NORM_INV not inverted
                        0x8d, 0x14,  # SET_CHARGE_PUMP
                        0xae | 0x01  # SET_DISP on
                       ))
    for c in cmdforinit:
        i2c.writeto(0x3c, bytes((0x80, c)))
        
        
    # checkerboard starting page
    for i in range(0, 128, 8):
        for j in range(0, 64, 8):
            fbuff.fill_rect(i, j, 8, 8, (i//8 + j//8)%2)
    oledshow()
    
else:
    print("OLED i2c not found")
    fbuff = framebuf.FrameBuffer1(bytearray(0), 0, 0)


# quick function for printing numbers double-size so we can see them
# chr45=- . / 0 1 2 3 4 5 6 7 8 9
num8x8 = b'\x00\x08\x08\x08\x08\x08\x08\x00\x00\x00\x00``\x00\x00\x00\x00@`0\x18\x0c\x06\x02\x00>\x7fIE\x7f>\x00\x00@D\x7f\x7f@@\x00\x00bsQIOF\x00\x00"cII\x7f6\x00\x00\x18\x18\x14\x16\x7f\x7f\x10\x00\'gEE}9\x00\x00>\x7fII{2\x00\x00\x03\x03y}\x07\x03\x00\x006\x7fII\x7f6\x00\x00&oII\x7f>\x00'
def fatntext(t, x, y):  # numbers only
    for s in t:
        k = max(0, min(12, ord(s) - 45))
        if k == 1:  x -= 4   # squeeze in the decimal point
        for c in num8x8[k*8:k*8+8]:
            for j in range(8):
                if (c & (1<<j)):
                    fbuff.fill_rect(x,y+j*2,2,2,1)
            x += 2
        if k == 1:  x -= 4

# copy image in corner to double size, for announcements
def doublepixels():
    if buffer is not None:
        for x in range(63, -1, -1):
            for y in range(31, -1, -1):
                fbuff.fill_rect(x*2,y*2,2,2,fbuff.pixel(x,y))

def oledshowfattext(ltxt):
    if buffer is not None:
        if type(ltxt) == str:
            ltxt = [ltxt]
        fbuff.fill(0)
        for i, s in enumerate(ltxt):
            fbuff.text(s, 0, i*8, 1)
        doublepixels()
        oledshow()
    