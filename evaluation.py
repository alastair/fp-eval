
import munge

# XXX: Time that a fingerprint takes to run?
# XXX: Time that a lookup takes to run

# Collect a random sampling of songs
# Look up the expected fingerprint
# Optionally perform a munge
# Do a lookup
# See what the result is
# Store result

import db
import sqlalchemy

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
        now.microsecond = 0
        self.created = now

    def __repr__(self):
        return "<Testset(id=%d, name=%s, created=%s)>" % (self.id, self.name, self.created)

class Testfile(db.Base):
    """ A testfile links together a testset and a file """
    __tablename__ = "testfile"
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    testset = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('testset.id'))
    file = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('file.id'))

    def __init__(self, testset, file):
        self.testset = testset
        self.file = file

    def __repr__(self):
        return "<Testfile(id=%d, testset=%d, file=%d)>" % (self.id, self.testset, self.file)

class Run(db.Base):
    """ A run links together a testset, a munger (or set of), and a fingerprint algorithm. """
    __tablename__ = "run"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    # the testset listing all the files that should be tested in this run
    testset = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('testset.id'))
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

    def __init__(self, testset, munge, engine):
        self.testset = testset
        self.munge = munge
        self.engine = engine
        now = datetime.datetime.now()
        now.microsecond = 0
        self.created = now
        self.started = None
        self.finished = None

    def __repr__(self):
        return "<Run(id=%d, testset=%d, engine=%s, munge=%s, created=%s, started=%s, finished=%s)>" % \
            (self.id, self.testset, self.engine, self.munge, self.created, self.started, self.finished)

class Result(db.Base):
    """ A row for every testset file for a run """
    __tablename__ = "result"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    run = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('run.id'))
    testfile = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('testfile.id'))
    result = sqlalchemy.Column(sqlalchemy.String)
    fptime = sqlalchemy.Column(sqlalchemy.Integer)
    lookuptime = sqlalchemy.Column(sqlalchemy.Integer)

    def __init__(self, run, file):
        if isinstance(run, Run):
            if run.id is None:
                raise Exception("This run isn't committed: %s" % str(run))
            run = run.id
        if isinstance(file, db.FPFile):
            file = file.id
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

def perform_run(run_id):
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
    print ", ".join(munge.munge_classes.keys())

def show_fp_engines():
    print "Available fingerprinting engines:"
    print ", ".join(fingerprint.fingerprint_index.keys())

if __name__ == "__main__":
    """
    commands:
    testset -c -n "foo" - create a testset
    testset -l - list all testsets

    makerun -t 1 -e echoprint -m "start10,noise30"
    make a run using testset 1, echoprint, and 2 munges

    run -l -- list all available runs (also the status of them? - or -s 1)
    run 1 -- execute run 1
    """
    p = argparse.ArgumentParser()
    g = p.add_argument_group()

    g.add_argument("-n", help="Number of files to test")
    g.add_argument("-m", "--munge", help="The method to use to modify input files")
    g.add_argument("-f", help="Fingerprint algorithm to use")
    g.add_argument("--show-engines", action="store_true", help="Show all fingerprint engines available")
    g.add_argument("--show-munge", action="store_true", help="List munge methods")
    # XXX: What about false positive files? Specify how many of them to test?

    args = p.parse_args()

    if args.show_munge:
        show_munge()
        sys.exit(1)

    if args.show_engines:
        show_fp_engines()
        sys.exit(1)

    if not args.f or not args.m:
        p.print_help()
        sys.exit(1)

    main()
