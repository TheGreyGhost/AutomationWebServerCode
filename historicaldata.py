import socket
import struct
import time
import errorhandler
import select
import subprocess
from collections import namedtuple
from enum import Enum
import time

CurrentStates = Enum("CurrentStates", "IDLE" "WAITING_FOR_ROWCOUNT" "WAITING_FOR_FIRST_ROW" "WAITING_FOR_ROWS")


class HistoricalData:
	"""
	Manages retrieval and storage of the historical data from the arduino
	"""
	m_dbautomation = None
	m_last_request_ID = 0
	m_current_state = CurrentStates["IDLE"]
	m_last_action_time = time.time()
	m_next_action_time = m_last_action_time
	m_fingerprint = 0
	m_configuration = None
	m_tablename = None

	m_row_count = 0			# the number of rows in the arduino's datastore
	m_row_count_time = 0	# the time (unixtime) that the row count was last received

	REQUEST_ROW_COUNT_TIMEOUT = 30 # timeout after this many seconds of a row count request
	WAIT_TIME_AFTER_TIMEOUT = 300 # wait this many seconds before trying again after a timeout
	REQUEST_ROWS_TIMEOUT = 30 # timeout if no rows received within this many seconds

	def __init__(self, dbautomation, configuration):
		self.m_dbautomation = dbautomation
		self.m_configuration = configuration
		self.m_tablename = configuration.get("LogDataRow")["tablename"]

	def request_row_count(self):
		"""
		Ask the arduino for the current number of rows in the data store
		:return:
		"""
		self.socket_datastream.sendto(b"!l" + self.protocol_version, self.ip_port_arduino_datastream)
		self.m_last_action_time = time.time()
		self.m_next_action_time = self.m_last_action_time + self.REQUEST_ROW_COUNT_TIMEOUT
		self.m_current_state = CurrentStates.WAITING_FOR_ROWCOUNT

	def received_data(self, data_entry, rawdata):
		"""
		call this function every time a data entry row is received - adds to the historical data database
		:param data_entry: named tuple of the row data
		:return:
		"""
		if self.m_current_state is CurrentStates.WAITING_FOR_FIRST_ROW:
			data_request_ID = int(data_entry["data_request_ID"])
			if data_request_ID != self.m_last_request_ID:
				errorhandler.loginfo("drop datarow with ID {}".format(data_request_ID))
				return
			rownumber = int(data_entry["row_number"])
			if rownumber != 0:
				errorhandler.loginfo("unexpected packet: asked for row 0 and received row {}".format(rownumber))
			self.m_fingerprint = hash(rawdata[1:])
			self.find_gaps_and_request()
		elif self.m_current_state is CurrentStates.WAITING_FOR_ROWS:
			datacopy = data_entry.copy()
			datacopy.pop("data_request_ID", None)
			datacopy["datastore_hash"] = self.m_fingerprint
			self.m_dbautomation.add_data_to_transaction(datacopy)


	def received_cancel(self, dataSequenceID):
		"""
        call this function when a "cancelled" message is received
		:param dataSequenceID: the ID of the row data request sent
        :return:
        """

	def received_end_of_data(self, dataSequenceID):
		"""
		call this function when an "end of data" message is received
		:param dataSequenceID: the ID of the row data request sent
		:return:
		"""

	def received_rowcount(self, row_count):
		"""
		call this function when the row count message is received
		:param row_count: the number of rows
		:return:
		"""
		if self.m_current_state is CurrentStates.WAITING_FOR_ROWCOUNT:
			self.m_row_count = int(row_count)
			self.m_row_count_time = time.time()


	def request_first_row(self):
		#  !l{version}{byte request ID}{dword row nr}{word count} in LSB first order = request entries from log file
		self.m_last_request_ID = (self.m_last_request_ID + 1) % 256
		self.socket_datastream.sendto(b"!l" + self.protocol_version +
									  self.m_last_request_ID.to_bytes(length=1, signed=False) +
									  b"\x00\x00\x00\x00\x01\x00", self.ip_port_arduino_datastream)
		self.m_last_action_time = time.time()
		self.m_next_action_time = self.m_last_action_time + self.REQUEST_ROWS_TIMEOUT
		self.m_current_state = CurrentStates.WAITING_FOR_FIRST_ROW

	def tick(self):
		try:
			timed_out = time.time() >= self.next_action_time
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
			self.m_last_action_time = time.time()
			self.m_next_action_time = self.m_last_action_time + self.WAIT_TIME_AFTER_TIMEOUT
			if self.m_current_state == CurrentStates.WAITING_FOR_ROWS:
				self.m_dbautomation.end_transaction()
			self.m_current_state = CurrentStates.IDLE

		head_index = 0
		tail_index = logfile_length


	def find_missing():

	def find_gaps_and_request(self):
		"""
		assumes that
		:return:
		"""

		self.m_dbautomation.start_transaction(self.m_tablename)


	def is_chunk_full(self, startidx, endidxp1):
		"""
		checks the database for the chunk from startidx (inclusive) to endidxp1 (exclusive)
		returns true if chunk is fully populated
		:param startidx:  the index of the first row to check
		:param endidxp1: one past the last row index to check
		:return:
		"""
		countSQL = "COUNT(*) FROM '{}' WHERE 'row_number' BETWEEN {} AND {} AND 'datastore_hash' = {};".format(self.m_tablename, startidx, endidxp1 - 1, self.m_fingerprint)
		result = self.m_dbautomation.execute_select(countSQL)
		errorhandler.logdebug("query {} gave result {}".format(countSQL, result))
		if int(result) < endidxp1 - startidx:
			return False
		return True


# basic algorithm is:
# 1) find out how many entries in log file.
# 2) get the first row of data and hash it (fingerprint)
# 3) OPTIONAL - ? look up first_sequence_number for this fingerprint
# 4) look for gaps in the database and request these in chunks.  Wait until chunk is fully received or timeout.
# Gap looking algorithm:
# count on where sequence number is a given range: if count is less than expected, narrow down by halves until the missing parts are identified or the incomplete chunk size is <= 100
# 5) once swept through them in order, wait a short time then repeat the algorithm
# when data are incoming, insert into a RAM table first then chunk to the main database periodically?
#
# Store in database:
# 1) A unique sequence number primary ID
# 2a) the fingerprint for the current arduino logfile
# 2b) The log file index number
# 3) timestamp
#
# Keep in a second table:  -OPTIONAL? NOT REQD?
# each row is a unique combination of first log file entry, i.e.
# 1) timestamp
# 2) sequence number corresponding to the first entry of this logfile
