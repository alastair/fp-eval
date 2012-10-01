import log
log.logging.disable(log.logging.WARNING)
import db
import evaluation
import stats
import sqlalchemy

import sys


def header(cols):
   ncols = len(cols)
   c = ["c" for x in range(ncols)]
   fmt = "r|%s" % ("|".join(c),)
   print r"\begin{tabular}{%s}" % (fmt,)
   print r" & %s \\ \hline" % (" & ".join(cols), )

def footer():
    print r"\end{tabular}"

def length():
    cols = ["30s", "15s", "8s", "30s from 30", "15s from 30", "8s from 30"]
    header(cols)
    rows = ["chromaprint", "echoprint", "landmark"]
    column_names = ["chop30", "chop15", "chop8", "30chop30", "30chop15", "30chop8"]
    for e in rows:
        r = []
        for m in column_names:
            row = db.session.query(evaluation.Run).filter(evaluation.Run.engine==e).filter(evaluation.Run.munge==m).one()
            i = row.id
            s = stats.stats(i)
            r.append(stats.prf(s)["precision"])
        print r"%s & %s \\" % (e.title(), " & ".join(["%2.2f\%%{}" % (x*100) for x in r]))
    footer()

def chroma():
    munge("chromaprint")

def echo():
    munge("echoprint")

def landmark():
    munge("landmark")

def munge(fp):
    cols = ["30", "15"]
    header(cols)
    rows = ["chop%s", "30chop%s", "chop%s,bitrate96", "chop%s,bitrate64", "chop35,speedup25,chop%s", 
            "chop35,speedup5,chop%s", "chop35,speeddown25,chop%s", "chop35,speeddown5,chop%s",
            "chop%s,volume50", "chop%s,volume80", "chop%s,volume120", "chop%s,mono", "chop%s,sample22",
            "chop%s,gsm", "chop%s,radio"]
    row_titles = ["Original query", "Query from 30s", "96k bitrate", "64k bitrate", "Speed up 2.5\%{}",
            "Speed up 5\%{}", "Slow down 2.5\%{}", "Slow down 5\%{}", "Volume 50\%{}", "Volume 80\%{}",
            "Volume 120\%{}", "Convert to mono", "22k samplerate", "8k samplerate", "Radio EQ"]
    for r, t in zip(rows, row_titles):
        ret = []
        for c in cols:
            munge = r % c
            try:
                row = db.session.query(evaluation.Run).filter(evaluation.Run.engine==fp).filter(evaluation.Run.munge==munge).one()
                i = row.id
                s = stats.stats(i)
                ret.append(stats.prf(s)["precision"])
            except sqlalchemy.orm.exc.NoResultFound:
                ret.append(None)
        print r"%s & %s \\" % (t.title(), " & ".join(["%2.2f\%%{}" % (x*100) if x else "-" for x in ret]))
    footer()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print "Usage: %s <mode>" % sys.argv[0]
        print "mode = length|chroma|echo|landmark|noise"
    else:
        a = sys.argv[1]
        if a == "length":
            length()
        elif a == "chroma":
            chroma()
        elif a == "landmark":
            landmark()
        elif a == "echo":
            echo()
