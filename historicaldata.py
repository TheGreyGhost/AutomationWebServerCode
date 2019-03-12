import socket
import struct
import time
import errorhandler
import select
import subprocess
from collections import namedtuple


class HistoricalData:
	m_dbautomation = None

    def __init__(self, dbautomation):
      m_dbautomation = dbautomation


	def received_data(data_entry):

	def received_cancel(dataSequenceID):

	def received_end_of_data(dataSequenceID):

	def received_length():

	def tick():




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




