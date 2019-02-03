# contains all the functions for interacting with the firewall database
import mysql.connector
from mysql.connector import errorcode
import errorhandler
from errorhandler import DatabaseError
import datetime
import time

class DBautomation:
    m_db = None
    m_cursor = None   # named tuple cursor into the db which holds access information
    # m_fifo_mode = False
    # m_max_rows = 0

    def __init__(self, username, dbpassword, host, port, dbname):
        try:
            self.m_db = mysql.connector.connect(host=host,  # your host, usually localhost
                                                port=port,
                                                user=username,  # your username
                                                passwd=dbpassword,  # your password
                                                db=dbname,
                                                use_pure=True) #use_pure=true to prevent bug https://bugs.mysql.com/bug.php?id=90585

            self.m_cursor = self.m_db.cursor(buffered=True, named_tuple=True)
                #buffered=True to prevent mysql.connector.errors.InternalError: Unread result found.
        except mysql.connector.Error as err:
            errorhandler.logerror(err)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # make sure the objects get closed
        if not self.m_cursor is None:
            self.m_cursor.close()
        if not self.m_db is None:
            self.m_db.close()

    # def set_fifo_mode(self, maxrows):
    #     """
    #     turn on First In First Out with specified max number of rows; old rows are deleted as new are inserted
    #     :param maxrows: the max number of rows to retain
    #     :return: none
    #     """
    #     self.m_fifo_mode = True
    #     self.m_max_rows = maxrows

    def write_single_row_fifo(self, tablename, data, maxrows):
        """
        writes the given data into the database; overwrites the existing row
        adds an autoincrement primary key
        :param tablename: table to write into
        :param data: named tuple containing the data to be written into the db (a single row)
        :param maxrows: maximum number of rows to retain in the table
        :return:
        """
        fieldnames = ",".join(name for name in data._fields)
        values = ",".join(str(i) for i in data)
        insertSQL = "INSERT INTO {tablename} ({fieldnames}) VALUES ({values});"\
            .format(tablename=tablename, fieldnames=fieldnames, values=values)
        self.m_cursor.execute(insertSQL)

        findrowcountSQL = "SELECT entry_number FROM {tablename} "\
                " ORDER BY entry_number DESC LIMIT {first_row_to_delete}, 1;"\
                .format(tablename=tablename, first_row_to_delete=maxrows)
        self.m_cursor.execute(findrowcountSQL)
        youngest_row_to_delete = self.m_cursor.fetchone()
        if not youngest_row_to_delete is None:
            deleteSQL = "DELETE FROM {tablename} WHERE entry_number <= {youngest_to_delete};"\
                        .format(tablename=tablename, youngest_to_delete=youngest_row_to_delete[0])
            self.m_cursor.execute(deleteSQL)

        self.m_db.commit()

