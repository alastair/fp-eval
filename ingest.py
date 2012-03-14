#!/usr/bin/python

import conf
import fingerprint
import echoprint
import db

import sys

#XXX Log errors to file
def main():
    for f in db.session.query(db.FPFile)[:10]:
        print f
        d = echoprint.fingerprint(f.path)
        # XXX Error checking if it didn't decode
        trid = d["track_id"]
        e = echoprint.Echoprint(f, trid)
        echoprint.ingest(d)
        db.session.add(e)
        # XXX commit after n imports

    db.session.commit()


if __name__ == "__main__":
    main()
