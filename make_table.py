import log
log.logging.disable(log.logging.WARNING)
import db
import evaluation
import stats
import sqlalchemy

import sys
import argparse
import matplotlib.pyplot as plt
import math

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
    c = "".join(["r" for x in range(ndpoints)])
    fmt = "l|%s" % ("|".join([c for x in range(ncols)]),)
    print r"\begin{tabular}{%s}" % (fmt,)
    print r" & %s \\" % (" & ".join([r" \multicolumn{%s}{|c}{%s}" % (ndpoints, c) for c in cols]), )
    print r" & %s \\ \hline" % (" & ".join([" & ".join(stats_head) for x in range(ncols)]), )

def footer():
    print r"\end{tabular}"

def finalplain(x, y):
    print r"\subfloat[Precision]{"
    length(None, calc_prec)
    print "}"
    print "\n"

    print r"\subfloat[Recall]{"
    length(None, calc_recall)
    print "}"
    print "\n"

    print r"\subfloat[Specificity]{"
    length(None, calc_spec)
    print "}"
    print "\n"

    print r"\subfloat[d']{"
    length(None, calc_dp)
    print "}"

def length(_, stats_method):
    stats_head = stats_header(stats_method)
    cols = ["8\,s", "15\,s", "30\,s", "0:30--0:38", "0:30--0:45", "0:30--0:60"]
    c = ["r" for x in cols*len(stats_head)]
    fmt = "l%s" % ("".join(c),)
    print r"\begin{tabular}{%s}" % (fmt,)
    colspans = [r"\multicolumn{%s}{c}{%s}" % (len(stats_head), cname) for cname in cols]
    print r" & %s \\" % (" & ".join(colspans), )

    stats_head = [r"\multicolumn{1}{c}{%s}" % (shname) for shname in stats_head]
    print r"Algorithm & %s \\ \hline" % (" & ".join([" & ".join(stats_head) for x in cols]), )
    
    rows = ["echoprint", "chromaprint", "landmark"]
    column_names = ["chop8", "chop15", "chop30", "30chop8", "30chop15", "30chop30"]
    for e in rows:
        r = []
        for m in column_names:
            row = db.session.query(evaluation.Run).filter(evaluation.Run.engine==e).filter(evaluation.Run.munge==m).one()
            i = row.id
            s = stats.stats(i)
            r.append(stats_method(s)[1])
        flat = [a for b in r for a in b]
        restofrow = " & ".join([i for i in flat])
        print r"%s & %s \\" % (e.title(), restofrow)
    footer()

def munge(fp, stats_method):
    """ Calculate the munged runs. fp is the table """
    cols = ["15", "30"]
    header(["15 second query", "30 second query"], stats_method)
    rows = ["chop%s", "", "chop%s,bitrate96", "chop%s,bitrate64", "", "chop35,speedup1,chop%s", "chop35,speedup25,chop%s",
            "chop35,speedup5,chop%s", "", "chop35,speeddown1,chop%s", "chop35,speeddown25,chop%s", "chop35,speeddown5,chop%s",
            "", "chop%s,volume50", "chop%s,volume80", "chop%s,volume120", "chop%s,mono", "", "chop%s,sample22",
            "chop%s,gsm", "chop%s,radio"]
    row_titles = ["\quad Original query", "\quad Reduce bitrate", "\qquad 96\,Kbps", "\qquad 64\,Kbps",
            "\quad Speed up", "\qquad 1\%{}", "\qquad 2.5\%{}",
            "\qquad 5\%{}", "\quad Slow down", "\qquad 1\%{}", "\qquad 2.5\%{}", "\qquad 5\%{}", "\quad Adjust volume",
            "\qquad 50\%{}", "\qquad 80\%{}",
            "\qquad 120\%{}", "\quad Convert to mono", "\quad Downsample", "\qquad 22\,kHz", "\qquad 8\,kHz", "\quad Radio EQ"]
    print_row(fp, rows, row_titles, cols, stats_method)
    footer()

