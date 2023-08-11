from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5 import QtCore
from PyQt5.QtCore import Qt, QCoreApplication, QUrl
from PyQt5.QtCore import QMutex
from PyQt5 import QtGui

import sys
import os
import threading

class WebBrowser(QMainWindow):
    _mutex = QMutex()

    def __init__(self):
        super().__init__()

        self.browser = QWebEngineView()
        self.browser.setUrl(QtCore.QUrl("http://127.0.0.1:5000/"))  # Replace with your desired URL

        self.setCentralWidget(self.browser)
        self.setWindowTitle("TagsAI")
        self.setWindowIcon(QtGui.QIcon(sys._MEIPASS + '/static/logo.ico'))
        self.setGeometry(100, 100, 1280, 720)

    def closeEvent(self, event):
        os._exit(1)
        self._mutex.unlock()

def openWindow():
    if not WebBrowser._mutex.tryLock():
        print("An instance of the browser is already running.")
        return None
    app = QApplication(sys.argv)
    main_window = WebBrowser()
    main_window.show()
    sys.exit(app.exec_())

read_thread = threading.Thread(target=openWindow)
read_thread.start()