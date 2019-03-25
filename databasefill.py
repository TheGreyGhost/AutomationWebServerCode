class DatabaseFill:
    """
    keeps track of which rows in the database are present

    always starts from the beginning of the dataset and fills upwards

    """

    m_dbautomation = None
    m_tablename = None
    m_rowcount = 0
    m_filled_up_to_p1 = 0
    m_fingerprint = 0


    MAX_CHUNK_SIZE = 10000

    def __init__(self, dbautomation, tablename):
        self.m_dbautomation = dbautomation
        self.m_tablename = tablename

    def update_rowcount_and_fingerprint(self, new_rowcount, fingerprint):
        self.m_rowcount = new_rowcount
        if fingerprint == self.m_fingerprint:
            if self.m_rowcount < self.m_filled_up_to_p1:
                self.m_filled_up_to_p1 = self.m_rowcount
        else:
            self.m_filled_up_to_p1 = 0


    def get_next_missing_rows(self, chunk_size):
        """
        finds the next group of missing rows
        :param chunk_size: the number of rows to request
        :return: tuple of startrow, endrow+1
        """

        self.find_earliest_missing_rows(chunk_size)
        last_idx_p1 = min(self.m_rowcount, self.m_filled_up_to_p1 + chunk_size)
        return (self.m_filled_up_to_p1, last_idx_p1)

    def find_earliest_missing_rows(self, chunk_size):
        """
        queries the database to find which rows are missing
        looks chunk_size rows at a time
        :param min_chunk_size:
        :return:
        """

        # just look for missing rows chunksize at a time.  If any are not found, mark the whole chunk for fetch
        if chunk_size < 1 or chunk_size > self.MAX_CHUNK_SIZE:
            raise ValueError("unexpected chunk size {}".format(chunk_size))

        while (self.m_filled_up_to_p1 < self.m_rowcount):
            rows_to_count = self.m_rowcount - self.m_filled_up_to_p1
            rows_to_count = min(rows_to_count, chunk_size)

            row_count = self.m_dbautomation.count_rows(self.m_tablename, self.m_fingerprint, self.m_filled_up_to_p1, rows_to_count)
            if row_count < rows_to_count:
                break

