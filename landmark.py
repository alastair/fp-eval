import fingerprint
import db
import sqlalchemy
import conf
import log

class LandmarkModel(db.Base):
    __tablename__ = "landmark"
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    file_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('file.id'))
    trid = sqlalchemy.Column(sqlalchemy.String)

    def __init__(self, file, trid):
        self.file_id = file.id
        self.trid = trid

    def __repr__(self):
        return "Landmark<%s, id=%s>" % (self.file_id, self.trid)

class Landmark(Fingerprint):
    def fingerprint(self, file):
        """ Fingerprint a file and return a tuple (fp, data)
            where fp is a unique fp identifier and data is an
            object suitable to be imported with ingest. """
        pass

    def lookup(self, file):
        """ Look up a file and return the unique fp identifier """
        pass

    def ingest_single(self, data):
        """ Ingest a single datapoint. data should
            be in a format that the fp understands
        """
        pass

    def ingest_many(self, data):
        """ Bulk import a list of data. May loop through data
            and do ingest single, or may do a bulk import
        """
        pass

    def delete_all(self):
        """ Delete all entries from the local database table
            and also any external stores
        """
        # Delete from the local database
        db.session.query(LandmarkModel).delete()
        db.session.commit()
        # Delete the matlab reference

fingerprint.fp_index["landmark"] = {
        "dbmodel": LandmarkModel,
        "instance": Landmark
        }

db.create_tables()

