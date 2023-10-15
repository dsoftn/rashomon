from PyQt5.QtWidgets import (QFrame, QPushButton, QTextEdit, QScrollArea, QVBoxLayout,
    QGridLayout, QWidget, QSpacerItem, QSizePolicy, QListWidget, QFileDialog, QDialog,
    QLabel, QListWidgetItem, QDesktopWidget, QLineEdit, QCalendarWidget, QTabWidget,
    QComboBox, QSlider, QProgressBar, QCheckBox, QFileIconProvider, QApplication, QTreeWidget,
    QTreeWidgetItem, QRadioButton, QGroupBox, QMainWindow, QAction, QMessageBox, QColorDialog)
from PyQt5.QtGui import (QIcon, QFont, QFontMetrics, QStaticText, QPixmap, QCursor, QDesktopServices,
     QImage, QClipboard, QColor, QResizeEvent, QMouseEvent, QKeyEvent)
from PyQt5.QtCore import (QMetaMethod, QSize, Qt, pyqtSignal, QObject, QCoreApplication, QRect,
    QPoint, QTimer, QThread, QDate, QEvent, QUrl, QFileInfo, QMimeDatabase)
from PyQt5 import uic, QtGui, QtCore
from PyQt5.QtMultimedia import QSound


class Settings(QDialog):
    signal_update_widgets = pyqtSignal()

    def __init__(self, parent_widget: QMainWindow, result: dict, setting_type: str = "general", *args, **kwargs):
        super().__init__(parent_widget, *args, **kwargs)

        self._parent_widget = parent_widget
        self.user_settings = result
        self.setting_type = setting_type

        uic.loadUi("data/rashomon/designer/settings.ui", self)

        self._setup_widgets()
        self._setup_apperance()
        self._populate_widgets()
        self.load_data()
        self.update_samples(dont_change_apply_buttons=True)

        # Connect events with slots
        self.cmb_font_name_result.currentTextChanged.connect(self.update_samples)
        self.cmb_font_name_code.currentTextChanged.connect(self.update_samples)
        self.cmb_font_name_seg.currentTextChanged.connect(self.update_samples)
        self.cmb_font_size_result.currentTextChanged.connect(self.update_samples)
        self.cmb_font_size_code.currentTextChanged.connect(self.update_samples)
        self.cmb_font_size_seg.currentTextChanged.connect(self.update_samples)

        self.chk_reload_source.stateChanged.connect(self.chk_reload_source_changed)
        self.chk_autocomplete_show.stateChanged.connect(self.update_samples)
        self.chk_autocomplete_select.stateChanged.connect(self.update_samples)

        self.btn_apply_general.clicked.connect(self.apply_general)
        self.btn_apply_result.clicked.connect(self.apply_result)
        self.btn_apply_code.clicked.connect(self.apply_code)
        self.btn_apply_seg.clicked.connect(self.apply_seg)
        self.btn_apply_all.clicked.connect(self.apply_all)

        self.btn_bg_color_result.clicked.connect(self.btn_bg_color_result_click)
        self.btn_bg_color_code.clicked.connect(self.btn_bg_color_code_click)

        self.btn_cancel.clicked.connect(self.btn_cancel_click)
        
    def show_me(self):
        self.show()
        self.exec_()

    def btn_cancel_click(self):
        self.close()

    def btn_bg_color_result_click(self):
        color = QColorDialog.getColor(QColor(self.btn_bg_color_result.objectName()), title="Pick a background color for Result TextBox")
        if color.isValid():
            self.lbl_color_sample_result.setStyleSheet(f'background-color: {color.name()}')
            self.btn_bg_color_result.setObjectName(color.name())
            self.btn_apply_result.setEnabled(True)
            self._set_apply_all_state()
            self.update_samples(dont_change_apply_buttons=True)

    def btn_bg_color_code_click(self):
        color = QColorDialog.getColor(QColor(self.btn_bg_color_code.objectName()), title="Pick a background color for Code TextBox")
        if color.isValid():
            self.lbl_color_sample_code.setStyleSheet(f'background-color: {color.name()}')
            self.btn_bg_color_code.setObjectName(color.name())
            self.btn_apply_code.setEnabled(True)
            self._set_apply_all_state()
            self.update_samples(dont_change_apply_buttons=True)

    def _set_apply_all_state(self):
        value = False
        if self.btn_apply_general.isEnabled():
            value = True
        if self.btn_apply_result.isEnabled():
            value = True
        if self.btn_apply_code.isEnabled():
            value = True
        if self.btn_apply_seg.isEnabled():
            value = True
        self.btn_apply_all.setEnabled(value)
        if value:
            self.btn_cancel.setText("Cancel")
        else:
            self.btn_cancel.setText("Close")
    
    def chk_reload_source_changed(self):
        self.btn_apply_general.setDisabled(False)
        self._set_apply_all_state()

    def apply_all(self):
        self.apply_general()
        self.apply_result()
        self.apply_code()
        self.apply_seg()
        self._set_apply_all_state()

    def apply_general(self):
        self.user_settings["general"]["reload_source_on_open"] = self.chk_reload_source.isChecked()
        self.btn_apply_general.setDisabled(True)
        self._set_apply_all_state()
        self.signal_update_widgets.emit()

    def apply_result(self):
        self.user_settings["txt_result"]["font"]["name"] = self.cmb_font_name_result.currentText()
        self.user_settings["txt_result"]["font"]["size"] = int(self.cmb_font_size_result.currentText())
        self.user_settings["txt_result"]["bg_color"] = self.btn_bg_color_result.objectName()
        self.btn_apply_result.setDisabled(True)
        self._set_apply_all_state()
        self.signal_update_widgets.emit()

    def apply_code(self):
        self.user_settings["txt_code"]["font"]["name"] = self.cmb_font_name_code.currentText()
        self.user_settings["txt_code"]["font"]["size"] = int(self.cmb_font_size_code.currentText())
        self.user_settings["txt_code"]["bg_color"] = self.btn_bg_color_code.objectName()
        self.user_settings["txt_code"]["autocomplete"]["show"] = self.chk_autocomplete_show.isChecked()
        self.user_settings["txt_code"]["autocomplete"]["autoselect"] = self.chk_autocomplete_select.isChecked()
        self.btn_apply_code.setDisabled(True)
        self._set_apply_all_state()
        self.signal_update_widgets.emit()

    def apply_seg(self):
        self.user_settings["tree_seg"]["font"]["name"] = self.cmb_font_name_seg.currentText()
        self.user_settings["tree_seg"]["font"]["size"] = int(self.cmb_font_size_seg.currentText())
        self.btn_apply_seg.setDisabled(True)
        self._set_apply_all_state()
        self.signal_update_widgets.emit()

    def update_samples(self, combo_box_current_text:str = None, dont_change_apply_buttons: bool = False):
        self.txt_sample_result.setFont(QFont(self.cmb_font_name_result.currentText(), int(self.cmb_font_size_result.currentText())))
        self.txt_sample_result.setStyleSheet(f"background-color: {self.btn_bg_color_result.objectName()};")
        
        self.txt_sample_code.setFont(QFont(self.cmb_font_name_code.currentText(), int(self.cmb_font_size_code.currentText())))
        self.txt_sample_code.setStyleSheet(f"background-color: {self.btn_bg_color_code.objectName()};")
        
        self.txt_sample_seg.setFont(QFont(self.cmb_font_name_seg.currentText(), int(self.cmb_font_size_seg.currentText())))

        if not dont_change_apply_buttons:
            if self.sender() == self.cmb_font_name_seg or self.sender() == self.cmb_font_size_seg:
                self.btn_apply_seg.setDisabled(False)
            if self.sender() == self.cmb_font_name_result or self.sender() == self.cmb_font_size_result:
                self.btn_apply_result.setDisabled(False)
            if self.sender() in [self.cmb_font_name_code, self.cmb_font_size_code, self.chk_autocomplete_show, self.chk_autocomplete_select]:
                self.btn_apply_code.setDisabled(False)
            self._set_apply_all_state()

    def load_data(self):
        if self.user_settings["general"]["reload_source_on_open"] is not None:
            self.chk_reload_source.setChecked(self.user_settings["general"]["reload_source_on_open"])

        if self.user_settings["txt_result"]["font"]["name"] is not None:
            self.cmb_font_name_result.setCurrentText(self.user_settings["txt_result"]["font"]["name"])
        if self.user_settings["txt_result"]["font"]["size"] is not None:
            self.cmb_font_size_result.setCurrentText(str(self.user_settings["txt_result"]["font"]["size"]))
        if self.user_settings["txt_result"]["bg_color"] is not None:
            self.lbl_color_sample_result.setStyleSheet(f"background-color: {self.user_settings['txt_result']['bg_color']};")
            self.btn_bg_color_result.setObjectName(self.user_settings['txt_result']['bg_color'])
            
        if self.user_settings["txt_code"]["font"]["name"] is not None:
            self.cmb_font_name_code.setCurrentText(self.user_settings["txt_code"]["font"]["name"])
        if self.user_settings["txt_code"]["font"]["size"] is not None:
            self.cmb_font_size_code.setCurrentText(str(self.user_settings["txt_code"]["font"]["size"]))
        if self.user_settings["txt_code"]["bg_color"] is not None:
            self.lbl_color_sample_code.setStyleSheet(f"background-color: {self.user_settings['txt_code']['bg_color']};")
            self.btn_bg_color_code.setObjectName(self.user_settings['txt_code']['bg_color'])
        if self.user_settings["txt_code"]["autocomplete"]["show"] is not None:
            self.chk_autocomplete_show.setChecked(self.user_settings["txt_code"]["autocomplete"]["show"])
        if self.user_settings["txt_code"]["autocomplete"]["autoselect"] is not None:
            self.chk_autocomplete_select.setChecked(self.user_settings["txt_code"]["autocomplete"]["autoselect"])

        if self.user_settings["tree_seg"]["font"]["name"] is not None:
            self.cmb_font_name_seg.setCurrentText(self.user_settings["tree_seg"]["font"]["name"])
        if self.user_settings["tree_seg"]["font"]["size"] is not None:
            self.cmb_font_size_seg.setCurrentText(str(self.user_settings["tree_seg"]["font"]["size"]))

    def _populate_widgets(self):
        self.cmb_font_name_result.clear()
        self.cmb_font_size_result.clear()
        self.cmb_font_name_code.clear()
        self.cmb_font_size_code.clear()
        self.cmb_font_name_seg.clear()
        self.cmb_font_size_seg.clear()

        for i in range(4, 73):
            self.cmb_font_size_result.addItem(str(i))
            self.cmb_font_size_seg.addItem(str(i))
            self.cmb_font_size_code.addItem(str(i))

        for family in QtGui.QFontDatabase().families():
            self.cmb_font_name_result.addItem(family)
            self.cmb_font_name_seg.addItem(family)
            self.cmb_font_name_code.addItem(family)

    def _setup_widgets(self):
        self.tab_settings: QTabWidget = self.findChild(QTabWidget, "tab_settings")
        self.btn_apply_all: QPushButton = self.findChild(QPushButton, "btn_apply_all")
        self.btn_cancel: QPushButton = self.findChild(QPushButton, "btn_cancel")
        
        # General
        self.chk_reload_source: QCheckBox = self.findChild(QCheckBox, "chk_reload_source")
        self.btn_apply_general: QPushButton = self.findChild(QPushButton, "btn_apply_general")

        # Result
        self.cmb_font_name_result: QComboBox = self.findChild(QComboBox, "cmb_font_name_result")
        self.cmb_font_size_result: QComboBox = self.findChild(QComboBox, "cmb_font_size_result")
        self.txt_sample_result: QLineEdit = self.findChild(QLineEdit, "txt_sample_result")
        self.btn_bg_color_result: QPushButton = self.findChild(QPushButton, "btn_bg_color_result")
        self.btn_apply_result: QPushButton = self.findChild(QPushButton, "btn_apply_result")
        self.lbl_color_sample_result: QLabel = self.findChild(QLabel, "lbl_color_sample_result")

        # Segment
        self.cmb_font_name_seg: QComboBox = self.findChild(QComboBox, "cmb_font_name_seg")
        self.cmb_font_size_seg: QComboBox = self.findChild(QComboBox, "cmb_font_size_seg")
        self.txt_sample_seg: QLineEdit = self.findChild(QLineEdit, "txt_sample_seg")
        self.btn_apply_seg: QPushButton = self.findChild(QPushButton, "btn_apply_seg")

        # Code
        self.cmb_font_name_code: QComboBox = self.findChild(QComboBox, "cmb_font_name_code")
        self.cmb_font_size_code: QComboBox = self.findChild(QComboBox, "cmb_font_size_code")
        self.txt_sample_code: QLineEdit = self.findChild(QLineEdit, "txt_sample_code")
        self.btn_bg_color_code: QPushButton = self.findChild(QPushButton, "btn_bg_color_code")
        self.chk_autocomplete_show: QCheckBox = self.findChild(QCheckBox, "chk_autocomplete_show")
        self.chk_autocomplete_select: QCheckBox = self.findChild(QCheckBox, "chk_autocomplete_select")
        self.btn_apply_code: QPushButton = self.findChild(QPushButton, "btn_apply_code")
        self.lbl_color_sample_code: QLabel = self.findChild(QLabel, "lbl_color_sample_code")

    def _setup_apperance(self):
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.setWindowFlag(Qt.FramelessWindowHint)

        self.tab_general: QWidget = self.tab_settings.widget(0)
        self.tab_txt_result: QWidget = self.tab_settings.widget(1)
        self.tab_tree_seg: QWidget = self.tab_settings.widget(2)
        self.tab_txt_code: QWidget = self.tab_settings.widget(3)

        if self.setting_type == "general":
            self.tab_settings.setCurrentWidget(self.tab_general)
        elif self.setting_type == "txt_result":
            self.tab_settings.setCurrentWidget(self.tab_txt_result)
        elif self.setting_type == "tree_seg":
            self.tab_settings.setCurrentWidget(self.tab_tree_seg)
        elif self.setting_type == "txt_code":
            self.tab_settings.setCurrentWidget(self.tab_txt_code)

        self.btn_apply_all.setDisabled(True)
        self.btn_apply_general.setDisabled(True)
        self.btn_apply_result.setDisabled(True)
        self.btn_apply_seg.setDisabled(True)
        self.btn_apply_code.setDisabled(True)
            
