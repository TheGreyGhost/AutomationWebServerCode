import argparse
import errorhandler
import logging

DEBUG_LOG_PATH = r"/home/pi/automationwebserver.log"
DEFAULT_DB_HOST_ADDR = "localhost"
DEFAULT_DB_HOST_PORT = 3306
DEFAULT_ARDUINO_ADDR = "192.168.2.35"
DEFAULT_ARDUINO_TERM_PORT = 53201
DEFAULT_ARDUINO_DS_PORT = 53202

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        epilog="Transfers information from the arduino (UDP) to All sound files should be 16 bit 44.1 kHz mono .wav."\
               " Hold button down during startup to start playing the test sound, press button again to stop."\
               " Errors written to logfile at {}".format(DEBUG_LOG_PATH))
    parser.add_argument("-d", "--debug", help="print debugging information", action="store_true")
    parser.add_argument("-db", "--databasename", help="name of the database to connect to", default="testfirewall")
    parser.add_argument("-dbaddr", help="the database host to connect to (IP address)", default=DEFAULT_DB_HOST_ADDR)
    parser.add_argument("-dbport", help="the database host port to connect to", default=DEFAULT_DB_HOST_PORT)
    parser.add_argument("-pw", "--password", help="the database password", default="TESTREADONLY")
    parser.add_argument("-user", "--username", help="the database username", default="testreadonly")
    parser.add_argument("-ardhost", help="the arduino address to connect to (IP address)", default=DEFAULT_ARDUINO_ADDR)
    parser.add_argument("-arddsport", help="the arduino datastream port to connect to", default=DEFAULT_ARDUINO_DS_PORT)
    parser.add_argument("-ardtermport", help="the arduino terminal port to connect to", default=DEFAULT_ARDUINO_TERM_PORT)

#    parser.add_argument("-i", "--indoorsoundfile", help="path to indoor sound effect file", default="indoorsound")
#    parser.add_argument("-o", "--outdoorsoundsfolder", help="path to outdoor sound effects folder ", default="outdoorsounds")
#    parser.add_argument("-t", "--testsound", help="play this sound continuously, if provided", default="")
    args = parser.parse_args()

    errorhandler.initialise("automationwebserver", DEBUG_LOG_PATH, logging.DEBUG if args.debug else logging.INFO)

    errorhandler.logdebug("Arguments provided:")
    errorhandler.logdebug(args)

    try:

    except IOError as e:
        errorhandler.logwarn("I/O error occurred ({0}): {1}".format(e.errno, e.strerror))
    except ValueError as e:
        errorhandler.logerror(repr(e))
    except:
        errorhandler.exception("Caught exception in main")
        raise

"""
    with DBaccess(host=args.host, port=args.port, dbname=args.databasename,
                  username=args.username, dbpassword=args.password) as db:
        ebtables = EbTables(db)
        eblist = ebtables.completeupdate(args.atomiccommitfilename)
"""

"""
    if args.debug:
#        print("wrote temp script to {}".format(DEBUG_LOG_PATH), file=sys.stderr)
#        with open(DEBUG_LOG_PATH, "w+t") as f:
            for singleline in eblist:
                errorhandler.logdebug(singleline)

    for singleline in eblist:
        print(singleline)
"""