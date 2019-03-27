import argparse
import errorhandler
import configuration
from configuration import Configuration
import arduinointerface
import time
import logging
import mysql.connector
from dbautomation import DBautomation
import databasefill

def run_debug_test():
    database_info = configuration.get["Databases"]
    realtime_info = configuration.get["REALTIME"]
    history_info = configuration.get["HISTORY"]
    db_realtime = DBautomation(realtime_info["user"], realtime_info["password"], database_info["HostAddress"],
                                    database_info.getint("HostPort"), realtime_info["databasename"]
                                    )
    max_realtime_rows = realtime_info.getint("max_rows")

    db_history = DBautomation(history_info["user"], history_info["password"], database_info["HostAddress"],
                                   database_info.getint("HostPort"), history_info["databasename"]
                                   )

    dbf_debug(db_history)


def dbf_debug(db_history):
        """
             tests to do on DatabaseFill:
             1) update the row count to a modest number
             2) gen_next_missing_rows with a small chunk size.  repeat several times
             3) switch to a new fingerprint, repeat
             4) gen_next_missing_rows with a larger chunk size
             5) gen_next_missing_rows with a chunk size larger than the rowcount

             Test for: iterate up through the chunks
             don't get confused by change of fingerprint
             don't get confused by chunks with missing rows

         """

        dbf = databasefill.DatabaseFill(db_history, "LoggedDataDebug")
        dbf.update_rowcount_and_fingerprint(10, 1234)
        rv = dbf.get_next_missing_rows(2) # expect to return (6,8)
        dbf.update_rowcount_and_fingerprint(10, 1235)
        rv = dbf.get_next_missing_rows(2) # expect to return (0,2)
        dbf.update_rowcount_and_fingerprint(10, 1236)
        rv = dbf.get_next_missing_rows(2) # expect to return (0,2)
        dbf.update_rowcount_and_fingerprint(5, 1234)
        rv = dbf.get_next_missing_rows(2) # expect to return (5,5)
        dbf.update_rowcount_and_fingerprint(20, 1234)
        rv = dbf.get_next_missing_rows(5) # expect to return (5,10)
        dbf.update_rowcount_and_fingerprint(20, 1234)
        rv = dbf.get_next_missing_rows(50) # expect to return (5,20)

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
        errorhandler.logerror("Successful start")
        run_debug_test()
        errorhandler.logerror("Exit from run_debug_test")

    except:
        errorhandler.exception("Caught exception in main")
        raise

