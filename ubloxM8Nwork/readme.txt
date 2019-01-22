From https://www.unmannedtechshop.co.uk/product/ublox-neo-m8n-gps-with-compass/
we have 
    Red – 5V (regulated down to 3.3)
    Yellow – RX (connects to pixhawk TX)
    Green – TX (connects to pixhawk RX)
    empty
    empty
    Black – Ground
baud 38400 (actuallg 9600 on startup)
    Orange – SCL
    Blue – SDA

Note, we are getting \\$GNGGA instead of \\$GPGGA

Jobs to do:
 * Find the I2C modules if they match compass (just a https://cdn.sparkfun.com/datasheets/Sensors/Magneto/HMC5883L-FDS.pdf
 
 * Find the UBlox config program
     need to run this https://forum.u-blox.com/index.php/12530/does-u-center-support-linux thing.
Do by:
   wine C:/Program\ Files\ \(x86\)/u-blox/u-center_v18.11/u-center

Missing an FTDI USB to Serial converter, so tried using the onboard ESP one: Pull EN low and then plug in RX0=Green, TX0=Yellow; doesn't work from ESP32, but does from ESP8266 to ESP32, but then not directly to the M8N
     
 * Get stream of data going to UDP app and recording
This works with the main_udpstream.py code

 * Start with the docs for the module
