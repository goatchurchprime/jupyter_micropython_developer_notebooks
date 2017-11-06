import ustruct, time
from i2cmodule import i2c

i2c = machine.I2C(scl=machine.Pin(5), sda=machine.Pin(4))

def set_reg8(address, value):
    i2c.writeto(0x29, ustruct.pack('>HB', address, value))

def set_reg16(address, value):
    i2c.writeto(0x29, ustruct.pack('>HH', address, value))

def get_reg8(address):
    i2c.writeto(0x29, ustruct.pack('>H', address))
    return i2c.readfrom(0x29, 1)[0]

def get_reg16(address):
    i2c.writeto(0x29, ustruct.pack('>H', address))
    return ustruct.unpack('>B', i2c.readfrom(0x29, 2))[0]
       
def init1():
    time.sleep_ms(50)
    if get_reg8(0x0016) != 1:
        raise RuntimeError("Failure reset")

    # Recommended setup from the datasheet
    set_reg8(0x0207, 0x01)
    set_reg8(0x0208, 0x01)
    set_reg8(0x0096, 0x00)
    set_reg8(0x0097, 0xfd)
    set_reg8(0x00e3, 0x00)
    set_reg8(0x00e4, 0x04)
    set_reg8(0x00e5, 0x02)
    set_reg8(0x00e6, 0x01)
    set_reg8(0x00e7, 0x03)
    set_reg8(0x00f5, 0x02)
    set_reg8(0x00d9, 0x05)
    set_reg8(0x00db, 0xce)
    set_reg8(0x00dc, 0x03)
    set_reg8(0x00dd, 0xf8)
    set_reg8(0x009f, 0x00)
    set_reg8(0x00a3, 0x3c)
    set_reg8(0x00b7, 0x00)
    set_reg8(0x00bb, 0x3c)
    set_reg8(0x00b2, 0x09)
    set_reg8(0x00ca, 0x09)
    set_reg8(0x0198, 0x01)
    set_reg8(0x01b0, 0x17)
    set_reg8(0x01ad, 0x00)
    set_reg8(0x00ff, 0x05)
    set_reg8(0x0100, 0x05)
    set_reg8(0x0199, 0x05)
    set_reg8(0x01a6, 0x1b)
    set_reg8(0x01ac, 0x3e)
    set_reg8(0x01a7, 0x1f)
    set_reg8(0x0030, 0x00)

def init2():
    time.sleep_ms(50)
    set_reg8(0x010A, 0x30) # Set Avg sample period
    set_reg8(0x003f, 0x46) # Set the ALS gain
    set_reg8(0x0031, 0xFF) # Set auto calibration period
                                 # (Max = 255)/(OFF = 0)
    set_reg8(0x0040, 0x63) # Set ALS integration time to 100ms
    set_reg8(0x002E, 0x01) # perform a single temperature calibration

    # Optional settings from datasheet
    set_reg8(0x001B, 0x09) # Set default ranging inter-measurement
                                 # period to 100ms
    set_reg8(0x003E, 0x0A) # Set default ALS inter-measurement
                                 # period to 100ms

    # Additional settings defaults from community
    set_reg8(0x001C, 0x32) # Max convergence time
    set_reg8(0x002D, 0x10 | 0x01) # Range check enables
    set_reg8(0x0022, 0x7B) # Eraly coinvergence estimate
    set_reg8(0x0120, 0x01) # Firmware result scaler

    # Julian settings
    set_reg8(0x001B, 0x00) # Set default ranging inter-measurement
    set_reg8(0x001C, 0x3F) # Max convergence time
    set_reg8(0x002D, 0x00) # Range check enables
    set_reg8(0x0022, 0x7B) # Early coinvergence estimate
    set_reg8(0x0120, 0x01) # Firmware result scaler

def distmm():
    set_reg8(0x0018, 0x01) # Sysrange start
    time.sleep(0.01)
    return get_reg8(0x0062) # Result range value

