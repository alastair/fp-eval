import ConfigParser

conf = ConfigParser.RawConfigParser()
conf.read('fingerprint.conf')

path = conf.get("main", "path")
negatives = conf.getint("main", "negatives")
