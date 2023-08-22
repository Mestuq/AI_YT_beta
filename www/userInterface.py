import sys, os, threading
from PyQt5.QtWidgets import QApplication, QMainWindow, QWebEngineView
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QIcon

class WebBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.browser = QWebEngineView()
        self.browser.setUrl(QUrl("http://127.0.0.1:5000/"))
        self.setCentralWidget(self.browser)
        self.setWindowTitle("TagsAI")
        self.setWindowIcon(QIcon(sys._MEIPASS + '/static/logo.ico'))
        self.setGeometry(100, 100, 1280, 720)
    def CloseEvent(self, event):
        os._exit(1)

def open_window():
    app = QApplication(sys.argv)
    main_window = WebBrowser()
    main_window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    read_thread = threading.Thread(target=open_window)
    read_thread.start()
