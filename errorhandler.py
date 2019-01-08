import logging
import logging.handlers
import sys

"""
debug
info
warn
error
critical
"""

logger = None
MAX_LOG_SIZE = 100000

if sys.platform.startswith('linux'):
    DEBUG_LOG_PATH = r"/var/ramdrive/test.txt"
else:
    DEBUG_LOG_PATH = r"c:/junk/test.txt"


def initialise(loggername="default", path=DEBUG_LOG_PATH, level=logging.INFO):
    """
    Set up the logger for this program
    :param loggername: the name of the logger
    :param path: path to a log file
    :param level: eg logging.INFO
    :return:
    """
    global logger
    logger = logging.getLogger(loggername)
    logger.setLevel(level)
    ch = logging.handlers.RotatingFileHandler(filename=path, maxBytes=MAX_LOG_SIZE, backupCount=1)
    ch.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s',
                                  datefmt="%Y-%m-%d %H:%M:%S")
    ch.setFormatter(formatter)
    logger.addHandler(ch)


def loginfo(msg):
    global logger
    logger.info(msg)


def logerror(msg):
    global logger
    logger.error(msg)


def logwarn(msg):
    global logger
    logger.warn(msg)


def logdebug(msg):
    global logger
    logger.debug(msg)


class DatabaseError(RuntimeError):
    def __init__(self, arg):
        self.args = arg


class LogDatabaseError(RuntimeError):
    def __init__(self, arg):
        self.args = arg