def calculate_row(fp, rows, cols, stats_method):
    ndpoints = len(stats_header(stats_method))
    all_data = []
    for r in rows:
        ret = []
        for c in cols:
            if r == "":
                ret.append(["" for i in range(ndpoints)])
                continue
            munge = r % c
            try:
                row = db.session.query(evaluation.Run).filter(evaluation.Run.engine==fp).filter(evaluation.Run.munge==munge).one()
                i = row.id
                s = stats.stats(i)
                ret.append(stats_method(s)[1])
            except sqlalchemy.orm.exc.NoResultFound:
                print "error, munge", munge
                raise
                ret.append(["-" for x in range(ndpoints)])
        flat = [a for b in ret for a in b]
        all_data.append(flat)
    return all_data

def print_row(fp, rows, row_titles, cols, stats_method):
    for t, flat in zip(row_titles, calculate_row(fp, rows, cols, stats_method)):
        restofrow = " & ".join([i for i in flat])
        print r"%s & %s \\" % (t, restofrow)

def noise(fp, stats_method):
    # Remove noise from the end of the fp name
    fp = fp.replace("noise", "")

    cols = ["30", "15", "8"]
    colheads = ["30\,s", "15\,s", "8\,s"]
    header(colheads, stats_method)
    rows = ["chop%s", "", "pink10,chop%s", "pink20,chop%s", "pink30,chop%s",
            "", "car10,chop%s", "car20,chop%s", "car30,chop%s",
            "", "babble10,chop%s", "babble20,chop%s", "babble30,chop%s"]
    row_titles = ["\quad Original query", "\quad Pink noise", "\qquad 0\,dB","\qquad -10\,dB","\qquad -20\,dB",
            "\quad Car noise", "\qquad 0\,dB","\qquad -10\,dB","\qquad -20\,dB",
            "\quad Babble noise", "\qquad 0\,dB","\qquad -10\,dB","\qquad -20\,dB"]
    print_row(fp, rows, row_titles, cols, stats_method)
    footer()

def pertime(ts, stats_method):
    ts = ts.replace("sec", "")
    cols = ["echoprint", "chromaprint", "landmark"]
    header(cols, stats_method)
    rows = ["chop%s", "30chop%s", "chop%s,bitrate96", "chop%s,bitrate64", "chop35,speedup1,chop%s", "chop35,speedup25,chop%s",
            "chop35,speedup5,chop%s", "chop35,speeddown1,chop%s", "chop35,speeddown25,chop%s", "chop35,speeddown5,chop%s",
            "chop%s,volume50", "chop%s,volume80", "chop%s,volume120", "chop%s,mono", "chop%s,sample22",
            "chop%s,gsm", "chop%s,radio"]
    row_titles = ["Original audio", "Original from 30s", "96k bitrate", "64k bitrate", "Speed up 1\%{}", "Speed up 2.5\%{}",
            "Speed up 5\%{}", "Slow down 1\%{}", "Slow down 2.5\%{}", "Slow down 5\%{}", "Volume 50\%{}", "Volume 80\%{}",
            "Volume 120\%{}", "Convert to mono", "22k samplerate", "8k samplerate", "Radio EQ"]

    print_time_row(ts, rows, row_titles, cols, stats_method)

    footer()

def pertimenoise(ts, stats_method):
    ts = ts.replace("secnoise", "")
    cols = ["echoprint", "chromaprint", "landmark"]
    header(cols, stats_method)
    rows = ["chop%s", "pink10,chop%s", "pink20,chop%s", "pink30,chop%s",
            "car10,chop%s", "car20,chop%s", "car30,chop%s",
            "babble10,chop%s", "babble20,chop%s", "babble30,chop%s"]
    row_titles = ["Original query", "Pink noise (0dB)","Pink noise (-10dB)","Pink noise (-20dB)",
            "Car noise (0dB)","Car noise (-10dB)","Car noise (-20dB)",
            "Babble noise (0dB)","Babble noise (-10dB)","Babble noise (-20dB)"]

    print_time_row(ts, rows, row_titles, cols, stats_method)

    footer()

