import ConfigParser

conf = ConfigParser.RawConfigParser()
conf.read('fingerprint.conf')

path = conf.get("main", "path")
negatives = conf.getint("main", "negatives")

def get(section, key):
    return conf.get(section, key)

def getint(section, key):
    return conf.getint(section, key)

def set(section, key, value):
    conf.set(section, key, value)

def has_section(section):
    return conf.has_section(section)

def import_fp_modules():
    mod = conf.get("modules", "module")
    mods = mod.split(",")
    for m in mods:
        m = m.strip()
        try:
            importlib.import_module(m)
        except ImportError, e:
            log.warning("Error when importing module %s" % m)
