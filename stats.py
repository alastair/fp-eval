#!/usr/bin/python

# Print statistics for a run

# True positive: Gives the right answer
# False positive A: Gives the wrong answer
# False positive B: Gives a match when we didn't expect one
# False negative: Says it's not there and it is
# True negative: Says it's not there and it isn't

import db
import evaluation
import fingerprint
import log

import sys
import argparse

def prf(numbers_dict):
    # compute precision, recall, F, etc
    precision = recall = f = true_negative_rate = accuracy = 0
    tp = float(numbers_dict["tp"])
    tn = float(numbers_dict["tn"])
    fp = float(numbers_dict["fp-a"]) + float(numbers_dict["fp-b"])
    fn = float(numbers_dict["fn"])
    if tp or fp:
        precision = tp / (tp + fp)
    if fn or tp:
        recall = tp / (tp + fn)
    if precision or recall:
        f = 2.0 * (precision * recall)/(precision + recall)
    if tn or fp:
        true_negative_rate = tn / (tn + fp)
    if tp or tn or fp or fn:
        accuracy = (tp+tn) / (tp + tn + fp + fn)
    print "P %2.4f R %2.4f F %2.4f TNR %2.4f Acc %2.4f %s" % (precision, recall, f, true_negative_rate, accuracy, str(numbers_dict))
    return {"precision":precision, "recall":recall, "f":f, "true_negative_rate":true_negative_rate, "accuracy":accuracy}

def dpwe(numbers_dict, old_queries, new_queries):
    total_queries = old_queries + new_queries
    # compute dan's measures.. probability of error, false accept rate, correct accept rate, false reject rate
    car = far = frr = pr = 0
    r1 = float(numbers_dict["tp"])
    r2 = float(numbers_dict["fp-a"])
    r3 = float(numbers_dict["fn"])
    r4 = float(numbers_dict["fp-b"])
    r5 = float(numbers_dict["tn"])
    if r1 or r2 or r3:
        car = r1 / (r1 + r2 + r3)
    if r4 or r5:
        far = r4 / (r4 + r5)
    if r1 or r2 or r3:
        frr = (r2 + r3) / (r1 + r2 + r3)
    # probability of error
    pr = ((old_queries / total_queries) * frr) + ((new_queries / total_queries) * far)    
    print "PR %2.4f CAR %2.4f FAR %2.4f FRR %2.4f %s" % (pr, car, far, frr, str(numbers_dict))
    stats = {}
    stats.update(numbers_dict)    
    dpwe_nums = {"pr":pr, "car": car, "far":far, "frr":frr}
    stats.update(dpwe_nums)
    return dpwe_nums

def stats(run_id):
    cur = db.session.query(evaluation.Run).filter(evaluation.Run.id == run_id)
    if cur.count() == 0:
        log.warning("No such run: %s" % run_id)
    else:
        run = cur.one()
        log.info(run)
        log.info("%s results so far" % len(run.results))

        engine = run.engine
        fptable = fingerprint.fingerprint_index[engine]["dbmodel"]

        if run.started is None:
            log.warning("This run hasn't started. Statistics are probably going to be pretty boring")
        elif run.finished is None:
            log.warning("This run hasn't finished. Statistics may be incomplete")

        numfiles = len(run.testset.testfiles)
        numresults = len(run.results)
        if run.finished and numfiles != numresults:
            log.warning("The run is finished, but the number of results (%d) doesn't match" % numresults)
            log.warning("the number of testfiles (%d). Something funny may be going on" % numfiles)


        stats = {"tp": 0, "fp-a": 0, "fn": 0, "fp-b": 0, "tn": 0}

        # Not negative files
        old_queries = 0
        # Negative files
        new_queries = 0

        # We get all of the fp-specific data up front because it's quicker than
        # doing a single query per result
        actuals = db.session.query(fptable).join(db.FPFile)\
                .join(evaluation.Testfile).join(evaluation.Testset)\
                .join(evaluation.Run).filter(evaluation.Run.id==run.id).all()
        actual_map = {}
        for a in actuals:
            actual_map[a.file_id] = a
        # Same with the actual files, too
        # As long as we just make the query, the data turns up in the
        # object cache!
        files = db.session.query(db.FPFile)\
                .join(evaluation.Testfile).join(evaluation.Testset)\
                .join(evaluation.Run).filter(evaluation.Run.id==run.id).all()

        for r in run.results:
            actual = r.result
            if r.testfile.file.negative:
                new_queries += 1
                expected = None
            else:
                old_queries += 1
                fileid = r.testfile.file_id
                if fileid in actual_map:
                    expected = actual_map[fileid].trid
                else:
                    print "NO RESULT FOR", r
                    expected = None

            if actual:
                # Result from the lookup
                if expected:
                    if actual == expected:
                        # Match, TP
                        stats["tp"] += 1
                    else:
                        # Match but wrong, FP-a
                        stats["fp-a"] += 1
                else:
                    # Got a match but didn't want it, FB-b
                    stats["fp-b"] += 1

            else:
                # No result from the lookup
                if expected:
                    # We wanted a match, FN
                    stats["fn"] += 1
                else:
                    # Didn't expect a match, TN
                    stats["tn"] += 1

        if old_queries + new_queries > 0:
            d = dpwe(stats, old_queries, new_queries)
            s = prf(stats)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("-l", action="store_true", help="list available runs")
    p.add_argument("-r", help="the run to list statistics for")

    args = p.parse_args()
    if not args.l and not args.r:
        p.print_help()
    elif args.l:
        evaluation.list_runs()
    elif args.r:
        stats(args.r)

if __name__ == "__main__":
    main()
