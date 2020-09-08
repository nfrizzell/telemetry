from PySide2.QtWidgets import QApplication

from ui import UserInterface
from database import DatabaseConnection


class Client:
    def __init__(self):
        # Create the QApplication first so that QThread, QTimer, etc. can be used
        self.qt_app = QApplication()
        self.qt_app.aboutToQuit.connect(self.quit)

        self.database_connection = DatabaseConnection(self)
        self.user_interface = UserInterface(self)

        self.qt_app.exec_()

    # Application destructor, may be used one day if I implement file logging
    def quit(self):
        quit(0)


client = Client()
