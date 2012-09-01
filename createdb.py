#!/usr/bin/python

import conf
import db
import evaluation
import log

import os
import sys
import math
import random
import fingerprint

def main(delete=False):
    num = db.session.query(db.FPFile).count()
    if num > 0 and not delete:
        print >>sys.stderr, "* Database already has %d files in it." % (num)
        print >>sys.stderr, "* run with -d to delete database first"
        print >>sys.stderr, "** BE WARNED: This will delete ALL results as well"
        sys.exit(1)
    if delete:
        for k,v in fingerprint.fingerprint_index.items():
            model = v["dbmodel"]
            db.session.query(model).delete()
        db.session.query(evaluation.Result).delete()
        db.session.query(evaluation.Run).delete()
        db.session.query(evaluation.Testfile).delete()
        db.session.query(db.FPFile).delete()
    path = conf.path
    neg = conf.negatives
    toprocess = []
    log.info("Reading all mp3 files from %s" % path)
    if not os.path.exists(path):
        log.info("  ...path does not exist")
        sys.exit(1)
    for root, dir, files in os.walk(path):
        for f in files:
            if os.path.splitext(f)[1] == ".mp3":
                toprocess.append(os.path.join(root, f))
    log.info("Found %d files" % (len(toprocess)))
    cutoff = int(math.ceil(len(toprocess) * neg / 100.0))
    log.info("Keeping back %d of them (%d%%)" % (cutoff, neg))
    random.shuffle(toprocess)
    negativefiles = toprocess[:cutoff]
    fpfiles = toprocess[cutoff:]

    for f in negativefiles:
        nfile = db.FPFile(f.decode("utf8"), negative=True)
        db.session.add(nfile)

    for f in fpfiles:
        fpfile = db.FPFile(f.decode("utf8"))
        db.session.add(fpfile)
    db.session.commit()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "-d":
        delete = True
    else:
        delete = False
    main(delete)


