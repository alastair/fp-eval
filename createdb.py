#!/usr/bin/python

import conf
import db

import os
import sys
import math
import random

def main(delete=False):
    num = db.session.query(db.FPFile).count()
    if num > 0 and not delete:
        print "* Database already has %d files in it." % (num)
        print "* run with -d to delete database first"
        sys.exit(1)
    if delete:
        db.session.query(db.FPFile).delete()
    path = conf.path
    neg = conf.negatives
    toprocess = []
    print "Reading all mp3 files from %s" % path
    if not os.path.exists(path):
        print "  ...path does not exist"
        sys.exit(1)
    for root, dir, files in os.walk(path):
        for f in files:
            if os.path.splitext(f)[1] == ".mp3":
                toprocess.append(os.path.join(root, f))
    print "Found", len(toprocess), "files"
    cutoff = int(math.ceil(len(toprocess) * neg / 100.0))
    print "Keeping back %d of them (%d%%)" % (cutoff, neg)
    random.shuffle(toprocess)
    negativefiles = toprocess[:cutoff]
    fpfiles = toprocess[cutoff:]

    for f in negativefiles:
        nfile = db.FPFile(unicode(f, errors="ignore"), negative=True)
        db.session.add(nfile)

    for f in fpfiles:
        fpfile = db.FPFile(unicode(f, errors="ignore"))
        db.session.add(fpfile)
    db.session.commit()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "-d":
        delete = True
    else:
        delete = False
    main(delete)


