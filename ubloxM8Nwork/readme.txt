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


--------------
Configuration code
--------------
--------------
There's code in extrepositories/RTKLIB/src/rcv/ublox.c
--------------

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


--------------
--------------
ublox_capture.py
--------------
dev = ublox.UBlox(opts.port, baudrate=opts.baudrate, timeout=2)

dev.set_logfile(opts.log, append=opts.append)
dev.set_binary()
    def set_binary(self):
	'''put a UBlox into binary mode using a NMEA string'''
        if not self.read_only:
            print("try set binary at %u" % self.baudrate)
            self.send_nmea("$PUBX,41,0,0007,0001,%u,0" % self.baudrate)
            self.send_nmea("$PUBX,41,1,0007,0001,%u,0" % self.baudrate)
            self.send_nmea("$PUBX,41,2,0007,0001,%u,0" % self.baudrate)
            self.send_nmea("$PUBX,41,3,0007,0001,%u,0" % self.baudrate)
            self.send_nmea("$PUBX,41,4,0007,0001,%u,0" % self.baudrate)
            self.send_nmea("$PUBX,41,5,0007,0001,%u,0" % self.baudrate)


dev.configure_poll_port()
        self.send_message(msg_class, msg_id, payload)
        self.configure_poll(CLASS_CFG, MSG_CFG_PRT)
CLASS_CFG = 0x06
MSG_CFG_PRT = 0x00
    (CLASS_CFG, MSG_CFG_USB)    : UBloxDescriptor('CFG_USB',
                                                  '<HHHHHH32s32s32s',
                                                  ['vendorID', 'productID', 'reserved1', 'reserved2', 'powerConsumption',
                                                   'flags', 'vendorString', 'productString', 'serialNumber']),


dev.configure_poll(ublox.CLASS_CFG, ublox.MSG_CFG_USB)

#dev.configure_poll(ublox.CLASS_MON, ublox.MSG_MON_HW)

dev.configure_port(port=ublox.PORT_SERIAL1, inMask=1, outMask=0)
dev.configure_port(port=ublox.PORT_USB, inMask=1, outMask=1)
dev.configure_port(port=ublox.PORT_SERIAL2, inMask=1, outMask=0)
dev.configure_poll_port()
dev.configure_poll_port(ublox.PORT_SERIAL1)
dev.configure_poll_port(ublox.PORT_SERIAL2)
dev.configure_poll_port(ublox.PORT_USB)

dev.configure_solution_rate(rate_ms=1000)
       payload = struct.pack('<HHH', rate_ms, nav_rate=1, timeref=0)
       self.send_message(CLASS_CFG, MSG_CFG_RATE, payload)
MSG_CFG_RATE = 0x08

dev.set_preferred_dynamic_model(opts.dynModel)
    set_preferred_dynamic_model
    self.configure_poll(CLASS_CFG, MSG_CFG_NAV5)
        self.configure_poll(CLASS_CFG, MSG_CFG_PRT)

dev.set_preferred_usePPP(opts.usePPP)
        self.preferred_usePPP = int(usePPP)
        self.configure_poll(CLASS_CFG, MSG_CFG_NAVX5)

CLASS_NAV = 0x01
CLASS_RXM = 0x02
MSG_RXM_RAW    = 0x10


dev.configure_message_rate(ublox.CLASS_NAV, ublox.MSG_NAV_POSLLH, 1)
dev.configure_message_rate(ublox.CLASS_NAV, ublox.MSG_NAV_STATUS, 1)
dev.configure_message_rate(ublox.CLASS_NAV, ublox.MSG_NAV_SOL, 1)
dev.configure_message_rate(ublox.CLASS_NAV, ublox.MSG_NAV_VELNED, 1)
dev.configure_message_rate(ublox.CLASS_NAV, ublox.MSG_NAV_SVINFO, 1)
dev.configure_message_rate(ublox.CLASS_NAV, ublox.MSG_NAV_VELECEF, 1)
dev.configure_message_rate(ublox.CLASS_NAV, ublox.MSG_NAV_POSECEF, 1)
dev.configure_message_rate(ublox.CLASS_RXM, ublox.MSG_RXM_RAW, 1)
dev.configure_message_rate(ublox.CLASS_RXM, ublox.MSG_RXM_SFRB, 1)
dev.configure_message_rate(ublox.CLASS_RXM, ublox.MSG_RXM_SVSI, 1)
dev.configure_message_rate(ublox.CLASS_RXM, ublox.MSG_RXM_ALM, 1)
dev.configure_message_rate(ublox.CLASS_RXM, ublox.MSG_RXM_EPH, 1)
dev.configure_message_rate(ublox.CLASS_NAV, ublox.MSG_NAV_TIMEGPS, 5)
dev.configure_message_rate(ublox.CLASS_NAV, ublox.MSG_NAV_CLOCK, 5)
#dev.configure_message_rate(ublox.CLASS_NAV, ublox.MSG_NAV_DGPS, 5)

--------------msgId=41, portID=1=UART, inProto=0007=inRTCM(4)+inNMEA(2)+inUbx(1), outProto=0001=outNMEA(2)+outUbx(1), baudrate=115200,autobauding=0
            self.send_nmea("$PUBX,41,1,0007,0001,%u,0" % self.baudrate)
