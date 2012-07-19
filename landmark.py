# export DYLD_LIBRARY_PATH=/Applications/MATLAB_R2011b.app/bin/maci64/

import fingerprint
import db
import sqlalchemy
import conf
import log

import os
from mlabwrap import mlab

SUPPORT_DIR = os.path.join(os.path.dirname(__file__), "landmark_support")
mlab.addpath(os.path.abspath(os.path.join(SUPPORT_DIR, "src")))

class LandmarkModel(db.Base):
    __tablename__ = "landmark"
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    file_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('file.id'))
    trid = sqlalchemy.Column(sqlalchemy.String(20))

    def __init__(self, file, trid):
        self.file_id = file.id
        self.trid = trid

    def __repr__(self):
        return "Landmark<%s, id=%s>" % (self.file_id, self.trid)

class Landmark(fingerprint.Fingerprinter):
    def fingerprint(self, file):
        """ Fingerprint a file and return a tuple (fp, data)
            where fp is a unique fp identifier and data is an
            object suitable to be imported with ingest. """
        pass

    def lookup(self, file):
        """ Look up a file and return the unique fp identifier """
        dt = mlab.mp3read(file)
        # XXX: This isn't always the samplerate
        samplerate = 44100
        r = mlab.match_query(dt, samplerate)
        return r[1][1]

    def ingest_many(self, data):
        """ Bulk import a list of data. May loop through data
            and do ingest single, or may do a bulk import
        """
        mlab.add_tracks(data)

    def delete_all(self):
        """ Delete all entries from the local database table
            and also any external stores
        """
        # Delete from the local database
        db.session.query(LandmarkModel).delete()
        db.session.commit()
        # Delete the matlab reference
        mlab.clear_hashtable()
        os.unlink(os.path.join(SUPPORT_DIR, "landmarkhashfile"))
        q = queue.FpQueue("ingest_landmark")
        q.clear_queue()

fingerprint.fingerprint_index["landmark"] = {
        "dbmodel": LandmarkModel,
        "instance": Landmark
        }

db.create_tables()

def stats():
    q = queue.FpQueue("ingest_landmark")
    print "Ingest queue size: %s" % q.size()

if __name__ == "__main__":
    stats()
