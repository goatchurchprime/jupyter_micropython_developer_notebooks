import os

def updateconfig(c="config.txt"):
    while True:
        print("\n\n", c, ":\n")
        with open(c) as fin:
            for x in fin:
                print(x.strip())
        y = input("input line> ")
        ys = y.split()
        if not 1 <= len(ys) <= 2:
            return
        cd = "E"+c
        with open(cd, "w") as fout:
            with open(c) as fin:
                x = None
                for x in fin:
                    xs = x.split()
                    if ys is not None and ys[0] == xs[0]:
                        if len(ys) == 2:
                            fout.write(y)
                            fout.write("\n")
                        ys = None
                    else:
                        fout.write(x)
            if ys is not None and len(ys) == 2:
                if x is not None:
                    fout.write("\n")
                fout.write(y)
                fout.write("\n")
        os.rename(cd, c)
        
