import fingerprint
import db
import sqlalchemy
import conf

class ExampleModel(db.Base):
    __tablename__ = "example"

class ExampleFP(Fingerprint):
    def fingerprint(self, file):
        pass

    def codegen(self, file, start=-1, duration=-1):
        pass

    def ingest(self, data):
        pass

    def lookup(self, file):
        pass

fingerprint.fp_index["example"] = {
        "dbmodel": ExampleModel,
        "instance": Landmark
        }

db.create_tables()

