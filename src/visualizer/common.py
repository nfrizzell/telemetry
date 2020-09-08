import datetime
from PySide2.QtCore import Qt
import PySide2.QtCore as QtCore
from PySide2.QtGui import QColor

from utility import Parser

# Common data and settings used across various files
# All-caps variables should be treated as read-only
DEBUG = True
SETTINGS = Parser.load_settings()

seconds_since_last_packet = 0 
arduino_uptime = 0 # Number of seconds that the Arduino has been running for 
packet_received = False # Flag that tracks if a valid packet has been received since init
database_connection_status = False
arduino_connection_status = False


# Aka. the schema, groups related sensors together
class Module:
    def __init__(self, tag, module_parameters):
        self.tag = tag
        self.label = module_parameters.pop("label")
        self.sensors = self.create_sensors(module_parameters)

    def create_sensors(self, module_parameters):
        sensors = []
        for sensor in module_parameters:
            sensor_parameters = module_parameters[sensor]
            sensor_parameters["parent_tag"] = self.tag
            sensor_parameters["parent_label"] = self.label
            sensors.append(Sensor(sensor, sensor_parameters))

        return sensors


# Aka. the table, keeps track of actual data
class Sensor:
    def __init__(self, tag, sensor_parameters):
        # Stores the specified number of values as defined in the parameters markup file
        self.value_cache = [[QtCore.QDateTime.currentDateTime(), -9999]] # Error value as default

        # Tag = the unique identifier used in the markup file to identify the element
        # Label = the user-friendly name used in the GUI to identify the element
        self.tag = tag
        self.label = sensor_parameters["label"]
        self.parent_tag = sensor_parameters["parent_tag"]
        self.parent_label = sensor_parameters["parent_label"]

        # Module name + sensor name (aka. schema name + table name),
        # used for database interfacing
        self.unique_tag = ".".join([self.parent_tag, self.tag])

        # Sensor-specific "value bounds" as defined in the parameters markup file
        # Bounds are non-inclusive (e.g. a value at the bound will not count as crossing it)
        self.lower_critical_bound = float(sensor_parameters["lcb"])
        self.lower_bound = float(sensor_parameters["lb"])
        self.upper_bound = float(sensor_parameters["ub"])
        self.upper_critical_bound = float(sensor_parameters["ucb"])
        # GUI-specific variables
        self.unit = sensor_parameters["unit"]
        self.value_color = None
        self.operational = False
        self.gui_reference = None
        self.value = -9999 # Error value as default
        self.lowest_recorded_value = 9999
        self.highest_recorded_value = -9999

    # Returns the color for the value cell in the user interface based upon the range 
    # the value falls into
    def determine_value_color(self):
        normal, warning, critical, error = Qt.white, QColor(0xFF, 0x8C, 0x00), Qt.red, Qt.darkRed  # Hex color is orange
        lcb, lb, ub, ucb = self.lower_critical_bound, self.lower_bound, self.upper_bound, self.upper_critical_bound
        value_color = normal

        # Check for the range that the value falls into 
        if lb < self.value < ub:
            value_color = normal
        elif lcb < self.value < ucb:
            value_color = warning
        elif self.value == -9999:
            value_color = error
        else:
            value_color = critical

        self.value_color = value_color

    def update_data_reading(self, new_value):
        max_values_to_store = settings["PacketCacheSize"]
        # Insert at beginning to make retrieval from the list size-agnostic
        self.value_cache.insert(0, new_value)
        if len(self.value_cache) > max_values_to_store:
            self.value_cache.pop(cache_max_size - 1)


# Somewhat misleading name; derives its name from the fact that it contains all of
# the process's local data as opposed to the data stored in the separate database,
# and so doesn't require a database query to retrieve the data located in it
class Cache:
    def __init__(self):
        self.modules = {}
        # Stores a reference to each sensor which can be retrieved by its unique
        # tag (simply the module tag + the sensor tag, aka. the schema name + the
        # table name
        self.sensors = {}

        # Initialize module data
        module_xml = Parser.parse_xml("Modules")
        for module_tag in module_xml:
            self.modules[module_tag] = Module(module_tag, module_xml[module_tag])

        # Create the reference to the sensor
        for module in self.modules.values():
            for sensor in module.sensors:
                self.sensors[sensor.unique_tag] = sensor


cache = Cache()
