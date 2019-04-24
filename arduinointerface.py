import socket
import errorhandler
import select
import struct
from collections import namedtuple
from dbautomation import DBautomation
import math
import truetime
from historicaldata import HistoricalData

MAX_EXPECTED_MSG_SIZE = 1024


class ArduinoMessager:
    """
    sends message to the Arduino
    """

    m_socket = None
    m_ip_port_arduino = None
    m_protocol_version = "A"

    def __init__(self, ip_rpi, port_rpi, ip_arduino, port_arduino, protocol_version):
        self.m_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.m_socket.bind((ip_rpi, port_rpi))
        self.m_ip_port_arduino = (ip_arduino, port_arduino)
        self.m_protocol_version = protocol_version

    def synchronise_time(self, time_and_zone):
        msg = b"!t" + self.m_protocol_version \
              + int(time_and_zone.time).to_bytes(length=4, byteorder="little", signed=False) \
              + int(time_and_zone.timezone).to_bytes(length=4, byteorder="little", signed=True)
        self.m_socket.sendto(msg, self.m_ip_port_arduino)

    def request_realtime_info(self):
        self.m_socket.sendto(b"!r" + self.m_protocol_version, self.m_ip_port_arduino)
        self.m_socket.sendto(b"!s" + self.m_protocol_version, self.m_ip_port_arduino)

    def request_row_count(self, protocol_version):
        self.m_socket.sendto(b"!n" + protocol_version, self.m_ip_port_arduino)

    def request_rows(self, first_row_idx, row_count, request_ID):
        self.m_socket.sendto(b"!l" + self.m_protocol_version +
                             request_ID.to_bytes(length=1, signed=False) +
                             first_row_idx.to_bytes(length=4, signed=False) +
                             row_count.to_bytes(length=2, signed=False),
                             self.m_ip_port_arduino)

    def check_for_incoming_msg(self):
        """
        check if there are any incoming messages from the arduino on this messager
        :return: data or None if nothing
        """
        POLL_ONLY_TIMEOUT_VALUE = 0
        readables, writables, errors = select.select([self.m_socket], [], [], POLL_ONLY_TIMEOUT_VALUE)
        if not self.m_socket in readables:
            return None
        data, remote_ip_port = self.m_socket.recvfrom(MAX_EXPECTED_MSG_SIZE)
        if remote_ip_port != self.m_ip_port_arduino:
            errorhandler.loginfo("Msg from unexpected source {}".format(remote_ip_port))
            return None

        return data


    def __exit__(self, exc_type, exc_val, exc_tb):
        # make sure the socket gets closed properly
        if not self.m_socket is None:
            self.m_socket.close()

class Arduino:
    """
        Communicates with the arduino to retrieve data and send commands
r
        The Arduino says:
        IPAddress IP_LOCAL(192, 168, 2, 35);
        IPAddress IP_REMOTE(192, 168, 2, 34);

        unsigned int PORT_LOCAL_TERMINAL = 53201;      // local port to listen on
        unsigned int PORT_REMOTE_TERMINAL = 53201;      // remote port to send to

        unsigned int PORT_LOCAL_DATASTREAM = 53202;      // local datastream port to listen on
        unsigned int PORT_REMOTE_DATASTREAM = 53202;      // remote port to send datastream to

        It does this asynchronously:
        periodically asks for an update, and then periodically reads all datagrams which have arrived

Datastream commands:
/*
!r{version} = request current sensor information (readings)
!s{version} = system status
!p{version} = request parameter information
!l{version}{byte request ID}{dword row nr}{word count} in LSB first order = request entries from log file
!n{version} = request number of entries in log file
!c{version} = cancel transmissions (log file)

response:
!{command letter echoed}{byte version} then:

for sensor readings:
native byte stream of
  uint flags of vbles being simulated
  solar intensity
  cumulative insolation
  surge tank level
  pump runtime
  for each temp probe: instant temp then smoothed temp
invalid values are sent as NAN

for system status
native byte stream of
  assert error
  real time clock status
  log file status
  ethernet status (duh)
  solar sensor status
  temp probe statuses
  pump status

for parameter:
native byte stream of all EEPROM settings

for logfile:
!l -> the byte stream from the log file itself, one entry per packet:
  !d{byte request ID}{dword row nr}{native byte stream of:
        // timestamp; min, avg, max for each temp probe; cumulative insolation; cumulative pump runtime (s); averaged surge tank level; pumpState
        const unsigned long DATALOG_BYTES_PER_SAMPLE = sizeof(long) + NUMBER_OF_PROBES * 3 * sizeof(float) + sizeof(float) + sizeof(float) + sizeof(float) + sizeof(PumpState);
  and finally:
  !l{byte request ID} when byte stream is finished
!n{dword number of entries in log file}
!c{byte request ID}

The final byte in the packet is {byte status: 0 = ok, else error code}
Each response is a single UDP packet only.

*/


    """
    m_messager_datastream = None

 #   socket_terminal = None
 #   socket_datastream = None

    ip_port_arduino_datastream = None
    configuration = None
    protocol_version = None

    db_realtime = None
