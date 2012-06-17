#!/usr/bin/python

import munge
import fingerprint
import conf
import log

import db
import sqlalchemy
from sqlalchemy.orm import relationship, backref
import random
import operator

import sys
import argparse
import datetime
import os

conf.import_fp_modules()

class Testset(db.Base):
    """ A testset is an identifier for a collection of files that are used in an evaluation """
    __tablename__ = "testset"
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.String(50))
    created = sqlalchemy.Column(sqlalchemy.DateTime)

    # (auto) testfiles <- list of all Testfiles

    def __init__(self, name):
        self.name = name
        now = datetime.datetime.now()
        now = now.replace(microsecond=0)
        self.created = now

    def __repr__(self):
        return "<Testset(id=%d, name=%s, created=%s)>" % (self.id, self.name, self.created)

class Testfile(db.Base):
    """ A testfile links together a testset and a file """
    __tablename__ = "testfile"
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    testset_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('testset.id'))
    file_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('file.id'))

    file = relationship(db.FPFile)
    testset = relationship(Testset, backref="testfiles")

    def __init__(self, testset, file):
        if isinstance(testset, Testset):
            testset = testset.id
        self.testset_id = testset
        if isinstance(file, db.FPFile):
            file = file.id
        self.file_id = file

    def __repr__(self):
        return "<Testfile(id=%d, testset=%d, file=%d)>" % (self.id, self.testset_id, self.file_id)

class Run(db.Base):
    """ A run links together a testset, a munger (or set of), and a fingerprint algorithm. """
    __tablename__ = "run"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    # the testset listing all the files that should be tested in this run
    testset_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('testset.id'))
    # A list of munge classes
    munge = sqlalchemy.Column(sqlalchemy.String(100))
    # The fp algorithm to use
    engine = sqlalchemy.Column(sqlalchemy.String(20))
    # The date this run was created
    created = sqlalchemy.Column(sqlalchemy.DateTime)
    #started
    started = sqlalchemy.Column(sqlalchemy.DateTime)
    # finished (there's a result for each testfile)
    finished = sqlalchemy.Column(sqlalchemy.DateTime)

    testset = relationship(Testset)
    # (auto) results <- list of results

    def __init__(self, testset, munge, engine):
        if not munge:
            raise Exception("munge not set")
        if not engine:
            raise Exception("engine not set")
        if isinstance(testset, Testset):
            testset = testset.id
        munge = ",".join(map(operator.methodcaller("strip"), munge.split(",")))
        self.testset_id = testset
        self.munge = munge
        self.engine = engine
        now = datetime.datetime.now()
        now = now.replace(microsecond=0)
        self.created = now
        self.started = None
        self.finished = None

    def __repr__(self):
        return "<Run(id=%d, testset=%d, engine=%s, munge=%s, created=%s, started=%s, finished=%s)>" % \
            (self.id, self.testset_id, self.engine, self.munge, self.created, self.started, self.finished)

class Result(db.Base):
    """ A row for every testset file for a run """
    __tablename__ = "result"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    run_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('run.id'))
    testfile_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('testfile.id'))
    result = sqlalchemy.Column(sqlalchemy.String(20))
    fptime = sqlalchemy.Column(sqlalchemy.Integer)
    lookuptime = sqlalchemy.Column(sqlalchemy.Integer)

    run = relationship(Run, backref="results")

    def __init__(self, run, testfile, result, fptime, lookuptime):
        """
        run -- the run id
        testfile -- a db file
        result -- what the FP returns
        fptime -- the time (in ms) taken to perform a fingerprint
        lookuptime -- the time (in ms) taken to perform a lookup
        """
        if isinstance(run, Run):
            if run.id is None:
                raise Exception("This run isn't committed: %s" % str(run))
            run = run.id
        if isinstance(testfile, db.FPFile):
            testfile = testfile.id
        self.testfile_id = testfile
        self.run_id = run
        self.result = result

    def __repr__(self):
        return "<Result(run=%d, testfile=%d, result=%s)>" % (self.run_id, self.testfile_id, self.result)

db.create_tables()

def create_testset(name, size, holdback):
    """
    Randomly select `size' tracks from the file list and make a testset.
    If `holdback' is set, make size-holdback positives and
    holdback negatives. Otherwise randomly select size files.
    """
    if holdback is None:
        files = db.session.query(db.FPFile).all()
        random.shuffle(files)
        todo = files[:size]
    else:
        num = size - holdback
        files = db.session.query(db.FPFile).filter(db.FPFile.negative == False).all()
        random.shuffle(files)
        todo = files[:num]
        neg = db.session.query(db.FPFile).filter(db.FPFile.negative == True).all()
        random.shuffle(neg)
        todo.extend(neg[:holdback])

    testset = Testset(name)
    db.session.add(testset)
    db.session.flush()
    for fpfile in todo:
        tfile = Testfile(testset, fpfile)
        db.session.add(tfile)
    db.session.commit()

def list_testsets():
    """
    List all the testsets that have been created, including
    their size and composition of positive/negative files
    """
    tsets = db.session.query(Testset).all()
    for t in tsets:
        handle = db.session.query(Testfile).filter(Testfile.testset == t)
        count = handle.count()
        poshandle = db.session.query(Testfile).filter(Testfile.testset == t).join(Testfile.file).filter(db.FPFile.negative == False)
        poscount = poshandle.count()
        neghandle = db.session.query(Testfile).filter(Testfile.testset == t).join(Testfile.file).filter(db.FPFile.negative == True)
        negcount = neghandle.count()
        print "%s (%d): %d files - %d positive, %d negative" % (t.name, t.id, count, poscount, negcount)

