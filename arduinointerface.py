import socket
import errorhandler
import select
import struct
from collections import namedtuple
from configuration import Configuration
from dbautomation import DBautomation
import math

MAX_EXPECTED_MSG_SIZE = 1024

class Arduino:
    """
        Communicates with the arduino to retrieve data and send commands

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
!r = request current sensor information (readings)
!s = system status
!p = request parameter information
!l{dword row nr}{word count} in LSB first order = request entries from log file
!n = request number of entries in log file
!c = cancel transmissions (log file)

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
!l -> the byte stream from the log file itself, one entry per packet
!n -> dword number of entries in log file

The final byte in the packet is {byte status: 0 = ok, else error code}
Each response is a single UDP packet only.

*/


    """

    socket_terminal = None
    socket_datastream = None

    ip_port_arduino_datastream = None
    configuration = None
    protocol_version = None

    db_realtime = None
    db_history = None

    max_realtime_rows = 1
    test_message_response = None

    def __init__(self, i_configuration):
        self.configuration = i_configuration
        arduinolink = i_configuration.get["ArduinoLink"]
        ip_rpi = arduinolink["RPiIPAddress"]
        port_rpi_terminal= arduinolink.getint("RPiTerminalPort")
        port_rpi_datastream = arduinolink.getint("RPiDatastreamPort")

        ip_arduino = arduinolink["ArdIPAddress"]
        port_arduino_terminal= arduinolink.getint("ArdTerminalPort")
        port_arduino_datastream = arduinolink.getint("ArdDatastreamPort")

        self.socket_datastream = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket_datastream.bind((ip_rpi, port_rpi_datastream))
        self.ip_port_arduino_datastream = (ip_arduino, port_arduino_datastream)

        self.protocol_version = i_configuration.get["DataTransfer"]["ProtocolVersion"]

        database_info = i_configuration.get["Databases"]
        realtime_info = i_configuration.get["REALTIME"]
        history_info = i_configuration.get["HISTORY"]
        self.db_realtime = DBautomation(realtime_info["user"], realtime_info["password"], database_info["HostAddress"],
                                        database_info.getint("HostPort"), realtime_info["databasename"]
                                        )
        self.max_realtime_rows = realtime_info.getint("max_rows")

        self.db_history = DBautomation(history_info["user"], history_info["password"], database_info["HostAddress"],
                                        database_info.getint("HostPort"), history_info["databasename"]
                                        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # make sure the objects get closed
        if not self.socket_datastream is None:
            self.socket_datastream.close()
        if not self.socket_terminal is None:
            self.socket_terminal.close()

    def request_realtime_info(self):
        """
           Asks the arduino to send the current status information and sensor information.  Doesn't wait for a reply.
        :return:
        """
        self.socket_datastream.sendto(b"!r", self.ip_port_arduino_datastream)
        self.socket_datastream.sendto(b"!s", self.ip_port_arduino_datastream)

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
            cleaned_message = self.replace_nan_with_none(message._asdict())
            return cleaned_message
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
                                                   .format(self.protocol_version, data[2].hex()))

        if data[-1] != 0:
            raise errorhandler.ArduinoMessageError("message error code was nonzero:{}", data[-1].hex())

        if data[1:2] == b"r":
            msg = self.parse_message("SensorReadings", data[3:-1])
            table_name = self.configuration.get["SensorReadings"]["tablename"]
            self.db_realtime.write_single_row_fifo(tablename=table_name, data=msg, maxrows=self.max_realtime_rows)
        elif data[1:2] == b"s":
            msg = self.parse_message("SystemStatus", data[3:-1])
            table_name = self.configuration.get["SystemStatus"]["tablename"]
            self.db_realtime.write_single_row_fifo(tablename=table_name, data=msg, maxrows=self.max_realtime_rows)
        elif data[1:2] == b"p":
            self.parse_message("ParameterInformation", data[3:-1])
        elif data[1:2] == b"l":
            self.parse_message("LogfileEntry", data[3:-1])
        elif data[1:2] == b"n":
            self.parse_message("NumberOfLogfileEntries", data[3:-1])
        else:
            raise errorhandler.ArduinoMessageError("invalid response command letter: {}".format(data[1].hex()))

    def check_for_incoming_info(self):
        """
           Checks for any incoming information and processes if found
        :return: true if any information was received, false otherwise
        """

        if self.test_message_response:
            self.parse_incoming_message(self.test_message_response)
            return True

        POLL_ONLY_TIMEOUT_VALUE = 0
        got_at_least_one = False
        while (True):
            readables, writables, errors = select.select([self.socket_datastream], [], [], POLL_ONLY_TIMEOUT_VALUE)
            if not self.socket_datastream in readables:
                return got_at_least_one
            got_at_least_one = True
            data, remote_ip_port = self.socket_datastream.recvfrom(MAX_EXPECTED_MSG_SIZE)
            if remote_ip_port != self.ip_port_arduino_datastream:
                errorhandler.loginfo("Msg from unexpected source {}".format(remote_ip_port))
            else:
                errorhandler.logdebug("msg received:{}".format(data.hex()))
                self.parse_incoming_message(data)

#    def perform_clock_synchronisation

    def set_test_response(self, response_msg_filename):
        with open(response_msg_filename, mode='rb') as file:  # b is important -> binary
            self.test_message_response = file.read()


