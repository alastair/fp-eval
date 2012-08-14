import fingerprint
import db
import sqlalchemy
import conf
import eyeD3
import uuid

from chromaprint_support import acoustid

if not conf.has_section("chromaprint"):
    raise Exception("No chromaprint configuration section present")

s = conf.get("chromaprint", "server")
app_key = conf.get("chromaprint", "app_key")
api_key = conf.get("chromaprint", "api_key")

acoustid.API_BASE_URL = s
# No rate-limiting
acoustid.REQUEST_INTERVAL = 0

class ChromaprintModel(db.Base):
    __tablename__ = "chromaprint"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    file_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('file.id'))
    trid = sqlalchemy.Column(sqlalchemy.String(50))

    def __init__(self, file, trid):
        self.file_id = file.id
        self.trid = trid

    def __repr__(self):
        return "Chromaprint<%s, id=%s>" % (self.file_id, self.trid)

class Chromaprint(fingerprint.Fingerprinter):
    def fingerprint(self, file):
        (duration, fp) = acoustid.fingerprint_file(file)
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
                "trackno": "%d" % track,
                "mbid": fpid
               }
        return (fpid, data)

    def ingest_single(self, data):
        acoustid.submit(app_key, api_key, data)

    def ingest_many(self, data):
        acoustid.submit(app_key, api_key, data)

    def lookup(self, file):
        stime = time.time()
        duration, fp = acoustid.fingerprint_file(path)
        mtime = time.time()
        response = lookup(app_key, fp, duration, acoustid.DEFAULT_META)
        etime = time.time()
        fptime = (mtime-stime)*1000
        looktime = (etime-mtime)*1000
        return (fptime, looktime, response)

    def delete_all(self):
        # Delete the chromaprint database
        # XXX: Need to connect to postgres
        # XXX: postgres database needs to be accessible from this machine.

        """
        fingerprint_source, fingerprint
        track_meta_source, track_meta, track_puid_source, track_mbid_source, submission, meta
        track_puid, track_mbid
        stats
        track

        """


        # Delete the local database
        db.session.query(ChromaprintModel).delete()
        db.session.commit()

fingerprint.fingerprint_index["chromaprint"] = {
        "dbmodel": ChromaprintModel,
        "instance": Chromaprint
        }

db.create_tables()

