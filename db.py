import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

engine = create_engine('sqlite:///fp.db', echo=True)
SqliteSession = sessionmaker(bind=engine)
session = SqliteSession()

""" Models """

class FPFile(Base):
    __tablename__ = "file"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    path = sqlalchemy.Column(sqlalchemy.String)

    def __init__(self, path):
        self.path = path

    def __repr__(self):
        return "<FPFile(%s)>" % self.path

class NegativeFile(Base):
    """ Files that should be negative matches - don't have a copy
        of them in the FP database.
    """
    __tablename__ = "negative"
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    path = sqlalchemy.Column(sqlalchemy.String)

    def __init__(self, path):
        self.path = path

    def __repr__(self):
        return "<FPFile(%s)>" % self.path


Base.metadata.create_all(engine)