def subgraph_perdb(noise):
    lengths = ["8", "15", "30"]
    levels = ["10", "20", "30"]
    fp = ["echoprint", "chromaprint", "landmark"]
    linestyle = ["-", ":", "--"]
    x = [8, 15, 30]
    pointstyle = ["o", "^", "+"]

    plt.figure()
    plt.xlim([5, 55])
    plt.xlabel("Query length (seconds)")
    plt.xticks(x)
    plt.ylabel("Accuracy")
    plt.ylim([0.0, 1.0])
    plt.title("Accuracy with added %s noise" % noise)

    count = 1
    for p, lev in zip(pointstyle, levels):
        plt.subplot(3, 1, count)

        dbel = 10 - int(lev)
        plt.xlim([5, 45])
        plt.xlabel("Query length (seconds)")
        plt.xticks(x)
        plt.ylabel("Accuracy")
        plt.ylim([0.0, 1.0])
        plt.title("Accuracy with %ddB %s noise" % (dbel, noise, ))

        count += 1
        print "noise", lev
        for line, c in zip(linestyle, fp):
            print "    fp", c
            data = []
            for lng in lengths:
                print ".",
                sys.stdout.flush()
                munge = "%s%s,chop%s" % (noise, lev, lng)
                row = db.session.query(evaluation.Run).filter(evaluation.Run.engine==c).filter(evaluation.Run.munge==munge).one()
                i = row.id
                s = stats.stats(i)
                accuracy = stats.prf(s)["accuracy"]
                data.append(accuracy)
            print ""
            linefmt = "k%s%s" % (line, p)
            lab = "%s" % (c, )
            plt.plot(x, data, linefmt, label=lab)
        plt.legend()
    plt.savefig("plot-%s-perdb.png" % noise)

def subgraph_perfp(noise):
    lengths = ["8", "15", "30"]
    levels = ["10", "20", "30"]
    fp = ["echoprint", "chromaprint", "landmark"]
    linestyle = ["-", ":", "--"]
    x = [8, 15, 30]
    pointstyle = ["o", "^", "+"]

    plt.figure()
    plt.xlim([5, 55])
    plt.xlabel("Query length (seconds)")
    plt.xticks(x)
    plt.ylabel("Accuracy")
    plt.ylim([0.0, 1.0])
    plt.title("Accuracy with added %s noise" % noise)

    count = 1
    for line, c in zip(linestyle, fp):
        plt.subplot(3, 1, count)

        plt.xlim([5, 45])
        plt.xlabel("Query length (seconds)")
        plt.xticks(x)
        plt.ylabel("Accuracy")
        plt.ylim([0.0, 1.0])
        plt.title("%s accuracy with added %s noise" % (c, noise))

        count += 1
        print "fp", c
        for p, lev in zip(pointstyle, levels):
            print "   noise", lev
            data = []
            for lng in lengths:
                print ".",
                sys.stdout.flush()
                munge = "%s%s,chop%s" % (noise, lev, lng)
                row = db.session.query(evaluation.Run).filter(evaluation.Run.engine==c).filter(evaluation.Run.munge==munge).one()
                i = row.id
                s = stats.stats(i)
                accuracy = stats.prf(s)["accuracy"]
                data.append(accuracy)
            print ""
            linefmt = "k%s%s" % (line, p)
            dbel = 10 - int(lev)
            lab = "%ddB" % (dbel, )
            plt.plot(x, data, linefmt, label=lab)
        plt.legend()
    plt.savefig("plot-%s-perfp.png" % noise)


def graph(mode, stats_method):
    noise = ["pink", "car", "babble"]
    for n in noise:
        if mode == "graphdb":
            subgraph_perdb(n)
        elif mode == "graphfp":
            subgraph_perfp(n)

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
                ret.append(stats_method(s)[1])
            except sqlalchemy.orm.exc.NoResultFound:
                ret.append(["-" for x in range(ndpoints)])
        flat = [a for b in ret for a in b]
        restofrow = " & ".join(["%2.0f" % i if i != "-" else i for i in flat])
        print r"%s & %s \\" % (t, restofrow)

def get_upper_lower(n, d):
    """Get the 95th percentile estimates for a ratio given
    the numerator (n) and denominator (d)

    returns (lower, upper) as percentages (0-100) to 0d.p.
    """
    p0 = (n + 2) / (d + 4)
    ll = p0 - 2 * math.sqrt(p0 * (1-p0) / (d + 4))
    ul = p0 + 2 * math.sqrt(p0 * (1-p0) / (d + 4))

    ll, ul = round(ll*100, 0), round(ul*100, 0)
    if ll < 0:
        ll = 0
    if ul > 100:
        ul = 100
    # Abs to get rid of -0
    return abs(ll), abs(ul)


