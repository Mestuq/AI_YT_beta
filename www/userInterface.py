import sys, os, threading
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QIcon
from PyQt5.QtWebEngineWidgets import QWebEngineView

class WebBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.browser = QWebEngineView()
        self.browser.setUrl(QUrl("http://127.0.0.1:5000/"))
        self.setCentralWidget(self.browser)
        self.setWindowTitle("TagsAI")
        main_path = getattr(sys, '_MEIPASS', '')
        self.setWindowIcon(QIcon(main_path+'/static/logo.ico'))
        self.setGeometry(100, 100, 1280, 720)
    def closeEvent(self, event):
        os._exit(1)

def open_window():
    app = QApplication(sys.argv)
    main_window = WebBrowser()
    main_window.show()
    sys.exit(app.exec_())

def new_window():
    user_interface_thread = threading.Thread(target=open_window)
    user_interface_thread.start()