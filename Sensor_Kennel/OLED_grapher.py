import array

yM = array.array("i", range(128))
yR = array.array("i", range(128))
yMin = 0
yMax = 0
yValFac = 0.01 
yGridLines = int(0.1/yValFac + 0.5) 
yValPrec = 1
yValOffset = 0 
nscrollcount = 0
yValmsstep = 200
yValmsstamp = 0
yLo128, yHi128 = 0, 0 
yTimestmps = array.array("h", range(10))
yTimestmpsstep = const(50)
jGfirst = 127

def scrollinit():
    global jGfirst, nscrollcount
    for i in range(128):
        yR[i] = -1 
    jGfirst = 127
    nscrollcount = 0

def joinscroll(j0, j1, jfirst):
    for j in range(j0, j1):
        yM[j-1] = yM[j] 
        yR[j-1] = yR[j]
        if jfirst == -1 and yR[j-1] != -1:
            jfirst = j-1
    if j1 != 128:
        if yR[j1] == -1:
            yM[j1] = yM[j1+1]
            yR[j1] = yR[j1+1] 
        if yR[j1+1] != -1:
            yA = min(yM[j1]-yR[j1], yM[j1+1]-yR[j1+1])
            yB = max(yM[j1]+yR[j1], yM[j1+1]+yR[j1+1])
            yM[j1-1] = (yA + yB)>>1 
            yR[j1-1] = (yB - yA)>>1 
            if jfirst == -1:
                jfirst = j1-1
    return jfirst 

def addscrollgraph(yval, mstamp):
    global yLo128, yHi128, jGfirst,nscrollcount, yValmsstamp
    
    m = -int(yval/yValFac - yValOffset)
    if m < yLo128 or nscrollcount == 0:  
        yLo128 = m 
    if m > yHi128 or nscrollcount == 0:  
        yHi128 = m 
    if yValmsstamp//yValmsstep == mstamp//yValmsstep:
        return False
    
    jfirst = -1
    if (nscrollcount % 8) == 0:
        jfirst = joinscroll(1, 9, jfirst)
    if (nscrollcount % 4) == 0:
        jfirst = joinscroll(10, 43, jfirst)
    if (nscrollcount % 2) == 0:
        jfirst = joinscroll(44, 83, jfirst)
    jfirst = joinscroll(84, 128, jfirst)
    if jfirst != -1 and jfirst < jGfirst:
        jGfirst = jfirst; 

    nscrollcount += 1

    if (nscrollcount % yTimestmpsstep) == 0 and nscrollcount < 10*yTimestmpsstep:
        yTimestmps[nscrollcount//yTimestmpsstep-1] = jGfirst 

    yM[127] = (yLo128 + yHi128)>>1
    yR[127] = (yHi128 - yLo128)>>1 
    yValmsstamp = mstamp 
    yLo128 = m 
    yHi128 = m 

    return True

def plotscrollgraph(fbuff):
    global yMax, yMin

    # calculate the shift and scaling
    yMid = (yMax + yMin)>>1 
    yShiftCount = 0
    yShifter = (yMax - yMin)>>1 
    while yShifter > 32:
        yShiftCount += 1 
        yShifter >>= 1 

    # draw the graph (while working out the new yRange)
    fbuff.fill(0) 
    x0 = -1
    for i in range(128):
        if yR[i] == -1:
            continue 
        yLo = yM[i]-yR[i]
        yHi = yM[i]+yR[i]
        if x0 == -1 or yLo < yMin:
            yMin = yLo
        if x0 == -1 or yHi > yMax:
            yMax = yHi
        if x0 == -1: 
            x0 = i 
        yB = ((yLo - yMid)>>yShiftCount) + 32 
        yBL = max(1, (yHi - yLo)>>yShiftCount)
        fbuff.vline(i, yB, yBL, 1)

    if yGridLines > 0:
        lyGridLines = yGridLines 
        lyValPrec = max(0, yValPrec)
        while (64<<yShiftCount)/lyGridLines >= 6:
            lyGridLines *= 5 
            if (64<<yShiftCount)/lyGridLines < 6: 
                break 
            lyGridLines *= 2 
            if lyValPrec != 0 and yValOffset == 0: 
                lyValPrec -= 1
                
        k0 = (((-32)<<yShiftCount) + yMid)//lyGridLines 
        k1 = min((((32)<<yShiftCount) + yMid)//lyGridLines, k0+10)
        for k in range(k0 - 2, k1 + 3):
            yG = k*lyGridLines 
            yP = ((yG - yMid)>>yShiftCount) + 32 
            if yP < -8:
                continue 
            if yP > 64:
                break 
            fbuff.hline(x0, yP, 128-x0, 1) 
            gval = (-yG+yValOffset)*yValFac
            charbuf = "{:8g}".format(gval)
            fbuff.text(charbuf, 128-len(charbuf)*8, yP+2, 1)
    
    for i in range(min(9, nscrollcount//yTimestmpsstep)-1, -1, -1):
        fbuff.vline(yTimestmps[i], 61, 3, 1)   # should be INVERSE


def scrollgraphtest(fbuff, oledshow):
    import math, time
    scrollinit()
    for i in range(0, 10000, 10):
        addscrollgraph(math.sin(math.radians(i))*200+i/2, i*10)
        plotscrollgraph(fbuff)
        oledshow()