def calc_prec(data):
    numbers_dict = data["stats"]
    tp = float(numbers_dict["tp"])
    fpa = float(numbers_dict["fp-a"])
    fpb = float(numbers_dict["fp-b"])
    precision = 0

    n = tp
    d = tp + fpa + fpb
    if d:
        precision = n / d

    ll, ul = get_upper_lower(n, d)

    p = round(precision*100, 0)

    return ((r"P", r"CI"), ("%2.0f" % p, "%2.0f--%2.0f" % (ll, ul)), (None, ))

def calc_recall(data):
    numbers_dict = data["stats"]
    tp = float(numbers_dict["tp"])
    tn = float(numbers_dict["tn"])
    fpa = float(numbers_dict["fp-a"])
    fpb = float(numbers_dict["fp-b"])
    fn = float(numbers_dict["fn"])

    recall = 0

    n = tp
    d = tp + fpa + fn
    if d:
        recall = n / d

    ll, ul = get_upper_lower(n, d)

    r = round(recall*100, 0)

    return ((r"R", r"LL", r"UL"), ("%2.0f" % r, "%2.0f" % ll, "%2.0f" % ul), (None, ))

def calc_spec(data):
    numbers_dict = data["stats"]
    tn = float(numbers_dict["tn"])
    fpb = float(numbers_dict["fp-b"])

    specificity = 0

    n = tn
    d = tn + fpb
    if d:
        specificity = n / d

    ll, ul = get_upper_lower(n, d)
    s = round(specificity*100, 0)

    return ((r"S", r"CI"), ("%2.0f" % s, "%2.0f--%2.0f" % (ll, ul)), (None, ))

def calc_pr(data):
    prf = stats.prf(data)
    return (("Precision", "Recall"), (prf["precision"]*100, prf["recall"]*100), ("%%", "%%"))

def calc_f(data):
    prf = stats.prf(data)
    return (("f measure", ), (prf["f"],), (None, ))

def calc_pe(data):
    r = stats.dpwe(data)
    return (("Prob of error", ), (r["pr"],), ("%%",))

def calc_dp(data):
    dprime = stats.dprime(data)
    return (("$d'$", ), ("%2.2f" % round(dprime, 2),), (None,))

def calc_ss(data):
    r = stats.sensitivity(data)
    return (("Sensitivity", "Specificity"), (r["sensitivity"]*100, r["specificity"]*100), ("%%", "%%"))

def finalnoise(_, stats_method):
    cols = ["8", "15", "30"]
    colheads = ["8\,s", "15\,s", "30\,s"]

    ncols = len(cols)
    stats_head = stats_header(stats_method)
    ndpoints = len(stats_head)
    sz = ncols*ndpoints
    c = "".join(["r" for x in range(sz)])
    fmt = "l|%s" % c

    print r"\begin{tabular}{%s}" % (fmt,)
    print r" & %s \\" % (" & ".join([r" \multicolumn{%s}{c}{%s}" % (ndpoints, c) for c in colheads]), )
    print r" & %s \\ \hline" % (" & ".join([" & ".join(stats_head) for x in range(ncols)]), )

    rows = ["chop%s", "", "pink10,chop%s", "pink20,chop%s", "pink30,chop%s",
            "", "car10,chop%s", "car20,chop%s", "car30,chop%s",
            "", "babble10,chop%s", "babble20,chop%s", "babble30,chop%s"]
    row_titles = ["\quad Original query", "\quad Pink noise", "\qquad 0\,dB","\qquad -10\,dB","\qquad -20\,dB",
            "\quad Car noise", "\qquad 0\,dB","\qquad -10\,dB","\qquad -20\,dB",
            "\quad Babble noise", "\qquad 0\,dB","\qquad -10\,dB","\qquad -20\,dB"]
    echoprint = calculate_row("echoprint", rows, cols, stats_method)
    chromaprint = calculate_row("chromaprint", rows, cols, stats_method)
    landmark = calculate_row("landmark", rows, cols, stats_method)

    print r"Echoprint & %s \\" % (" & ".join(["" for i in range(sz)]))
    for data, title in zip(echoprint, row_titles):
        text = " & ".join([i for i in data])
        print r"%s & %s \\" % (title, text)

    print r"Chromaprint & %s \\" % (" & ".join(["" for i in range(sz)]))
    for data, title in zip(chromaprint, row_titles):
        text = " & ".join([i for i in data])
        print r"%s & %s \\" % (title, text)

    print r"Landmark & %s \\" % (" & ".join(["" for i in range(sz)]))
    for data, title in zip(landmark, row_titles):
        text = " & ".join([i for i in data])
        print r"%s & %s \\" % (title, text)
    footer()

