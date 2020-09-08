import random
import time

import psycopg2
import psycopg2.sql as sql
import serial
import serial.tools.list_ports
from sys import platform

from PySide2.QtCore import QTimer

import common

"""
Database Model:

    - Each module (group of sensors) is its own schema

    - Each sensor has its own table located in its parent's schema (prefix its name with the schema name to access it)

    - Tables look something like this:
    
                 ~~ Battery Voltage ~~
        +---------+---------------------+-------+
        | Entry # |      Timestamp      | Value |
        +---------+---------------------+-------+
        |       1 | 2019-03-26 17:50:30 |  5.11 |
        |       2 | 2019-03-26 17:50:31 |  5.09 |
        |       3 | 2019-03-26 17:50:32 |  5.12 |
        +---------+---------------------+-------+
    
    ~~~~~~~~~~~~~~~~
    telemetry=> select column_name, data_type from information_schema.columns where table_name = 'voltage';
    column_name |        data_type
    -------------+--------------------------
    id          | integer (actually a serial primary key but i guess that's metadata or something)
    timestamp   | timestamp with time zone
    value       | numeric
    ~~~~~~~~~~~~~~~~
"""


class DatabaseConnection:
    def __init__(self, client):
        self.client = client
        self.dbname = common.SETTINGS["DatabaseName"]
        self.role = common.SETTINGS["DatabaseRole"]
        # Storing password locally isn't a security concern because it shouldn't be open to outside connections
        self.password = common.SETTINGS["DatabasePassword"]

        self.connection = None
        self.cursor = None

        # Attempt to connect the number of times specified in the parameters/SETTINGS file
        for attempt in range(0, int(common.SETTINGS["DatabaseConnectionAttempts"])):
            try:
                self.attempt_connection()
                common.database_connection_status = True
                break
            except psycopg2.DatabaseError as error:
                if attempt == int(common.SETTINGS["DatabaseConnectionAttempts"]):
                    print("Database connection failed. Application will proceed to open but functionality will be limited.")
                    break

                print(f"Connection failed, {int(common.SETTINGS['DatabaseConnectionAttempts']) - attempt - 1}"
                      f" attempts left. Error: ", error)

        self.serial_reader = SerialReader(self)

    # Attempt to make a connection to the locally-hosted Postgres database process
    def attempt_connection(self):
        # Linux specific
        if platform == "linux":
            self.connection = psycopg2.connect(dbname=self.dbname, user=self.role, host="/tmp")

        # Windows specific 
        elif platform == "win32" or platform == "cygwin":
            self.connection = psycopg2.connect(dbname=self.dbname, user=self.role)
            self.cursor = self.connection.cursor()

        else:
            print("Operating system not supported.")

    # Retrieve the specified number of rows from a single table
    def query_individual_table(self, schema, table, values=5):
        query = sql.SQL(
            """
            SELECT * FROM {0}.{1}
            ORDER BY id DESC
            """
        ).format(sql.Identifier(schema), sql.Identifier(table))
        if self.cursor:
            self.cursor.execute(query)
            try:
                return self.cursor.fetchmany(values)
            except:
                return []
        else:
            return []

    # Return the specified number of rows from all tables
    def query_all_tables(self, values=5):
        data = []
        for sensor in [sensor.name for sensor in common.sensor_id_enum]:
            schema, table = sensor.split(".")
            data.append(self.query_individual_table(schema, table, values))

        return data

    # Add a row to the specified table
    def append_value(self, schema, table, data):
        insert_query = sql.SQL(
            "INSERT INTO {0}.{1} (timestamp, value) VALUES (current_timestamp, %s)"
        ).format(
            sql.Identifier(schema), sql.Identifier(table))

        self.cursor.execute(insert_query, (data,))  # You have to add comma to make a tuple so don't remove it
        self.connection.commit()

    # Debug function to simulate incoming packets
    def insert_debug_records(self):
        for unique_tag in common.sensor_unique_tags:
            schema, table = unique_tag.split(".")
            rand_val = random.randrange(0, 50)
            self.append_value(schema, table, rand_val)


class SerialReader:
    def __init__(self, db_conn):
        self.unique_data_values = 6
        self.db_conn = db_conn
        self.client = self.db_conn.client
        self.connection = False
        self.serial = None
        self.port = None
        
        self.attempt_serial_connection()

    # Searches for and makes connection with Arduino over USB    
    def attempt_serial_connection(self):
        try:
            self.port = [port for port in serial.tools.list_ports.comports() if port.serial_number ==
                         common.SETTINGS["ArduinoUSBUID"]][0]
            self.serial = serial.Serial(self.port.device, 9600, timeout=1)
            common.arduino_connection_status = True

        except IndexError:
            print("Arduino not detected. Double check to see if it is connected to the USB port on the PC.")

        if self.serial:
            self.connection = True

    # Check if there is any new data to be read over USB
    def read(self):
        packet = self.serial.readline()
        if packet:
            if not common.packet_received:
                common.packet_received = True
            self.parse_incoming_packet(packet)
            print(packet)

    # Read and parse incoming data 
    def parse_incoming_packet(self, packet):
        packet_str = packet.decode()
        packet_str.replace(" ", "")
        data = packet_str.split(",")

        # Checks for corrupt (invalid length) and extraneous (debug message) packets
        if len(data) != self.unique_data_values:
            return

        main_battery_voltage = data[0]
        main_battery_amperage = data[1]
        aux_battery_voltage = data[2]
        dht11_temperature = data[3]
        uptime = data[4]
        rssi = data[5]

        state_of_charge_main = ((float(main_battery_voltage) - 46.04) / 4.88) * 100
        state_of_charge_aux = ((float(aux_battery_voltage) - 11.51) / 1.22) * 100

        # Truncate
        state_of_charge_main = float(int(state_of_charge_main*100)/100)
        state_of_charge_aux = float(int(state_of_charge_aux*100)/100)

        self.db_conn.append_value("main_battery", "voltage", main_battery_voltage)
        self.db_conn.append_value("main_battery", "amperage", main_battery_amperage)
        self.db_conn.append_value("main_battery", "amp_hours", str(state_of_charge_main))
        #self.db_conn.append_value("aux_battery", "state_of_charge", str(state_of_charge_aux))
        self.db_conn.append_value("aux_battery", "voltage", aux_battery_voltage)
        self.db_conn.append_value("dht11", "temperature", dht11_temperature)
        self.db_conn.append_value("rfm95", "rssi", rssi)

        common.time_since_last_packet = 0
        common.uptime = uptime

