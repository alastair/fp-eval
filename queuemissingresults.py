#!/usr/bin/python
import sys
import random

import db
import queue
import conf
import evaluation
from chromaprint_support import audioread

testset_id = 4

num_neg = 1
num_pos = 3

def add_missing():
    # For this testset, find how short of 10,000 we are

    # Find that many new FpFiles that are not
    # already part of our testset, add to testset (make sure >60sec)
    files = db.session.query(db.FPFile).filter(db.FPFile.negative == False)\
            .outerjoin(evaluation.Testfile).filter(evaluation.Testfile.id==None).all()
    print "need %s candidate pos files. got %s to choose from" % (num_pos, len(files))
    todo = []
    random.shuffle(files)
    while len(todo) < num_pos:
        x = files.pop(0)
        with audioread.audio_open(x.path.encode("utf-8")) as f:
            duration = f.duration
            print duration
        if duration >= 60.0:
            todo.append(x)
    neg = db.session.query(db.FPFile).filter(db.FPFile.negative == True)\
            .outerjoin(evaluation.Testfile).filter(evaluation.Testfile.id==None).all()
    print "need %s candidate neg files. got %s to choose from" % (num_neg, len(neg))
    random.shuffle(neg)
    while len(todo) < num_pos+num_neg:
        x = neg.pop(0)
        with audioread.audio_open(x.path.encode("utf-8")) as f:
            duration = f.duration
        if duration >= 60.0:
            todo.append(x)

    print "adding %s files" % len(todo)
    testset = db.session.query(evaluation.Testset).get(testset_id)
    for fpfile in todo:
        tfile = evaluation.Testfile(testset, fpfile)
        db.session.add(tfile)
    db.session.commit()


def add_queue(run):
    print "Adding missing files for run %s" % run
    results = db.session.query(evaluation.Result.testfile_id).filter(evaluation.Result.run_id==run).subquery()
    testfiles = db.session.query(evaluation.Testfile).filter(~evaluation.Testfile.id.in_(results))
    thequeue = queue.FpQueue("run_%s" % run)
    for tf in testfiles:
        data = {"testfile_id": tf.id}
        thequeue.put(data)
    # For this run
    # Find all testfiles that don't have a result
    # Add to queue

if __name__ == "__main__":
    if sys.argv[1] == "add":
        add_missing()
    elif sys.argv[1] == "reset":
        add_queue(int(sys.argv[2]))
