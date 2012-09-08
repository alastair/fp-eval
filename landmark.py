# export DYLD_LIBRARY_PATH=/Applications/MATLAB_R2011b.app/bin/maci64/

import fingerprint
import db
import sqlalchemy
import conf
import log
import subprocess
import queue

import sqlalchemy.dialects.mysql
import os
import codecs
import tempfile

if not conf.has_section("landmark"):
    raise Exception("No landmark configuration section present")

FPRINT_PATH = conf.get("landmark", "audfprint_path")

class LandmarkModel(db.Base):
    __tablename__ = "landmark"
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    file_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('file.id'))
    trid = sqlalchemy.Column(sqlalchemy.dialects.mysql.VARCHAR(255, charset='utf8'))

    def __init__(self, file, trid):
        self.file_id = file.id
        self.trid = trid

    def __repr__(self):
        return "Landmark<%s, id=%s>" % (self.file_id, self.trid)

class Landmark(fingerprint.Fingerprinter):
    def fingerprint(self, file):
        """
        The audfprint app uses filenames to reference items in the hashtable.
        So, we just return (shortname, fname) as the (key, data).
        shortname is the file name less the prefix in the config
        file. Data is just the filename to pass to audfprint
        """
        read_path = conf.path
        shortname = file.replace(read_path, "")
        if shortname.startswith("/"):
            shortname = shortname[1:]
        return shortname, file

    def num_lookups(self):
        """
        The number of files to look up at a time
        """
        return 100

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
        if not len(data):
            return
        # If the database file doesn't exist, we need to add the flag to 
        #  create it the first time we run
        args = [FPRINT_PATH, "-dbase", "landmarkdb"]
        if not os.path.exists("landmarkdb.mat"):
            args.extend(["-cleardbase", "1"])
        args.append("-addlist")

        fp,fname = tempfile.mkstemp()
        os.close(fp)
        fp = codecs.open(fname, "w", "utf8")
        for line in data:
            if "!" not in line and "&" not in line:
                fp.write("%s\n" % line)
        fp.close()
        log.debug("importing from %s" % fname)
        args.append(fname)
        data = self.run_process(args)
        os.unlink(fname)
        log.debug(data)

    def run_process(self, args):
        """ Run some args with subprocess and get *all* stdout """
        p = subprocess.Popen(args, stdout=subprocess.PIPE)
        data = ""
        while True:
            out = p.stdout.read(1)
            if out == '' and p.poll() != None:
                break
            if out != '':
                data += out
        return data

    def delete_all(self):
        """ Delete all entries from the local database table
            and also any external stores
        """
        # Delete from the local database
        db.session.query(LandmarkModel).delete()
        db.session.commit()
        # Delete hash file
        try:
            os.unlink("landmarkdb.mat")
        except OSError:
            pass

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
