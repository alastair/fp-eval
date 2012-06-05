#!/usr/bin/python

# Use simple-lookup as a quick way to see what a engine thinks a file's fingerprint is.

import sys
import os

import db
import echoprint
import chromaprint
import landmark

def lookup(engine, file):
    if engine == "echoprint":
        fp = echoprint.Echoprint()
        model = echoprint.EchoprintModel
    elif engine == "chromaprint":
        fp = chromaprint.Chromaprint()
        model = chromaprint.ChromaprintModel
    elif engine == "landmark":
        fp = landmark.Landmark()
        model = landmark.LandmarkModel

    full_path = os.path.abspath(file)
    cur = db.session.query(db.FPFile).filter(db.FPFile.path == full_path)
    if cur.count() > 0:
        thefile = cur.one()
    else:
        raise Exception("Can't find the file in the database. Is it ingested?")
    cur = db.session.query(model).filter(model.file_id == thefile.id)
    if cur.count() > 0:
        thefp = cur.one()
    else:
        raise Exception("Can't find the canonical FP for this file. Is it ingested?")

    res = fp.lookup(file)
    print "result for %s:" % file
    print res
    print "database reference:"
    print thefp.trid

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print >>sys.stderr, "Use simple_lookup to see what a FP thinks a file's ID is"
        print >>sys.stderr, "and what the database thinks it should be. Use with simple_ingest.py"
        print >>sys.stderr, "Usage: %s engine file" % sys.argv[0]
        print >>sys.stderr, "Engine: landmark,chromaprint,echoprint"
        sys.exit(1)
    lookup(sys.argv[1], sys.argv[2])
