import subprocess
import time
import os
from sys import platform

import psycopg2
import psycopg2.sql as sql

from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QLineEdit, QDateTimeEdit, QComboBox, QApplication, QPushButton, QMessageBox

import matplotlib.pyplot as plt


class DBTools:
    def __init__(self):
        self.qt_app = QApplication()
        self.settings = self.load_settings()
        self.db_conn = DatabaseConnection(self)

        # ===== Input fields =====

        loader = QUiLoader()
        self.main_window = loader.load("dbtools.ui")
        self.schema_input = self.main_window.findChild(QLineEdit, "schema")
        self.table_input = self.main_window.findChild(QLineEdit, "table")
        self.max_values_input = self.main_window.findChild(QLineEdit, "max_values")
        self.time_min_input = self.main_window.findChild(QDateTimeEdit, "time_min")
        self.time_max_input = self.main_window.findChild(QDateTimeEdit, "time_max")
        self.retrieve_by_input = self.main_window.findChild(QComboBox, "retrieve_by")

        # ===== Buttons =====

        self.start_up_button = self.main_window.findChild(QPushButton, "start_up")
        self.start_up_button.clicked.connect(self.start_postgres_daemon)

        self.shut_down_button = self.main_window.findChild(QPushButton, "shut_down")
        self.shut_down_button.clicked.connect(self.shut_down_postgres_daemon)

        self.connect_button = self.main_window.findChild(QPushButton, "connect")
        self.connect_button.clicked.connect(self.connect_to_database)

        self.visualize_button = self.main_window.findChild(QPushButton, "graph")
        self.visualize_button.clicked.connect(self.create_graph)

        self.export_button = self.main_window.findChild(QPushButton, "export_2")
        self.export_button.clicked.connect(self.export_as_csv)

        self.backup_button = self.main_window.findChild(QPushButton, "backup")
        self.backup_button.clicked.connect(self.backup_database)

        self.restore_button = self.main_window.findChild(QPushButton, "restore")
        self.restore_button.clicked.connect(self.restore_to_backup)
        self.main_window.show()
        self.qt_app.exec_()

    def start_postgres_daemon(self):
        command = '{0}/pg_ctl -D {1} start'.format(self.settings["postgres_binary_path"], self.settings["data_cluster_path"])
        subprocess.Popen(command, shell=True)
        self.db_conn.attempt_connection()

    def shut_down_postgres_daemon(self):
        command = '{0}/pg_ctl -D {1} stop'.format(self.settings["postgres_binary_path"], self.settings["data_cluster_path"])
        subprocess.Popen(command, shell=True)

    def connect_to_database(self):
        self.db_conn.attempt_connection()

    def create_graph(self):
        schema = self.schema_input.text()
        table = self.table_input.text()
        max_values = self.max_values_input.text()
        date_lower = self.time_min_input.dateTime().toPython()
        date_upper = self.time_max_input.dateTime().toPython()
        query_type = self.retrieve_by_input.currentText()

        results = self.db_conn.query_individual_table(schema, table, query_type, date_lower, date_upper, max_values)

        timestamps = [result[1] for result in results]
        values = [result[2] for result in results]
        plt.plot(timestamps, values)
        plt.show()

    def export_as_csv(self):
        schema = self.schema_input.text()
        table = self.table_input.text()
        max_values = self.max_values_input.text()
        date_lower = self.time_min_input.dateTime().toPython()
        date_upper = self.time_max_input.dateTime().toPython()
        query_type = self.retrieve_by_input.currentText()

        results = self.db_conn.query_individual_table(schema, table, query_type, date_lower, date_upper, max_values)
        unique_key = [result[0] for result in results]
        timestamps = [result[1] for result in results]
        values = [result[2] for result in results]

        with open(self.settings["export_path"], "w") as export_file:
            export_file.write("unique_key, timestamp, value\n")
            for idx, _ in enumerate(results):
                line = "{0},{1},{2}\n".format(unique_key[idx], timestamps[idx], values[idx])
                export_file.write(line)

    def backup_database(self, force=False):
        if not force:
            msg = QMessageBox()
            result = QMessageBox.question(msg, "Warning", "Backing up the database may take some time. "
                                                          "Do you wish to continue?", QMessageBox.Yes, QMessageBox.No)
            if result == QMessageBox.No:
                return

            command = self.settings["postgres_binary_path"] + '/pg_dump -U database telemetry > ' + self.settings["backup_path"]\
                + "/{0}.bak".format(int(time.time()))
            subprocess.Popen(command, shell=True)

            QMessageBox.information(msg, "Attention", "Enter 'teleuser' in the command prompt for password.")

    def restore_to_backup(self):
        msg = QMessageBox()
        result = QMessageBox.question(msg, "Warning", "Are you sure you wish to roll back the database to a previous backup? "
                                                      "This may take some time.", QMessageBox.Yes, QMessageBox.No)
        if result == QMessageBox.No:
            return
        else:
            result = QMessageBox.question(msg, "Warning", "Do you wish to back up the current state of the database? "
                                                          "This will take longer, but is recommended.", QMessageBox.Yes, QMessageBox.No)
            if result == QMessageBox.No:
                pass
            elif result == QMessageBox.Yes:
                self.backup_database(force=True)

        QMessageBox.information(msg, "Important", "Please move the backup you want to use into the 'backup_to_use' "
                                                  "folder. Restoring will not work if this folder is empty.")
        backup_file_name = ""

        for root, dirs, files in os.walk(self.settings["backup_path"] + "/backup_to_use"):
            if len(files) != 1:
                QMessageBox.warning(msg, "Error", "No backups present or more than one backup present. Will cancel restoration.")
                return

            for file in files:
                backup_file_name = file

        try:
            self.db_conn.connection.close()
        except:
            pass

        command1 = os.path.join(self.settings["postgres_binary_path"], "dropdb") + " -U teleuser telemetry"
        command2 = os.path.join(self.settings["postgres_binary_path"], "createdb") + " -U teleuser telemetry"
        command3 = os.path.join(self.settings["postgres_binary_path"], "psql -U teleuser -d telemetry -f ",
                                self.settings["backup_path"], "backup_to_use", backup_file_name)
        print(command1)

        subprocess.run(command1, shell=True)
        subprocess.run(command2, shell=True)
        subprocess.run(command3, shell=True)

        self.db_conn.attempt_connection()

    def load_settings(self):
        settings = {}
        with open("./settings.txt") as file:
            for line in file:
                line = line.strip()  # Remove newline character
                line = line.replace("/", os.sep)
                key, value = line.split("=")
                settings[key] = value
        return settings


