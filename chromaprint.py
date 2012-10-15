import fingerprint
import db
import sqlalchemy
from sqlalchemy.engine.url import URL
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import conf
import eyeD3
import uuid
import time

from chromaprint_support import acoustid
from chromaprint_support import tables
from chromaprint_support import audioread

if not conf.has_section("chromaprint"):
    raise Exception("No chromaprint configuration section present")

s = conf.get("chromaprint", "server")
app_key = conf.get("chromaprint", "app_key")
api_key = conf.get("chromaprint", "api_key")

dbhost = conf.get("chromaprint", "dbhost")
dbuser = conf.get("chromaprint", "dbuser")
dbdb = conf.get("chromaprint", "dbdb")

acoustid.API_BASE_URL = s
# No rate-limiting
acoustid.REQUEST_INTERVAL = 0

class ChromaprintModel(db.Base):
    __tablename__ = "chromaprint"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    file_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('file.id'), nullable=False)
    trid = sqlalchemy.Column(sqlalchemy.String(50))

    def __init__(self, file, trid):
        self.file_id = file.id
        self.trid = trid

    def __repr__(self):
        return "Chromaprint<%s, id=%s>" % (self.file_id, self.trid)

class Chromaprint(fingerprint.Fingerprinter):
    def fingerprint(self, file):
        duration, fp = acoustid.fingerprint_file(file)
        tag = eyeD3.Tag()
        tag.link(file)
        artist = tag.getArtist()
        album = tag.getAlbum()
        title = tag.getTitle()
        track = tag.getTrackNum()
        if isinstance(track, tuple):
            track = track[0]

        u = uuid.uuid4()
        fpid = str(u)
        data = {"duration": "%d" % int(duration),
                "fingerprint": fp,

                "artist": artist,
                "album": album,
                "track": title,
                "mbid": fpid
               }
        if track:
            data["trackno"] = "%s" % track
        return (fpid, data)

    def ingest_single(self, data):
        acoustid.submit(app_key, api_key, data)

    def ingest_many(self, data):
        acoustid.submit(app_key, api_key, data)

    def pre_lookup(self, file):
        with audioread.audio_open(file) as f:
            duration = f.duration
        return {"duration": duration}

    def lookup(self, files):
        if len(files) > 1:
            raise Exception("Can only look up one file at a time")
        res = files[0]
        fname = res["file"]
        stime = time.time()
        duration, fp = acoustid.fingerprint_file(fname)
        actual_dur = res.get("data", {}).get("duration", duration)
        mtime = time.time()
        answer = None
        fptime = 0
        looktime = 0
        try:
            response = acoustid.lookup(app_key, fp, actual_dur, acoustid.DEFAULT_META)
            etime = time.time()
            fptime = (mtime-stime)*1000
            looktime = (etime-mtime)*1000
            if response.get("status") == "ok":
                chromaresults = response.get("results", [])
                if len(chromaresults):
                    rec = chromaresults[0].get("recordings", [])
                    if len(rec):
                        answer = rec[0].get("id")
        except acoustid.WebServiceError:
            pass
        res["result"] = answer
        res["fptime"] = fptime
        res["lookuptime"] = looktime
        return [res]

    def delete_all(self):
        u = URL("postgresql", host=dbhost, username=dbuser, database=dbdb)
        engine = create_engine(u)
        PgDbSession = sessionmaker(bind=engine)
        pgsession = PgDbSession()

        print pgsession.query(tables.account).all()

        pgsession.execute(tables.track_foreignid_source.delete())
        pgsession.execute(tables.track_foreignid.delete())
        pgsession.execute(tables.track_meta_source.delete())
        pgsession.execute(tables.track_meta.delete())
        pgsession.execute(tables.track_puid_source.delete())
        pgsession.execute(tables.track_puid.delete())
        pgsession.execute(tables.track_mbid_flag.delete())
        pgsession.execute(tables.track_mbid_change.delete())
        pgsession.execute(tables.track_mbid_source.delete())
        pgsession.execute(tables.track_mbid.delete())
        pgsession.execute(tables.fingerprint_index_queue.delete())
        pgsession.execute(tables.fingerprint_source.delete())
        pgsession.execute(tables.fingerprint.delete())
        pgsession.execute(tables.foreignid.delete())
        pgsession.execute(tables.foreignid_vendor.delete())
        pgsession.execute(tables.stats_top_accounts.delete())
        pgsession.execute(tables.stats.delete())
        pgsession.execute(tables.submission.delete())
        pgsession.execute(tables.meta.delete())
        pgsession.execute(tables.source.delete())
        pgsession.execute(tables.format.delete())
        pgsession.execute(tables.track.delete())
        pgsession.commit()

        # Delete the index server
        # This needs to be done manually

        # Delete the local database
        db.session.query(ChromaprintModel).delete()
        db.session.commit()

fingerprint.fingerprint_index["chromaprint"] = {
        "dbmodel": ChromaprintModel,
        "instance": Chromaprint
        }

db.create_tables()

def stats():
    cur = db.session.query(ChromaprintModel)
    print "Number of records: %d" % cur.count()

    u = URL("postgresql", host=dbhost, username=dbuser, database=dbdb)
    engine = create_engine(u)
    PgDbSession = sessionmaker(bind=engine)
    pgsession = PgDbSession()

    cur = pgsession.query(tables.submission)
    print "Number of submitted entries: %d" % cur.count()

    cur = pgsession.query(tables.submission).filter("handled='f'")
    print "Number of not imported submitted entries: %d" % cur.count()

    cur = pgsession.query(tables.fingerprint)
    print "Number of imported entries: %d" % cur.count()

if __name__ == "__main__":
    stats()
