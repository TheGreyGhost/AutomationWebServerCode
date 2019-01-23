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

logger_temp = None
logger_permanent = None
MAX_LOG_SIZE = 100000

def create_logger(name, path, level):
    """
    Set up a logger
    :param name: the name of the logger
    :param path: path to a log file
    :param level: eg logging.INFO
    :return: the created logger
    """
    newlogger = logging.getLogger(name)
    newlogger.setLevel(level)
    ch = logging.handlers.RotatingFileHandler(filename=path, maxBytes=MAX_LOG_SIZE, backupCount=1)
    ch.setLevel(level)

    formatter = logging.Formatter('%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s',
                                  datefmt="%Y-%m-%d %H:%M:%S")
    ch.setFormatter(formatter)
    newlogger.addHandler(ch)
    return newlogger


def initialise(loggername, temppath, permpath, templevel=logging.INFO, permlevel=logging.ERROR):
    """
    Set up the loggers for this program:
    a logfile stored in temporary memory (RAM) and one stored on disk
    """
    global logger_temp, logger_permanent
    logger_temp = create_logger(loggername + ".temp", temppath, templevel)
    logger_permanent = create_logger(loggername + ".permanent", permpath, permlevel)


def loginfo(msg, *args, **kwargs):
    global logger_temp
    logger_temp.info(msg, *args, **kwargs)


def logerror(msg, *args, **kwargs):
    global logger_permanent
    logger_permanent.error(msg, *args, **kwargs)


def logwarn(msg, *args, **kwargs):
    global logger_temp
    logger_temp.warn(msg, *args, **kwargs)


def logdebug(msg, *args, **kwargs):
    global logger_temp
    logger_temp.debug(msg, *args, **kwargs)

def exception(msg, *args, **kwargs):
    global logger_permanent
    logger_permanent.exception(msg, *args, **kwargs)

class DatabaseError(RuntimeError):
    pass

class LogDatabaseError(RuntimeError):
    pass

class ArduinoMessageError(ValueError):
    pass

