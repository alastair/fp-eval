#!/usr/bin/python

import conf
import fingerprint
import echoprint
import db

import sys

# Choose fp engine
# Get all files that haven't yet been fingerprinted by this engine
# ingest
# Commit

#XXX Log errors to file
def main():
    # XXX: Import all, not just 10.
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

def show_fp()
    print ", ".join(fingerprint.fp_index.keys())

if __name__ == "__main__":
    import sys
    import argparse

    p = argparse.ArgumentParser()
    g = p.add_argument_group()

    g.add_argument("-f", help="Fingerprint algorithm to use")
    g.add_argument("--show-fp", action="store_true", help="Show all fingerprint algorithms available")

    args = p.parse_args()

    if args.show_fp:
        show_fp()
        sys.exit(1)

    main()
