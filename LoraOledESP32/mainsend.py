import utils, time

params = {  'frequency': 868100000, 
            'tx_power_level': 14, 
            'signal_bandwidth': 125E3, 
            'spreading_factor': 7, 
            'coding_rate': 5, 
            'preamble_length': 8,
            'implicitHeader': False, 
            'sync_word': 0x34,    # from _loraModem
            'enable_CRC': True }
utils.MakeLora(params)

utils.lora.init()

utils.lora.onReceive(utils._doReceive)
utils.lora.onTransmit(utils._doTransmit)
utils.lora.receive()

n = 0
while True:
    n += 1
    txt = "Hello %d there"%n
    utils.writeoled(txt)
    btxt = txt.encode()
    #btxt = b"\x90\x91\x92"
    utils.sendPacket(0xfe, 0x41, btxt) 
    time.sleep(2.5)
               
