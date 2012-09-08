""" The fingerprint class is a common interface to all fingerprint engines."""

""" A map of string->Fingerprinter subclasses"""
fingerprint_index = {}

class Fingerprinter(object):

    def __init__(self):
        pass

    def fingerprint(self, file):
        """ Fingerprint a file and return a tuple (fp, data)
            where fp is a unique fp identifier and data is an
            object suitable to be imported with ingest. """
        raise NotImplementedError()

    def pre_lookup(self, file):
        """ Called before the lookup method, on the
            original file used to create the input query,
            not the query file itself.
        """
        return {}

    def num_lookups(self):
        return 1

    def lookup(self, file, metadata={}):
        """ Look up a file and return the unique fp identifier 
            Arguments:
               file: the file to look up
               metadata: any data returned by the pre_fingerprint method
        """
        # Return a tuple (fingerprint time, lookup time, result)
        # Times should be in milliseconds
        raise NotImplementedError()

    def ingest_many(self, data):
        """ Bulk import a list of data. May loop through data
            and do ingest single, or may do a bulk import
        """
        raise NotImplementedError()

    def delete_all(self):
        """ Delete all entries from the local database table
            and also any external stores
        """
        raise NotImplementedError()
