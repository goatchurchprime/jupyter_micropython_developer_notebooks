import curses, time, re
import paho.mqtt.client as mqtt

# This is a special lightweight text display that can sit on the MQTT-broker to show its 
# activity and help with debugging the system.  (A bit of a waste of a touchscreen, but we could replace it.)
# You can run it on on any command line screen and it should resize
# Inspired by https://github.com/jusplainmike/mqttmon but rewritten from scratch using https://docs.python.org/3/howto/curses.html

# Recommends to use curses.wrapper() to avoid leaving your text terminal in an unusable state.  (This isn't working now!)

# To do:
#
#  If this gets overloaded with too many messages then will need to throttle this down by preventing calls to 
#  writething() more frequently than every half second and recording a set() of topics which are to change
#
#  We might needs some special full-width lines that show the current status of each ESPURNA so they don't 
#  take up all the space for the more interesting MQTT signals 
# 
#  Hit 'q' to quit and 's' to sort by most recent message.


broker_address="mqtt.local"
reignoredtopics = re.compile("ESPURNA......./(?:factor|energy|voltage|apparent|vcc|freeheap|current|reactive|version|host|loadavg|mac)")

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
    stdscr.refresh()


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
curses.endwin()
client.loop_stop()
