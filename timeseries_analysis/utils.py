import pandas, numpy

# this turns out to be the Savitzky-Golay filter
sec1 = pandas.Timedelta(seconds=1)
def intercurvefitdifferentiate(seriestimeindex, rx, ws, deg=3):
    rx0 = pandas.Series(0, seriestimeindex)
    rx1 = pandas.Series(0, seriestimeindex)
    rx2 = pandas.Series(0, seriestimeindex)
    wt = ws*sec1
    wt2 = ws*2*sec1
    wt4 = ws*4*sec1
    for n in range(len(seriestimeindex)):
        t = seriestimeindex[n]
        lx = rx[t-wt:t+wt]
        if len(lx) <= 3:
            lx = rx[t-wt2:t+wt2]
            if len(lx) <= 3:
                lx = rx[t-wt4:t+wt4]
                if len(lx) <= 3:
                    #print(t)
                    continue
        ts = (lx.index - t)/sec1
        weights = 1/((abs(ts)/ws)**2+1)
        pm = numpy.polyfit(ts, lx, deg=deg, w=weights)
        rx0.iloc[n] = numpy.polyval(pm, 0)
        pm1 = numpy.polyder(pm)
        rx1.iloc[n] = numpy.polyval(pm1, 0)
        pm2 = numpy.polyder(pm, 2)
        rx2.iloc[n] = numpy.polyval(pm2, 0)
    return rx0, rx1, rx2

