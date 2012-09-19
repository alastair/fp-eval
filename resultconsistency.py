import evaluation
import log
import db
import sys
from sqlalchemy import func

def main():
    if len(sys.argv) == 2:
        runs = [int(sys.argv[1])]
    elif len(sys.argv) == 3:
        runs = range(int(sys.argv[1]), int(sys.argv[2])+1)
    else:
        runs = []

    for r in runs:
        print "Run",r
        cur = db.session.query(evaluation.Testfile.id, func.count(evaluation.Result.id)).join(evaluation.Result)\
                .filter(evaluation.Result.run_id==r).group_by(evaluation.Testfile.id).all()
        for testfile, count in cur:
            if count != 1:
                print "Got %d results for run %d, testfile %d, deleting" % (count, r, testfile)
                db.session.query(evaluation.Result).filter(evaluation.Result.run_id==r).filter(evaluation.Result.testfile_id==testfile).delete()
                db.session.commit()

if __name__ == "__main__":
    main()
