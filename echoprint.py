import json
import os
import subprocess
import time

import fingerprint
import db
import sqlalchemy
import conf
import queue

import echoprint_support.fp
import echoprint_support.solr

if not conf.has_section("echoprint"):
    raise Exception("No echoprint configuration section present")

s = conf.get("echoprint", "solr_server")
th = conf.get("echoprint", "tyrant_host")
tp = conf.getint("echoprint", "tyrant_port")
echoprint_support.fp._fp_solr = echoprint_support.solr.SolrConnectionPool(s)
echoprint_support.fp._tyrant_address = [th, tp]

codegen_path = conf.get("echoprint", "codegen_path")

class EchoprintModel(db.Base):
    __tablename__ = "echoprint"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    file_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('file.id'))
    trid = sqlalchemy.Column(sqlalchemy.String(20))

    def __init__(self, file, trid):
        self.file_id = file.id
        self.trid = trid

    def __repr__(self):
        return "<Echoprint(id=%s, file=%s, trid=%s)>" % (self.id, self.file_id, self.trid)

class Echoprint(fingerprint.Fingerprinter):

    def fingerprint(self, file):
        data = self._codegen(file)
        trid = echoprint_support.fp.new_track_id()
        data = data[0]
        ret = {}
        ret["track_id"] = trid
        if "code" in data:
            ret["fp"] = echoprint_support.fp.decode_code_string(data["code"])
            ret["codever"] = data["metadata"]["version"]
            ret.update(data["metadata"])
            ret["length"] = ret["duration"]
        else:
            ret["error"] = data

        return (trid, ret)

    def _codegen(self, file, start=-1, duration=-1):
        proclist = [codegen_path, os.path.abspath(file)]
        if start > 0:
            proclist.append("%d" % start)
        if duration > 0:
            proclist.append("%d" % duration)
        p = subprocess.Popen(proclist, stdout=subprocess.PIPE)
        code = p.communicate()[0]
        try:
            return json.loads(code)
        except ValueError as e:
            print "Error loading"
            print code
            return [{}]

    def ingest_many(self, data):
        # echoprint ingest will take a list then commit
        echoprint_support.fp.ingest(data, do_commit=True)

    def lookup(self, file, metadata={}):
        stime = time.time()
        data = self._codegen(file)
        mtime = time.time()
        res = data[0]
        if "code" in res:
            code = res["code"]
        else:
            print res
            code = ""
        match = echoprint_support.fp.best_match_for_query(code)
        etime = time.time()

        fptime = (mtime-stime)*1000
        looktime = (etime-mtime)*1000
        return (fptime, looktime, match.TRID)

    def delete_all(self):
        # Erase solr and tokyo tyrant
        echoprint_support.fp.erase_database(True)
        # Erase the local database
        db.session.query(EchoprintModel).delete()
        db.session.commit()
        q = queue.FpQueue("ingest_echoprint")
        q.clear_queue()

fingerprint.fingerprint_index["echoprint"] = {
    "dbmodel": EchoprintModel,
    "instance": Echoprint
}

db.create_tables()

def stats():
    cur = db.session.query(EchoprintModel)
    print "Number of records: %d" % cur.count()
    numtyrant = len(echoprint_support.fp.get_tyrant())
    print "Number of TT records: %d" % numtyrant
    uniqsolr = set()
    with echoprint_support.solr.pooled_connection(echoprint_support.fp._fp_solr) as host:
        cur = host.query("*:*", fields="track_id", rows=10000)
        numsolr = cur.results.numFound
        #while cur.results is not None:
        #    for r in cur.results:
        #        uniqsolr.add(r["track_id"][:-1])
        #    cur = cur.next_batch()
    print "Number of Solr records: %s" % numsolr
    alltyrant = echoprint_support.fp.get_tyrant().iterkeys()
    uniqtt = set()
    for x in alltyrant:
        uniqtt.add(x.split("-")[0])
    print "Number of unique TT records: %s " % len(uniqtt)
    q = queue.FpQueue("ingest_echoprint")
    print "Ingest queue size: %s" % q.size()

if __name__ == "__main__":
    stats()

