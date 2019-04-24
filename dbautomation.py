import mysql.connector
import errorhandler
import time
import debugdefines

class DBautomation:
    m_cnx_fifo = None
    m_cnx_trans = None
    m_cnx_select = None
    m_cursor_fifo = None   # cursor for one-row-at-a-time addition
    m_cursor_trans = None  # cursor for transaction-based row addition
    m_tablename_trans = None # table for the current transaction-based row additions

    def __init__(self, username, dbpassword, host, port, dbname):
        try:
            self.m_cnx_fifo = mysql.connector.connect(host=host,  # your host, usually localhost
                                                      port=port,
                                                      user=username,  # your username
                                                      passwd=dbpassword,  # your password
                                                      db=dbname,
                                                      use_pure=True) #use_pure=true to prevent bug https://bugs.mysql.com/bug.php?id=90585
            self.m_cnx_fifo.autocommit = False
            self.m_cursor_fifo = self.m_cnx_fifo.cursor(buffered=True, named_tuple=True)
            #buffered=True to prevent mysql.connector.errors.InternalError: Unread result found.

            self.m_cnx_trans = mysql.connector.connect(host=host,  # your host, usually localhost
                                                       port=port,
                                                       user=username,  # your username
                                                       passwd=dbpassword,  # your password
                                                       db=dbname,
                                                       use_pure=True) #use_pure=true to prevent bug https://bugs.mysql.com/bug.php?id=90585
            self.m_cnx_trans.autocommit = False
            self.m_cursor_trans = self.m_cnx_trans.cursor(buffered=True, named_tuple=True)
            # buffered=True to prevent mysql.connector.errors.InternalError: Unread result found.

            self.m_cnx_select = mysql.connector.connect(host=host,  # your host, usually localhost
                                                        port=port,
                                                        user=username,  # your username
                                                        passwd=dbpassword,  # your password
                                                        db=dbname,
                                                        use_pure=True) #use_pure=true to prevent bug https://bugs.mysql.com/bug.php?id=90585

        except mysql.connector.Error as err:
            errorhandler.logerror(err)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # make sure the objects get closed
        if self.m_cursor_fifo is not None:
            self.m_cursor_fifo.close()
        if self.m_cnx_fifo is not None:
            self.m_cnx_fifo.close()

        if self.m_cursor_trans is not None:
            self.m_cursor_trans.close()
        if self.m_cnx_trans is not None:
            self.m_cnx_trans.close()

    def start_transaction(self, tablename):
        """
        Prepare for a transaction to add multiple rows
        Can only have one transaction running at once.
        :param tablename: the table to insert rows into
        :return:
        """
        if self.m_cursor_trans is not None:
            self.m_cursor_trans.close()
            self.m_cursor_trans = None
            self.m_cnx_trans.rollback()
            errorhandler.logwarn("Tried to start a new transaction when the previous one was still open, rolled back")

        self.m_cursor_trans = self.m_cnx_trans.cursor(buffered=True, named_tuple=True)
        self.m_tablename_trans = tablename

    def add_data_to_transaction(self, data):
        """
        adds a single row of data to the currently-in-progress transaction
        if row is already in the db, ignore
        :param data: dictionary of row to add
        :return:
        """
        if self.m_cursor_trans is None:
            errorhandler.logwarn("Tried to add data to transaction which isn't open")
        else:
            try:
                firstentry = True
                for key, value in data.items():
                    if firstentry:
                        fieldnames = key
                        values = "%(" + key + ")s"
                        firstentry = False
                    else:
                        fieldnames = fieldnames + "," + key
                        values = values + "," + "%(" + key + ")s"
                insertSQL = "INSERT IGNORE INTO {tablename} ({fieldnames}) VALUES ({values});" \
                    .format(tablename=self.m_tablename_trans, fieldnames=fieldnames, values=values)
                if debugdefines.sql:
                    errorhandler.logdebug("INSERT:{}".format(insertSQL))
                self.m_cursor_trans.execute(insertSQL, data)

            except mysql.connector.Error as err:
                errorhandler.logdebug("Might be related to insertSQL which is:{}".format(insertSQL))
                raise

    def end_transaction(self):
        if self.m_cursor_trans is None:
            errorhandler.logwarn("Tried to end transaction which isn't open")
            return
        self.m_cursor_trans.close()
        self.m_cnx_trans.commit()

    def execute_select_fifo(self, selectSQL):
        """
        execute the given select statement
        :return: results of the query
        """
        cursor = self.m_cnx_fifo.cursor(buffered=True, named_tuple=True)
        result = cursor.execute(selectSQL)
        cursor.close()
        return result

    def write_single_row_fifo(self, tablename, data, maxrows):
        """
        writes the given data into the database; overwrites the existing row
        adds an autoincrement primary key
        :param tablename: table to write into
        :param data: dictionary containing the data to be written into the db (a single row).
        :param maxrows: maximum number of rows to retain in the table
        :return:
        https://dev.mysql.com/doc/connector-python/en/connector-python-api-mysqlcursor-execute.html
        """

        timenow = time.time()
        datacopy = data.copy()
        datacopy["timestamp"] = timenow

        try:
            firstentry = True
            for key, value in datacopy.items():
                if firstentry:
                    fieldnames = key
                    values = "%(" + key + ")s"
                    firstentry = False
                else:
                    fieldnames = fieldnames + "," + key
                    values = values + "," + "%(" + key + ")s"
            insertSQL = "INSERT INTO {tablename} ({fieldnames}) VALUES ({values});"\
                .format(tablename=tablename, fieldnames=fieldnames, values=values)
            if debugdefines.sql:
                errorhandler.logdebug("INSERT:{}".format(insertSQL))
            self.m_cursor_fifo.execute(insertSQL, datacopy)

            findrowcountSQL = "SELECT entry_number FROM {tablename} "\
                    " ORDER BY entry_number DESC LIMIT {first_row_to_delete}, 1;"\
                    .format(tablename=tablename, first_row_to_delete=maxrows)
            self.m_cursor_fifo.execute(findrowcountSQL)
            youngest_row_to_delete = self.m_cursor_fifo.fetchone()
            if not youngest_row_to_delete is None:
                deleteSQL = "DELETE FROM {tablename} WHERE entry_number <= {youngest_to_delete};"\
                            .format(tablename=tablename, youngest_to_delete=youngest_row_to_delete[0])
                self.m_cursor_fifo.execute(deleteSQL)

            self.m_cnx_fifo.commit()

        except mysql.connector.Error as err:
            errorhandler.logdebug("Might be related to insertSQL which is:{}".format(insertSQL))
            raise

    def count_rows(self, tablename, fingerprint, start_row_idx, number_of_rows):
        """
        return the number of rows in the database with
        :param fingerprint: the arduino datastore fingerprint we're filling
        :param start_row_idx: row index of the first row to count
        :param number_of_rows: max # of rows to count
        :return: the number of rows between start_row_idx and start_row_idx + number_of_rows which are actually in the db
        """

        cursor = None
        try:
            cursor = self.m_cnx_select.cursor(buffered=True, named_tuple=True)
            cursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ UNCOMMITTED")
            countSQL = "SELECT COUNT(*) AS rowsfound FROM {tablename} WHERE datastore_hash = {hash}" \
                       " AND row_number BETWEEN {startrow} AND {endrow};"\
                       .format(tablename=tablename, hash=fingerprint,
                               startrow=start_row_idx, endrow=start_row_idx + number_of_rows - 1)
            cursor.execute(countSQL)
            row_count = cursor.fetchone()
            return row_count[0]

        finally:
            if cursor is not None:
                cursor.close

    def clear_all_rows(self, tablename):
        cursor = None
        try:
            cursor = self.m_cnx_select.cursor(buffered=True, named_tuple=True)
            sql = "TRUNCATE TABLE {tablename};".format(tablename=tablename)
            cursor.execute(sql)

        finally:
            if cursor is not None:
                cursor.close

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
