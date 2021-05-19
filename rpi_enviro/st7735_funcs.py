from machine import Pin, SPI
import framebuf, time

width, height = 80, 160

fdata = bytearray(width*height*2)
fbuf = framebuf.FrameBuffer(fdata, width, height, framebuf.RGB565)

spi = SPI(1, baudrate=10000000, polarity=0, phase=0, sck=Pin(14), mosi=Pin(13), miso=Pin(12))
cs = Pin(18, Pin.OUT)
dc = Pin(16, Pin.OUT)
backlight = Pin(17, Pin.OUT)

def color565(r, g, b):
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)

backlight.value(0)
time.sleep(0.1)
backlight.value(1)

def cmddata(cmd, data=None):
    cs.value(0)
    dc.value(0)
    spi.write(bytearray([cmd]))
    if data:
        dc.value(1)
        spi.write(data)
    cs.value(1)


# Initialize the display.
cmddata(0x01);  time.sleep_ms(120)     # Software reset
cmddata(0x11);  time.sleep_ms(120)     # Out of sleep mode
cmddata(0x13);  time.sleep_ms(120)     # Normal display mode
cmddata(0x29);  time.sleep_ms(120)     # Display on

#cmddata(0xB1, bytearray([0x02, 0x2C, 0x2D]))  # Frame rt 60Hz 333000/((1+20)*(160+0x2C+0x2D))
cmddata(0xC0, bytearray([0x02, 0x70]))     # 4.7V 1.0uA
#cmddata(0xC1, bytearray([0x05]))     # VGH 6X 14.7  VGL -3X -7.35
cmddata(0xC2, bytearray([0x01, 0x02]))     # Opamp current small, Boost frequency
cmddata(0xC3, bytearray([0x8A, 0x2A]))     # Power control
cmddata(0xC5, bytearray([0x3C, 0x38]))     # VCOMH 4.0, VCOML -1.050
cmddata(0x21)  # Don't invert display
cmddata(0x3A, bytearray([0x05]))     # 16-bit color
cmddata(0x36, bytearray([0x00]))     # Row order (0xC0 for reverse) + RGB

# gamma setting
cmddata(0xE0, bytearray([0x02, 0x1c, 0x07, 0x12, 0x37, 0x32, 0x29, 0x2d, 0x29, 0x25, 0x2B, 0x39, 0x00, 0x01, 0x03, 0x10]))    # Set Gamma
cmddata(0xE1, bytearray([0x03, 0x1d, 0x07, 0x06, 0x2E, 0x2C, 0x29, 0x2D, 0x2E, 0x2E, 0x37, 0x3F, 0x00, 0x00, 0x02, 0x10]))    # Set Gamma

# Columns and rows embedding of 80x160 into 132x162
cmddata(0x2A, bytearray([0x00, 0x1A, 0x00, 0x69]))   # Column address 
cmddata(0x2B, bytearray([0x00, 0x01, 0x00, 0xA0]))   # Row address set

def display():
    cmddata(0x2C, fdata)       # write to RAM

# checkerboard startup
fbuf.fill(0x0000)
for x in range(0, width, 8):
    for y in range(0, height, 8):
        fbuf.fill_rect(x, y, 8, 8, 0xFFFF if ((((x+y)//8)%2) == 0) else 0x0000)
display()
