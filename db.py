import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import conf

Base = declarative_base()

#engine = create_engine('sqlite:///fp.db')
engine = create_engine(conf.dbhost)
DbSession = sessionmaker(bind=engine)
session = DbSession()

""" Models """

class FPFile(Base):
    __tablename__ = "file"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    path = sqlalchemy.Column(sqlalchemy.String(1000))
    negative = sqlalchemy.Column(sqlalchemy.Boolean)

    def __init__(self, path, negative=False):
        self.path = path
        self.negative = negative

    def __repr__(self):
        return "<FPFile(%s,n=%s)>" % (self.path, self.negative)

def create_tables():
    """ For other modules to call if they want tables created """
    Base.metadata.create_all(engine)

Base.metadata.create_all(engine)
