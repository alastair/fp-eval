#!/usr/bin/python

import db
import evaluation
from chromaprint_support import audioread

def short():
    """Actually delete bad testfiles (and all their results)"""
    countneg = 0
    countpos = 0
    testset_id = 4

    testfiles = db.session.query(evaluation.Testfile).filter(evaluation.Testfile.testset_id==testset_id)
    print "Number testfiles: %s" % testfiles.count()
    for i, tf in enumerate(testfiles):
        if i % 100 == 0:
            print i
        with audioread.audio_open(tf.file.path.encode("utf-8")) as f:
            duration = f.duration
        if duration < 60.0:
            if tf.file.negative:
                countneg+=1
            else:
                countpos+=1
            print "Removing short duration file: %s (%s)" % (tf.file.path.encode("utf-8"), duration)
            cur = db.session.query(evaluation.Result).filter(evaluation.Result.testfile_id==tf.id)
            print "%d results to remove" % cur.count()
            cur.delete()
            db.session.query(evaluation.Testfile).filter(evaluation.Testfile.id==tf.id).delete()
    db.session.commit()
    testfiles = db.session.query(evaluation.Testfile).filter(evaluation.Testfile.testset_id==testset_id)
    print "New number testfiles: %s" % testfiles.count()
    print "deleted negative: %s" % countneg
    print "deleted positive: %s" % countpos

def rate():
    """ Delete results for files that have a non-44.1k samplerate so we can re-do"""
    testset_id = 4
    c = 0
    testfiles = db.session.query(evaluation.Testfile).filter(evaluation.Testfile.testset_id==testset_id)
    print "Number testfiles: %s" % testfiles.count()
    for i, tf in enumerate(testfiles):
        if i % 100 == 0:
            print i
        with audioread.audio_open(tf.file.path.encode("utf-8")) as f:
            rate = f.samplerate
            if rate != 44100:
                c += 1
                print "Unexpected samplerate: %s (%s)" % (tf.file.path.encode("utf-8"), rate)
                cur = db.session.query(evaluation.Result).filter(evaluation.Result.testfile_id==tf.id)
                print "%d results to remove" % cur.count()
                #cur.delete()
    db.session.commit()
    testfiles = db.session.query(evaluation.Testfile).filter(evaluation.Testfile.testset_id==testset_id)
    print "to change", c
    print "New number testfiles: %s" % testfiles.count()

if __name__ == "__main__":
    import sys
    if sys.argv[1] == "short":
        short()
    elif sys.argv[1] == "rate":
        rate()
