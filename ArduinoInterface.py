import socket
import errorhandler
import select

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

    MAX_EXPECTED_MSG_SIZE = 1024

    def __init__(self, ip_rpi, ip_arduino,
                 port_rpi_terminal, port_arduino_terminal, port_rpi_datastream, port_arduino_datastream):

        self.socket_datastream = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket_datastream.bind((ip_rpi, port_rpi_datastream))
        self.ip_port_arduino_datastream = (ip_arduino, port_arduino_datastream)

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
        self.socket_datastream.sendto("!r", self.ip_port_arduino_datastream)
        self.socket_datastream.sendto("!s", self.ip_port_arduino_datastream)

    def check_for_incoming_info(self):
        """
           Checks for any incoming information and processes if found
        :return:
        """
        POLL_ONLY_TIMEOUT_VALUE = 0
        while (True):
            readables, writables, errors = select.select([self.socket_datastream], [], [], POLL_ONLY_TIMEOUT_VALUE)
            if not self.socket_datastream in readables:
                return
            data, remote_ip_port = serverSock.recvfrom(MAX_EXPECTED_MSG_SIZE)
            if remote_ip_port != self.ip_port_arduino_datastream:
                errorhandler.loginfo("Unexpected msg from {}".format(remote_ip_port))
            else:
                parse_incoming_message(data)



