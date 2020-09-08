import time
import random

from PySide2.QtUiTools import QUiLoader
from PySide2.QtCore import Qt, QTimer
from PySide2.QtWidgets import QTreeWidget, QTreeWidgetItem, QLabel, QWidget, QVBoxLayout,\
    QGraphicsView, QVBoxLayout, QFrame
from PySide2.QtCharts import QtCharts
import PySide2.QtCore as QtCore

import common


class UserInterface:
    def __init__(self, client):
        self.client = client

        # The timer that tells the gui to update at the end of every specified interval
        self.refresh_timer = QTimer()
        self.refresh_timer_interval = 1000

        self.find_gui_elements()
        self.connect_signal_methods()
        self.initialize_module_tree(common.cache.modules.values())
 
        # The QChart that will allow for data visualization at the bottom of the window
        # (previously Matplotlib)
        self.active_chart = None
        self.create_chart()

        self.refresh_timer.start(self.refresh_timer_interval)
        self.main_window.show()

    # ====================================
    # ~~~ Methods for initializing GUI ~~~
    # ====================================

    # Gets reference to GUI items from main_window.ui so that they can be manipulated programmatically
    def find_gui_elements(self):
        loader = QUiLoader()
        self.main_window = loader.load("main_window.ui")
        self.uptime_widget = self.main_window.findChild(QLabel, "uptime")
        self.database_status_widget = self.main_window.findChild(QLabel, "database_status")
        self.arduino_status_widget = self.main_window.findChild(QLabel, "arduino_status")
        self.uptime_widget = self.main_window.findChild(QLabel, "uptime")
        self.packet_time_widget = self.main_window.findChild(QLabel, "packet_time")
        self.module_tree_widget = self.main_window.findChild(QTreeWidget, "module_tree")
        self.chart_frame = self.main_window.findChild(QFrame, "chart_frame")
        self.sensor_detail_label = self.main_window.findChild(QLabel, "sensor_label")
        self.sensor_detail_unit = self.main_window.findChild(QLabel, "sensor_unit")
        self.sensor_detail_parent_label = self.main_window.findChild(QLabel, "sensor_parent")
        self.sensor_detail_lower_bound = self.main_window.findChild(QLabel, "sensor_lb")
        self.sensor_detail_lower_critical_bound = self.main_window.findChild(QLabel, "sensor_lcb")
        self.sensor_detail_upper_bound = self.main_window.findChild(QLabel, "sensor_ub")
        self.sensor_detail_upper_critical_bound = self.main_window.findChild(QLabel, "sensor_ucb")
        self.sensor_detail_max = self.main_window.findChild(QLabel, "sensor_max")
        self.sensor_detail_min = self.main_window.findChild(QLabel, "sensor_min")

    # Connect Qt signals to relevant application methods
    def connect_signal_methods(self):
        self.refresh_timer.timeout.connect(self.refresh_gui)
        self.module_tree_widget.itemSelectionChanged.connect(self.update_sidebar)

    # Sets up the initial data and dimensions of the QTreeWidget for displaying module and sensor data
    def initialize_module_tree(self, module_data):
        # Set the data for the column headers
        self.module_tree_widget.setAllColumnsShowFocus(True)
        self.module_tree_widget.setColumnCount(5)
        self.module_tree_widget.setHeaderLabels(["Sensor", "Value", "Min", "Max", "Status"])

        # Create a new blank root tree item for each module that acts as a container for sensor sub-items
        for module in module_data:
            self.create_tree_item(module)
        self.update_module_tree(module_data)

    def create_tree_item(self, module):
        tree_item = QTreeWidgetItemWrapper([module.label, "", "", "", ""])
        self.module_tree_widget.addTopLevelItem(tree_item)
        tree_item.setExpanded(True)

        for sensor in module.sensors:
            self.create_tree_subitem(tree_item, sensor)

    def create_tree_subitem(self, parent_item, sensor):
        filler = "-9999 " + sensor.unit
        sub_tree_item = QTreeWidgetItemWrapper([sensor.label, filler, filler, filler], sensor=sensor)
        sensor.gui_reference = sub_tree_item
        parent_item.addChild(sub_tree_item)

    def create_chart(self, chart_type="line"):
        if chart_type == "line":
            self.active_chart = LineChart(self.chart_frame)

        elif chart_type == "gauge":
            self.active_chart = GaugeChart(self.chart_frame)

    # ================================
    # ~~~ Methods for updating GUI ~~~
    # ================================

    # Updates each of the individual active gui elements
    def refresh_gui(self):
        self.update_module_tree(common.cache.modules.values())
        self.update_sidebar()
        self.active_chart.update(None)

    def update_module_tree(self, module_data):
        for module in module_data:
            # Update each column (except the label column) for each sensor(row) with relevant data
            # -9999 signifies an error
            for sensor in module.sensors:
                str_value = "{0} {1}".format(sensor.value, sensor.unit)
                sensor.determine_value_color()
                str_color = sensor.value_color

                # Most recent value column
                if sensor.value == -9999:
                    sensor.gui_reference.setData(1, Qt.ItemDataRole.DisplayRole, str_value)
                    sensor.gui_reference.setBackground(1, Qt.white)
                else:
                    sensor.gui_reference.setData(1, Qt.ItemDataRole.DisplayRole, str_value)
                    sensor.gui_reference.setBackground(1, str_color)

                # Lowest recorded value column
                if sensor.value <= sensor.lowest_recorded_value and sensor.value != -9999:
                    sensor.gui_reference.setData(2, Qt.ItemDataRole.DisplayRole, str_value)

                # Highest recorded value column
                if sensor.value >= sensor.highest_recorded_value:
                    sensor.gui_reference.setData(3, Qt.ItemDataRole.DisplayRole, str_value)

                # Status column
                if sensor.value != -9999:
                    sensor.gui_reference.setData(4, Qt.ItemDataRole.DisplayRole, "Operational")
                else:
                    sensor.gui_reference.setData(4, Qt.ItemDataRole.DisplayRole, "Error")

    def update_sidebar(self):
        if common.database_connection_status:
            self.database_status_widget.setText("Connected")
            self.database_status_widget.setStyleSheet("color:green")
        else:
            self.database_status_widget.setText("Not connected")
            self.database_status_widget.setStyleSheet("color:red")

        if common.arduino_connection_status:
            self.arduino_status_widget.setText("Connected")
            self.arduino_status_widget.setStyleSheet("color:green")
        else:
            self.arduino_status_widget.setText("Not connected")
            self.arduino_status_widget.setStyleSheet("color:red")

        if common.packet_received:
            self.packet_time_widget.setText(str(common.time_since_last_packet) + " seconds")
            self.uptime_widget.setText(str(common.uptime) + " seconds")
        else:
            self.packet_time_widget.setText("N/A")
            self.uptime_widget.setText("N/A")

        # Get the current item highlighted
        selected_tree_item = self.module_tree_widget.currentItem()

        # Each treeview item is actually a wrapper around the base class & a reference to the
        # sensor it represents; this retrieves the sensor
        if selected_tree_item.sensor:
            sensor = selected_tree_item.sensor

            self.sensor_detail_label.setText(sensor.label)
            self.sensor_detail_unit.setText(sensor.unit)
            self.sensor_detail_parent_label.setText(sensor.parent_label)
            self.sensor_detail_lower_bound.setText(str(sensor.lower_bound))
            self.sensor_detail_lower_critical_bound.setText(str(sensor.lower_critical_bound))
            self.sensor_detail_upper_bound.setText(str(sensor.upper_bound))
            self.sensor_detail_upper_critical_bound.setText(str(sensor.upper_critical_bound))
            self.sensor_detail_max.setText(str(sensor.highest_recorded_value))
            self.sensor_detail_min.setText(str(sensor.lowest_recorded_value))

        # Do not display any values for modules (it wouldn't make sense)
        else:
            self.sensor_detail_label.setText("")
            self.sensor_detail_unit.setText("")
            self.sensor_detail_parent_label.setText("")
            self.sensor_detail_lower_bound.setText("")
            self.sensor_detail_lower_critical_bound.setText("")
            self.sensor_detail_upper_bound.setText("")
            self.sensor_detail_upper_critical_bound.setText("")
            self.sensor_detail_max.setText("")
            self.sensor_detail_min.setText("")

        self.module_tree_widget.clearSelection()  # Prevents "ghosting" effect with selected items

