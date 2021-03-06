import argparse
import errorhandler
import configuration
from configuration import Configuration
import arduinointerface
import time
import logging

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        epilog="Transfers information from the arduino to MySQL database using UDP messages." \
               " Errors written to the logfiles specified in the .ini config file.")
    parser.add_argument("-d", "--debug", help="print debugging information", action="store_true")
    parser.add_argument("initfile", help="the configuration ini file to use")
    # parser.add_argument("-ic", "--initfilecreate", help="create default configuration ini file if none found" \
    #                                                     " (you must manually edit database names and passwords)"
    #                     , action="store_true")
    parser.add_argument("-t", "--testresponse", help="use the indicated file as a command response", default="")
    args = parser.parse_args()

    configuration = Configuration()
    try:
        # if args.initfilecreate:
        #     Configuration.generate_file_if_doesnt_exist(args.initfile)
        configuration.initialise_from_file(args.initfile)
        templogginglevel = logging.DEBUG if args.debug else logging.INFO
        errorhandler.initialise("automationwebserver",
                                temppath=configuration.get["General"]["TempLogPath"],
                                permpath=configuration.get["General"]["PermanentLogPath"],
                                templevel=templogginglevel, permlevel=logging.ERROR)

    except:
        errorhandler.exception("caught exception while processing config file")
        raise

    try:
        errorhandler.logdebug("Arguments provided:")
        errorhandler.logdebug(args)
        errorhandler.logdebug("Config file used {}:".format(configuration.get_file_path()))
        errorhandler.logdebug(configuration.listall())
    except:
        errorhandler.exception("Caught exception in main")
        raise

    try:
        arduino = arduinointerface.Arduino(configuration)

        if args.testresponse:
            arduino.set_test_response(args.testresponse)

        WAIT_TIME_FOR_REPLY = 10  # seconds to wait for a reply to our request
        WAIT_TIME_IO_ERROR = 60  # seconds to pause if we get an IO error
        WAIT_TIME_MSG_ERROR = 60  # seconds to pause if we get an incorrect message
        POLL_TIME = 10  # number of seconds to wait before sending another request

        last_request_time = time.time()
        next_request_time = last_request_time
        while True:
            if time.time() >= next_request_time:
                try:
                    arduino.request_realtime_info()
                    last_request_time = time.time()
                    next_request_time += POLL_TIME
                    if next_request_time < last_request_time:
                        next_request_time = last_request_time + POLL_TIME

                    gotmsg = False
                    while time.time() < last_request_time + WAIT_TIME_FOR_REPLY:
                        gotmsg = arduino.check_for_incoming_info()
                        if gotmsg:
                            break
                        time.sleep(1)
                    errorhandler.logdebug("got reply" if gotmsg else "timeout waiting for reply")

                except IOError as e:
                    errorhandler.logwarn("I/O error occurred ({0}): {1}".format(e.errno, e.strerror))
                    next_request_time = last_request_time + WAIT_TIME_IO_ERROR
                except errorhandler.ArduinoMessageError as e:
                    errorhandler.loginfo(e)
                    next_request_time = last_request_time + WAIT_TIME_MSG_ERROR
                except ValueError as e:
                    errorhandler.logwarn(repr(e))
                    next_request_time = last_request_time + WAIT_TIME_MSG_ERROR
            time.sleep(1)

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
