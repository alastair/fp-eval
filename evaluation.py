
import munge
import fingerprint
import conf

import db
import sqlalchemy
from sqlalchemy.orm import relationship, backref
import random

import sys
import argparse
import datetime

class Testset(db.Base):
    """ A testset is an identifier for a collection of files that are used in an evaluation """
    __tablename__ = "testset"
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.String)
    created = sqlalchemy.Column(sqlalchemy.DateTime)

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
    testset = relationship(Testset)

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
    munge = sqlalchemy.Column(sqlalchemy.String)
    # The fp algorithm to use
    engine = sqlalchemy.Column(sqlalchemy.String)
    # The date this run was created
    created = sqlalchemy.Column(sqlalchemy.DateTime)
    #started
    started = sqlalchemy.Column(sqlalchemy.DateTime)
    # finished (there's a result for each testfile)
    finished = sqlalchemy.Column(sqlalchemy.DateTime)

    testset = relationship(Testset)

    def __init__(self, testset, munge, engine):
        if not munge:
            raise Exception("munge not set")
        if not engine:
            raise Exception("engine not set")
        if isinstance(testset, Testset):
            testset = testset.id
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
    result = sqlalchemy.Column(sqlalchemy.String)
    fptime = sqlalchemy.Column(sqlalchemy.Integer)
    lookuptime = sqlalchemy.Column(sqlalchemy.Integer)

    def __init__(self, run, testfile):
        if isinstance(run, Run):
            if run.id is None:
                raise Exception("This run isn't committed: %s" % str(run))
            run = run.id
        if isinstance(testfile, db.FPFile):
            testfile = testfile.id
        self.testfile_id = testfile
        self.run_id = run
        self.done = False
        self.result = None

    def __repr__(self):
        return "<Result(run=%d, d=%d, res=%s)>" % (self.run_id, self.done, self.result)

db.create_tables()

def create_run(engine, munge):
    run = Run(munge, engine)
    db.session.add(run)
    db.session.commit()
    # XXX: Get run id

    # XXX: A run needs to be over all fingerprint types
    # Because we want the same files for all engines

    files = db.session.query(db.FPFile).all()
    # Randomise
    # Choose how mnay to do
    for f in files:
        eval = Evaluation(run, f)
        db.session.add(eval)
    db.session.commit()


def create_testset(name, size, holdback):
    if holdback is None:
        files = db.session.query(db.FPFile).all()
        random.shuffle(files)
        todo = files[:size]
    else:
        num = size - holdback
        files = db.session.query(db.FPFile).filter(db.FPFile.negative == False)
        random.shuffle(files)
        todo = files[:num]
        neg = db.session.query(db.FPFile).filter(db.FPFile.negative == True)
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
    tsets = db.session.query(Testset).all()
    for t in tsets:
        print "testset",t
        handle = db.session.query(Testfile).filter(Testfile.testset == t)
        count = handle.count()
        print "%s: %d files" % (t.name, count)

def make_run(testset, fp, munge):
    run = Run(testset, munge, fp)
    db.session.add(run)
    db.session.commit()

def list_runs():
    runs = db.session.query(Run).all()
    for r in runs:
        print r

def execute_run(run):
    run = db.session.query(Run).filter(Run.id == run_id).one()
    evals = db.session.query(Evaluation).filter(Evaluation.run_id == run.id).filter(Evaluation.done == False).all()
    # Make the fp instance based on the run
    for e in evals:
        f = e.file_id
        # Perform the munge
        #do the lookup
        e.result = res
        db.session.add(e)

    # Commit every n
    db.session.commit()

def show_munge():
    print ", ".join(sorted(munge.munge_classes.keys()))

def show_fp_engines():
    conf.import_fp_modules()
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
            munge = args.m
            make_run(testset, fp, munge)
    elif args.subparser == "run":
        if args.l:
            list_runs()
        elif args.r:
            run = args.r
            execute_run(run)
