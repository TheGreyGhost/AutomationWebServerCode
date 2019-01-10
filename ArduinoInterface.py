import socket
import errorhandler
import select
import struct
from collections import namedtuple

MAX_EXPECTED_MSG_SIZE = 1024
PROTOCOL_VERSION = 'a'
NUM_OF_TEMPERATURE_PROBES = 5

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

    def parse_sensor_readings(self, data):
        """
        native byte stream of
          uint flags of vbles being simulated (2 bytes)
          solar intensity (float)
          cumulative insolation (float)
          surge tank level (bool = 1 byte)
          pump runtime (float)
          for each temp probe: instant temp then smoothed temp.
          invalid values are sent as NAN
            const int HX_HOT_INLET = 0;
            const int HX_HOT_OUTLET = 1;
            const int HX_COLD_INLET = 2;
            const int HX_COLD_OUTLET = 3;
            const int AMBIENT = 4;

          https://docs.python.org/3.6/library/struct.html#struct.unpack
        """

        try:
            SensorReadingsStruct = namedtuple("SensorReadingsStruct",
                                              "sim_flags solar_intensity cumulative_insolation surge_tank_ok pump_runtime"\
                                              " hx_hot_inlet_inst hx_hot_inlet_smooth" \
                                              " hx_hot_outlet_inst hx_hot_outlet_smooth" \
                                              " hx_cold_inlet_inst hx_cold_inlet_smooth" \
                                              " hx_cold_outlet_inst hx_cold_outlet_smooth" \
                                              " temp_ambient_inst temp_ambient_smooth"
                                              )
            sensor_readings = SensorReadingsStruct._make(struct.unpack("<Hff?fffffffffff"))

        except struct.error as e:
            raise errorhandler.ArduinoMessageError("invalid msg:" + str(e))



  unsigned int simflags = isBeingSimulatedAll();
  dest.write((byte *)&simflags, sizeof simflags);
  float solarIntensity = NAN;
  if (!solarIntensityReadingInvalid && smoothedSolarIntensity.isValid()) {
    solarIntensity = smoothedSolarIntensity.getEWMA();
  }
  dest.write((byte *)&solarIntensity, sizeof solarIntensity);
  dest.write((byte *)&cumulativeInsolation, sizeof cumulativeInsolation);
  dest.write((byte *)&surgeTankLevelOK, sizeof surgeTankLevelOK);
  dest.write((byte *)&pumpRuntimeSeconds, sizeof pumpRuntimeSeconds);
  for (int i = 0; i < NUMBER_OF_PROBES; ++i) {
    float value = smoothedTemperatures[i].getInstantaneous();
    dest.write((byte *)&value, sizeof value);
    value = smoothedTemperatures[i].getEWMA();
    dest.write((byte *)&value, sizeof value);
  }
  return DSE_OK;

    def parse_system_status(self, data):

    def parse_parameter_information(self, data):

    def parse_logfile_entry(self, data):

    def parse_number_of_logfile_entries(self, data):

    def parse_incoming_message(self, data):
        """
         response:
        !{command letter echoed}{byte version} then:
        """
        if len(data) < 3:
            raise errorhandler.ArduinoMessageError("msg too short")
        if data[0] != "!" :
            raise errorhandler.ArduinoMessageError("msg didn't start with !")
        if data[2] != PROTOCOL_VERSION:
            raise errorhandler.ArduinoMessageError("protocol mismatch: expected {} received {}".format(PROTOCOL_VERSION, data[2]))

        if data[1] == "r":
            self.parse_sensor_readings(data[3:])
        elif data[1] == "s":
            self.parse_system_status(data[3:])
        elif data[1] == "p":
            self.parse_parameter_information(data[3:])
        elif data[1] == "l":
            self.parse_logfile_entry(data[3:])
        elif data[1] == "n":
            self.parse_number_of_logfile_entries(data[3:])
        else:
            raise errorhandler.ArduinoMessageError("invalid response command letter: {}".format(data[1]))

    def check_for_incoming_info(self):
        """
           Checks for any incoming information and processes if found
        :return: true if any information was received, false otherwise
        """
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
                self.parse_incoming_message(data)



