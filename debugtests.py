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
from historicaldata import HistoricalData
from currenttime import current_time
from currenttime import simulate_time
from collections import namedtuple

def run_debug_test(configuration):
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
    hd_debug(db_history, configuration)


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


class HD_Messager:

    last_request_ID = 0
    last_request_rows_idx = 0
    last_request_rows_count = 0

    def synchronise_time(self, time_and_zone):
        errorhandler.logdebug("synchronise_time:{}".format(time_and_zone))

    def request_realtime_info(self):
        errorhandler.logdebug("request_realtime_info")

    def request_row_count(self, protocol_version):
        errorhandler.logdebug("request_row_count")

    def request_rows(self, first_row_idx, row_count, request_ID):
        self.last_request_ID = request_ID
        self.last_request_rows_idx = first_row_idx
        self.last_request_rows_count = row_count
        errorhandler.logdebug("request_rows: first {}, count {}, ID {}".format(first_row_idx, row_count, request_ID))

def hd_debug(db_history, configuration):
    """
         tests to do on HistoricalData

        1) test response to empty database with no fingerprint
        2) fill the database up to 10 rows using a small chunksize
        3) poll against a full database a couple of times
        4) increase the row count to 15 and poll again; expect it to fill up
        5) change count to 20
        6) change fingerprint
        7) refill to 20 rows with the new fingerprint
        8) test timeouts for each of the stages
     """
    hd_messager = HD_Messager

    simulate_time(50)

    hd = HistoricalData(db_history, configuration, hd_messager)
    db_history.clear_all_rows("LoggedDataDebug2")

    simulate_time(55)
    hd.tick()  # stay in IDLE
    simulate_time(150)
    hd.tick() # advance to row count request; expect to get request_row_count
    hd.tick() # nothing happens
    hd.received_rowcount(0) #zero rows, return to IDLE
    hd.tick() # should be idle now

    DebugRec = namedtuple('DebugRecord', ['data_request_ID', 'row_number', 'timestamp_UTC'])

    simulate_time(1000)
    hd.tick()           # expect request_row_count
    hd.received_rowcount(10)
    hd.tick()           # expect fingerprint request
    id = hd_messager.last_request_ID
    hd.received_data(DebugRec(id, 0, 50))  # return first row info
    hd.received_end_of_data(id)
    hd.tick()
    simulate_time(1005)
    hd.tick()

    # fill table up until end, keep requesting even when full
    for i in range(0, 6):
        i1 = hd_messager.last_request_rows_idx
        i2 = hd_messager.last_request_rows_count
        id = hd_messager.last_request_ID
        for j in range(i1, i1+i2-1):
            hd.received_data(DebugRec(id, j, j+50))
            hd.received_end_of_data(id)
        hd.tick()

    # increase row_count to 15 and go again
    hd.received_rowcount(15)
    hd.tick()           # expect fingerprint request
    id = hd_messager.last_request_ID
    hd.received_data(DebugRec(id, 0, 50))  # return first row info
    hd.received_end_of_data(id)
    hd.tick()
    simulate_time(1020)
    hd.tick()

    # fill table up until end, keep requesting even when full
    for i in range(0, 6):
        i1 = hd_messager.last_request_rows_idx
        i2 = hd_messager.last_request_rows_count
        id = hd_messager.last_request_ID
        for j in range(i1, i1+i2-1):
            hd.received_data(DebugRec(id, j, j+50))
            hd.received_end_of_data(id)
        hd.tick()

    # new database; count = 0 and different hash
    simulate_time(4000)
    hd.tick()           # expect request_row_count
    hd.received_rowcount(20)
    hd.tick()           # expect fingerprint request
    id = hd_messager.last_request_ID
    hd.received_data(DebugRec(id, 0, 1050))  # return first row info
    hd.received_end_of_data(id)
    hd.tick()

    # fill table up until end, keep requesting even when full
    for i in range(0, 20):
        i1 = hd_messager.last_request_rows_idx
        i2 = hd_messager.last_request_rows_count
        id = hd_messager.last_request_ID
        for j in range(i1, i1+i2-1):
            hd.received_data(DebugRec(id, j, j+1050))
            hd.received_end_of_data(id)
        hd.tick()

    #timeout on row count
    simulate_time(0)
    hd.tick()       # in idle
    simulate_time(1000)
    hd.tick()
    simulate_time(1005)
    hd.tick()
    simulate_time(1100)
    hd.tick()               #expect timeout on rowcount

    simulate_time(0)
    hd.tick()       # in idle
    simulate_time(1000)
    hd.tick()
    hd.received_rowcount(20)
    simulate_time(1005)
    hd.tick()
    simulate_time(1100)
    hd.tick()               #expect timeout on fingerprint

    simulate_time(0)
    hd.tick()       # in idle
    simulate_time(1000)
    hd.tick()
    hd.received_rowcount(20)
    hd.received_data(DebugRec(id, 0, 1050))  # return first row info
    hd.received_end_of_data(id)
    hd.tick()
    simulate_time(1005)
    hd.tick()
    simulate_time(1100)
    hd.tick()               #expect timeout on waiting for rows


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
        run_debug_test(configuration)
        errorhandler.logerror("Exit from run_debug_test")

    except:
        errorhandler.exception("Caught exception in main")
        raise

