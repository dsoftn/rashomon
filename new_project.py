from PyQt5.QtWidgets import (QFrame, QPushButton, QTextEdit, QScrollArea, QVBoxLayout,
    QGridLayout, QWidget, QSpacerItem, QSizePolicy, QListWidget, QFileDialog, QDialog,
    QLabel, QListWidgetItem, QDesktopWidget, QLineEdit, QCalendarWidget, QHBoxLayout,
    QComboBox, QSlider, QProgressBar, QCheckBox, QFileIconProvider, QApplication, QTreeWidget,
    QTreeWidgetItem, QRadioButton, QGroupBox, QMainWindow, QAction, QMessageBox)
from PyQt5.QtGui import (QIcon, QFont, QFontMetrics, QStaticText, QPixmap, QCursor, QDesktopServices,
     QImage, QClipboard, QColor, QResizeEvent, QMouseEvent, QKeyEvent)
from PyQt5.QtCore import (QMetaMethod, QSize, Qt, pyqtSignal, QObject, QCoreApplication, QRect,
    QPoint, QTimer, QThread, QDate, QEvent, QUrl, QFileInfo, QMimeDatabase)
from PyQt5 import uic, QtGui, QtCore
from PyQt5.QtMultimedia import QSound

import urllib.request
from urllib.parse import urlparse


class NewProject(QDialog):
    def __init__(self, parent_widget: QMainWindow, result: dict, clipboard: QClipboard, *args, **kwargs):
        super().__init__(parent_widget, *args, **kwargs)

        self._parent_widget = parent_widget
        self.result = result
        self.clipboard = clipboard

        uic.loadUi("data/rashomon/designer/new_project.ui", self)

        self._setup_widgets()
        self._setup_apperance()

        # Connect events with slots
        self.btn_web.clicked.connect(self.btn_web_click)
        self.btn_close_web_frm.clicked.connect(self.btn_close_web_frm_click)
        self.btn_load.clicked.connect(self.btn_load_click)
        self.txt_url.returnPressed.connect(self.txt_url_return_pressed)
        self.txt_url.textChanged.connect(self.txt_url_text_changed)
        self.btn_confirm.clicked.connect(self.btn_confirm_click)
        self.btn_file.clicked.connect(self.btn_file_click)
        self.btn_clip.clicked.connect(self.btn_clip_click)
        

        self.show()
        self.exec_()

    def btn_clip_click(self):
        txt = self.clipboard.text()
        if not txt:
            QMessageBox.information(self, "No data", "There is no text data in clipboard !", QMessageBox.Ok)
            return
        self.result["source"] = "clipboard"
        self.result["text"] = txt
        self.result["selected"] = "clip"
        self.close()

    def btn_file_click(self):
        result = QFileDialog.getOpenFileName(self, "Select File", "", "All Files (*);;Text Files (*.txt)")
        if result[0]:
            try:
                with open(result[0], 'r', encoding="utf-8") as f:
                    txt = f.read()
                    self.result["source"] = result[0]
                    self.result["text"] = txt
                    self.result["selected"] = "file"
                    self.close()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error loading file: {e}", QMessageBox.Ok)
                return

    def btn_confirm_click(self):
        self.result["selected"] = "web"
        self.close()

    def txt_url_text_changed(self):
        self.lbl_info.setText("")
        self.btn_confirm.setVisible(False)

    def txt_url_return_pressed(self):
        self._load_webpage()

    def btn_load_click(self):
        self._load_webpage()

    def btn_close_web_frm_click(self):
        self.frm_web.setVisible(False)

    def btn_web_click(self):
        if self.frm_web.isVisible():
            self.frm_web.setVisible(False)
            self.setFixedHeight(320)
        else:
            self.frm_web.setVisible(True)
            self.setFixedHeight(440)
            self.lbl_info.setText("")
            self.txt_url.setFocus()

    def _load_webpage(self):
        url = self.txt_url.text().strip()

        self.lbl_info.setText("Loading...")
        QCoreApplication.processEvents()
        if url.find(" ") != -1:
            self.lbl_info.setText("Bad URL. Spaces are not allowed in URLs.")
            return
        if not url.startswith("http"):
            self.lbl_info.setText("Bad URL. URL must start with 'http'.")
            return
        
        if not url:
            return

        try:
            result = urllib.request.urlopen(url).read().decode("utf-8")
        except Exception as e:
            self.lbl_info.setText(f"Error.  URL is not loaded.\n{e}")
            return
        
        if not result:
            self.lbl_info.setText("Unexpected error.")
            return

        self.result["text"] = result
        self.result["source"] = url
        self.lbl_info.setText("URL Loaded.")
        self.btn_confirm.setVisible(True)

    def _setup_widgets(self):
        self.lbl_title: QLabel = self.findChild(QLabel, "lbl_title")
        self.btn_web: QPushButton = self.findChild(QPushButton, "btn_web")
        self.btn_file: QPushButton = self.findChild(QPushButton, "btn_file")
        self.btn_clip: QPushButton = self.findChild(QPushButton, "btn_clip")

        self.frm_web: QFrame = self.findChild(QFrame, "frm_web")
        self.txt_url: QLineEdit = self.findChild(QLineEdit, "txt_url")
        self.btn_load: QPushButton = self.findChild(QPushButton, "btn_load")
        self.lbl_info: QLabel = self.findChild(QLabel, "lbl_info")
        self.btn_close_web_frm: QPushButton = self.findChild(QPushButton, "btn_close_web_frm")
        self.btn_confirm: QPushButton = self.findChild(QPushButton, "btn_confirm")

    def _setup_apperance(self):
        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.setFixedSize(800, 320)
        self.frm_web.setVisible(False)
        self.btn_confirm.setVisible(False)

