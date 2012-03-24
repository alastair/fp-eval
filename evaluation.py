
import munge
# Perform an evaluation

class Evaluation(object):
    pass

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

def main():
    pass

def show_munge():
    print ", ".join(munge.munge_classes.keys())

if __name__ == "__main__":
    import sys
    import argparse

    p = argparse.ArgumentParser()
    g = p.add_argument_group()

    g.add_argument("-n", help="Number of files to test")
    g.add_argument("-m", "--munge", help="The method to use to modify input files")
    g.add_argument("--show-munge", action="store_true", help="List munge methods")
    # XXX: What about false positive files? Specify how many of them to test?

    args = p.parse_args()

    if args.show_munge:
        show_munge()
        sys.exit(1)

    if not args.n:
        p.error("Need number of files (-n)")
        sys.exit(1)

import db
import sqlalchemy

class Testset(db.Base):
    """ A test set is a subset of the full database used to perform a single test. """
    __tablename__ = "testset"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    testsetnumber = sqlalchemy.Column(sqlalchemy.Integer)


class Run(db.Base):
    """ A run is a combination of testset files, a munger, and a fingerprint algorithm. """
    __tablename__ = "run"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    testset_id = sqlalchemy.Column(sqlalchemy.Integer)
    munge = sqlalchemy.Column(sqlalchemy.String)
    fingerprint = sqlalchemy.Column(sqlalchemy.String)
    date = sqlalchemy.Column(sqlalchemy.Date)


class Evaluation(db.Base):
    """ A row for every testset file * run """
    __tablename__ = "evaluation"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    testset_id = sqlalchemy.Column(sqlalchemy.Integer)
    run_id = sqlalchemy.Column(sqlalchemy.Integer)


