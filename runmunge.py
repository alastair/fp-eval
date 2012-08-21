#!/usr/bin/python

import munge
import os
import sys
import shutil
import log
log.ch.setLevel(log.logging.DEBUG)

def main(mclass, infile):
    if mclass not in munge.munge_classes:
        print "No such munge: %s" % mclass
        return
    m = munge.munge_classes[mclass]()
    res = m.perform(infile)
    ext = os.path.splitext(res)[1]
    outfile = "%s%s" % (mclass, ext)
    shutil.copy(res, outfile)
    os.unlink(res)

def list_munge():
    print ", ".join(sorted(munge.munge_classes))

if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "-l":
        list_munge()
        sys.exit(1)
    if len(sys.argv) < 3:
        print "usage: %s munge file" % sys.argv[0]
        print "       %s -l    (list munge)" % sys.argv[0]
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
