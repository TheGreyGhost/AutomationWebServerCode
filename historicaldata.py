import socket
import struct
import time
import errorhandler
import select
import subprocess
from collections import namedtuple
from enum import Enum
import time

CurrentStates = Enum("CurrentStates", "IDLE" "WAITING_FOR_ROWCOUNT" "WAITING_FOR_ROWS")


class HistoricalData:
	m_dbautomation = None
	m_last_request_ID = 0
	m_current_state = CurrentStates["IDLE"]
	m_last_action_time = time.time()
	m_next_action_time = last_action_time

	m_row_count = 0
	m_row_count_time = 0

	REQUEST_ROW_COUNT_TIMEOUT = 30 # timeout after this many seconds of a row count request

	def __init__(self, dbautomation):
		m_dbautomation = dbautomation

	def request_row_count(self):
		self.socket_datastream.sendto(b"!r" + self.protocol_version, self.ip_port_arduino_datastream)
		self.m_last_action_time = time.time()
		self.m_next_action_time = self.m_last_action_time + self.REQUEST_ROW_COUNT_TIMEOUT

	def received_data(self, data_entry):

	def received_cancel(self, dataSequenceID):

	def received_end_of_data(self, dataSequenceID):

	def received_rowcount(self):

	def tick(self):
		if self.m_current_state is CurrentStates.IDLE:
			if time.time() >= self.next_action_time:

		elif self.m_current_state is CurrentStates.WAITING_FOR_ROWCOUNT:

		elif self.m_current_state is CurrentStates.WAITING_FOR_ROWS:

		else:
			raise AssertionError("Invalid m_current_state: {}".format(repr(self.m_current_state)))

		head_index = 0
		tail_index = logfile_length


	def find_missing():




	def is_chunk_full(startidx, endidxp1):
		# checks the database for the chunk from startidx (inclusive) to endidxp1 (exclusive)
		# returns true if chunk is fully populated


# basic algorithm is:
# 1) find out how many entries in log file.
# 2) find first timestamp in log file
# 3) look up first_sequence_number for this timestamp
# 4) look for gaps in the database and request these in chunks.  Wait until chunk is fully received or timeout.
# Gap looking algorithm:
# count on where sequence number is a given range: if count is less than expected, narrow down by halves until the missing parts are identified or the incomplete chunk size is <= 100
# 5) once swept through them in order, wait a short time then repeat the algorithm
# when data are incoming, insert into a RAM table first then chunk to the main database periodically?
#
# Store in database:
# 1) A unique sequence number
# 2) The log file index number
# 3) timestamp
#
# Keep in a second table:
# each row is a unique combination of first log file entry, i.e.
# 1) timestamp
# 2) sequence number corresponding to the first entry of this logfile