class DatabaseConnection:
    def __init__(self, context):
        self.context = context
        self.dbname = "telemetry"
        self.role = "teleuser"
        self.password = "teleuser"

        self.connection = None
        self.cursor = None

        try:
            self.attempt_connection()
        except:
            print("Connection failed. Please ensure the server is running")

    def attempt_connection(self):
        if platform == "linux":
            self.connection = psycopg2.connect(dbname=self.dbname, user=self.role, host="/tmp")
        else:
            self.connection = psycopg2.connect(dbname=self.dbname, user=self.role)
        self.cursor = self.connection.cursor()

    def query_individual_table(self, schema, table, type, date_lower, date_upper, values=5):
        query = None
        if type == "Most recent":
            query = sql.SQL(
                """
                SELECT * FROM {0}.{1}
                ORDER BY id DESC
                """
            ).format(sql.Identifier(schema), sql.Identifier(table))

            try:
                self.cursor.execute(query)
                return self.cursor.fetchmany(int(values))
            except psycopg2.ProgrammingError:
                query = sql.SQL("ROLLBACK;")
                self.cursor.execute(query)

        elif type == "Date":
            query = sql.SQL(
                """
                SELECT * FROM {0}.{1}
                WHERE timestamp > (%s) AND timestamp < (%s)
                """
            ).format(sql.Identifier(schema), sql.Identifier(table)), (date_lower, date_upper)
            try:
                self.cursor.execute(query[0], query[1])
                return self.cursor.fetchmany(int(values))
            except psycopg2.ProgrammingError:
                query = sql.SQL("ROLLBACK;")
                self.cursor.execute(query)

        return []


db_tools = DBTools()
