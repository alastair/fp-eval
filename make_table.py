import log
log.logging.disable(log.logging.WARNING)
import db
import evaluation
import stats
import sqlalchemy

import sys
import argparse

def stats_header(stats_method):
    # Dummy data to see how many things it returns to get the size of the header right
    dummy = {"stats": {"tp": 1, "fp-a": 1, "fn":1, "fp-b":1, "tn":1}, "old_queries":2, "new_queries":3}
    stats = stats_method(dummy)
    return stats[0]

def header(cols, stats_method):
    ncols = len(cols)
    # Number data points (p, r, f)
    stats_head = stats_header(stats_method)
    ndpoints = len(stats_head)
    c = "|".join(["c" for x in range(ndpoints)])
    fmt = "r|%s" % ("||".join([c for x in range(ncols)]),)
    print r"\begin{tabular}{%s}" % (fmt,)
    print r" & %s \\" % (" & ".join([r" \multicolumn{%s}{c}{%s}" % (ndpoints, c) for c in cols]), )
    print r" & %s \\ \hline" % (" & ".join([" & ".join(stats_head) for x in range(ncols)]), )

def simpleheader(cols):
    ncols = len(cols)
    c = ["c" for x in range(ncols)]
    fmt = "r|%s" % ("|".join(c),)
    print r"\begin{tabular}{%s}" % (fmt,)
    print r" & %s \\ \hline" % (" & ".join(cols), )

def footer():
    print r"\end{tabular}"

def length(stats_method):
    cols = ["30s", "15s", "8s", "30s from 30", "15s from 30", "8s from 30"]
    simpleheader(cols)
    rows = ["chromaprint", "echoprint", "landmark"]
    column_names = ["chop30", "chop15", "chop8", "30chop30", "30chop15", "30chop8"]
    for e in rows:
        r = []
        for m in column_names:
            row = db.session.query(evaluation.Run).filter(evaluation.Run.engine==e).filter(evaluation.Run.munge==m).one()
            i = row.id
            s = stats.stats(i)
            r.append(stats_method(s))
        percentages = [((p*100), (r*100), f) for p,r,f, in r]
        restofrow = " & ".join(["%2.2f\%%{}" % (x*100) for x in r])
        print r"%s & %s \\" % (e.title(), restofrow)
    footer()

def munge(fp, stats_method):
    """ Calculate the munged runs. fp is the table """
    cols = ["30", "15"]
    header(["30 second query", "15 second query"], stats_method)
    rows = ["chop%s", "30chop%s", "chop%s,bitrate96", "chop%s,bitrate64", "chop35,speedup1,chop%s", "chop35,speedup25,chop%s",
            "chop35,speedup5,chop%s", "chop35,speeddown1,chop%s", "chop35,speeddown25,chop%s", "chop35,speeddown5,chop%s",
            "chop%s,volume50", "chop%s,volume80", "chop%s,volume120", "chop%s,mono", "chop%s,sample22",
            "chop%s,gsm", "chop%s,radio"]
    row_titles = ["Original query", "Query from 30s", "96k bitrate", "64k bitrate", "Speed up 1\%{}", "Speed up 2.5\%{}",
            "Speed up 5\%{}", "Slow down 1\%{}", "Slow down 2.5\%{}", "Slow down 5\%{}", "Volume 50\%{}", "Volume 80\%{}",
            "Volume 120\%{}", "Convert to mono", "22k samplerate", "8k samplerate", "Radio EQ"]
    print_row(fp, rows, row_titles, cols, stats_method)
    footer()

def print_row(fp, rows, row_titles, cols, stats_method):
    ndpoints = len(stats_header(stats_method))
    for r, t in zip(rows, row_titles):
        ret = []
        for c in cols:
            munge = r % c
            try:
                row = db.session.query(evaluation.Run).filter(evaluation.Run.engine==fp).filter(evaluation.Run.munge==munge).one()
                i = row.id
                s = stats.stats(i)
                ret.append(stats_method(s)[1])
            except sqlalchemy.orm.exc.NoResultFound:
                ret.append(["-" for x in range(ndpoints)])
        flat = [a for b in ret for a in b]
        restofrow = " & ".join(["%2.2f\%%{}" % i if i != "-" else i for i in flat])
        print r"%s & %s \\" % (t, restofrow)

