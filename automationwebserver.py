import argparse
import errorhandler
import configuration
from configuration import Configuration
import arduinointerface
import time

DEFAULT_LOG_PATH = r"/home/pi/automationwebserver.log"

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        epilog="Transfers information from the arduino to MySQL database using UDP messages." \
               " Errors written to default logfile at {} or in the file specified in the .ini config file." \
               " The default .ini file is at {}".format(DEFAULT_LOG_PATH, configuration.DEF_CONFIGURATION_FILE))
    parser.add_argument("-d", "--debug", help="print debugging information", action="store_true")
    parser.add_argument("-i", "--initfile", help="the configuration ini file to use")
    parser.add_argument("-ic", "--initfilecreate", help="create default configuration ini file if none found" \
                                                        " (you must manually edit database names and passwords)"
                        , action="store_true")
    args = parser.parse_args()

    configuration = Configuration()
    try:
        if args.initfile:
            if args.initfilecreate:
                Configuration.generate_file_if_doesnt_exist(args.initfile)
            configuration.initialise_from_file(args.initfile)
        else:
            if args.initfilecreate:
                Configuration.generate_file_if_doesnt_exist()
            configuration.initialise_from_file()
        errorhandler.initialise("automationwebserver", configuration.get["General"]["DebugLogPath"], args.debug)

    except:
        errorhandler.initialise("automationwebserver", DEFAULT_LOG_PATH)
        print("caught exception while processing config file, see default log {}".format(DEFAULT_LOG_PATH))
        errorhandler.exception("caught exception while processing config file")
        raise

    try:
        errorhandler.logdebug("Arguments provided:")
        errorhandler.logdebug(args)
        errorhandler.logdebug("Config file used {}:".format(configuration.get_file_path()))
        errorhandler.logdebug(configuration.listall())

        #        with DBautomation(host=args.dbaddr, port=args.dbport, dbname=args.databasename,
        #                          username=args.username, dbpassword=args.password) as db:
        arduino = arduinointerface.Arduino(configuration)

        arduino.request_realtime_info()
        for i in range(6):
            gotmsg = arduino.check_for_incoming_info()
            errorhandler.logdebug("gotmsg:{}".format(gotmsg))
            time.sleep(1)

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
