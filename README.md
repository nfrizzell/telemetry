# Telemetry

This is a set of telemetry tools developed for the Bath County Solar Car Team by Nicholas Frizzell. As of right now it consists of the
following programs:
 
   - DBTools
       - A GUI wrapper around several PostgreSQL and command line tools to simplify database management, data retrieval and visualization, backups and restoring from a previous state, etc.
   - Telemetry
       - The actual telemetry software, which interfaces with various sensors and inputs from the car, transmits them using a LoRa radio module, then appends it to the database, which is queried to provide data information and visualization to the operator
       
       
Compatability:
   - 
   - The programs are designed to work on both Linux and Windows operating systems.
   - The arduino code was written to run on an Arduino Uno.
   - Due to the fickle nature of running a PostgreSQL instance (as well as potential security problems), a working copy of the database schema is not provided. Contact me for more info.

Dependencies:
   -
   - Arduino:
       - RadioHead
       - Arduino IDE (if Arduino programs need to be uploaded)
   - Raspberry Pi:
       - PySide2 (QT)
       - Matplotlib
       - Psycopg2
       - PostgreSQL service
       - PySerial
           
Specifications:
   - 
   - Radio frequency: 905MHz
   - Resistor values for high voltage ADC: 10k and 100k (Drop ~52V to ~4.4V)
   
   
Installation:
   -
   - PC
      - Ensure that a recent version of Python 3 is installed on the system
      - Run setup.sh. This script is designed to install all other dependencies for Linux and Windows. It also initializes the PostgreSQL database.

ToDo:
   - 
   - Fix dbtools to work on Windows; currently there is a trivial issue with backslashes that I need to fix.
   - Add code comments and make documentation better overall
   - Enable editing of program settings from within the application, without needing to manually edit the XML & settings files.
   - Test the backup and restore functionalities of the dbtools program more thoroughly
