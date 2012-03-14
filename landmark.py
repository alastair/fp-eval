import fingerprint
import db
import sqlalchemy
import conf

class LandmarkModel(db.Base):
    __tablename__ = "ke"

class Landmark(Fingerprint):
    def fingerprint(self, file):
        pass

    def codegen(self, file, start=-1, duration=-1):
        pass

    def ingest(self, data):
        pass

    def lookup(self, file):
        pass

fingerprint.fp_index["landmark"] = {
        "dbmodel": LandmarkModel,
        "instance": Landmark
        }

db.create_tables()