#     def log_common(self, tablename, logfield, entries, timestart, timefinish):
#         if self.db is None or self.cursor is None:
#             raise DatabaseError("Not connected to a database")
#         if len(entries) == 0:
#             return
#         sqlstringparts = ["INSERT INTO {0} ({1}, count, timestart, timefinish) "
#                           "VALUES".format(tablename, logfield)]
#         separator = " "
#         for k, v in entries.items():
#             sqlstringparts.append("{0}('{1}', {2}, '{3}', '{4}')".format(separator, k, v, timestart, timefinish))
#             separator = ","
#         sqlstringparts.append(";")
#         sqlstring = "".join(sqlstringparts)
#         self.cursor.execute(sqlstring)
#         self.db.commit()
#
#     def getknown_macs(self):
#         """ returns a list of all known MAC addresses on the network
#
#         :return: list of mac addresses in the format 08:60:6e:42:f0:fb
#         :raises: DatabaseError
#         """
#         if self.db is None or self.cursor is None:
#             raise DatabaseError("Not connected to a database")
#
#         self.cursor.execute("SELECT MAC FROM clients")
#
#         allmacs = self.cursor.fetchall()
#         if allmacs is None:
#             return None
#         allmacslist = [i.MAC for i in allmacs]
#         return allmacslist
#
#     def getknown_mac_ips(self):
#         """ returns a list of all known mac+IP addresses on the network
#
#         :return: list of mac addresses with IP in the format 08:60:6e:42:f0:fb=192.168.1.3
#         :raises: DatabaseError
#         """
#         if self.db is None or self.cursor is None:
#             raise DatabaseError("Not connected to a database")
#
#         self.cursor.execute("SELECT MAC, IP4 FROM clients")
#
#         allmacips = self.cursor.fetchall()
#         if allmacips is None:
#             return None
#         allmacipslist = ["{0}={1}".format(i.MAC, i.IP4) for i in allmacips]
#         return allmacipslist
#
#
#     def getaccess(self, macaddress, datetimenow):
#         """  Returns the current access for the given MAC address at the given time
#
#         :param macaddress: in the format 08:60:6e:42:f0:fb
#         :param datetimenow: current date+time (datetime object)
#         :return: true if the MAC currently has access, false otherwise
#         :raises: DatabaseError
#         """
#
# #        Logic:
# #            1) check owner: if blocked/unblocked, apply.  Else:
# #            2) check client: if blocked/unblocked, apply.  Else:
# #            3) check timetable - first for owner, if none then check device.  If neither:
# #               TODO: If whitelist, check whitelist IPs.
# #            4) use global default
#
#         if self.db is None or self.cursor is None:
#             raise DatabaseError("Not connected to a database")
#
#         self.cursor.execute("SELECT * FROM qryClientAccess WHERE MAC='{}'".format(macaddress))
#
#         # if we don't know this MAC, or the device has no owner, use reserved entry in owners table: unknown
#         clientrow = self.cursor.fetchone()
#         if clientrow is None or clientrow.ownerstatus is None:
#             ownername = self.UNKNOWN_MAC_OWNER_NAME
#             self.cursor.execute("SELECT * FROM owners WHERE name='{}'".format(ownername))
#             ownerrow = self.cursor.fetchone()
#             if ownerrow is None:
#                 raise DatabaseError("'unknown' owner {} not found in database".format(ownername))
#             owneraccess = self.checkowner(ownerrow.status, ownerrow.endtime, datetimenow, ownerrow.timetable)
#             if clientrow is None:
#                 return owneraccess[0]
#         else:
#             owneraccess = self.checkowner(clientrow.ownerstatus, clientrow.ownerendtime, datetimenow,
#                                            clientrow.ownertimetable)
#
#         clientaccess = self.checkclient(clientrow.clientstatus, clientrow.clientendtime, datetimenow, clientrow.clienttimetable)
#         return owneraccess[0] if owneraccess[1] < clientaccess[1] else clientaccess[0]
#
#     def checkclient(self, clientstatus, clientendtime, datetimenow, timetable):
#         """ Check if the named client has access or not.
#
#         :param clientstatus: the status of the owner ('Default','BlockedUntil','UnblockedUntil','Timetable')
#         :param clientendtime: for 'BlockedUntil' or 'UnblockedUntil', the end time of the status, in datetime
#         :param datetimenow: the current date+time (datetime object)
#         :param timetable: the name of the timetable to be applied (Null = no timetable)
#         :returns a tuple: (access, priority) where access==true if access is permitted, and blocking priority:
#         :raises DatabaseError
#         """
#
#         #        Logic:
#         #            1) if blocked/unblocked and time hasn't expired, apply it, otherwise fall back to timetable or default
#         if clientstatus == "BlockedUntil" or clientstatus == "UnblockedUntil":
#
#             if (datetimenow < clientendtime):
#                 return (False, self.BLOCKING_PRIORITY_CLIENT_EXPLICIT) if clientstatus == "BlockedUntil" \
#                     else (True, self.BLOCKING_PRIORITY_CLIENT_EXPLICIT)
#
#             clientstatus2 = "Default" if timetable is None else "Timetable"
#         else:
#             clientstatus2 = clientstatus
#
#         #   2) Use Default or timetable to find access
#         if clientstatus2 == "Default":
#             return (self.DEFAULT_ACCESS, self.BLOCKING_PRIORITY_CLIENT_DEFAULT)
#         elif clientstatus2 == "Timetable":
#             # TODO look up timetable
#             return (False, self.BLOCKING_PRIORITY_CLIENT_TIMETABLE)
#         else:
#             raise (DatabaseError("Invalid clientstatus:{}".format(clientstatus)))
#
#
#     def checkowner(self, ownerstatus, ownerendtime, datetimenow, timetable):
#         """ Check if the named owner has access or not.
#
#         :param ownerstatus: the status of the owner ('Default','BlockedUntil','UnblockedUntil','Timetable')
#         :param ownerendtime: for 'BlockedUntil' or 'UnblockedUntil', the end time of the status, in datetime format
#         :param datetimenow: the current date+time (datetime object)
#         :param timetable: the name of the timetable to be applied (Null = no timetable)
#         :returns a tuple: (access, priority) where access==true if access is permitted, and blocking priority:
#         :raises DatabaseError
#         """
#
#     #        Logic:
#     #            1) if blocked/unblocked and time hasn't expired, apply it, otherwise fall back to timetable or default
#         if ownerstatus == "BlockedUntil" or ownerstatus == "UnblockedUntil":
#             timevalid = False
#             if (datetimenow < ownerendtime):
#                 return (False, self.BLOCKING_PRIORITY_OWNER_EXPLICIT) if ownerstatus == "BlockedUntil" \
#                                                                       else (True, self.BLOCKING_PRIORITY_OWNER_EXPLICIT)
#             ownerstatus2 = "Default" if timetable is None else "Timetable"
#         else:
#             ownerstatus2 = ownerstatus
#
#     #   2) Use Default or timetable to find access
#         if ownerstatus2 == "Default":
#             return (self.DEFAULT_ACCESS, self.BLOCKING_PRIORITY_OWNER_DEFAULT)
#         elif ownerstatus2 == "Timetable":
#             #TODO look up timetable
#             return (False, self.BLOCKING_PRIORITY_OWNER_TIMETABLE)
#         else:
#             raise(DatabaseError("Invalid ownerstatus:{}".format(ownerstatus)))
#
#     def testconnection(self, sqlstring="SELECT * FROM clients LIMIT 3"):
#         if self.db is None or self.cursor is None:
#             raise DatabaseError("Not connected to a database")
#
#         # Use all the SQL you like
#         self.cursor.execute(sqlstring)
#
#         # print all the first cell of all the rows
#         for row in self.cursor.fetchall():
#             print(row[0:])
#
#     def log_unknown_MACs(self, entries, timestart, timefinish):
#         self.log_common("unknown_macs_log", "mac", entries, timestart, timefinish)
#
#     def log_unknown_IPs(self, entries, timestart, timefinish):
#         self.log_common("unknown_ips_log", "ip", entries, timestart, timefinish)
#
#     def log_IP_traffic_in(self, entries, timestart, timefinish):
#         self.log_common("ip_traffic_in_log", "ip_src_and_dest", entries, timestart, timefinish)
#
#     def log_IP_traffic_out(self, entries, timestart, timefinish):
#         self.log_common("ip_traffic_out_log", "ip_src_and_dest", entries, timestart, timefinish)
#
#     def log_dropped_traffic(self, entries, timestart, timefinish):
#         self.log_common("dropped_traffic", "ip_src_and_dest", entries, timestart, timefinish)
#
#     def log_common(self, tablename, logfield, entries, timestart, timefinish):
#         if self.db is None or self.cursor is None:
#             raise DatabaseError("Not connected to a database")
#         if len(entries) == 0:
#             return
#         sqlstringparts = ["INSERT INTO {0} ({1}, count, timestart, timefinish) "
#                           "VALUES".format(tablename, logfield)]
#         separator = " "
#         for k, v in entries.items():
#             sqlstringparts.append("{0}('{1}', {2}, '{3}', '{4}')".format(separator, k, v, timestart, timefinish))
#             separator = ","
#         sqlstringparts.append(";")
#         sqlstring = "".join(sqlstringparts)
#         self.cursor.execute(sqlstring)
#         self.db.commit()
