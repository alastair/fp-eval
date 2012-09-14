#!/usr/bin/python

import db
import evaluation
from chromaprint_support import audioread

def main():
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

if __name__ == "__main__":
    main()
