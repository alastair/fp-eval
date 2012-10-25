import log
log.logging.disable(log.logging.WARNING)
import db
import evaluation
import stats
import sqlalchemy

import sys
import argparse


def header(cols, stats_method):
    # Dummy data to see how many things it returns to get the size of the header right
    dummy = {"stats": {"tp": 1, "fp-a": 1, "fn":1, "fp-b":1, "tn":1}, "old_queries":2, "new_queries":3}
    stats = stats_method(dummy)
    ncols = len(cols)
    # Number data points (p, r, f)
    ndpoints = len(stats)
    c = "|".join(["c" for x in range(ndpoints)])
    fmt = "r|%s" % ("||".join([c for x in range(ncols)]),)
    print r"\begin{tabular}{%s}" % (fmt,)
    print r" & %s \\" % (" & ".join([r" \multicolumn{%s}{c}{%s}" % (ndpoints, c) for c in cols]), )
    print r" & %s \\ \hline" % (" & ".join([r"\textit{p} & \textit{r} & $F_1$" for x in range(ncols)]), )

def simpleheader(cols):
    ncols = len(cols)
    c = ["c" for x in range(ncols)]
    fmt = "r|%s" % ("|".join(c),)
    print r"\begin{tabular}{%s}" % (fmt,)
    print r" & %s \\ \hline" % (" & ".join(cols), )

def footer():
    print r"\end{tabular}"

def length(stat_method):
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
            r.append(stat_method(s))
        percentages = [((p*100), (r*100), f) for p,r,f, in r]
        restofrow = " & ".join(["%2.2f\%%{}" % (x*100) for x in r])
        print r"%s & %s \\" % (e.title(), restofrow)
    footer()

def munge(fp, stat_method):
    """ Calculate the munged runs. fp is the table """
    cols = ["30", "15"]
    header(cols, stat_method)
    rows = ["chop%s", "30chop%s", "chop%s,bitrate96", "chop%s,bitrate64", "chop35,speedup25,chop%s", 
            "chop35,speedup5,chop%s", "chop35,speeddown25,chop%s", "chop35,speeddown5,chop%s",
            "chop%s,volume50", "chop%s,volume80", "chop%s,volume120", "chop%s,mono", "chop%s,sample22",
            "chop%s,gsm", "chop%s,radio"]
    row_titles = ["Original query", "Query from 30s", "96k bitrate", "64k bitrate", "Speed up 2.5\%{}",
            "Speed up 5\%{}", "Slow down 2.5\%{}", "Slow down 5\%{}", "Volume 50\%{}", "Volume 80\%{}",
            "Volume 120\%{}", "Convert to mono", "22k samplerate", "8k samplerate", "Radio EQ"]
    print_row(fp, rows, row_titles, cols, stat_method)
    footer()

def print_row(fp, rows, row_titles, cols, stat_method):
    for r, t in zip(rows, row_titles):
        ret = []
        for c in cols:
            munge = r % c
            try:
                row = db.session.query(evaluation.Run).filter(evaluation.Run.engine==fp).filter(evaluation.Run.munge==munge).one()
                i = row.id
                s = stats.stats(i)
                ret.append(stat_method(s))
            except sqlalchemy.orm.exc.NoResultFound:
                ret.append((None, None, None))
        percentages = [((p*100), (r*100), (f*100)) if p is not None else ("-", "-", "-") for p,r,f, in ret]
        flat = [a for b in percentages for a in b]
        restofrow = " & ".join(["%2.2f\%%{}" % i if i != "-" else i for i in flat])
        print r"%s & %s \\" % (t, restofrow)

def noise(fp, stat_method):
    # Remove noise from the end of the fp name
    fp = fp.replace("noise", "")

    cols = ["30", "15", "8"]
    header(cols, stat_method)
    rows = ["pink10,chop%s", "pink20,chop%s", "pink30,chop%s",
            "car10,chop%s", "car20,chop%s", "car30,chop%s",
            "babble10,chop%s", "babble20,chop%s", "babble30,chop%s"]
    row_titles = ["Pink noise (0dB)","Pink noise (-10dB)","Pink noise (-20dB)",
            "Car noise (0dB)","Car noise (-10dB)","Car noise (-20dB)",
            "Babble noise (0dB)","Babble noise (-10dB)","Babble noise (-20dB)"]
    print_row(fp, rows, row_titles, cols, stat_method)
    footer()

def pertime(ts, stats_method):
    pass

def calc_pr(data):
    prf = stats.prf(data)
    return (prf["precision"], prf["recall"])

def calc_f(data):
    prf = stats.prf(data)
    return (prf["f"],)

def calc_pe(data):
    r = stats.dpwe(data)
    return (r["pr"],)

if __name__ == "__main__":

    p = argparse.ArgumentParser()
    stats = {"pr": calc_pr,
            "pe": calc_pe,
            "f": calc_f
            }
    p.add_argument("-s", type=str, choices=stats.keys(), default="pr")
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
    method = stats[args.s]

    # The type of graph to run
    m = args.mode
    torun = modes[m]

    # Run the method with the type and stats as arguments
    torun(m, method)
