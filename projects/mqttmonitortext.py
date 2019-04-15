import curses, time, re
import paho.mqtt.client as mqtt

# See https://docs.python.org/3/howto/curses.html

msgdict = { }
topiclinedict = { }
topictimedict = { }
height, width = 0, 0

def writething(topic):
    colnums = int(width/50+1)
    colwidth = width//colnums
    scolwidtht = colwidth//2
    scolwidthm = colwidth - scolwidtht - 2
    
    payload = msgdict[topic]
    ffy = topiclinedict[topic]
    
    ftxt = "%%-%ds:%%0%ds" % (scolwidtht, scolwidthm)
    txt = ftxt % (topic[:scolwidtht], payload[:scolwidthm])
    fy = ffy % (height*colnums)
    ix = fy//height
    y, x = fy - ix*height, ix*colwidth
    
    client.stdscr.addstr(y, x, ("%%%ds " % scolwidtht) % payload[:scolwidtht], curses.A_BOLD)
    client.stdscr.addstr(y, x+scolwidtht+1, ("%%-%ds" % scolwidthm) % topic[:scolwidthm])
    
def sortwritethings(stdscr):
    for i, (topic, t) in enumerate(sorted(list(topictimedict.items()), key=lambda X:X[1], reverse=True)):
        topiclinedict[topic] = i
    stdscr.clear()
    for topic in msgdict:
        writething(topic)
        #break
    stdscr.refresh()

reignoredtopics = re.compile("ESPURNA......./(?:factor|energy|voltage|apparent|vcc|freeheap|current|reactive|version|host|loadavg|mac)")

def on_message(client, userdata, message):
    if height == 0:
        return
    
    #print("message ", message.topic, str(message.payload.decode("utf-8")))
    topic, payload = str(message.topic), str(message.payload.decode("utf-8"))
    if reignoredtopics.match(topic):
        return
    
    msgdict[topic] = payload
    topictimedict[topic] = time.time()
    
    if topic not in topiclinedict:
        topiclinedict[topic] = len(topiclinedict)
    
    writething(topic)
    client.stdscr.refresh()
    
broker_address="mqtt.local"
print("creating new instance")
client = mqtt.Client("P1") 
client.on_message = on_message 
client.stdscr = None
client.connect("mqtt.local")

def main(stdscr):
    global height, width
    stdscr.clear()
    client.stdscr = stdscr
    height, width = stdscr.getmaxyx()

    stdscr.addstr(13, 0, str(stdscr.getmaxyx()))
    stdscr.refresh()
    while True:
        k = stdscr.getkey()
        if k == "q":
            break
        if k == "s":
            sortwritethings(client.stdscr)

    
client.loop_start() 
client.subscribe("#")
curses.wrapper(main)
client.loop_stop()
