import json
import os
import subprocess

import fingerprint
import db
import sqlalchemy
import conf

import echoprint_support.fp
import echoprint_support.solr

s = conf.conf.get("echoprint", "solr_server")
th = conf.conf.get("echoprint", "tyrant_host")
tp = conf.conf.getint("echoprint", "tyrant_port")
echoprint_support.fp._fp_solr = echoprint_support.solr.SolrConnectionPool(s)
echoprint_support.fp._tyrant_address = [th, tp]

codegen_path = conf.conf.get("echoprint", "codegen_path")

class EchoprintModel(db.Base):
    __tablename__ = "echoprint"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    file_id = sqlalchemy.Column(sqlalchemy.Integer) #, sqlalchemy.ForeignKey("file.id"))
    #file = sqlalchemy.orm.relationship()
    trid = sqlalchemy.Column(sqlalchemy.String)

    def __init__(self, file, trid):
        self.file_id = file.id
        self.trid = trid

class Echoprint(Fingerprint):

    def fingerprint(self, file):
        data = self.codegen(file)
        trid = echoprint_support.fp.new_track_id()
        data = data[0]
        ret = {}
        ret["track_id"] = trid
        ret["fp"] = echoprint_support.fp.decode_code_string(data["code"])
        ret["codever"] = data["metadata"]["version"]
        ret.update(data["metadata"])
        ret["length"] = ret["duration"]

        return ret

    def codegen(self, file, start=-1, duration=-1):
        proclist = [codegen_path, os.path.abspath(file)]
        if start > 0:
            proclist.append("%d" % start)
        if duration > 0:
            proclist.append("%d" % duration)
        p = subprocess.Popen(proclist, stdout=subprocess.PIPE)
        code = p.communicate()[0]
        return json.loads(code)

    def ingest(self, data):
        echoprint_support.fp.ingest(data)

    def lookup(self, file):
        data = self.codegen(file)
        code = data["code"]
        match = echoprint_support.fp.best_match_for_query(code)
        return match

fingerprint.fp_index["echoprint"] = {
    "dbmodel": EchoprintModel
    "instance": Echoprint
}

db.create_tables()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "-d":
        echoprint_support.fp.erase_database(True)
        db.session.query(EchoprintModel).delete()
        db.session.commit()
    else:
        print "run with -d to delete solr and tyrant and temp database"
