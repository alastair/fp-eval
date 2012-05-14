import ConfigParser

conf = ConfigParser.RawConfigParser()
conf.read('fingerprint.conf')

path = conf.get("main", "path")
negatives = conf.getint("main", "negatives")

def import_fp_modules():
    mod = conf.get("modules", "module")
    mods = mod.split(",")
    for m in mods:
        try:
            importlib.import_module(m)
        except ImportError, e:
            log.warning("Error when importing module %s" % m)
