#!/usr/bin/python

import conf
import fingerprint
import echoprint
import db

import sys

def main():
    for f in db.session.query(db.FPFile)[:10]:
        print f
        d = echoprint.fingerprint(f.path)
        trid = d["track_id"]
        e = echoprint.Echoprint(f, trid)
        echoprint.ingest(d)
        db.session.add(e)

    db.session.commit()


if __name__ == "__main__":
    main()
