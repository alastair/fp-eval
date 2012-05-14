
import munge

# XXX: Reproducability - want to create a "dataset", that is all the files we want to test
# Then create a "run" - combination of dataset, munge chain, fingerprint algorithm
# A comparison is a dataset, munge and all fp algorithms.
# Save the results so that we can 1) continue if things fail, 2) reproduce, 3) get stats.

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

class Run(db.Base):
    """ A run is a combination of testset files, a munger, and a fingerprint algorithm. """
    __tablename__ = "run"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    # A list of munge classes
    munge = sqlalchemy.Column(sqlalchemy.String)
    # The fp algorithm to use
    engine = sqlalchemy.Column(sqlalchemy.String)
    # The date this run was performed
    time = sqlalchemy.Column(sqlalchemy.DateTime)

    def __init__(self, munge, engine):
        # XXX: Check munges are valid
        # XXX: Check engine is valid
        self.munge = munge
        self.engine = engine
        now = datetime.datetime.now()
        now.microsecond = 0
        self.time = now

    def __repr__(self):
        return "<Run(engine=%s, munge=%s, date=%s)>" % (self.engine, self.munge, self.time)


class Evaluation(db.Base):
    """ A row for every testset file * run
        The intent is that when you create an evaluation you
        make all of the rows with done=False, then
        as they are fingerprinted, write the result and update done"""
    __tablename__ = "evaluation"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    run_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('run.id'))
    file_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('file.id'))
    done = sqlalchemy.Column(sqlalchemy.Boolean)
    result = sqlalchemy.Column(sqlalchemy.String)

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
        return "<Evaluation(run=%d, d=%d, res=%s)>" % (self.run_id, self.done, self.result)

db.create_tables()

def create_run(engine, munge):
    run = Run(munge, engine)
    db.session.add(run)
    db.session.commit()
    # XXX: Get run id

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
