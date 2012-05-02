""" The fingerprint class is a common interface to all fingerprint engines."""

""" A map of string->Fingerprinter subclasses"""
fingerprint_index = {}

class Fingerprinter(object):

    def __init__(self):
        pass

    def fingerprint(self, file):
        raise NotImplementedError()

    def lookup(self, file):
        raise NotImplementedError()

    def ingest_all(self, data):
        raise NotImplementedError()

    def _create_table(self):
        raise NotImplementedError()

    def _fp_all(self):
        raise NotImplementedError()
        # Get list of files not already added
        # FP individual file
        # Add to database - unique identifier
        # Also get metadata if it supports it

    def delete_all(self):
        raise NotImplementedError()