#    db_history = None
    m_historicaldata = None

    max_realtime_rows = 1
    test_message_response = None
    true_time = None		

    def __init__(self, i_configuration):
        self.configuration = i_configuration

        self.protocol_version = bytes(i_configuration.get["DataTransfer"]["ProtocolVersion"][0], 'utf-8')

        arduinolink = i_configuration.get["ArduinoLink"]
        ip_rpi = arduinolink["RPiIPAddress"]
        port_rpi_terminal= arduinolink.getint("RPiTerminalPort")
        port_rpi_datastream = arduinolink.getint("RPiDatastreamPort")

        ip_arduino = arduinolink["ArdIPAddress"]
        port_arduino_terminal= arduinolink.getint("ArdTerminalPort")
        port_arduino_datastream = arduinolink.getint("ArdDatastreamPort")

        self.m_messager_datastream = ArduinoMessager(ip_rpi, port_rpi_datastream,
                                                     ip_arduino, port_arduino_datastream,
                                                     self.protocol_version)

        # self.socket_datastream = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # self.socket_datastream.bind((ip_rpi, port_rpi_datastream))
        # self.ip_port_arduino_datastream = (ip_arduino, port_arduino_datastream)

        database_info = i_configuration.get["Databases"]
        realtime_info = i_configuration.get["REALTIME"]
        history_info = i_configuration.get["HISTORY"]
        self.db_realtime = DBautomation(realtime_info["user"], realtime_info["password"], database_info["HostAddress"],
                                        database_info.getint("HostPort"), realtime_info["databasename"]
                                        )
        self.max_realtime_rows = realtime_info.getint("max_rows")

        # self.db_history = DBautomation(history_info["user"], history_info["password"], database_info["HostAddress"],
        #                                database_info.getint("HostPort"), history_info["databasename"]
        #                                )
        truetime_info = i_configuration.get["TimeServer"]
        self.true_time = truetime.TrueTime(truetime_info.getint("max_timeout_seconds"))


    # def __enter__(self):
    #     return self

    # def __exit__(self, exc_type, exc_val, exc_tb):
    #     # make sure the objects get closed
    #     if not self.socket_datastream is None:
    #         self.socket_datastream.close()
    #     if not self.socket_terminal is None:
    #         self.socket_terminal.close()

    def set_historicaldata(self, i_historicaldata):
        self.m_historicaldata = i_historicaldata

    def request_realtime_info(self):
        """
           Asks the arduino to send the current status information and sensor information.  Doesn't wait for a reply.
        :return:
        """
        self.m_messager_datastream.request_realtime_info()
        # self.socket_datastream.sendto(b"!r" + self.protocol_version, self.ip_port_arduino_datastream)
        # self.socket_datastream.sendto(b"!s" + self.protocol_version, self.ip_port_arduino_datastream)

    def synchronise_time(self):
        """
           Sends the current time to the Arduino to allow it to sync up.  Doesn't wait for a reply.
        :return: true for success, false if the time isn't available
        """
        try:
            time_and_zone = self.true_time.get_true_time()
            self.m_messager_datastream.synchronise_time(time_and_zone)
            # msg = b"!t" + self.protocol_version \
            #       + int(time_and_zone.time).to_bytes(length=4, byteorder="little", signed=False) \
            #       + int(time_and_zone.timezone).to_bytes(length=4, byteorder="little", signed=True)
            # self.socket_datastream.sendto(msg, self.ip_port_arduino_datastream)
        except truetime.TimeServerError as e:
            return False

    def replace_nan_with_none(self, message):
        for key, value in message.items():
            if type(value) is float and math.isnan(value):
                message[key] = None

    def parse_message(self, structname, data):
        """
        :param structname: the name of the structure used for the message (to be retrieved from configuration)
        :param data: the binary data stream
        :return: ordered dict of the message fields
        """
        try:
            structinfo = self.configuration.get[structname]
            message_struct = namedtuple(structname, structinfo["fieldnames"])
            message = message_struct._make(struct.unpack(structinfo["unpackformat"], data))
            errorhandler.logdebug("unpacked message:{}".format(repr(message)))
            clean_message = message._asdict()
            self.replace_nan_with_none(clean_message)
            errorhandler.logdebug("cleaned message:{}".format(repr(clean_message)))
            return clean_message
        except struct.error as e:
            raise errorhandler.ArduinoMessageError("invalid msg for {}:{}".format(structname, str(e)))

    def parse_incoming_message(self, data):
        """
         response:
        !{command letter echoed}{byte version} then:
        """
        if len(data) < 3:
            raise errorhandler.ArduinoMessageError("msg too short")
        if data[0:1] != b"!":
            raise errorhandler.ArduinoMessageError("msg didn't start with !")
        if data[2] != ord(self.protocol_version):
            raise errorhandler.ArduinoMessageError("protocol mismatch: expected {} received 0x{}"
                                                   .format(self.protocol_version, hex(data[2])))

        if data[-1] != 0:
            raise errorhandler.ArduinoMessageError("message error code was nonzero:{}", hex(data[-1]))

        if data[1:2] == b"r":
            msg = self.parse_message("SensorReadings", data[3:-1])
            table_name = self.configuration.get["SensorReadings"]["tablename"]
            self.db_realtime.write_single_row_fifo(tablename=table_name, data=msg, maxrows=self.max_realtime_rows)
        elif data[1:2] == b"s":
            msg = self.parse_message("SystemStatus", data[3:-1])
            table_name = self.configuration.get["SystemStatus"]["tablename"]
            self.db_realtime.write_single_row_fifo(tablename=table_name, data=msg, maxrows=self.max_realtime_rows)
        elif data[1:2] == b"t":
            msg = self.parse_message("TimeSynchronisation", data[3:-1])
            errorhandler.loginfo("Time synch reply:{}".format(msg))
        elif data[1:2] == b"p":
            pass  # NOT IMPLEMENTED YET
            # self.parse_message("ParameterInformation", data[3:-1])
        elif data[1:2] == b"l":
            msg = self.parse_message("LogfileCancel", data[3:-1])
            self.m_historicaldata.received_cancel(msg["data_request_ID"])
        elif data[1:2] == b"c":
            msg = self.parse_message("LogfileComplete", data[3:-1])
            self.m_historicaldata.received_end_of_data(msg["data_request_ID"])
        elif data[1:2] == b"d":
            msg = self.parse_message("LogfileEntry", data[3:-1])
            self.m_historicaldata.received_data(msg, data[3:-1])
        elif data[1:2] == b"n":
            msg = self.parse_message("NumberOfLogfileEntries", data[3:-1])
            self.m_historicaldata.received_rowcount(msg["data_request_ID"])
        else:
            raise errorhandler.ArduinoMessageError("invalid response command letter: {}".format(hex(data[1])))

    def check_for_incoming_info(self):
        """
           Checks for any incoming information and processes if found
        :return: true if any information was received, false otherwise
        """

        if self.test_message_response:
            self.parse_incoming_message(self.test_message_response)
            return True

        got_at_least_one = False
        MAX_ITERATIONS = 50
        for i in range(MAX_ITERATIONS):
            data = self.m_messager_datastream.check_for_incoming_msg()
            if data is None:
                return got_at_least_one
            got_at_least_one = True
            errorhandler.logdebug("msg received:{}".format(data.hex()))
            self.parse_incoming_message(data)
        return got_at_least_one

    def set_test_response(self, response_msg_filename):
        with open(response_msg_filename, mode='rb') as file:  # b is important -> binary
            self.test_message_response = file.read()


