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
GP=GPS, GL=GLONASS, GA=Galileo, GB=Beidou, GN=Unknown
High Precision Mode adds 7 post decimal digits in latlng, 3 in alt


Jobs to do:

 * Find the I2C modules if they match compass (just a https://cdn.sparkfun.com/datasheets/Sensors/Magneto/HMC5883L-FDS.pdf


 * Find the UBlox config program
     need to run this https://forum.u-blox.com/index.php/12530/does-u-center-support-linux thing.
Do by:
   wine C:/Program\ Files\ \(x86\)/u-blox/u-center_v18.11/u-center

Missing an FTDI USB to Serial converter, so tried using the onboard ESP one: Pull EN low and then plug in RX0=Green, TX0=Yellow; doesn't work from ESP32, but does from ESP8266 to ESP32, but then not directly to the M8N


 * Get stream of data going to UDP app and recording
This works with the main_udpstream.py code
(needed to account for 5 decimal places in the minutes field)



 * Start with the docs to configure it.
There's some code here:
    https://github.com/tridge/pyUblox
    There's code in extrepositories/RTKLIB/src/rcv/ublox.c
And a massive datasheet here:
    https://www.u-blox.com/sites/default/files/products/documents/u-blox8-M8_ReceiverDescrProtSpec_%28UBX-13003221%29_Public.pdf



 * The firmware downgrade https://forum.u-blox.com/index.php/1965/firmware-downgrade-m8n
See for full list https://www.u-blox.com/en/product-resources?f%5B0%5D=property_file_product_filter%3A2688

 needs u-center and the /home/julian/.wine/drive_c/Program Files (x86)/u-blox/u-center_v18.11/flash.xml file.  Check instructions.
 

* Get the stream of *pubx commands going to the UDP records

wine C:/Program\ Files\ \(x86\)/u-blox/u-center_v18.11/ubxfwupdate.exe -p /dev/ttyACM1 -b 9600:9600:9600 -F C:/Program\ Files\ \(x86\)/u-blox/u-center_v18.11/flash.xml -s 1 -t 1 -v 1 "Z:/home/julian/executables/ubloxGPSfirmware/UBLOX_M8_201.89cc4f1cd4312a0ac1b56c790f7c1622.bin"

/usr/bin/rtkconv_qt to convert the UBX

/usr/bin/rtkpost_qt 

Or use the files in:
   /home/julian/executables/RTKLIB-qt-Linux-x64/

--------------
Configuration code
--------------
--------------
There's code in extrepositories/RTKLIB/src/rcv/ublox.c
--------------

*          UBX-RXM-RAW  : raw measurement data
*          UBX-RXM-RAWX : multi-gnss measurement data
*          UBX-RXM-SFRB : subframe buffer
*          UBX-RXM-SFRBX: subframe buffer extension
*
*          UBX-TRK-MEAS and UBX-TRK-SFRBX are based on NEO-M8N (F/W 2.01).
*          UBX-TRK-D5 is based on NEO-7N (F/W 1.00). They are not formally
*          documented and not supported by u-blox.
*          Users can use these messages by their own risk.

#define ID_NAVSOL   0x0106      /* ubx message id: nav solution info */
#define ID_NAVTIME  0x0120      /* ubx message id: nav time gps */
#define ID_RXMRAW   0x0210      /* ubx message id: raw measurement data */
#define ID_RXMSFRB  0x0211      /* ubx message id: subframe buffer */
#define ID_RXMSFRBX 0x0213      /* ubx message id: raw subframe data */
#define ID_RXMRAWX  0x0215      /* ubx message id: multi-gnss raw meas data */
#define ID_TRKD5    0x030A      /* ubx message id: trace mesurement data */

Undocumented but necessary
#define ID_TRKMEAS  0x0310      /* ubx message id: trace mesurement data */
#define ID_TRKSFRBX 0x030F      /* ubx message id: trace subframe buffer */

--------------------------
        case ID_RXMRAW  : return decode_rxmraw  (raw);
        case ID_RXMRAWX : return decode_rxmrawx (raw);
        case ID_RXMSFRB : return decode_rxmsfrb (raw);
        case ID_RXMSFRBX: return decode_rxmsfrbx(raw);
        case ID_NAVSOL  : return decode_navsol  (raw);
        case ID_NAVTIME : return decode_navtime (raw);
        case ID_TRKMEAS : return decode_trkmeas (raw);
        case ID_TRKD5   : return decode_trkd5   (raw);
        case ID_TRKSFRBX: return decode_trksfrbx(raw);



Generates UBlox binary message
extern int gen_ubx(const char *msg, unsigned char *buff)

Called from
extern void strsendcmd(stream_t *str, const char *cmd)
  when a message begins with UBX


#define UBXSYNC1    0xB5        /* ubx message sync code 1 */
#define UBXSYNC2    0x62        /* ubx message sync code 2 */
#define UBXCFG      0x06        /* ubx message cfg-??? */

GNSS=0x3E  prm=    {FU1,FU1,FU1,FU1,FU1,FU1,FU1,FU1,FU4},    /* GNSS */
MSG=0x01   prm=    {FU1,FU1,FU1,FU1,FU1,FU1,FU1,FU1},        /* MSG */
RATE=0x08  prm=    {FU2,FU2,FU2},                            /* RATE */

#define FU1         1           /* ubx message field types */
#define FU2         2
#define FU4         3

static void setU1(unsigned char *p, unsigned char  u) {*p=u;}
static void setU2(unsigned char *p, unsigned short u) {memcpy(p,&u,2);}
static void setU4(unsigned char *p, unsigned int   u) {memcpy(p,&u,4);}

case FU1 : setU1(q,j<narg?(unsigned char )atoi(args[j]):0); q+=1; break;
case FU2 : setU2(q,j<narg?(unsigned short)atoi(args[j]):0); q+=2; break;
case FU4 : setU4(q,j<narg?(unsigned int  )atoi(args[j]):0); q+=4; break;

setU2(buff+4,(unsigned short)(n-8));
setcs(buff,n);

Commands in the config file is:
!UBX CFG-GNSS 0 32 32 1 6 16 16 0 0
!UBX CFG-GNSS 0 32 32 1 3 16 16 0 1
!UBX CFG-MSG 2 21 0 0 0 1 0 0
!UBX CFG-MSG 2 19 0 0 0 1 0 0
!UBX CFG-RATE 200 1 1
!UBX CFG-GNSS msgVer=0 numTrkChHw=32 numTrkChUse32 numConfigBlocks=1 
    gnssId=6(GLONASS) resTrkCh=16 maxTrkCh=16 reserved1=0 flags=0 (4bytes, second byte)
Then gnssId=3(BeiDou)

!UBX CFG-MSG msgClass=2 msgId=21 rateport0=0 rateport1=0 rateport2=0 
    rateport3=1 rateport4=0 rateport5=0
Then msgId=19

!UBX CFG-RATE measRate=200 navRate=1 timeRef=1=GPS time


----------------------
----------------------
Lots is working, byt the 0x0215 command is failing (limited only to the high precision ones)
Try to rerun this one to get data into a file that RTKLIB can load!

https://github.com/PaulZC/NEO-M8T_GNSS_FeatherWing/blob/a40a0504815cf2055cf6d297de27dd14ec3316c4/Python/NEO-M8T_GNSS_RAWX_Logger.py
----------------------
# We have spooled the code out into test.bin, and now to run:
wine C:\\rtklib5\\rtkconv.exe
downloaded from: http://rtkexplorer.com/downloads/rtklib-code/
as described at: https://github.com/PaulZC/NEO-M8T_GNSS_FeatherWing/blob/master/POST_PROCESS.md





