#
# class RowRange:
#     m_left_idx = 0
#     m_right_idx_p1 = 0
#     m_left_rowrange = None
#     m_right_rowrange = None
#     m_none_missing = False
#
#     def __int__(self, left_idx, right_idx_p1):
#         self.m_left_idx = left_idx
#         self.m_right_idx_p1 = right_idx_p1
#         self.m_none_missing = False
#
#     def expand(self, new_right_idx_p1):
#         """
#            expand the RowRange node to include the new rightmost idx
#         :param new_right_idx_p1:
#         :return:
#         """
#
#         if new_right_idx_p1 <= self.m_right_idx_p1:
#             return
#         if self.m_right_rowrange is not None:
#             self.m_right_rowrange.expand(new_right_idx_p1)
#         elif self.m_left_rowrange is not None:
#             self.m_right_rowrange.expand(new_right_idx_p1)
#         else:
#             if self.m_none_missing:
#                 self.m_right_rowrange = RowRange(self.m_right_idx_p1, new_right_idx_p1)
#             else:
#                 self.m_right_idx_p1 = new_right_idx_p1
#
#         self.m_right_idx_p1 = new_right_idx_p1
#         self.m_none_missing = False
#
#
#     def contract(self, new_right_idx_p1):
#         """
#            contract the RowRange node to move the rightmost index inwards
#         :param new_right_idx_p1:
#         :return: returns itself if the node is still required otherwise None (node is empty)
#         """
#
#         """
#         four cases:
#             no nodes, left only, right only, both
#
#         for a node:
#             >= right -> nothing
#             between left & right -> contract
#             <= left -> delete entirely
#         """
#         if new_right_idx_p1 <= self.m_left_idx:
#             return None
#         if new_right_idx_p1 >= self.m_right_idx_p1:
#             return self
#         self.m_right_idx_p1 = new_right_idx_p1
#         if self.m_right_rowrange is not None:
#             self.m_right_rowrange = self.m_right_rowrange.contract(new_right_idx_p1)
#         if self.m_left_rowrange is not None:
#             self.m_left_rowrange = self.m_left_rowrange.contract(new_right_idx_p1)
#         return self
#
#     def compress_tree(self):
#         """
#             rules to compress a node:
#             if there are two daughter nodes, and both are full (none_missing) then delete both nodes
#             if there is only one node, copy it up into this node
#         :return:
#         """
#
#         if self.m_left_rowrange is None and self.m_right_rowrange is None:
#             return
#
#         if self.m_left_rowrange is not None and self.m_right_rowrange is not None:
#             if self.m_left_rowrange.m_none_missing and self.m_right_rowrange.m_none_missing:
#                 self.m_none_missing = True
#                 self.m_left_rowrange = None
#                 self.m_right_rowrange = None
#             else:
#                 self.m_left_rowrange.compress_tree()
#                 self.m_right_rowrange.compress_tree()
#             return
#
#         if self.m_left_rowrange is not None:
#             source = self.m_left_rowrange
#         else:
#             source = self.m_right_rowrange
#
#         source.compress_tree()
#         self.m_none_missing = source.m_none_missing
#         self.m_left_idx = source.m_left_idx
#         self.m_right_idx_p1 = source.m_right_idx_p1
#         self.m_left_rowrange = source.m_left_rowrange
#         self.m_right_rowrange = source.m_right_rowrange
#
#
# class RowStatuses:
#     """
#     keeps track of which rows have been retrieved and stored
#     """
#
#     m_top_row_range = None
#
#     def __init__(self, rowcount, db_automation, tablename):
#         self.m_top_row_range = RowRange(0, rowcount)
#
#     def update_rowcount(self, newcount):
#         """
#         updates the number of rows in rowStatuses
#         :param newcount: the new number of rows
#         :return:
#         """
#         if newcount == self.m_top_row_range.m_right_idx_p1:
#             return
#         elif newcount < self.m_top_row_range.m_right_idx_p1:
#             self.m_top_row_range = self.m_top_row_range.contract(newcount)
#         else:
#             self.m_top_row_range.expand(newcount)
#
#     def rows_added
#
#     needs to have:
#     db_automation
#     name of table
#
#     update rowcount
#
#
#     check rowcount
#     recheck range; merge rowranges as possible
#
#
#
#
