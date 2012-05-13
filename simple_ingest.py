#!/usr/bin/python

import sys
import os

import db
import echoprint
import chromaprint

def main(engine, files):
    if engine == "echoprint":
        fp = echoprint.Echoprint()
        model = echoprint.EchoprintModel
    elif engine == "chromaprint":
        fp = chromaprint.Chromaprint()
        model = chromaprint.ChromaprintModel
    for f in files:
        (fpid, data) = fp.fingerprint(f)
        fp.ingest_single(data)

        full_path = os.path.abspath(f)

        cur = db.session.query(db.FPFile).filter(db.FPFile.path == full_path)
        if cur.count() > 0:
            thefile = cur.one()
        else:
            thefile = db.FPFile(full_path)
            db.session.add(thefile)
            db.session.commit()

        thefp = model(thefile, fpid)
        db.session.add(thefp)
        db.session.commit()

        print "New fingerprint: %s (from %s)" % (fpid, f)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print >>sys.stderr, "Usage: %s engine files..." % sys.argv[0]
        sys.exit(1)
    main(sys.argv[1], sys.argv[2:])
