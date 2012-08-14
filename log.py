import logging
import sys
from cloghandler.cloghandler import ConcurrentRotatingFileHandler

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter("%(asctime)s %(levelname) 7s:%(message)s");

fh = ConcurrentRotatingFileHandler("fingerprint.log")
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
logger.addHandler(fh)

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
logger.addHandler(ch)

# If you import the logger and run a file, the logger will
# start with a message of what file is running
logger.debug("=" * 40)
logger.debug("Running %s" % sys.argv[0])
logger.debug("=" * 40)

def debug(msg, *args, **kwargs):
    logging.debug(msg)

def info(msg, *args, **kwargs):
    logging.info(msg)

def warning(msg):
    logging.warning(msg)