def noise(fp, stats_method):
    # Remove noise from the end of the fp name
    fp = fp.replace("noise", "")

    cols = ["30", "15", "8"]
    header(cols, stats_method)
    rows = ["pink10,chop%s", "pink20,chop%s", "pink30,chop%s",
            "car10,chop%s", "car20,chop%s", "car30,chop%s",
            "babble10,chop%s", "babble20,chop%s", "babble30,chop%s"]
    row_titles = ["Pink noise (0dB)","Pink noise (-10dB)","Pink noise (-20dB)",
            "Car noise (0dB)","Car noise (-10dB)","Car noise (-20dB)",
            "Babble noise (0dB)","Babble noise (-10dB)","Babble noise (-20dB)"]
    print_row(fp, rows, row_titles, cols, stats_method)
    footer()

def pertime(ts, stats_method):
    ts = ts.replace("sec", "")
    cols = ["echoprint", "chromaprint", "landmark"]
    header(cols, stats_method)
    rows = ["pink10,chop%s", "pink20,chop%s", "pink30,chop%s",
            "car10,chop%s", "car20,chop%s", "car30,chop%s",
            "babble10,chop%s", "babble20,chop%s", "babble30,chop%s"]
    row_titles = ["Pink noise (0dB)","Pink noise (-10dB)","Pink noise (-20dB)",
            "Car noise (0dB)","Car noise (-10dB)","Car noise (-20dB)",
            "Babble noise (0dB)","Babble noise (-10dB)","Babble noise (-20dB)"]

    print_time_row(ts, rows, row_titles, cols, stats_method)

    footer()

def graph(x, y):
    pass

def print_time_row(querysize, rows, row_titles, cols, stats_method):
    ndpoints = len(stats_header(stats_method))
    for r, t in zip(rows, row_titles):
        ret = []
        for c in cols:
            munge = r % querysize
            try:
                row = db.session.query(evaluation.Run).filter(evaluation.Run.engine==c).filter(evaluation.Run.munge==munge).one()
                i = row.id
                s = stats.stats(i)
                ret.append(stats_method(s)[1:])
            except sqlalchemy.orm.exc.NoResultFound:
                ret.append(["-" for x in range(ndpoints)])
        print ret
        flat = [a for b in ret for a in b]
        print flat
        restofrow = " & ".join(["%2.2f\%%{}" % i if i != "-" else i for i in flat])
        print r"%s & %s \\" % (t, restofrow)

def calc_pr(data):
    prf = stats.prf(data)
    return (("Precision", "Recall"), (prf["precision"]*100, prf["recall"]*100), ("%%", "%%"))

def calc_f(data):
    prf = stats.prf(data)
    return (("f measure", ), (prf["f"],), (None, ))

def calc_pe(data):
    r = stats.dpwe(data)
    return (("Prob of error", ), (r["pr"],), ("%%",))

if __name__ == "__main__":

    p = argparse.ArgumentParser()
    stat_types = {"pr": calc_pr,
            "pe": calc_pe,
            "f": calc_f
            }
    p.add_argument("-s", type=str, choices=stat_types.keys(), default="pr")
    modes = {"chromaprint": munge,
            "echoprint": munge,
            "landmark": munge,
            "chromaprintnoise": noise,
            "echoprintnoise": noise,
            "landmarknoise": noise,
            "15sec": pertime,
            "30sec": pertime,
            "graph": graph
            }
    p.add_argument("mode", type=str, choices=modes.keys())

    args = p.parse_args()

    # The stats method
    method = stat_types[args.s]

    # The type of graph to run
    m = args.mode
    torun = modes[m]

    # Run the method with the type and stats as arguments
    torun(m, method)
