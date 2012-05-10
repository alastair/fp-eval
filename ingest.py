#!/usr/bin/python

import fingerprint
import db
import log
import conf

import sys
import importlib

def import_fp():
    mod = conf.conf.get("modules", "module")
    mods = mod.split(",")
    for m in mods:
        try:
            importlib.import_module(m)
        except ImportError, e:
            log.warning("Cannot find module %s to import" % m)

def delete(engine):
    """ Call the delete-specific method for a fingerprint engine to
        remove all traces of it from this eval test, and from
        the engine's specific storage system """
    engine_map = fingerprint.fingerprint_index.get(engine)
    engine_class = engine_map.get("instance") if engine_map else None
    if not engine_class:
        raise Exception("%s is not a valid fingerprint engine" % (engine))
    instance = engine_class()
    instance.delete_all()

#XXX: Don't want to continually fingerprint files that had errors
def main(engine):
    engine_map = fingerprint.fingerprint_index.get(engine)
    engine_class = engine_map.get("instance") if engine_map else None
    if not engine_class:
        raise Exception("%s is not a valid fingerprint engine" % (engine))
    engine_table = engine_map.get("dbmodel") if engine_map else None

    instance = engine_class()

    log.info("Importing files for engine %s" % (engine))
    print_list = []
    cur = db.session.query(db.FPFile).filter(db.FPFile.negative == False)\
            .outerjoin(engine_table).filter(engine_table.file_id == None)
    log.info("got %d things to do stuff with" % cur.count())
    for f in cur:
        (trackid, fpdata) = instance.fingerprint(f.path)
        error = "error" in fpdata
        if not error:
            e = engine_table(f, trackid)
            db.session.add(e)
            print_list.append(fpdata)
        else:
            log.debug("Error parsing file %s. Error was: %s" % (f, fpdata["error"]))

        # Ingest every 100 songs
        if len(print_list) > 99:
            log.info("Ingesting 100 files at once")
            db.session.commit()
            instance.ingest_all(print_list)
            print_list = []

def show_fp_engines():
    print "Available fingerprinting engines:"
    print ", ".join(fingerprint.fingerprint_index.keys())

if __name__ == "__main__":
    import argparse
    import_fp()

    p = argparse.ArgumentParser()
    g = p.add_argument_group()

    g.add_argument("-f", help="Fingerprint algorithm to use")
    g.add_argument("--show-engines", action="store_true", help="Show all fingerprint engines available")
    g.add_argument("-d", action="store_true", help="Delete the database for the given algorithm")

    args = p.parse_args()

    if args.show_engines:
        show_fp_engines()
        sys.exit(1)

    if not args.f:
        p.print_help()
        sys.exit(1)

    if args.d:
        delete(args.f)
    else:
        main(args.f)
