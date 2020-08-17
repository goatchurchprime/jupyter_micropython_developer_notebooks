from parse3ddmp import DMP3d
import os

dump3dexe = '"C:\\Program Files (x86)\\Survex\\dump3d.exe"'
dump3dexe = 'dump3d'
fname = "Ireby/Ireby2/Ireby2.3d"
outputfile = "Ireby/Ireby2/Ireby2.json"

dstream = os.popen("%s -d %s" % (dump3dexe, fname))
lines = dstream.readlines()
dmp3d = DMP3d(lines)

from parse3ddmp import P3
import json

leglines = [line  for line in dmp3d.lines  if line[0] != line[1] and "SURFACE" not in line[4]]
xsects = [xsect  for xsect in dmp3d.xsects  if len(xsect) >= 2]

assert not dmp3d.cs, "We need to convert from absolute coords in this case"

# points as triples
stationpoints = set()
stationpoints.update(line[0]  for line in leglines)
stationpoints.update(line[1]  for line in leglines)
stationpoints = list(stationpoints)
stationpoints.sort(key=lambda X: (X[2], X[0], X[1]))

# centralize the sketch
def rangerat(ps, i, maxfac):
    return (1-maxfac)*min(p[i]  for p in ps) + maxfac*max(p[i]  for p in ps)
svxp0 = P3(rangerat(stationpoints, 0, 0.5), rangerat(stationpoints, 1, 0.5), rangerat(stationpoints, 2, 1.0))

stationpointsdict = dict((p, i)  for i, p in enumerate(stationpoints))
stationpointscoords = sum((tuple(stationpoint - svxp0)  for stationpoint in stationpoints), ())
stationpointsnames = [ dmp3d.nodepmap[stationpoint][0][0]  for stationpoint in stationpoints ]
legsconnections = sum(((stationpointsdict[legline[0]], stationpointsdict[legline[1]])  for legline in leglines), ())
legsconnections = sum(((stationpointsdict[legline[0]], stationpointsdict[legline[1]])  for legline in leglines), ())
legsstyles = [ legline[3]  for legline in leglines ]

xsectgps = [ ]
for xsectseq in xsects:
    xsectpoints = [dmp3d.nmapnodes[xs[0]]  for xs in xsectseq]
    xsectindexes = [ stationpointsdict[xsectpoint]  for xsectpoint in xsectpoints ]
    xsectrightvecs = [ ]
    for i in range(len(xsectpoints)):
        pback = xsectpoints[max(0, i-1)]
        p = xsectpoints[i]
        pfore = xsectpoints[min(len(xsectpoints)-1, i+1)]
        vback = P3.ZNorm(P3(p.x - pback.x, p.y - pback.y, 0.0))
        vfore = P3.ZNorm(P3(pfore.x - p.x, pfore.y - p.y, 0.0))
        xsectplanevec = P3.ZNorm(vback + vfore)
        xsectrightvecs.append(xsectplanevec[1])
        xsectrightvecs.append(-xsectplanevec[0])
    xsectrightvecs
    xsectlruds = sum((xs[1]  for xs in xsectseq), ())
    xsectlruds
    xsectgps.append({ "xsectindexes":xsectindexes, "xsectrightvecs":xsectrightvecs, "xsectlruds":xsectlruds })
xsectgps

jrec = { "stationpointscoords": stationpointscoords,
         "stationpointsnames":  stationpointsnames, 
         "legsconnections":     legsconnections,
         "legsstyles":          legsstyles, 
         "xsectgps":            xsectgps
       }

open(outputfile, "w").write(json.dumps(jrec))