def create_run(testset, fp, mungename):
    """
    Make a run. A run is a testset with a specific fingerprinter.
    Files are put through a list of munges before looked up in
    the fingerprinter
    """
    if fp not in fingerprint.fingerprint_index.keys():
        raise Exception("Unknown fingerprint name %s" % (fp))
    munges = munge.munge_classes.keys()
    for m in mungename.split(","):
        m = m.strip()
        if m not in munges:
            raise Exception("Unknown munge %s" % (m))
    testset = int(testset)
    tscursor = db.session.query(Testset).filter(Testset.id == testset)
    if tscursor.count() == 0:
        raise Exception("Testset %d not in database" % testset)
    run = Run(testset, mungename, fp)
    db.session.add(run)
    db.session.commit()

def list_runs():
    """
    List all the runs in the database
    """
    runs = db.session.query(Run).all()
    for r in runs:
        print r

def munge_file(file, munges):
    """ apply a list of munges to `file' and return a path
    to a file to read in
    """
    if not isinstance(munges, list):
        munges = map(operator.methodcaller("strip"), munges.split(","))

    newfile = file
    #XXX: If no munge, newfile is same as infile.
    for m in munges:
        # XXX: Remove intermediate files
        cls = munge.munge_classes[m]
        inst = cls()
        tmpfile = inst.perform(newfile)
        remove_file(newfile)
        newfile = tmpfile

    return newfile

def remove_file(file):
    print "remove file", file
    #os.unlink(file)
    pass

def execute_run(run_id):
    """
    Execute a run.

    This does most of the magic. 

    Get all the testfiles in which for this run's testset that have not been evaluated

    """
    run = db.session.query(Run).filter(Run.id == run_id)
    if run.count() == 0:
        raise Exception("No run with this id")
    else:
        run = run.one()

    if run.started is None:
        now = datetime.datetime.now()
        now = now.replace(microsecond=0)
        run.started = now
    db.session.add(run)

    engine = run.engine
    munges = run.munge
    fpclass = fingerprint.fingerprint_index[engine]
    fp = fpclass["instance"]()
    # All files that are part of this testset
    # That don't already have a result
    testfiles = db.session.query(Testfile)\
                    .join(Testset)\
                    .outerjoin(Result)\
                    .filter(Testset.id == run.testset_id)\
                    .filter(Result.id == None)
    for i, t in enumerate(testfiles):
        print t
        fpfile = t.file
        print fpfile

        newpath = munge_file(fpfile.path, munges)

        if newpath is None or not os.path.exists(newpath):
            log.warning("File %s doesn't exist, not fingerprinting it" % newpath)
            continue

        try:
            fptime, lookuptime, fpresult = fp.lookup(newpath)
            remove_file(newpath)
            result = Result(run, t.id, fpresult, int(fptime), int(lookuptime))
            print result
            db.session.add(result)
        except Exception as e:
            log.warning("Error performing fingerprint")
            log.warning(e)

        if i % 10 == 0:
            db.session.commit()

    now = datetime.datetime.now()
    now = now.replace(microsecond=0)
    run.finished = now
    db.session.add(run)
    db.session.commit()

def show_munge():
    print ", ".join(sorted(munge.munge_classes.keys()))

def show_fp_engines():
    print "Available fingerprinting engines:"
    print ", ".join(fingerprint.fingerprint_index.keys())

if __name__ == "__main__":
    """
    commands:
    testset -c -n "foo" -s S -b B - create a testset of size S
                    if B is set, then B of the S are not in the database,
                    otherwise, the amount of 'new queries' is random
    testset -l - list all testsets

    makerun -t 1 -f echoprint -m "start10,noise30"
    make a run using testset 1, echoprint, and 2 munges

    run -l -- list all available runs (also the status of them? - or -s 1)
    run 1 -- execute run 1
    """
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='subparser')
    test = sub.add_parser("testset", help="create and show test sets")
    mex = test.add_mutually_exclusive_group(required=True)
    mex.add_argument("-c", action="store_true", help="create a testset")
    test.add_argument("-n", help="name of the testset")
    test.add_argument("-s", type=int, help="size of the testset")
    test.add_argument("-b", type=int, help="if set, guarantee that at least B files in the test set aren't in the FP database")
    mex.add_argument("-l", action="store_true", help="list all testsets")

    mkrun = sub.add_parser("makerun", help="make a run")
    mkrun.add_argument("-t", type=int, help="The testset to use for this run")
    mkrun.add_argument("-f", help="Fingerprint algorithm to use")
    mkrun.add_argument("-m", help="comma separated list of munges to run (in order)")
    mkrun.add_argument("--show-engines", action="store_true", help="Show all fingerprint engines available")
    mkrun.add_argument("--show-munge", action="store_true", help="List munge methods")

    run = sub.add_parser("run", help="run an evaluation")
    run = run.add_mutually_exclusive_group(required=True)
    run.add_argument("-l", action="store_true", help="list all available runs")
    run.add_argument("r", type=int, help="execute run R", nargs="?")

    args = p.parse_args()

    if args.subparser == "testset":
        if args.c:
            name = args.n
            size = args.s
            if not size or not name:
                print "size (-s) and name (-n) required"
                sys.exit(1)
            holdback = args.b
            create_testset(name, size, holdback)
        elif args.l:
            list_testsets()
    elif args.subparser == "makerun":
        if args.show_munge:
            show_munge()
        elif args.show_engines:
            show_fp_engines()
        else:
            testset = args.t
            fp = args.f
            themunge = args.m
            if not testset or not fp or not themunge:
                print "testset (-t), fp engine (-f) and munge (-m) needed"
                sys.exit(1)
            create_run(testset, fp, themunge)
    elif args.subparser == "run":
        if args.l:
            list_runs()
        elif args.r:
            run = args.r
            execute_run(run)
