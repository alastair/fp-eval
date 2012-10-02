#!/usr/bin/python

# Print statistics for a run

# True positive: Gives the right answer
# False positive A: Gives the wrong answer
# False positive B: Gives a match when we didn't expect one
# False negative: Says it's not there and it is
# True negative: Says it's not there and it isn't

import log
log.logging.getLogger('sqlalchemy.engine').setLevel(log.logging.INFO)
import db
import evaluation
import fingerprint

import sys
import argparse

def prf(data):
    numbers_dict = data["stats"]
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
    return {"precision":precision,
            "recall":recall,
            "f":f,
            "true_negative_rate":true_negative_rate,
            "accuracy":accuracy,
            "numbers_dict":numbers_dict}

def print_prf(prf):
    log.info("prf")
    print "P %2.4f R %2.4f F %2.4f TNR %2.4f Acc %2.4f %s" % \
            (prf["precision"], prf["recall"], prf["f"],
             prf["true_negative_rate"], prf["accuracy"], str(prf["numbers_dict"]))

def dpwe(data):
    numbers_dict = data["stats"]
    old_queries = data["old_queries"]
    new_queries = data["new_queries"]
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
    dpwe_nums = {"pr":pr, "car": car, "far":far, "frr":frr, "numbers_dict":numbers_dict}
    return dpwe_nums

def print_dpwe(dpwe):
    log.info("dpwe")
    print "PR %2.4f CAR %2.4f FAR %2.4f FRR %2.4f %s" % \
        (dpwe["pr"], dpwe["car"], dpwe["far"], dpwe["frr"], str(dpwe["numbers_dict"]))

def check_run(run_id):
    run = db.session.query(evaluation.Run).get(run_id)
    if run is None:
        log.warning("No such run: %s" % run_id)
        return None
    else:
        log.info(run)
        #log.info("%s results so far" % len(run.results))

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

        print_stats()

def stats(run_id):
    run = db.session.query(evaluation.Run).get(run_id)
    engine = run.engine
    fptable = fingerprint.fingerprint_index[engine]["dbmodel"]

    stats = {"tp": 0, "fp-a": 0, "fn": 0, "fp-b": 0, "tn": 0}

    # Not negative files
    old_queries = 0
    # Negative files
    new_queries = 0

    # We get all of the fp-specific data up front because it's quicker than
    # doing a single query per result
    actuals = db.session.query(db.FPFile, fptable, evaluation.Testfile, evaluation.Result).outerjoin(fptable)\
            .join(evaluation.Testfile).join(evaluation.Testset).join(evaluation.Result)\
            .join(evaluation.Run).filter(evaluation.Run.id==run.id).all()
    dbfiles = {}
    testfiles = {}
    actual_map = {}
    results = []
    for a in actuals:
        dbfiles[a[0].id] = a[0]
        if a[1] is not None:
            actual_map[a[1].file_id] = a[1]
        testfiles[a[2].id] = a[2]
        results.append(a[3])
    for r in results:
        actual = r.result
        tf_id = r.testfile_id
        f_id = testfiles[tf_id].file_id
        if dbfiles[f_id].negative:
            new_queries += 1
            expected = None
        else:
            old_queries += 1
            if f_id in actual_map:
                expected = actual_map[f_id].trid
            else:
                log.warning("NO RESULT FOR: %s" % r)
                expected = None

        # If we're on landmark, it's a little too eager to match. We store the number of
        # matching hashes in result.fptime. We only treat it as a match if
        # fptime > 9 (10 or more hashes match)
        if engine == "landmark":
            extra = r.fptime > 9
        else:
            extra = True
        if actual and extra:
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
        return {"stats":stats, "old_queries":old_queries, "new_queries":new_queries}

def print_stats(run):
    data = stats(run)
    if data:
        print_dpwe(dpwe(data))
        print_prf(prf(data))

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
        print_stats(args.r)

if __name__ == "__main__":
    main()
