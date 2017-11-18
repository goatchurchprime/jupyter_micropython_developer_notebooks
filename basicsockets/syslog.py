import os, time, sys

powid = 0   # id of when 
try:
    powid = os.stat("syslog.txt")[6]
except OSError as e:
    pass

slout = open("syslog.txt", "a")
slout.write("\n------\n")

def elog(e):
    st = str(time.time())
    slout.write(st)
    slout.write(" ")
    sys.print_exception(e, slout)
    slout.write("\n")
    slout.flush()
    print("ELOG", [e])

def log(m, m1=""):
    st = str(time.time())
    slout.write(st)
    slout.write(" ")
    slout.write(str(m))
    if m1 != "":
        slout.write(" ")
        slout.write(str(m1))
    slout.write("\n")
    slout.flush()
    print("LOG", st, m, m1)
    
log("ON", powid)   # second parameter should be machine.reset_cause() when it is working
    