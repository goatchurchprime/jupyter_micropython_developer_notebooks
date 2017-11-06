import machine
i2c = machine.I2C(scl=machine.Pin(5), sda=machine.Pin(4))