# completely minimal functions to control the lora and the oled
# (no classes, only module variables)

# functions are broken out for easy testing in a notebook cell

import time
from LightLora import spicontrol, sx127x

pkt = { }
def _doReceive(sx12, pay):
    if pay and len(pay) > 4:
        pkt["srcAddress"] = pay[0]
        pkt["dstAddress"] = pay[1]
        pkt["srcLineCount"] = pay[2]
        pkt["payLength"] = pay[3]
        pkt["rssi"] = sx12.packetRssi()
        pkt["snr"] = sx12.packetSnr()
        try:
            pkt["msgTxt"] = pay[4:].decode('utf-8', 'ignore')
        except Exception as ex:
            print("doReceiver error: ")
            print(ex)
    
    
doneTransmit = False
def _doTransmit():
    global doneTransmit
    doneTransmit = True
    lora.receive() # wait for a packet (?)

spic = spicontrol.SpiControl()
spic.initLoraPins()

lora = None
def MakeLora(params):
    global lora
    lora = sx127x.SX127x(spiControl=spic, parameters=params)


linecounter = 0
def sendPacket(dstAddress, localAddress, outGoing):
    global linecounter, doneTransmit
    linecounter = linecounter + 1
    doneTransmit = False
    lora.beginPacket()
    lora.write(bytearray([dstAddress, localAddress, linecounter, len(outGoing)]))
    lora.write(outGoing)
    lora.endPacket()

def waitforsendPacket():
    slt = 0
    while (not doneTransmit) and (slt < 50):
        time.sleep_ms(100)
        slt = slt + 1
    if slt == 50:
        print("Transmit timeout")
