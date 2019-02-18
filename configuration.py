import configparser
import errorhandler
from enum import Enum

StorageTypes = Enum("StorageTypes", "REALTIME HISTORY SETTINGS TERMINAL")

class Configuration:
    """
        Holds configuration information stored on file:
        - database name, password, table name for each information type

    """

    config = configparser.ConfigParser()
    path = None

    def initialise_from_file(self, filename):
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

    @property
    def get(self):
        return self.config