"""
    def update_chart(self):
        sensor = self.module_tree_widget.currentItem().sensor
        if not sensor:
            return

        # Process retrieved data into a form usable by Matplotlib
        try:
            print(common.cache.sensors[sensor.unique_tag])
            relevant_records = common.cache.sensors[sensor.unique_tag].value_cache
            # Pass only the timestamp and value into the graph function, as they are the only relevant values
            truncated_records = ([record[1:] for record in relevant_records])

            # Remove microsecond in timestamp
            for record in truncated_records:
                record[0].replace(microsecond=0)

            self.sensor_graph.update_chart(sensor, truncated_records)

        except IndexError:
            return
"""


# Wrapper that keeps a reference to the sensor object that the tree item represents
class QTreeWidgetItemWrapper(QTreeWidgetItem):
    # Has to be done this way to allow passing the sensor to the constructor
    def __init__(self, *args, **kwargs):
        try:
            self.sensor = kwargs.pop("sensor")
        except KeyError:
            self.sensor = None
        QTreeWidgetItem.__init__(self, *args, **kwargs)


class LineChart:
    def __init__(self, frame):
        self.series = QtCharts.QLineSeries()
        self.series.setColor(Qt.red)

        self.axis_x = QtCharts.QDateTimeAxis()
        # Number of items to display
        self.axis_x.setTickCount(int(common.SETTINGS["DataCacheSize"]))
        self.axis_x.setFormat("hh:mm:ss:z") # Date format
        self.axis_x.setTitleText("Time")

        self.axis_y = QtCharts.QValueAxis()
        self.axis_y.setTitleText("Value")

        self.chart = QtCharts.QChart()
        self.chart.setTitle("")
        self.chart.addSeries(self.series)
        self.chart.addAxis(self.axis_x, QtCore.Qt.AlignBottom)
        self.chart.addAxis(self.axis_y, QtCore.Qt.AlignLeft)

        self.series.attachAxis(self.axis_x)
        self.series.attachAxis(self.axis_y)

        self.chart_view = QtCharts.QChartView(self.chart)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.chart_view)

        self.frame = frame
        self.frame.setLayout(self.layout)

    def update(self, sensor):
        # Remove all previous values; list will be updated with relevant values
        self.series.removePoints(0, len(self.series.points()))

        if sensor:
            for entry in sensor.value_cache:
                # Time/value, respectively
                self.series.append(entry[0].toMSecsSinceEpoch(), entry[1])

        # Insert debug values for testing
        else:
            for x in range(10):
                # Float to avoid int overflow problems on Windows
                self.series.append(float(QtCore.QDateTime.currentMSecsSinceEpoch()), 10*random.random())
                time.sleep(.001)

        raw_x_list = [value.x() for value in self.series.points()]
        raw_y_list = [value.y() for value in self.series.points()]
 
        min_x = min(raw_x_list)
        max_x = max(raw_x_list)

        min_y = min(raw_y_list)
        max_y = max(raw_y_list)
        y_margin = (max_y - min_y) / 10

        self.axis_x.setRange(QtCore.QDateTime().fromMSecsSinceEpoch(min_x), QtCore.QDateTime().fromMSecsSinceEpoch(max_x))
        self.axis_y.setRange(min_y - y_margin, max_y + y_margin)


class GaugeChart:
    def __init__(self):
        pass 
"""
class SensorGraph(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # a figure instance to plot on
        self.figure = Figure()
        self.figure.set_size_inches(1, 2.5)

        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)

        # Integrate into QT so that it can be displayed
        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        self.axes = self.figure.add_subplot(111)
        self.axes.grid(True)

    def update_graph(self, sensor, data):
        self.axes.cla()
        for index, record in enumerate(data):
            color = "k"  # Black (debug)

            current_value = record[1]
            if sensor.lower_bound <= current_value <= sensor.upper_bound:
                color = "b"  # Blue (normal)
            elif sensor.lower_critical_bound <= current_value <= sensor.upper_critical_bound:
                color = "y"  # Yellow (warning)
            else:
                color = "r"  # Red (critical)

            if index < len(data)-1:
                # Draw line between points
                x_values = [record[0], data[index+1][0]]
                y_values = [record[1], data[index+1][1]]
                line = lines.Line2D(x_values, y_values, linewidth=3, color=color)
                self.axes.add_line(line)

            self.axes.plot(record[0], record[1], color+"o")
            self.add_graph_details()
        self.canvas.draw()

    def add_graph_details(self):
        self.axes.grid(True)
"""
