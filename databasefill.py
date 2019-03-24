class DatabaseFill:
    """
    keeps track of which rows in the database are present

    always starts from the beginning of the dataset and fills upwards

    """

    m_dbautomation
    m_rowcount = 0
    m_filled_up_to_p1 = 0

    def update_rowcount(self, new_rowcount):
        self.m_rowcount = new_rowcount
        if self.m_rowcount < self.m_filled_up_to_p1:
            self.m_filled_up_to_p1 = self.m_rowcount

    def get_next_missing_rows(self, chunk_size):
        """
        finds the next group of missing rows
        :param chunk_size: the number of rows to request
        :return: tuple of startrow, endrow+1
        """

        last_idx_p1 = min(self.m_rowcount, self.m_filled_up_to_p1 + chunk_size)
        return (self.m_filled_up_to_p1, last_idx_p1)

    def find_earliest_missing_rows(self, min_chunk_size):

        rows_to_count = self.m_rowcount - self.m_filled_up_to_p1

        num_of_rows = self.m_dbautomation.count_rows(self.m_filled_up_to_p1, self.m_rowcount)

        if num_of_rows == rows_to_count:



