import fingerprint
import db
import sqlalchemy
import conf

class ChromaprintModel(db.Base):
    __tablename__ = "ke"

class Chromaprint(Fingerprint):
    def fingerprint(self, file):
        pass

    def codegen(self, file, start=-1, duration=-1):
        pass

    def ingest(self, data):
        pass

    def lookup(self, file):
        pass

fingerprint.fp_index["chromaprint"] = {
        "dbmodel": ChromaprintModel,
        "instance": Chromaprint
        }

db.create_tables()

