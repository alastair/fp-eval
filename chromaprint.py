import fingerprint
import db
import sqlalchemy
import conf
import eyeD3

from chromaprint_support import acoustid

if not conf.conf.has_section("chromaprint"):
    raise Exception("No chromaprint configuration section present")

s = conf.conf.get("chromaprint", "server")
app_key = conf.conf.get("chromaprint", "app_key")
api_key = conf.conf.get("chromaprint", "api_key")

acoustid.API_BASE_URL = s
# No rate-limiting
acoustid.REQUEST_INTERVAL = 0

class ChromaprintModel(db.Base):
    __tablename__ = "chromaprint"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    file_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('file.id'))
    trid = sqlalchemy.Column(sqlalchemy.String)

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

        fpid = "x"
        data = {"duration": "%d" % int(duration),
                "fingerprint": fp,

                "artist": artist,
                "album": album,
                "track": title,
                "trackno": track
               }
        return (fpid, data)

    def ingest_single(self, data):
        """    ``fingerprint`` key and a ``duration`` key and may include the
            following: ``puid``, ``mbid``, ``track``, ``artist``, ``album``,
                ``albumartist``, ``year``, ``trackno``, ``discno``, ``fileformat``,
                    ``bitrate``
        """
        acoustid.submit(app_key, api_key, data)

    def ingest_many(self, data):
        acoustid.submit(app_key, api_key, data)

    def lookup(self, file):
        acoustid.match(api_key, file)

    def delete_all(self):
        # Delete the chromaprint database

        # Delete the local database
        db.session.query(ChromaprintModel).delete()
        db.session.commit()

fingerprint.fingerprint_index["chromaprint"] = {
        "dbmodel": ChromaprintModel,
        "instance": Chromaprint
        }

db.create_tables()