def finalmods(_, stats_method):
    cols = ["15", "30"]
    colheads = ["15\,s", "30\,s"]

    ncols = len(cols)
    stats_head = stats_header(stats_method)
    ndpoints = len(stats_head)
    sz = ncols*ndpoints
    c = "".join(["r" for x in range(ndpoints*3)])
    fmt = "l|%s" % ("".join([c for x in range(ncols)]),)
    print r"\begin{tabular}{%s}" % (fmt,)
    print r"\multicolumn{%s}{c}{Echoprint} & \multicolumn{%s}{c}{Chromaprint} & \multicolumn{%s}{c}{Landmark} \\" % (sz, sz, sz)
    print r" & %s \\" % (" & ".join([r" \multicolumn{%s}{c}{%s}" % (ndpoints, c) for c in colheads*3]), )
    print r" & %s \\ \hline" % (" & ".join([" & ".join(stats_head) for x in range(ncols*3)]), )

    rows = ["chop%s", "", "chop%s,bitrate96", "chop%s,bitrate64", "", "chop35,speedup1,chop%s", "chop35,speedup25,chop%s",
            "chop35,speedup5,chop%s", "", "chop35,speeddown1,chop%s", "chop35,speeddown25,chop%s", "chop35,speeddown5,chop%s",
            "", "chop%s,volume50", "chop%s,volume80", "chop%s,volume120", "chop%s,mono", "", "chop%s,sample22",
            "chop%s,gsm", "chop%s,radio"]
    row_titles = ["\quad Original query", "\quad Reduce bitrate", "\qquad 96\,Kbps", "\qquad 64\,Kbps",
            "\quad Speed up", "\qquad 1\%{}", "\qquad 2.5\%{}",
            "\qquad 5\%{}", "\quad Slow down", "\qquad 1\%{}", "\qquad 2.5\%{}", "\qquad 5\%{}", "\quad Adjust volume",
            "\qquad 50\%{}", "\qquad 80\%{}",
            "\qquad 120\%{}", "\quad Convert to mono", "\quad Downsample", "\qquad 22\,kHz", "\qquad 8\,kHz", "\quad Radio EQ"]



    echoprint = calculate_row("echoprint", rows, cols, stats_method)
    chromaprint = calculate_row("chromaprint", rows, cols, stats_method)
    landmark = calculate_row("landmark", rows, cols, stats_method)

    for i, title in enumerate(row_titles):
        epd = echoprint[i]
        cpd = chromaprint[i]
        lmd = landmark[i]
        ep_text = " & ".join([i for i in epd])
        cp_text = " & ".join([i for i in cpd])
        lm_text = " & ".join([i for i in lmd])
        print r"%s & %s & %s & %s \\" % (title, ep_text, cp_text, lm_text)
    footer()

if __name__ == "__main__":

    p = argparse.ArgumentParser()
    stat_types = {"pr": calc_pr,
            "pe": calc_pe,
            "f": calc_f,
            "ss": calc_ss,
            "dp": calc_dp,
            "p": calc_prec,
            "r": calc_recall,
            "s": calc_spec
            }
    p.add_argument("-s", type=str, choices=stat_types.keys(), default="pr")
    modes = {"chromaprint": munge,
            "echoprint": munge,
            "landmark": munge,
            "chromaprintnoise": noise,
            "echoprintnoise": noise,
            "landmarknoise": noise,
            "8sec": pertime,
            "15sec": pertime,
            "30sec": pertime,
            "8secnoise": pertimenoise,
            "15secnoise": pertimenoise,
            "30secnoise": pertimenoise,
            "graphfp": graph,
            "graphdb": graph,
            "finalplain": finalplain,
            "finalmods": finalmods,
            "finalnoise": finalnoise
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
