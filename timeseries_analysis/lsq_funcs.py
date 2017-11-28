dx0 = const(0); dn = const(1); dSx = const(2); dSx2 = const(3); dSy = const(4); dSy2 = const(5); dSxy = const(6); 

# least squares terse functions (done as a list)
# [x0, n, Sx, Sx2, Sy, Sy2, Sxy]
def setpt0(lq, x, y):
    lq[dx0] = x; lq[dn] = 1
    lq[dSx] = 0; lq[dSx2] = 0 
    lq[dSy] = y; lq[dSy2] = y**2; lq[dSxy] = 0

def addpt(lq, x, y):
    x = x - lq[0]
    lq[dn] += 1
    lq[dSx] += x; lq[dSx2] += x**2; 
    lq[dSy] += y; lq[dSy2] += y**2; lq[dSxy] += x*y

def mergelq(lq, llq):
    dx = llq[dx0] - lq[dx0]
    nl = llq[dn]
    lq[dn] += nl
    lq[dSx] += llq[dSx] + nl*dx
    lq[dSx2] += llq[dSx2] + 2*llq[dSx]*dx + nl*dx**2
    lq[dSy] += llq[dSy]
    lq[dSy2] += llq[dSy2]
    lq[dSxy] += llq[dSxy] + llq[dSy]*dx

def copylq(lq, llq):
    for i in range(7):
        lq[i] = llq[i]
    
def calcrsq(lq, m, c):
    rsq = m**2*lq[dSx2] + lq[dn]*c**2 + lq[dSy2] + 2*m*c*lq[dSx] - 2*m*lq[dSxy] - 2*c*lq[dSy]
    return rsq/lq[dn]

def calcmc(lq):
    m = (lq[dSxy] - lq[dSx]*lq[dSy]/lq[dn])/(lq[dSx2] - lq[dSx]**2/lq[dn])
    c = lq[dSy]/lq[dn] - m*lq[dSx]/lq[dn]
    return m, c

def calcmcL(x0, c0, lqP, lqA):
    cf = (lqA[dSy]*x0**2 + lqP[dSx]*c0*x0 + lqP[dSx2]*c0 - lqP[dSxy]*x0)
    mnum = (lqA[dSx]*cf - lqA[dSxy]*(lqP[dSx2] + lqA[dn]*x0**2))
    cnum = lqA[dSx]*lqA[dSxy]*x0**2 - lqA[dSx2]*cf
    cden = lqA[dSx]**2*x0**2 - lqA[dSx2]*(lqP[dSx2] + lqA[dn]*x0**2)
    return mnum/cden, cnum/cden

