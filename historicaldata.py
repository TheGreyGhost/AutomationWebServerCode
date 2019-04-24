import errorhandler
from enum import Enum
from databasefill import DatabaseFill
from currenttime import current_time
import binascii
import debugdefines

CurrentStates = Enum("CurrentStates", "IDLE WAITING_FOR_ROWCOUNT WAITING_FOR_FIRST_ROW WAITING_FOR_ROWS")


class HistoricalData:
    """
    Manages retrieval and storage of the historical data from the arduino
    """
    m_dbautomation = None
    m_current_state = CurrentStates["IDLE"]
    m_last_action_time = current_time()
    m_next_action_time = m_last_action_time
    m_fingerprint = 0
    m_configuration = None
    m_tablename = None
    m_databasefill = None
    m_messager = None
    m_protocol_version = "A" #dummy

    m_row_count = 0			# the number of rows in the arduino's datastore
    m_row_count_time = 0	# the time (unixtime) that the row count was last received
    m_last_request_ID = 0
    m_rows_requested = 0
    m_rows_received = 0

    REQUEST_ROW_COUNT_TIMEOUT = 30 # timeout after this many seconds of a row count request
    WAIT_TIME_AFTER_TIMEOUT = 300 # wait this many seconds before trying again after a timeout
    REQUEST_ROWS_TIMEOUT = 30 # timeout if no rows received within this many seconds
    WAIT_TIME_AFTER_UP_TO_DATE = 60 # how long to wait for re-poll once all rows have been fetched

    ROW_FETCH_CHUNK_SIZE = 100 # fetch this many rows of data at once

    def __init__(self, dbautomation, configuration):
        self.m_dbautomation = dbautomation
        self.m_configuration = configuration
        self.m_tablename = configuration.get["LogfileEntry"]["tablename"]
        self.m_databasefill = DatabaseFill(dbautomation, self.m_tablename)
        self.m_protocol_version = bytes(configuration.get["DataTransfer"]["ProtocolVersion"][0], 'utf-8')

        hcfg = configuration.get["HISTORY"]
        self.REQUEST_ROW_COUNT_TIMEOUT = hcfg.getint("REQUEST_ROW_COUNT_TIMEOUT", fallback=self.REQUEST_ROW_COUNT_TIMEOUT)
        self.WAIT_TIME_AFTER_TIMEOUT = hcfg.getint("WAIT_TIME_AFTER_TIMEOUT", fallback=self.WAIT_TIME_AFTER_TIMEOUT)
        self.REQUEST_ROWS_TIMEOUT = hcfg.getint("REQUEST_ROWS_TIMEOUT", fallback=self.REQUEST_ROWS_TIMEOUT)
        self.WAIT_TIME_AFTER_UP_TO_DATE = hcfg.getint("WAIT_TIME_AFTER_UP_TO_DATE", fallback=self.WAIT_TIME_AFTER_UP_TO_DATE)
        self.ROW_FETCH_CHUNK_SIZE = hcfg.getint("ROW_FETCH_CHUNK_SIZE", fallback=self.ROW_FETCH_CHUNK_SIZE)

        self.m_last_action_time = current_time()
        self.m_next_action_time = self.m_last_action_time

    def set_messager(self, i_messager):
        self.m_messager = i_messager

    def request_row_count(self):
        """
        Ask the arduino for the current number of rows in the data store
        :return:
        """
        if debugdefines.historicaldata:
            errorhandler.logdebug("request_row_count")
        self.m_messager.request_row_count(self.m_protocol_version)
        # self.socket_datastream.sendto(b"!l" + self.protocol_version, self.ip_port_arduino_datastream)
        self.m_last_action_time = current_time()
        self.m_next_action_time = self.m_last_action_time + self.REQUEST_ROW_COUNT_TIMEOUT
        self.m_current_state = CurrentStates.WAITING_FOR_ROWCOUNT

    def received_data(self, data_entry, rawdata):
        """
        call this function every time a data entry row is received - adds to the historical data database
        :param data_entry: named tuple of the row data
        :param rawdata: the raw data received (used for fingerprinting)
        :return:
        """
        data_request_ID = int(data_entry["data_request_ID"])
        if debugdefines.historicaldata:
            errorhandler.logdebug("received_data ID:{} row_number:{}".format(data_request_ID, data_entry["row_number"]))

        if data_request_ID != self.m_last_request_ID:
            errorhandler.loginfo("drop datarow with ID {}".format(data_request_ID))
            return
        if self.m_current_state is CurrentStates.WAITING_FOR_FIRST_ROW:
            rownumber = int(data_entry["row_number"])
            if rownumber != 0:
                errorhandler.loginfo("unexpected packet: asked for row 0 and received row {}".format(rownumber))
            self.m_fingerprint = binascii.crc32(rawdata[1:])
            self.find_gaps_and_request()
        elif self.m_current_state is CurrentStates.WAITING_FOR_ROWS:
            self.m_rows_received += 1
            datacopy = dict(data_entry)
            datacopy.pop("data_request_ID", None)
            datacopy["datastore_hash"] = self.m_fingerprint
            self.m_dbautomation.add_data_to_transaction(datacopy)

    def received_cancel(self, dataSequenceID):
        """
        call this function when a "cancelled" message is received
        :param dataSequenceID: the ID of the row data request sent
        :return:
        """
        if debugdefines.historicaldata:
            errorhandler.logdebug("received_cancel ID:{}".format(dataSequenceID))
        if dataSequenceID != self.m_last_request_ID:
            return
        errorhandler.loginfo("cancel received for ID {}".format(dataSequenceID))

    def received_end_of_data(self, dataSequenceID):
        """
        call this function when an "end of data" message is received
        :param dataSequenceID: the ID of the row data request sent
        :return:
        """
        if debugdefines.historicaldata:
            errorhandler.logdebug("received_end_of_data ID:{}".format(dataSequenceID))
        if dataSequenceID != self.m_last_request_ID:
            return
        self.m_dbautomation.end_transaction()
        if self.m_rows_received == self.m_rows_requested:
            self.find_gaps_and_request()
        else:
            errorhandler.loginfo("received_end_of_data for dataSequenceID {} when m_rows_received was {}"
                                 " but expected m_rows_requested {}"
                                 .format(dataSequenceID, self.m_rows_received, self.m_rows_requested))
            self.m_current_state = CurrentStates["IDLE"]
            self.m_last_action_time = current_time()
            self.m_next_action_time = self.m_last_action_time + self.WAIT_TIME_AFTER_UP_TO_DATE

    def received_rowcount(self, row_count):
        """
        call this function when the row count message is received
        :param row_count: the number of rows
        :return:
        """
        if debugdefines.historicaldata:
            errorhandler.logdebug("received_rowcount:{}", row_count)
        if self.m_current_state is CurrentStates.WAITING_FOR_ROWCOUNT:
            self.m_row_count = int(row_count)
            self.m_row_count_time = current_time()
            self.request_fingerprint()

    def request_fingerprint(self):
        #  !l{version}{byte request ID}{dword row nr}{word count} in LSB first order = request entries from log file
        if self.m_row_count == 0:
            self.m_current_state = CurrentStates["IDLE"]
            self.m_last_action_time = current_time()
            self.m_next_action_time = self.m_last_action_time + self.WAIT_TIME_AFTER_UP_TO_DATE
            return

        self.m_last_request_ID = (self.m_last_request_ID + 1) % 256
        self.m_messager.request_rows(0, 1, self.m_last_request_ID)

        self.m_last_action_time = current_time()
        self.m_next_action_time = self.m_last_action_time + self.REQUEST_ROWS_TIMEOUT
        self.m_current_state = CurrentStates.WAITING_FOR_FIRST_ROW

    def tick(self):
        try:
            timed_out = current_time() >= self.m_next_action_time
            if self.m_current_state is CurrentStates.IDLE:
                if timed_out:
                    self.request_row_count()
            elif self.m_current_state is CurrentStates.WAITING_FOR_ROWCOUNT:
                if timed_out:
                    raise TimeoutError("timeout waiting for reply to row count request")
            elif self.m_current_state is CurrentStates.WAITING_FOR_FIRST_ROW:
                if timed_out:
                    raise TimeoutError("timeout waiting for reply to first row data request")
            elif self.m_current_state is CurrentStates.WAITING_FOR_ROWS:
                if timed_out:
                    raise TimeoutError("timeout waiting for reply row data request")
            else:
                raise AssertionError("Invalid m_current_state: {}".format(repr(self.m_current_state)))

        except TimeoutError as te:
            errorhandler.logdebug(str(te))
            self.m_last_action_time = current_time()
            self.m_next_action_time = self.m_last_action_time + self.WAIT_TIME_AFTER_TIMEOUT
            if self.m_current_state == CurrentStates.WAITING_FOR_ROWS:
                self.m_dbautomation.end_transaction()
            self.m_current_state = CurrentStates.IDLE

    def find_gaps_and_request(self):
        """
        looks for gaps in the database and issues a request for the next rows to fill the gap
        :return:
        """
        self.m_databasefill.update_rowcount_and_fingerprint(self.m_row_count, self.m_fingerprint)
        range_to_fetch = self.m_databasefill.get_next_missing_rows(self.ROW_FETCH_CHUNK_SIZE)
        if range_to_fetch[0] >= range_to_fetch[1]:  # nothing to fetch.  return to IDLE.
            self.m_current_state = CurrentStates["IDLE"]
            self.m_last_action_time = current_time()
            self.m_next_action_time = self.m_last_action_time + self.WAIT_TIME_AFTER_UP_TO_DATE
            return

        #  !l{version}{byte request ID}{dword row nr}{word count} in LSB first order = request entries from log file
        self.m_last_request_ID = (self.m_last_request_ID + 1) % 256
        self.m_rows_requested = range_to_fetch[1] - range_to_fetch[0]
        self.m_rows_received = 0
        self.m_messager.request_rows(range_to_fetch[0], self.m_rows_requested, self.m_last_request_ID)
        if debugdefines.historicaldata:
            errorhandler.logdebug("request_rows start:{} number:{} ID:{}".format(range_to_fetch[0], self.m_rows_requested, self.m_last_request_ID))

        # self.socket_datastream.sendto(b"!l" + self.protocol_version +
        # 							  self.m_last_request_ID.to_bytes(length=1, signed=False) +
        # 							  range_to_fetch[0].to_bytes(length=4, signed=False) +
        # 							  (range_to_fetch[1] - range_to_fetch[0]).to_bytes(length=2, signed=False),
        # 							  self.ip_port_arduino_datastream)
        self.m_last_action_time = current_time()
        self.m_next_action_time = self.m_last_action_time + self.REQUEST_ROWS_TIMEOUT
        self.m_current_state = CurrentStates.WAITING_FOR_ROWS
        self.m_dbautomation.start_transaction(self.m_tablename)


#
# def is_chunk_full(self, startidx, endidxp1):
# 	"""
# 	checks the database for the chunk from startidx (inclusive) to endidxp1 (exclusive)
# 	returns true if chunk is fully populated
# 	:param startidx:  the index of the first row to check
# 	:param endidxp1: one past the last row index to check
# 	:return:
# 	"""
# 	countSQL = "COUNT(*) FROM '{}' WHERE 'row_number' BETWEEN {} AND {} AND 'datastore_hash' = {};".format(self.m_tablename, startidx, endidxp1 - 1, self.m_fingerprint)
# 	result = self.m_dbautomation.execute_select_fifo(countSQL)
# 	errorhandler.logdebug("query {} gave result {}".format(countSQL, result))
# 	if int(result) < endidxp1 - startidx:
# 		return False
# 	return True


# basic algorithm is:
# 1) find out how many entries in log file.
# 2) get the first row of data and hash it (fingerprint)
# 3) look for gaps in the database and request these in chunks.  Wait until chunk is fully received or timeout.
#
# Store in database:
# 1) the fingerprint for the current arduino logfile
# 2) the log file index number for the current arduino logfile.  (1) and (2) combined form a primary key
# 3) timestamp
#
