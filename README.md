Fingerprint evaluation
----------------------

Requirements

* SQLAlchemy
* Sqlite

License: BSD 2-clause

To run the stuff:

Import files into the database (will keep back a percentage of files for
false negative tests - default 10%):

    python createdb.py

Perform a reference fingerprint with each FP engine.

    python ingest.py
