import datetime
from xml.etree import ElementTree


class Parser:
    # Returns the XML file in DOM/tree form
    @staticmethod
    def parse_xml(section):
        path = "Parameters.xml"
        xml_tree = ElementTree.parse(path)
        root = xml_tree.getroot()

        if section == "Modules":
            return Parser.parse_modules(root.find(section))
        elif section == "Settings":
            return Parser.parse_SETTINGS(root.find(section))
        else:
            raise ValueError("Section key not supported")

    # Extracts useful information from the tree 
    @staticmethod
    def parse_modules(tree):
        all_module_data = {}
        for module in tree:
            individual_module_data = module.attrib
            for sensor in module:
                sensor_data = sensor.attrib
                individual_module_data[sensor.tag] = sensor_data
            all_module_data[module.tag] = individual_module_data
        return all_module_data

    # Extracts key/value pairs from the separate "settings.txt" file
    @staticmethod
    def load_settings():
        settings = {}
        with open("./settings.txt") as file:
            for line in file:
                line = line.strip()  # Remove newline character
                key, value = line.split("=")
                settings[key] = value
        return settings


class Logger:
    # Simple logging tool, haven't put to use yet
    @staticmethod
    def log_data(data):
        path = "Data/ClientLog.txt"
        with open(path, 'a') as file:
            timestamp = datetime.datetime.now()
            file.write("{0} :: {1}".format(data, timestamp) + '\n')

