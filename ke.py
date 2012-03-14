
import fingerprint
import db
import sqlalchemy
import conf

class KeModel(db.Base):
    __tablename__ = "ke"

class Ke(Fingerprint):
    def fingerprint(self, file):
        pass

    def codegen(self, file, start=-1, duration=-1):
        pass

    def ingest(self, data):
        pass

    def lookup(self, file):
        pass

fingerprint.fp_index["ke"] = {
        "dbmodel": KeModel,
        "instance": Ke
        }

db.create_tables()



