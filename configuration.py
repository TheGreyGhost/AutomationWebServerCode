import configparser
import errorhandler
from enum import Enum

StorageTypes = Enum("StorageTypes", "REALTIME HISTORY SETTINGS TERMINAL")

DEF_CONFIGURATION_FILE = r"/home/pi/automationwebserver.ini"

class Configuration:
    """
        Holds configuration information stored on file:
        - database name, password, table name for each information type

    """

    config = configparser.ConfigParser()
    path = DEF_CONFIGURATION_FILE

    def initialise_from_file(self, filename=DEF_CONFIGURATION_FILE):
        self.path = filename
        self.config.read(filename)

    def listall(self):
        retval = ""
        for section_name, section_data in self.config.items():
            retval += section_name + ":"
            retval += str(self.config.items(section_name))
            retval += "\n"
        return retval

    def get_file_path(self):
        return self.path

    @staticmethod
    def get_default():
        """
        provides the default text of the ini file
        :return: a ConfigParser initialised to the structure
        """
        default_config = configparser.ConfigParser(allow_no_value=True)

        default_config.add_section("General")
        general = default_config["General"]
        general["PermanentLogPath"] = r"/home/pi/automationwebserver.log"
        general["TempLogPath"] = r"/var/ramdrive/test.txt"

        default_config.add_section("ArduinoLink")
        arduino = default_config["ArduinoLink"]
        arduino["ArdIPAddress"] = "192.168.2.35"
        arduino["ArdTerminalPort"] = "53201"
        arduino["ArdDatastreamPort"] = "53202"
        arduino["RPiIPAddress"] = "192.168.2.34"
        arduino["RpiTerminalPort"] = "53201"
        arduino["RpiDatastreamPort"] = "53202"

        default_config.add_section("Databases")
        databases = default_config["Databases"]
        databases["HostAddress"] = "localhost"
        databases["HostPort"] = "3306"
        default_config['REALTIME'] = {'databasename': 'testname', 'user': 'testuser',
                                      'password': 'testpassword', 'tablename': 'realtime'}
        default_config['HISTORY'] = {'databasename': 'testname', 'user': 'testuser',
                                     'password': 'testpassword', 'tablename': 'history'}

        default_config.add_section("DataTransfer")
        default_config.set("DataTransfer", r"# see https://docs.python.org/3.6/library/struct.html#struct.unpack", None)
        datatransfer = default_config["DataTransfer"]
        datatransfer["ProtocolVersion"] = 'a'
        default_config["SensorReadings"] = {"unpackformat": "<Hff?fffffffffff",
                                                "fieldnames":
                                                    "sim_flags solar_intensity cumulative_insolation"\
                                                    " surge_tank_ok pump_runtime"\
                                                    " hx_hot_inlet_inst hx_hot_inlet_smooth"\
                                                    " hx_hot_outlet_inst hx_hot_outlet_smooth"\
                                                    " hx_cold_inlet_inst hx_cold_inlet_smooth"\
                                                    " hx_cold_outlet_inst hx_cold_outlet_smooth"\
                                                    " temp_ambient_inst temp_ambient_smooth"
                                                }

        return default_config

    @staticmethod
    def generate_file_if_doesnt_exist(filename=DEF_CONFIGURATION_FILE):
        default_config = Configuration.get_default()
        with open(filename, 'x') as configfile:
            default_config.write(configfile)

    @property
    def get(self):
        return self.config



