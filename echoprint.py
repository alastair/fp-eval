import json
import os
import subprocess

#from fingerprint import Fingerprint
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

class Echoprint(db.Base):
    __tablename__ = "echoprint"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    file_id = sqlalchemy.Column(sqlalchemy.Integer) #, sqlalchemy.ForeignKey("file.id"))
    #file = sqlalchemy.orm.relationship()
    trid = sqlalchemy.Column(sqlalchemy.String)

    def __init__(self, file, trid):
        self.file_id = file.id
        self.trid = trid

def fingerprint(file):
    data = codegen(file)
    trid = echoprint_support.fp.new_track_id()
    data = data[0]
    ret = {}
    ret["track_id"] = trid
    ret["fp"] = echoprint_support.fp.decode_code_string(data["code"])
    ret["codever"] = data["metadata"]["version"]
    ret.update(data["metadata"])
    ret["length"] = ret["duration"]

    return ret

def codegen(file, start=-1, duration=-1):
    proclist = [codegen_path, os.path.abspath(file)]
    if start > 0:
        proclist.append("%d" % start)
    if duration > 0:
        proclist.append("%d" % duration)
    p = subprocess.Popen(proclist, stdout=subprocess.PIPE)
    code = p.communicate()[0]
    return json.loads(code)

def ingest(data):
    echoprint_support.fp.ingest(data)

def lookup(fp):
    pass


#class Echoprint(Fingerprint):
#    pass

db.create_tables()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "-d":
        # XXX also delete echoprint table
        echoprint_support.fp.erase_database(True)
    else:
        print "run with -d to delete solr and tyrant"
