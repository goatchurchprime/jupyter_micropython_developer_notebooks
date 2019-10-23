from machine import I2C, Pin
import uasyncio as asyncio

def MLX90614_task(fqm, boardname, i2c):
    from MLX90614_funcs import mlx90614temps
    from sevensegmentdisplay import encodeledstring # wired to heltecwhite
    i2c.init(scl=Pin(15), sda=Pin(4), freq=100000)  # can't handle higher frequencies
    topic = boardname+"/MLX90614"
    topicambient = topic+"/temp/ambient"
    topicir = topic+"/temp/ir"
    n = 0
    while True:
        tempAmbient, tempIR = mlx90614temps(i2c)
        if tempAmbient is not None:
            encodeledstring("%.2f c"% tempIR)
            if (n % 5) == 0 and tempIR > -10:
                fqm.fput(topicambient, "%.2f"%tempAmbient)
                fqm.fput(topicir, "%.2f"%tempIR)
            n += 1
        if fqm.rqueue:
            topic, msg = fqm.rqueue.popleft()
            encodeledstring(msg)
            await asyncio.sleep_ms(800)
        await asyncio.sleep_ms(200)

        
        
from OLED_driver import i2c, fbuff, oledshow, doublepixels, fatntext
import machine, time, ubinascii
        
async def plotdevices(fqm, boardname, devname):
    topic = boardname+"/"+devname
    if devname == "VL53L0X":
        from VL53L0X_funcs import VL53L0Xinit, VL53L0Xdist
        VL53L0Xinit(i2c)
        while True:
            d = VL53L0Xdist()
            fbuff.fill(0)
            fbuff.text("VL53L0X", 0, 0, 1)
            fbuff.text("dist(mm):", 8, 20, 1)
            fatntext("%d" % d, 40, 36)
            oledshow()
            fqm.fput(topic, "%d"%d)
            await asyncio.sleep_ms(50)
        
    if devname == "VL6180":
        from VL6180_funcs import VL6180init, distmm
        VL6180init(i2c)
        while True:
            d = distmm()
            fbuff.fill(0)
            fbuff.text("VL6180", 0, 0, 1)
            fbuff.text("dist(mm):", 8, 20, 1)
            fatntext("%d" % d, 40, 36)
            oledshow()
            fqm.fput(topic, "%d" % d)
            await asyncio.sleep_ms(50)

    if devname == "BME280" or devname == "BME180":
        from BME280_funcs import bme280init, readBME280
        bme280init(i2c)
        topictemp = topic+"/temp"
        topichumid = topic+"/humid"
        topicpressure = topic+"/pressure"
        n = 0
        while True:
            temp, pressure, humid = readBME280()
            fbuff.fill(0)
            fbuff.text("BME280", 0, 0, 1)
            fbuff.text("tmp:", 0, 16, 1)
            fatntext("%.2f"%(temp), 32, 10)
            fbuff.text("prs:", 0, 36, 1)
            fatntext("%.2f"%(pressure), 32, 30)
            fbuff.text("hum:", 0, 54, 1)
            fatntext("%.2f"%(humid), 32, 50)
            oledshow()
            if (n % 5) == 0:
                fqm.fput(topichumid, "%.2f"%humid)
                fqm.fput(topictemp, "%.2f"%temp)
                fqm.fput(topicpressure, "%.2f"%pressure)
            n += 1
            await asyncio.sleep_ms(110)

    if devname == "SDOF":
        from SDOF_funcs import SetupAccGyrMag, readvectorsensor
        SetupAccGyrMag(i2c)
        topicaccx = topic+"/acc/x"
        topicaccy = topic+"/acc/y"
        topicaccz = topic+"/acc/z"
        n = 0
        while True:
            fbuff.fill(0)
            ax, ay, az = readvectorsensor("a")
            fbuff.text("Acc:", 0, 0, 1)
            fbuff.text("%d"%ax, 8, 8, 1)
            fbuff.text("%d"%ay, 8, 16, 1)
            fbuff.text("%d"%az, 8, 24, 1)
            x, y, z = readvectorsensor("g")
            fbuff.text("gyr:", 64, 0, 1)
            fbuff.text("%d"%x, 72, 8, 1)
            fbuff.text("%d"%y, 72, 16, 1)
            fbuff.text("%d"%z, 72, 24, 1)
            x, y, z = readvectorsensor("c")
            fbuff.text("mag:", 40, 32, 1)
            fbuff.text("%d"%x, 48, 40, 1)
            fbuff.text("%d"%y, 48, 48, 1)
            fbuff.text("%d"%z, 48, 56, 1)
            oledshow()
            
            if (n % 5) == 0:
                fqm.fput(topicaccx, "%d"%ax)
                fqm.fput(topicaccy, "%d"%ay)
                fqm.fput(topicaccz, "%d"%az)
            n += 1
            await asyncio.sleep_ms(100)
            

            
    if devname == "LP55231":
        fqm.addsubscription("LP55231/#")
        while True:
            if fqm.rqueue:
                topic, msg = fqm.rqueue.popleft()
                print((topic, msg))
                fbuff.fill(0)
                fbuff.text("LP55231", 0, 0, 1)
                fbuff.text("topic:", 0, 8, 1)
                fbuff.text(topic.decode(), 0, 16, 1)
                fbuff.text("msg:", 0, 53, 1)
                fatntext(msg.decode(), 50, 46)
                oledshow()
                try:
                    pos, col = topic.decode().split("/")[1:]
                    intensity = int(msg)
                    if col == "red":
                        bpos = 0x1C + int(pos)
                    else:
                        bpos = (0x16 if col == "green" else 0x17) + int(pos)*2
                    i2c.writeto(0x32, bytes((bpos, intensity)))
                except ValueError as e:
                    print(e)
            else:
                await asyncio.sleep_ms(5)
