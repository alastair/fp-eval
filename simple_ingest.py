#!/usr/bin/python

# Use simple-ingest to quickly add a file to an engine's table and the reference database.

import sys
import os

import db
import echoprint
import chromaprint
import landmark

def main(engine, files):
    if engine == "echoprint":
        fp = echoprint.Echoprint()
        model = echoprint.EchoprintModel
    elif engine == "chromaprint":
        fp = chromaprint.Chromaprint()
        model = chromaprint.ChromaprintModel
    elif engine == "landmark":
        fp = landmark.Landmark()
        model = landmark.LandmarkModel

    for f in files:
        (fpid, data) = fp.fingerprint(f)
        fp.ingest_many([data])

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
        print >>sys.stderr, "Use simple_ingest to add some files to an engine and the local database"
        print >>sys.stderr, "Usage: %s engine files..." % sys.argv[0]
        print >>sys.stderr, "Engine: landmark,chromaprint,echoprint"
        sys.exit(1)
    main(sys.argv[1], sys.argv[2:])
