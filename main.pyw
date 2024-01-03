from PyQt5.QtWidgets import (QFrame, QPushButton, QTextEdit, QScrollArea, QVBoxLayout,
    QGridLayout, QWidget, QSpacerItem, QSizePolicy, QListWidget, QFileDialog, QDialog,
    QLabel, QListWidgetItem, QDesktopWidget, QLineEdit, QCalendarWidget, QSpinBox,
    QComboBox, QSlider, QProgressBar, QCheckBox, QFileIconProvider, QApplication, QTreeWidget,
    QTreeWidgetItem, QRadioButton, QGroupBox, QMainWindow, QAction, QMenuBar, QMenu, QMessageBox, QInputDialog)
from PyQt5.QtGui import (QIcon, QFont, QFontMetrics, QStaticText, QPixmap, QCursor, QDesktopServices,
     QImage, QClipboard, QColor, QResizeEvent, QMouseEvent, QKeyEvent, QTextCharFormat, QTextCursor)
from PyQt5.QtCore import (QMetaMethod, QSize, Qt, pyqtSignal, QObject, QCoreApplication, QRect,
    QPoint, QTimer, QThread, QDate, QEvent, QUrl, QFileInfo, QMimeDatabase)
from PyQt5 import uic, QtGui, QtCore
from PyQt5.QtMultimedia import QSound


import requests
import json
import sys
import os
import html as HtmlLib
from cyrtranslit import to_latin
# from bs4 import BeautifulSoup as bs
from unidecode import unidecode

import new_project
import script_cls
import segment_cls
import code_cls
import text_to_html_cls
import settings_cls


class RashomonGUI(QMainWindow):
    SEARCHED_COLOR = "#0000a2"
    FOUND_COLOR = "#007300"
    MARKED_COLOR = "#989898"

    USER_SETTINGS_STRUCTURE = [
        ["window", [
            ["position", [["x", []], ["y",[]]]],
            ["size", [["width", []], ["height", []]]]
        ]],
        ["separator", [
            ["position", []]
        ]],
        ["general", [
            ["reload_source_on_open", []]
        ]],
        ["txt_code", [
            ["font", [["name",[]], ["size", []]]],
            ["bg_color", []],
            ["autocomplete", [["show", []], ["autoselect", []]]]
        ]],
        ["chk_apply_all", [
            ["is_checked", []]
        ]],
        ["chk_apply_all_code", [
            ["is_checked", []]
        ]],
        ["txt_result", [
            ["font", [["name",[]], ["size", []]]],
            ["bg_color", []],
            ["show_image", []]
        ]],
        ["tree_seg", [
            ["font", [["name",[]], ["size", []]]]
        ]]
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        uic.loadUi("data/rashomon/designer/main.ui", self)

        # Define variables
        self.abort_action = False
        self._code_txtbox_protected = False
        self._tree_change_current_protected = False
        self.drag_mode = None
        self.user_settings = {}
        self.data_source: dict = None
        self.script = script_cls.Script()
        self.current_segment = None
        self.shown_picture = {}

        self.search_position = 0

        self._setup_widgets()
        self._setup_apperance()

        self._check_user_setting_structure()
        self.load_user_settings()

        self.old_txt_rule_cf = self.txt_code.textCursor().charFormat()

        # Connect events with slots
        self.closeEvent = self.close_event
        # Menu Items
        self.mnu_file_new.triggered.connect(self.mnu_file_new_triggered)
        self.mnu_file_save.triggered.connect(self.mnu_file_save_triggered)
        self.mnu_file_save_as.triggered.connect(self.mnu_file_save_as_triggered)
        self.mnu_file_open.triggered.connect(self.mnu_file_open_triggered)
        self.mnu_file_close.triggered.connect(self.mnu_file_close_triggered)
        self.mnu_file_export.triggered.connect(self.mnu_file_export_triggered)
        self.mnu_file_settings.triggered.connect(self.mnu_file_settings_triggered)
        # Context Menu Items
        self.mnu_lst_rules_del_item.triggered.connect(self.mnu_lst_rules_del_item_triggered)
        self.mnu_lst_rules_del_all.triggered.connect(self.mnu_lst_rules_del_all_triggered)
        self.mnu_tree_del.triggered.connect(self.mnu_tree_del_triggered)
        self.mnu_tree_add_top_level.triggered.connect(self.mnu_tree_add_top_level_triggered)
        self.mnu_tree_rename.triggered.connect(self.mnu_tree_rename_triggered)
        # Code TextBox
        self.btn_code_zoom_in.clicked.connect(self.btn_code_zoom_in_click)
        self.btn_code_zoom_out.clicked.connect(self.btn_code_zoom_out_click)
        self.btn_code_setup.clicked.connect(self.show_settings_dialog)
        self.btn_apply_code.clicked.connect(self.btn_apply_code_click)
        self.txt_code.textChanged.connect(self.txt_code_text_changed)
        self.txt_code.keyPressEvent = self.txt_code_key_press
        self.txt_code.focusOutEvent = self.txt_code_focus_out
        # Result TextBox
        self.txt_find.textChanged.connect(self.txt_find_text_changed)
        self.txt_find.returnPressed.connect(self.txt_find_return_pressed)
        self.txt_result.mouseMoveEvent = self.txt_result_mouse_move
        self.txt_result.mousePressEvent = self.txt_result_mouse_press
        self.txt_result.leaveEvent = self.txt_result_leave
        self.btn_find_next.clicked.connect(self.btn_find_next_click)
        self.btn_find_prev.clicked.connect(self.btn_find_prev_click)
        self.btn_find_go.clicked.connect(self.btn_find_go_click)
        self.btn_result_zoom_in.clicked.connect(self.btn_result_zoom_in_click)
        self.btn_result_zoom_out.clicked.connect(self.btn_result_zoom_out_click)
        self.btn_result_setup.clicked.connect(self.show_settings_dialog)
        self.btn_tag_remove.clicked.connect(self.btn_tag_remove_click)
        # Tree
        self.tree_seg.currentChanged = self.tree_seg_current_changed
        self.tree_seg.itemDoubleClicked.connect(self.tree_seg_item_double_click)
        self.tree_seg.customContextMenuRequested.connect(self.tree_seg_context_menu)
        self.btn_seg_zoom_in.clicked.connect(self.btn_seg_zoom_in_click)
        self.btn_seg_zoom_out.clicked.connect(self.btn_seg_zoom_out_click)
        self.btn_seg_setup.clicked.connect(self.show_settings_dialog)
        self.btn_seg_collapse.clicked.connect(self.btn_seg_collapse_click)
        self.btn_seg_expand.clicked.connect(self.btn_seg_expand_click)
        # Rules
        self.txt_rule_is_equal_to.returnPressed.connect(self.txt_rule_is_equal_to_return_press)
        self.txt_rule_starts_with.returnPressed.connect(self.txt_rule_starts_with_return_press)
        self.txt_rule_ends_with.returnPressed.connect(self.txt_rule_ends_with_return_press)
        
        self.txt_rule_starts.textChanged.connect(self.txt_rule_starts_text_changed)
        self.txt_rule_ends.textChanged.connect(self.txt_rule_ends_text_changed)
        self.txt_rule_contain.textChanged.connect(self.txt_rule_contain_text_changed)

        self.txt_rule_is_equal_to.textChanged.connect(self.txt_rule_is_equal_to_text_changed)
        self.txt_rule_starts_with.textChanged.connect(self.txt_rule_starts_with_text_changed)
        self.txt_rule_ends_with.textChanged.connect(self.txt_rule_ends_with_text_changed)

        self.btn_rule_add_starts.clicked.connect(self.btn_rule_add_starts_click)
        self.btn_rule_add_ends.clicked.connect(self.btn_rule_add_ends_click)
        self.btn_rule_add_contain.clicked.connect(self.btn_rule_add_contain_click)
        self.lst_rules.customContextMenuRequested.connect(self.lst_rules_context_menu)
        self.btn_apply_rule.clicked.connect(self.btn_apply_rule_click)
        self.btn_rule_add_is_equal_to.clicked.connect(self.txt_rule_is_equal_to_return_press)
        self.btn_rule_add_starts_with.clicked.connect(self.txt_rule_starts_with_return_press)
        self.btn_rule_add_ends_with.clicked.connect(self.txt_rule_ends_with_return_press)

        self.chk_apply_all.stateChanged.connect(self.chk_apply_all_state_changed)
        self.chk_apply_all_code.stateChanged.connect(self.chk_apply_all_code_state_changed)
        # Separator line
        self.line_sep.enterEvent = self.line_sep_enter
        self.line_sep.leaveEvent = self.line_sep_leave
        self.line_sep.mousePressEvent = self.line_sep_mouse_press
        self.line_sep.mouseMoveEvent = self.line_sep_mouse_move
        self.line_sep.mouseReleaseEvent = self.line_sep_mouse_release
        # Frame Working
        self.btn_abort.clicked.connect(self.btn_abort_click)
        # Autocomplete
        self.lst_autocomplete.mouseReleaseEvent = self.lst_autocomplete_mouse_release
        # Change Source
        self.btn_change_source.clicked.connect(self.btn_change_source_click)

    def btn_seg_collapse_click(self):
        self._seg_tree_expand_all(False)

    def btn_seg_expand_click(self):
        self._seg_tree_expand_all(True)
    
    def _seg_tree_expand_all(self, value: bool = True):
        for i in range(self.tree_seg.topLevelItemCount()):
            item = self.tree_seg.topLevelItem(i)
            item.setExpanded(value)
            for j in range(item.childCount()):
                child = item.child(j)
                child.setExpanded(value)

    def txt_result_leave(self, e):
        self.lbl_pic.setVisible(False)
        self._mark_image_link(unmark=True)
        QTextEdit.leaveEvent(self.txt_result, e)

    def txt_result_mouse_press(self, e: QMouseEvent):
        cur = self.txt_result.cursorForPosition(e.pos())
        pos = cur.position()
        near_result = self._click_near_result(pos)
        if near_result:
            self.search_position = near_result
            self.lbl_search_info.setText("Clicked near result: " + str(near_result))
            self.spin_find_go.setValue(near_result)
        QTextEdit.mousePressEvent(self.txt_result, e)
    
    def txt_result_mouse_move(self, e: QMouseEvent):
        if self.user_settings["txt_result"]["show_image"]:
            self._mark_image_link(unmark=True)
            cur = self.txt_result.cursorForPosition(e.pos())
            pos = cur.position()
            txt = self.txt_result.toPlainText()
            pos_start = txt[:pos].rfind('"')
            pos_end = txt.find('"', pos)
            self.lbl_pic.setVisible(False)
            if pos_start != -1 and pos_end != -1:
                img_data = self._get_image_from_url(txt[pos_start+1:pos_end])
                if img_data:
                    img = img_data.scaled(350, 350, Qt.KeepAspectRatio)
                    self.lbl_pic.setPixmap(img)
                    self.lbl_pic.setVisible(True)
                    self.shown_picture = {"start": pos_start+1, "end": pos_end}
                    self._mark_image_link()
                else:
                    self.lbl_pic.setVisible(False)
            else:
                self.lbl_pic.setVisible(False)
        QTextEdit.mouseMoveEvent(self.txt_result, e)

    def _mark_image_link(self, unmark: bool = False):
        if not self.shown_picture:
            return
        
        cur = self.txt_result.textCursor()
        cf = QTextCharFormat()
        font = self.txt_result.font()
        if unmark:
            font.setUnderline(False)
            font.setItalic(False)
        else:
            font.setUnderline(True)
            font.setItalic(True)
        cf.setFont(font)
        
        cur.setPosition(self.shown_picture["start"])
        cur.movePosition(cur.Right, cur.KeepAnchor, self.shown_picture["end"] - self.shown_picture["start"])
        cur.mergeCharFormat(cf)
        cur.setPosition(self.shown_picture["start"])
        self.txt_result.setTextCursor(cur)
        if unmark:
            self.shown_picture = {}

    def _get_image_from_url(self, url: str) -> QPixmap:
        frm_working_state = self.frm_working.isVisible()
        self.frm_working.setVisible(True)
        self.prg_working.setVisible(False)
        QCoreApplication.processEvents()
        result = True
        if url.count(" "):
            result = False
        
        url = self.fix_url(url)
        if not url.startswith("http"):
            result = False
        
        if not result:
            self.frm_working.setVisible(frm_working_state)
            self.abort_action = False
            return None
            
        try:
            response = requests.get(url, timeout=2)
            img = QPixmap()
            result = img.loadFromData(response.content)
            if result:
                self.frm_working.setVisible(frm_working_state)
                self.abort_action = False
                return img
            else:
                self.frm_working.setVisible(frm_working_state)
                self.abort_action = False
                return None
        except:
            self.frm_working.setVisible(frm_working_state)
            self.abort_action = False
            return None

    def fix_url(self, url: str) -> str:
        if url.startswith("//"):
            url = "https:" + url
            return url
        elif url.startswith("/"):
            pos = self.data_source["source"].find("/", self.data_source["source"].find("//")+2)
            url = self.data_source["source"][:pos] + url
            return url
        return url

    def mnu_file_settings_triggered(self):
        self.show_settings_dialog()

    def show_settings_dialog(self):
        sender = "general"
        if self.sender() == self.btn_code_setup:
            sender = "txt_code"
        elif self.sender() == self.btn_result_setup:
            sender = "txt_result"
        elif self.sender() == self.btn_seg_setup:
            sender = "tree_seg"

        settings = settings_cls.Settings(self, self.user_settings, setting_type=sender)
        settings.signal_update_widgets.connect(self.update_widgets_apperance)
        settings.show_me()
        settings.signal_update_widgets.disconnect()
        self.update_widgets_apperance()

    def update_widgets_apperance(self):
        self.txt_result.setFont(QFont(self.user_settings["txt_result"]["font"]["name"], self.user_settings["txt_result"]["font"]["size"]))
        self.txt_result.setStyleSheet(f"background-color: {self.user_settings['txt_result']['bg_color']};")

        self.txt_code.setFont(QFont(self.user_settings["txt_code"]["font"]["name"], self.user_settings["txt_code"]["font"]["size"]))
        self.txt_code.setStyleSheet(f"background-color: {self.user_settings['txt_code']['bg_color']};")

        self.tree_seg.setFont(QFont(self.user_settings["tree_seg"]["font"]["name"], self.user_settings["tree_seg"]["font"]["size"]))

    def mnu_file_export_triggered(self):
        if self.data_source is None:
            QMessageBox.information(self, "Export", "No data loaded to export!", QMessageBox.Ok)
            return
        
        if self.data_source["selected"] == "clip":
            QMessageBox.information(self, "Export", "Clipboard data cannot be exported!\nYou can use project file in your app instead.", QMessageBox.Ok)
            return

        filename = QFileDialog.getSaveFileName(self, "Export Project As", filter="Rashomon Project Files (*.rpf)")[0]
        if filename:
            txt = self.data_source["text"]
            txt_formated = self.data_source["formated_text"]
            self.data_source["text"] = ""
            self.data_source["formated_text"] = ""
            success = True
            try:
                with open(filename, "w", encoding="utf-8") as file:
                    json.dump(self.data_source, file, indent=2)
            except Exception as e:
                success = False
            
            self.data_source["text"] = txt
            self.data_source["formated_text"] = txt_formated
            
            if success:
                QMessageBox.information(self, "Export", "Project exported successfully!", QMessageBox.Ok)
            else:
                QMessageBox.critical(self, "Error", f"Error exporting project: {e}", QMessageBox.Ok)

    def mnu_file_close_triggered(self):
        if self.data_source is None:
            return
        if not self.data_source["saved"]:
            result = self.ask_to_save_project()
            if not result:
                return
        
        self.data_source = None
        self.refresh_tree()
        self.setWindowTitle("Rashomon")

    def ask_to_save_project(self) -> bool:
        result = QMessageBox.question(self, "Unsaved Changes", "Save unsaved changes?", QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, QMessageBox.Yes)
        if result == QMessageBox.Yes:
            self.save_project()
            return True
        elif result == QMessageBox.No:
            return True
        else:
            return False

    def mnu_file_open_triggered(self):
        if self.data_source and not self.data_source["saved"]:
            result = self.ask_to_save_project()
            if not result:
                return
            
        # Open File
        file_path = QFileDialog.getOpenFileName(self, "Open File", "", "Rashomon Project Files (*.rpf)")[0]
        if file_path:
            self.open_project(file_path)

    def open_project(self, filename: str):
        # Load project from file
        if not os.path.isfile(filename):
            QMessageBox.critical(self, "Error", "File not found")
            return
        
        try:
            with open(filename, "r", encoding="utf-8") as file:
                self.data_source =  json.load(file)
            self.data_source["project_filename"] = filename
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error loading project file: {e}")
            return

        self.setWindowTitle("Rashomon - " + os.path.basename(filename))
        self.load_project()
        self.data_source["saved"] = True

    def mnu_file_save_triggered(self):
        if self.data_source is None:
            QMessageBox.information(self, "Save", "You currently have no open projects!\nSave has been cancelled.", QMessageBox.Ok)
            return
        self.save_project()

    def save_project(self, silence: bool = False):
        if not self.data_source["project_filename"]:
            self.mnu_file_save_as_triggered()
            return

        try:
            with open(self.data_source["project_filename"], "w", encoding="utf-8") as file:
                json.dump(self.data_source, file, indent=2)
            self.setWindowTitle("Rashomon - " + os.path.basename(self.data_source["project_filename"]))
            self.data_source["saved"] = True
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Error saving project: {e}", QMessageBox.Ok)
            return
        if not silence:
            QMessageBox.information(self, "Save", "The project was successfully saved.", QMessageBox.Ok)

    def mnu_file_save_as_triggered(self):
        filename = QFileDialog.getSaveFileName(self, "Save Project As", filter="Rashomon Project Files (*.rpf)")[0]
        if filename:
            self.data_source["project_filename"] = filename
            self.save_project()

    def lst_autocomplete_mouse_release(self, e: QMouseEvent):
        if e.button() == Qt.LeftButton:
            self.autocomplete_insert_command()
            self.frm_autocomplete.setVisible(False)

    def txt_code_focus_out(self, e):
        self.frm_autocomplete.setVisible(False)
        QTextEdit.focusOutEvent(self.txt_code, e)

    def txt_code_key_press(self, a0: QKeyEvent):
        cur = self.txt_code.textCursor()
        pos = cur.position()
        txt = self.txt_code.toPlainText()
        double_chars = {
            Qt.Key_Apostrophe : ["'", "'"],
            Qt.Key_QuoteDbl: ['"', '"'],
            Qt.Key_ParenLeft: ["(", ")"],
            Qt.Key_BracketLeft: ["[", "]"],
            Qt.Key_BraceLeft: ["{", "}"],
        }
        if a0.key() in double_chars:
            cur.insertText(double_chars[a0.key()][1])
            cur.setPosition(pos)
            self.txt_code.setTextCursor(cur)
        elif a0.key() == Qt.Key_Backspace and a0.modifiers() == Qt.NoModifier:
            if pos < len(txt) and pos > 0 and txt[pos-1:pos+1] in ["''", '""', "()", "[]", "{}"]:
                cur.setPosition(pos-1)
                cur.movePosition(cur.Right, cur.KeepAnchor, 2)
                cur.removeSelectedText()
                cur.setPosition(pos-1)
                self.txt_code.setTextCursor(cur)
                return
            else:
                QTextEdit.keyPressEvent(self.txt_code, a0)
                return
        elif a0.key() == Qt.Key_Home and a0.modifiers() == Qt.NoModifier:
            line_start = txt[:pos].rfind("\n") + 1
            if line_start == -1:
                line_start = 0
            if txt[line_start:].strip():
                text_start = txt.find(next(x for x in txt[line_start:] if x not in " \n\t"), line_start)
            else:
                text_start = line_start
            if pos > text_start:
                cur.setPosition(text_start)
            elif pos < text_start:
                cur.setPosition(text_start)
            else:
                cur.setPosition(line_start)
            self.txt_code.setTextCursor(cur)
            return
        elif a0.key() == Qt.Key_End and a0.modifiers() == Qt.NoModifier:
            if pos < len(txt):
                if txt[pos] != "\n":
                    line_end = txt.find("\n", pos)
                    if line_end == -1:
                        line_end = len(txt)
                    cur.setPosition(line_end)
                    self.txt_code.setTextCursor(cur)
            return
        elif a0.key() == Qt.Key_Backtab and (a0.modifiers() == Qt.NoModifier or a0.modifiers() == Qt.ShiftModifier):
            tab_pos = txt[:pos].rfind("    ")
            if tab_pos != -1:
                cur.setPosition(tab_pos)
                cur.movePosition(cur.Right, cur.KeepAnchor, 4)
                cur.removeSelectedText()
                cur.setPosition(tab_pos)
                self.txt_code.setTextCursor(cur)
            return
        elif a0.key() == Qt.Key_Tab and a0.modifiers() == Qt.NoModifier:
            cur.insertText("    ")
            cur.setPosition(pos + 4)
            self.txt_code.setTextCursor(cur)
            return
        elif a0.key() == Qt.Key_Up and a0.modifiers() == Qt.NoModifier:
            if self.frm_autocomplete.isVisible() and self.lst_autocomplete.count():
                if self.lst_autocomplete.currentItem() is None:
                    self.lst_autocomplete.setCurrentRow(0)

                item_pos = self.lst_autocomplete.currentRow()
                item_pos -= 1
                if item_pos < 0:
                    item_pos = self.lst_autocomplete.count() - 1
                self.lst_autocomplete.setCurrentRow(item_pos)
            else:
                QTextEdit.keyPressEvent(self.txt_code, a0)
            return
        elif a0.key() == Qt.Key_Down and a0.modifiers() == Qt.NoModifier:
            if self.frm_autocomplete.isVisible() and self.lst_autocomplete.count():
                if self.lst_autocomplete.currentItem() is None:
                    self.lst_autocomplete.setCurrentRow(self.lst_autocomplete.count() - 1)

                item_pos = self.lst_autocomplete.currentRow()
                item_pos += 1
                if item_pos >= self.lst_autocomplete.count():
                    item_pos = 0
                self.lst_autocomplete.setCurrentRow(item_pos)
            else:
                QTextEdit.keyPressEvent(self.txt_code, a0)
            return
        elif (a0.key() == Qt.Key_Enter or a0.key() == Qt.Key_Return) and a0.modifiers() == Qt.NoModifier:
            if self.frm_autocomplete.isVisible() and self.lst_autocomplete.currentItem() is not None:
                self.autocomplete_insert_command()
            else:
                indent_start = txt[:pos].rfind("\n") + 1
                if not txt[indent_start:pos].strip():
                    indent_value = pos - indent_start
                else:
                    indent_value = txt[indent_start:pos].find(next(x for x in txt[indent_start:pos] if x not in " \t\n"))
                if txt[indent_start:pos].lstrip().startswith(("BeginSegment", "DefineStartString", "DefineEndString", "If")):
                    indent_value += 4
                cur.insertText("\n" + " " * indent_value)
                cur.setPosition(pos + indent_value + 1)
                self.txt_code.setTextCursor(cur)
            return
        elif a0.key() == Qt.Key_Escape and a0.modifiers() == Qt.NoModifier:
            if self.frm_autocomplete.isVisible():
                self.frm_autocomplete.setVisible(False)
            return

        QTextEdit.keyPressEvent(self.txt_code, a0)

    def mnu_tree_rename_triggered(self):
        self._rename_segment()

    def autocomplete_insert_command(self):
        if self.lst_autocomplete.currentItem() is None:
            return
        
        txt = self.txt_code.toPlainText()

        self._code_txtbox_protected = True
        command = self.lst_autocomplete.currentItem().text()
        end_command = self.lst_autocomplete.currentItem().data(Qt.UserRole)
        if command == "BeginSegment":
            command += " ()"
            cur_pos = len(command) - 1
        elif command == "Parent":
            command += ' = ``'
            cur_pos = len(command) - 1
        elif command in ["IsEqual", "StartsWith", "EndsWith", "StartString", "EndString", "ContainsString"]:
            command += ' ``'
            cur_pos = len(command) - 1
        elif command in ["Index", "MatchCase"]:
            command += ' = '
            cur_pos = len(command)
        elif command in ["And", "Or", "Not"]:
            command += " "
            cur_pos = len(command)
        else:
            command += "\n"
            cur_pos = len(command)

        cur = self.txt_code.textCursor()
        cur.select(QTextCursor.WordUnderCursor)
        pos = cur.position()

        indent_start = txt[:pos].rfind("\n") + 1
        if not txt[indent_start:pos].strip():
            indent_value = pos - indent_start
        else:
            indent_value = txt[indent_start:pos].find(next(x for x in txt[indent_start:pos] if x not in " \t\n"))

        cur.insertText("")
        pos = cur.position()
        
        cur.insertText(command)

        if command.strip() in ("DefineStartString", "DefineEndString", "If"):
            cur.insertText(" " * (indent_value + 4))
            cur_pos += indent_value + 4

        if end_command:
            cur.insertText("\n" + " " * indent_value + end_command)
        cur.setPosition(pos + cur_pos)
        self.txt_code.setTextCursor(cur)
        self._code_txtbox_protected = False
        self.txt_code_text_changed()

    def autocomplete(self):
        """Autocomplete code in txtbox"""
        if self.user_settings["txt_code"]["autocomplete"]["show"] is not None:
            if not self.user_settings["txt_code"]["autocomplete"]["show"]:
                return

        cursor = self.txt_code.textCursor()
        
        # Get current word
        cursor.select(QTextCursor.WordUnderCursor)
        word_under_cursor = cursor.selectedText()

        cancel_chars = "()\"'=0123456789`|!@#\$%^&*+-={}[];:.,<>?~"
        if any(char in cancel_chars for char in word_under_cursor):
            self.frm_autocomplete.setVisible(False)
            return

        # If there is no word, return
        if not word_under_cursor.strip():
            self.frm_autocomplete.setVisible(False)
            return
        self.frm_autocomplete.setVisible(True)

        # Check autocomplete suggestions
        suggestions = self.get_autocomplete_suggestions()
        self.refresh_autocomplete_frame(suggestions)

    def _command_description(self, command_line: str) -> str:
        command_line = command_line.strip()
        if not command_line:
            return ""
        
        command = self.script.code.get_command_object_for_code_line(command_line)
        if command is None:
            if command_line.startswith("And"):
                command_desc = '"And" is a logical operator between two conditions.\nBoth conditions must be satisfied for the expression to be true.'
                command_exm = 'n/a'
                command_name = "And"
            elif command_line.startswith("Or"):
                command_desc = '"Or" is a logical operator between two conditions.\nEither of the conditions must be satisfied for the expression to be true.'
                command_exm = 'n/a'
                command_name = "Or"
            elif command_line.startswith("Not"):
                command_desc = '"Not" is a logical operator placed before a condition.\nIf the condition is false, the expression is true and vice versa.'
                command_exm = 'n/a'
                command_name = "Not"
            else:
                return ""
        else:
            command_obj = command(command_line, 0, "", "")
            command_desc = command_obj.data.Description
            command_exm = command_obj.data.Example
            command_name = command_obj.name

        txt = "#1\n\n#2\n\nEXAMPLE:\n#3"
        html = text_to_html_cls.TextToHTML(txt)
        html_rule_title = text_to_html_cls.TextToHtmlRule(
            text="#1",
            replace_with=command_name,
            fg_color="#55ff00",
            font_bold=True,
            font_size=42,
            font_underline=True)
        html_rule_desc = text_to_html_cls.TextToHtmlRule(
            text="#2",
            replace_with=command_desc,
            font_size=16,
            fg_color="#aaff7f"
        )
        html_rule_exm = text_to_html_cls.TextToHtmlRule(
            text="#3",
            replace_with=command_exm,
            font_size=14,
            fg_color="#aaffff"
        )
        html_rule_basic = text_to_html_cls.TextToHtmlRule(fg_color="#ffff7f", font_size=20)
        html.general_rule = html_rule_basic
        html.add_rule(html_rule_title)
        html.add_rule(html_rule_exm)
        html.add_rule(html_rule_desc)
        return html.get_html()
    
    def refresh_autocomplete_frame(self, suggestions: list):
        frame_pos = self.mapFromGlobal(self.txt_code.mapToGlobal(self.txt_code.cursorRect().bottomRight()))

        color_map = {
            0: "#00ff00",
            1: "#aaff00",
            10: "#00ffff",
            11: "#aaffff",
            12: "#d0d0d0",
            13: "#818181"
        }
        
        self.lst_autocomplete.clear()
        
        self.lst_autocomplete.setFont(self.txt_code.font())
        self.frm_autocomplete.setStyleSheet(self.txt_code.styleSheet())
        
        fm = QFontMetrics(self.lst_autocomplete.font())

        max_item_width = 100
        list_height = 0

        for suggestion in suggestions:
            item_text_width = fm.width(suggestion[0])
            if item_text_width > max_item_width:
                max_item_width = item_text_width

            item = QListWidgetItem()
            item.setText(suggestion[0])
            item.setData(Qt.UserRole, suggestion[1])
            item.setToolTip(self._command_description(suggestion[0]))
            item.setIcon(QIcon(QPixmap(suggestion[3])))
            item.setForeground(QColor(color_map.get(suggestion[2],"#cbcb65")))
            
            self.lst_autocomplete.addItem(item)
        
        for i in range(self.lst_autocomplete.count()):
            list_height += self.lst_autocomplete.sizeHintForRow(i)
        list_height += self.lst_autocomplete.contentsMargins().top()
        list_height += self.lst_autocomplete.contentsMargins().bottom()

        max_item_width += 50
        if list_height < 40:
            list_height = 40
        x = frame_pos.x()
        y = frame_pos.y()
        if y > self.contentsRect().height() - 100:
            y = self.contentsRect().height() - 100
        if y < 0:
            y = 0
        if x + max_item_width > self.contentsRect().width():
            x = self.contentsRect().width() - max_item_width
        if x < 0:
            x = 0
        self.frm_autocomplete.move(x, y)
        if self.contentsRect().height() - self.frm_autocomplete.pos().y() < list_height:
            list_height = self.contentsRect().height() - self.frm_autocomplete.pos().y()
        self.frm_autocomplete.resize(max_item_width + 50, list_height)

        self.lst_autocomplete.move(0, 0)
        self.lst_autocomplete.resize(self.frm_autocomplete.contentsRect().width(), self.frm_autocomplete.contentsRect().height())
        if self.user_settings["txt_code"]["autocomplete"]["autoselect"] is not None:
            if self.user_settings["txt_code"]["autocomplete"]["autoselect"]:
                self.lst_autocomplete.setCurrentRow(0)

    def get_autocomplete_suggestions(self)-> list:
        """Return list of autocomplete suggestions"""

        # priority [Command name, 
        # complete with, out of segment, in segment, in start/end, in if, in line operator]
        priority = [
            ["BeginSegment",            1,      1,  0,  0,  0,  0, "data/rashomon/images/segment_code.png"],
            ["EndSegment",              1000,   0,  2,  0,  0,  0, "data/rashomon/images/segment_code.png"],
            ["Parent",                  None,   0,  1,  0,  0,  0, "data/rashomon/images/parent.png"],
            ["Index",                   None,   0,  1,  0,  0,  0, "data/rashomon/images/index.png"],
            ["IsEqual",                 None,   0,  0,  1,  0,  0, "data/rashomon/images/condition.png"],
            ["StartsWith",              None,   0,  0,  1,  0,  0, "data/rashomon/images/condition.png"],
            ["EndsWith",                None,   0,  0,  1,  0,  0, "data/rashomon/images/condition.png"],
            ["MatchCase",               None,   0,  1,  0,  0,  0, "data/rashomon/images/matchcase.png"],
            ["DefineStartString",       9,      0,  1,  0,  0,  0, "data/rashomon/images/code_block.png"],
            ["EndDefineStartString",    1008,   0,  0,  2,  0,  0, "data/rashomon/images/code_block.png"],
            ["DefineEndString",         11,     0,  1,  0,  0,  0, "data/rashomon/images/code_block.png"],
            ["EndDefineEndString",      1010,   0,  0,  2,  0,  0, "data/rashomon/images/code_block.png"],
            ["If",                      13,     0,  0,  1,  0,  0, "data/rashomon/images/if.png"],
            ["EndIf",                   1012,   0,  0,  0,  2,  0, "data/rashomon/images/if.png"],
            ["ContainsString",          None,   0,  0,  0,  1,  1, "data/rashomon/images/if_condition.png"],
            ["StartString",             None,   0,  0,  0,  1,  1, "data/rashomon/images/if_condition.png"],
            ["EndString",               None,   0,  0,  0,  1,  1, "data/rashomon/images/if_condition.png"],
            ["Or",                      None,   0,  0,  0,  0,  1, "data/rashomon/images/operator_or.png"],
            ["And",                     None,   0,  0,  0,  0,  1, "data/rashomon/images/operator_and.png"],
            ["Not",                     None,   0,  0,  0,  1,  1, "data/rashomon/images/operator_not.png"]
        ]

        txt = self.txt_code.toPlainText()
        if not txt:
            return []
        
        cur = self.txt_code.textCursor()
        cur.select(QTextCursor.WordUnderCursor)
        word_under_cursor = cur.selectedText()

        pos = cur.position()
        pos_in_code = 0
        txt_list = txt.split("\n")
        pos_index = 2
        
        cancel_commands = ["BeginSegment"]
        for i in txt_list:
            if i.lstrip().startswith("Parent"):
                cancel_commands.append("Parent")
            if i.lstrip().startswith("Index"):
                cancel_commands.append("Index")
            if i.lstrip().startswith("MatchCase"):
                cancel_commands.append("MatchCase")
        
        for idx, line in enumerate(txt_list):
            original_line = line
            line = line.lstrip()

            if line.startswith("BeginSegment"):
                pos_index = 3
            elif line.startswith("EndSegment"):
                pos_index = 2
            elif line.startswith("DefineStartString") or line.startswith("DefineEndString"):
                pos_index = 4
            elif line.startswith("EndDefineStartString") or line.startswith("EndDefineEndString"):
                pos_index = 3
            elif line.startswith("If"):
                pos_index = 5
            elif line.startswith("EndIf"):
                pos_index = 4
            if pos_index == 5 or pos_index == 6:
                if line.count(" ") > 0:
                    pos_index = 6
                else:
                    pos_index = 5

            if not (pos >= pos_in_code and pos < (pos_in_code + len(original_line) + 1)):
                pos_in_code += len(original_line) + 1
                continue

            prior1 = []
            prior2 = []
            for item in priority:
                complete_with = ""
                if item[1] is not None and item[1] < 1000:
                    complete_with = priority[item[1]][0]

                if item[pos_index] == 1:
                    prior1.append([item[0], complete_with, item[7]])
                if item[pos_index] == 0:
                    prior2.append([item[0], complete_with, item[7]])
                
                if item[pos_index] == 2:
                    has_part1 = False
                    for i in range(0, idx):
                        if txt_list[i].lstrip().startswith(priority[item[1] - 1000][0]):
                            has_part1 = True
                            break
                    has_part2 = False
                    for i in range(idx, len(txt_list)):
                        if txt_list[i].lstrip().startswith(item[0]):
                            has_part2 = True
                    if has_part1 and not has_part2:
                        prior1.append([item[0], complete_with, item[7]])
                    else:
                        prior2.append([item[0], complete_with, item[7]])
            break
            
        result = []
        word_under_cursor = word_under_cursor.lower()
        if len(word_under_cursor) < 2:
            for i in prior1:
                if i[0] in cancel_commands and pos_index >= 3:
                    result.append([i[0], i[1], 13, i[2]])
                else:
                    if i[0].lower().startswith(word_under_cursor):
                        result.append([i[0], i[1], 0, i[2]])
                    else:
                        result.append([i[0], i[1], 11, i[2]])
            for i in prior2:
                if i[0] in cancel_commands and pos_index >= 3:
                    result.append([i[0], i[1], 13, i[2]])
                else:
                    if i[0].lower().startswith(word_under_cursor):
                        result.append([i[0], i[1], 10, i[2]])
                    else:
                        result.append([i[0], i[1], 11, i[2]])
        else:
            for i in prior1:
                if i[0] in cancel_commands and pos_index >= 3:
                    result.append([i[0], i[1], 13, i[2]])
                else:
                    if i[0].lower().startswith(word_under_cursor):
                        result.append([i[0], i[1], 0, i[2]])
                    elif i[0].lower().find(word_under_cursor) != -1:
                        result.append([i[0], i[1], 1, i[2]])
                    else:
                        result.append([i[0], i[1], 12, i[2]])
            for i in prior2:
                if i[0] in cancel_commands and pos_index >= 3:
                    result.append([i[0], i[1], 13, i[2]])
                else:
                    if i[0].lower().startswith(word_under_cursor):
                        result.append([i[0], i[1], 10, i[2]])
                    elif i[0].lower().find(word_under_cursor) != -1:
                        result.append([i[0], i[1], 11, i[2]])
                    else:
                        result.append([i[0], i[1], 13, i[2]])
        
        result.sort(key=lambda x: x[2])
        return result

    def _rename_segment(self, segment_to_rename: str = None, new_name: str = None):
        is_working_visible = self.frm_working.isVisible()
        self.frm_working.setVisible(True)
        QCoreApplication.processEvents()

        if not segment_to_rename:
            if self.tree_seg.currentItem():
                segment_to_rename = self.tree_seg.currentItem().text(0)
        
        if segment_to_rename:
            if not new_name:
                new_name, ok = QInputDialog.getText(self, "Rename Segment", 
                    "New Name:", QLineEdit.Normal, segment_to_rename)
            else:
                ok = True
            if ok and new_name != "":
                result = self.script.rename_segment(segment_to_rename, new_name)
                if result["error"]:
                    QMessageBox.critical(self, "Error", result["error"], QMessageBox.Ok)
                else:
                    self.refresh_tree(new_name)
                    self.refresh_project()
                    txt = f'{result["renamed"]} segment(s) is renamed.\n'
                    txt += f'{result["parent_changed"]} child segment(s) "Parent" value is updated.\n'
                    txt += f'In total {result["renamed"] + result["parent_changed"]} segment(s) are affected.'
                    QMessageBox.information(self, "Segment Renamed", txt, QMessageBox.Ok)
                    self.data_source["saved"] = False
        self.frm_working.setVisible(is_working_visible)

    def chk_apply_all_code_state_changed(self):
        self.user_settings["chk_apply_all_code"]["is_checked"] = self.chk_apply_all_code.isChecked()
    
    def chk_apply_all_state_changed(self):
        self.user_settings["chk_apply_all"]["is_checked"] = self.chk_apply_all.isChecked()

    def btn_abort_click(self):
        self.abort_action = True

    def txt_code_text_changed(self):
        if not self._code_txtbox_protected:
            slider_pos = self.txt_code.verticalScrollBar().value()
            cur = self.txt_code.textCursor()
            pos = cur.position()
            self.format_code_textbox(self.txt_code.toPlainText())
            cur.setPosition(pos)
            cur.setCharFormat(self.old_txt_rule_cf)
            self.txt_code.setTextCursor(cur)
            self.txt_code.verticalScrollBar().setValue(slider_pos)
            QCoreApplication.processEvents()
            self.autocomplete()
    
    def btn_apply_code_click(self):
        if self.current_segment is None:
            QMessageBox.information(self, "Error", "No Active Segment !", QMessageBox.Ok)
            return
        
        if not self.txt_code.toPlainText().strip():
            QMessageBox.information(self, "Error", "No Code !", QMessageBox.Ok)
            return
        
        self.frm_working.setVisible(True)
        self.prg_working.setVisible(True)
        self.abort_action = False
        QCoreApplication.processEvents()

        new_code = self.txt_code.toPlainText().strip()
        new_code_list = new_code.split("\n")

        if not new_code_list[0].startswith("BeginSegment") or not new_code_list[-1].startswith("EndSegment"):
            QMessageBox.critical(self, "Error", 'Code must start with "BeginSegment" and end with "EndSegment"\nCode execution canceled!', QMessageBox.Ok)
            return

        self.data_source["saved"] = False

        # Rename if needed
        old_segment_name = self.current_segment.name
        new_segment_name = self.script.code.get_command_value(new_code_list[0])
        if old_segment_name != new_segment_name:
            self._rename_segment(old_segment_name, new_segment_name)

        siblings = []

        include_siblings = self.chk_apply_all_code.isChecked()
        if self.current_segment.parent is None:
            include_siblings = False
        
        if include_siblings:
            siblings_map = self.script.get_segments_map_name_parent(siblings_for=self.current_segment.name)
            for i in siblings_map:
                siblings.append(i[0])
        else:
            siblings.append(self.current_segment.name)

        for idx, seg in enumerate(siblings):
            self.prg_working.setValue(int(idx / len(siblings) * 100))
            QCoreApplication.processEvents()
                
            segment = segment_cls.Segment(self.script._get_segment_script(seg))
            updated_code = self.script.update_segment_code(segment.code, new_code)
            result = self.script.update_block_in_segment(seg, updated_code.strip(), replace_in_all_siblings=False)

            if self.abort_action:
                result["errors"] += "Interupted by User !\n"

            if result["errors"]:
                QMessageBox.critical(self, "Error", result["errors"], QMessageBox.Ok)
                break

        self.current_segment = self.script.segment(self.current_segment.name)
        self.refresh_tree(self.current_segment.name)
        self.refresh_project()

        self.frm_working.setVisible(False)
        self.prg_working.setVisible(False)
        self.abort_action = False
        if not result["errors"]:
            QMessageBox.information(self, "Success", f'Code is applied successfully!\n Found {result["count"]} new segments.', QMessageBox.Ok)

    def line_sep_mouse_move(self, e: QMouseEvent):
        x = QCursor.pos().x() - self.drag_mode[1]
        x = self.drag_mode[0] + x
        if x < 50:
            x = 50
        if x > self.contentsRect().width() - 50:
            x = self.contentsRect().width() - 50
        
        self.line_sep.move(x, self.line_sep.pos().y())
        self._resize_me()

    def line_sep_mouse_release(self, e: QMouseEvent):
        self.drag_mode = None
        self.user_settings["separator"]["position"] = self.line_sep.pos().x()

    def line_sep_mouse_press(self, e: QMouseEvent):
        self.drag_mode = [self.line_sep.pos().x(), QCursor.pos().x()]

    def line_sep_enter(self, e: QMouseEvent):
        self.setCursor(Qt.SizeHorCursor)

    def line_sep_leave(self, e: QMouseEvent):
        self.setCursor(Qt.ArrowCursor)

    def btn_apply_rule_click(self):
        if self.current_segment is None:
            return
        
        self.frm_working.setVisible(True)
        self.prg_working.setVisible(True)
        self.prg_working.setValue(1)
        QCoreApplication.processEvents()
        self.data_source["saved"] = False

        start_rules = []
        end_rules = []
        for i in range(self.lst_rules.count()):
            rule = self.lst_rules.item(i).text()
            if rule.startswith("START:"):
                start_rules.append(rule[6:].strip())
            elif rule.startswith("END:"):
                end_rules.append(rule[4:].strip())
        
        with_if = "        If\n"
        without_if = ""
        for i in start_rules:
            if i.startswith("If"):
                with_if += f"            {i[3:]}\n"
            else:
                without_if += f"        {i}\n"
        
        with_if += "        EndIf\n"
        start_block = "    DefineStartString\n" + without_if + "\n" + with_if + "\n" + "    EndDefineStartString"
        
        with_if = "        If\n"
        without_if = ""
        for i in end_rules:
            if i.startswith("If"):
                with_if += f"            {i[3:]}\n"
            else:
                without_if += f"        {i}\n"
        
        with_if += "        EndIf\n"
        end_block = "    DefineEndString\n" + without_if + "\n" + with_if + "\n" + "    EndDefineEndString"

        include_siblings = self.chk_apply_all.isChecked()
        if self.current_segment.parent is None:
            include_siblings = False

        result = self.script.update_block_in_segment(self.current_segment.name, start_block, replace_in_all_siblings=include_siblings, feedback_function=self.feedback_progress)
        if result["errors"]:
            QMessageBox.critical(self, "Error", result["errors"], QMessageBox.Ok)

        QCoreApplication.processEvents()
        if not self.abort_action:                
            result = self.script.update_block_in_segment(self.current_segment.name, end_block, replace_in_all_siblings=include_siblings, feedback_function=self.feedback_progress)
            if result["errors"]:
                QMessageBox.critical(self, "Error", result["errors"], QMessageBox.Ok)

        self.current_segment = self.script.segment(self.current_segment.name)
        self.refresh_tree(self.current_segment.name)
        self.refresh_project()

        self.frm_working.setVisible(False)
        self.prg_working.setVisible(False)
        self.abort_action = False
        if not result["errors"]:
            QMessageBox.information(self, "Success", f'Rules applied successfully!\n Found {result["count"]} new segments.', QMessageBox.Ok)

    def feedback_progress(self, data: dict) -> bool:
        if data["total"] == 0:
            self.prg_working.setValue(0)
            QCoreApplication.processEvents()
            return
        percent = data["current"] / data["total"]
        self.prg_working.setValue(int(percent*100))
        QCoreApplication.processEvents()
        return self.abort_action

    def mnu_lst_rules_del_item_triggered(self):
        if not self.lst_rules.currentItem():
            return
        self.lst_rules.takeItem(self.lst_rules.currentRow())

    def mnu_lst_rules_del_all_triggered(self):
        self.lst_rules.clear()

    def txt_rule_is_equal_to_return_press(self):
        self._add_rule_click(self.txt_rule_is_equal_to, False)
    
    def txt_rule_starts_with_return_press(self):
        self._add_rule_click(self.txt_rule_starts_with, False)

    def mnu_tree_del_triggered(self):
        segment_name = self.current_segment.name
        if segment_name != self.tree_seg.currentItem().text(0):
            return
        
        result = QMessageBox.question(self, "Delete Segment", f'Are you sure you want to delete the current segment?\nSegment "{segment_name}" and all its subsegments will be deleted!', QMessageBox.Yes|QMessageBox.No|QMessageBox.Cancel, QMessageBox.No)
        if result != QMessageBox.Yes:
            return
        self.script.delete_segment_children(segment_name, segments_map=None, delete_current_segment_also=True)
        self.refresh_tree()
        self.refresh_project()
        self.frm_working.setVisible(False)
        self.data_source["saved"] = False
        QMessageBox.information(self, "Segment Deleted", "The segment was successfully deleted!", QMessageBox.Ok)

    def mnu_tree_add_top_level_triggered(self):
        if not self.data_source["text"]:
            QMessageBox.critical(self, "No Data", "There is no working text!\nPlease first open an existing project or start a new one.\nTop level segment cannot be added!", QMessageBox.Ok)
            return

        msg = "Enter segment name:"
        while True:
            segment_name, ok = QInputDialog.getText(self, 'New Segment', msg, QLineEdit.Normal, '')
            if ok and segment_name:
                if segment_name in self.script.get_all_segments(names_only=True):
                    msg = f'A segment named "{segment_name}" already exists.\nYou cannot add a segment with the same name as a segment that already exists.\nPlease choose a different name.\nEnter segment name:'
                else:
                    break
            else:
                break
        
        if ok and segment_name:
            if segment_name in self.script.get_all_segments(names_only=True):
                QMessageBox.critical(self, "Segment Error", "")
            self.data_source["code"] += "\n" + self._new_top_level_segment_code(segment_name=segment_name)
            self.refresh_tree(segment_name)
            self.data_source["saved"] = False

    def tree_seg_context_menu(self):
        if self.data_source is None or (not self.data_source["formated_text"] and not self.data_source["text"]):
            self.mnu_tree_add_top_level.setDisabled(True)
        else:
            self.mnu_tree_add_top_level.setDisabled(False)
        if self.tree_seg.currentItem() is None:
            self.mnu_tree_del.setDisabled(True)
            self.mnu_tree_del.setText("Delete (No Current Segment)")
        else:
            self.mnu_tree_del.setDisabled(False)
            self.mnu_tree_del.setText(f"Delete ({self.tree_seg.currentItem().text(0)})")

        self.mnu_tree.exec_(QCursor.pos())

    def txt_rule_ends_with_return_press(self):
        self._add_rule_click(self.txt_rule_ends_with, False)
    
    def lst_rules_context_menu(self):
        if self.lst_rules.count():
            self.mnu_lst_rules_del_all.setEnabled(True)
        else:
            self.mnu_lst_rules_del_all.setEnabled(False)
        if self.lst_rules.currentItem() is None:
            self.mnu_lst_rules_del_item.setText("Delete Item")
            self.mnu_lst_rules_del_item.setEnabled(False)
        else:
            self.mnu_lst_rules_del_item.setText(f'Delete "{self.lst_rules.currentItem().text()}"')
            self.mnu_lst_rules_del_item.setEnabled(True)

        self.mnu_lst_rules.exec_(QCursor.pos())

    def txt_rule_is_equal_to_text_changed(self):
        if self.txt_rule_is_equal_to.text():
            self.btn_rule_add_is_equal_to.setEnabled(True)
        else:
            self.btn_rule_add_is_equal_to.setEnabled(False)

    def txt_rule_starts_with_text_changed(self):
        if self.txt_rule_starts_with.text():
            self.btn_rule_add_starts_with.setEnabled(True)
        else:
            self.btn_rule_add_starts_with.setEnabled(False)

    def txt_rule_ends_with_text_changed(self):
        if self.txt_rule_ends_with.text():
            self.btn_rule_add_ends_with.setEnabled(True)
        else:
            self.btn_rule_add_ends_with.setEnabled(False)

    def txt_rule_starts_text_changed(self):
        if self.txt_rule_starts.text():
            self.btn_rule_add_starts.setEnabled(True)
        else:
            self.btn_rule_add_starts.setEnabled(False)

    def txt_rule_ends_text_changed(self):
        if self.txt_rule_ends.text():
            self.btn_rule_add_ends.setEnabled(True)
        else:
            self.btn_rule_add_ends.setEnabled(False)

    def txt_rule_contain_text_changed(self):
        if self.txt_rule_contain.text():
            self.btn_rule_add_contain.setEnabled(True)
        else:
            self.btn_rule_add_contain.setEnabled(False)

    def btn_rule_add_starts_click(self):
        self._add_rule_click(self.txt_rule_starts, self.btn_rule_not_starts)
        
    def btn_rule_add_ends_click(self):
        self._add_rule_click(self.txt_rule_ends, self.btn_rule_not_ends)

    def btn_rule_add_contain_click(self):
        self._add_rule_click(self.txt_rule_contain, self.btn_rule_not_contain)

    def _add_rule_click(self, txtbox: QLineEdit, not_btn: QPushButton):
        if not txtbox.text():
            return
        
        txt = txtbox.text()
        add_string = ""
        if txtbox.objectName() == "txt_rule_starts":
            add_string = "If StartString"
        elif txtbox.objectName() == "txt_rule_ends":
            add_string = "If EndString"
        elif txtbox.objectName() == "txt_rule_contain":
            add_string = "If ContainsString"
        elif txtbox.objectName() == "txt_rule_is_equal_to":
            add_string = "IsEqual"
        elif txtbox.objectName() == "txt_rule_starts_with":
            add_string = "StartsWith"
        elif txtbox.objectName() == "txt_rule_ends_with":
            add_string = "EndsWith"
        else:
            return

        if txt.find('"') == -1:
            add_string += f' "{txt}"'
        elif txt.find("'") == -1:
            add_string += f" '{txt}'"
        elif txt.find("|") == -1:
            add_string += f" |{txt}|"
        elif txt.find("`") == -1:
            add_string += f" `{txt}`"
        else:
            QMessageBox.critical(self, "Error", "Rule text cannot be parsed!\nThe problem was caused by some of the characters ( \", ', |, ` )\nPlease remove some of these characters from the expression.", QMessageBox.Ok)
            return None

        not_string = False
        if isinstance(not_btn, QPushButton):
            not_string = not_btn.isChecked()
        elif isinstance(not_btn, bool):
            not_string = not_btn

        if not_string:
            if add_string.startswith("If "):
                add_string = "If Not " + add_string[3:]
            else:
                add_string = "Not " + add_string
        
        if self.rbt_start.isChecked():
            add_string = "START: " + add_string
        elif self.rbt_end.isChecked():
            add_string = "END: " + add_string

        self.lst_rules.addItem(add_string)

    def tree_seg_current_changed(self, x = None, y = None):
        if not self._tree_change_current_protected:
            if self.tree_seg.currentItem() is not None and self.current_segment is not None:
                if self.tree_seg.currentItem().text(0) != self.current_segment.name:
                    self.refresh_project()

    def tree_seg_item_double_click(self):
        self.refresh_project()

    def btn_seg_zoom_in_click(self):
        self._font_zoom(self.tree_seg, 1)

    def btn_seg_zoom_out_click(self):
        self._font_zoom(self.tree_seg, -1)

    def btn_result_zoom_in_click(self):
        self._font_zoom(self.txt_result, 1)

    def btn_result_zoom_out_click(self):
        self._font_zoom(self.txt_result, -1)

    def btn_code_zoom_in_click(self):
        self._font_zoom(self.txt_code, 1)

    def btn_code_zoom_out_click(self):
        self._font_zoom(self.txt_code, -1)

    def _font_zoom(self, object: QWidget, step: int) -> None:
        size = object.font().pointSize()
        size += step
        if size < 4:
            size = 4
        if size > 72:
            size = 72
        font = object.font()
        font.setPointSize(size)
        object.setFont(font)
        self.user_settings[object.objectName()]["font"]["size"] = size

    def _click_near_result(self, cur_pos: int) -> int:
        txt = self.txt_find.text().lower()
        if not txt:
            return None

        result_txt = self.txt_result.toPlainText().lower()
        total_results = result_txt.count(txt)

        count = 1
        pos = 0
        found_position = None
        prev_near = None
        while True:
            prev_near = abs(pos - cur_pos)
            pos = result_txt.find(txt, pos)
            if pos == -1:
                break

            if pos >= cur_pos:
                now_near = abs(pos - cur_pos)
                if prev_near < now_near:
                    found_position = count - 1
                else:
                    found_position = count
                break
            
            count += 1
            pos += 1

        if found_position is None:
            found_position = total_results
        
        if found_position == 0:
            found_position = 1

        return found_position

    def btn_find_go_click(self):
        txt = self.txt_find.text().lower()
        if not txt:
            return
        result_txt = self.txt_result.toPlainText().lower()

        cur = self.txt_result.textCursor()
        cf = QTextCharFormat()
        color = QColor()

        count = 1
        pos = 0
        position = 0
        while True:
            pos = result_txt.find(txt, pos)
            if pos == -1:
                break
            
            if count == self.search_position:
                cur.setPosition(pos)
                cur.movePosition(cur.Right, cur.KeepAnchor, len(txt))
                color.setNamedColor(self.FOUND_COLOR)
                cf.setBackground(color)
                cur.mergeCharFormat(cf)
                position = pos
                break
            
            pos += len(txt)
            count += 1

        cur.setPosition(position)
        self.txt_result.setTextCursor(cur)
        self.lbl_search_info.setText(f"Found result {self.search_position}/{result_txt.count(txt)}")

    def btn_find_next_click(self):
        txt = self.txt_find.text().lower()
        if not txt:
            return
        result_txt = self.txt_result.toPlainText().lower()
        if self.search_position >= result_txt.count(txt):
            if result_txt.count(txt):
                self.search_position -= 1
            else:
                return
        
        cur = self.txt_result.textCursor()
        cf = QTextCharFormat()
        color = QColor()

        count = 1
        pos = 0
        position = 0
        while True:
            pos = result_txt.find(txt, pos)
            if pos == -1:
                break
            
            if count == self.search_position:
                cur.setPosition(pos)
                cur.movePosition(cur.Right, cur.KeepAnchor, len(txt))
                color.setNamedColor(self.SEARCHED_COLOR)
                cf.setBackground(color)
                cur.mergeCharFormat(cf)
            
            if count == self.search_position + 1:
                cur.setPosition(pos)
                cur.movePosition(cur.Right, cur.KeepAnchor, len(txt))
                color.setNamedColor(self.FOUND_COLOR)
                cf.setBackground(color)
                cur.mergeCharFormat(cf)
                position = pos
                self.search_position += 1
                break
            
            pos += len(txt)
            count += 1

        cur.setPosition(position)
        self.txt_result.setTextCursor(cur)
        self.lbl_search_info.setText(f"Found result {self.search_position}/{result_txt.count(txt)}")

    def btn_find_prev_click(self):
        if self.search_position <= 1:
            return 
        
        txt = self.txt_find.text().lower()
        if not txt:
            return
        result_txt = self.txt_result.toPlainText().lower()
        cur = self.txt_result.textCursor()
        cf = QTextCharFormat()
        color = QColor()

        count = 1
        pos = 0
        position = 0
        while True:
            pos = result_txt.find(txt, pos)
            if pos == -1:
                break
            
            if count == self.search_position - 1:
                cur.setPosition(pos)
                cur.movePosition(cur.Right, cur.KeepAnchor, len(txt))
                color.setNamedColor(self.FOUND_COLOR)
                cf.setBackground(color)
                cur.mergeCharFormat(cf)
                position = pos

            if count == self.search_position:
                cur.setPosition(pos)
                cur.movePosition(cur.Right, cur.KeepAnchor, len(txt))
                color.setNamedColor(self.SEARCHED_COLOR)
                cf.setBackground(color)
                cur.mergeCharFormat(cf)
                break
            
            pos += len(txt)
            count += 1

        cur.setPosition(position)
        self.txt_result.setTextCursor(cur)
        self.search_position -= 1
        self.lbl_search_info.setText(f"Found result {self.search_position}/{result_txt.count(txt)}")

    def txt_find_return_pressed(self):
        self.spin_find_go.setMaximum(self.txt_result.toPlainText().lower().count(self.txt_find.text().lower()))
        self._find_text_in_results()

    def txt_find_text_changed(self):
        txt = self.txt_find.text().lower()

        if not txt:
            self.lbl_search_info.setText("")
            return
        
        self.spin_find_go.setMaximum(self.txt_result.toPlainText().lower().count(self.txt_find.text().lower()))
        if len(txt) < 3:
            self.lbl_search_info.setText("Type at least 3 characters for automatic search or press ENTER to search")
            return
        
        if self.txt_result.toPlainText().lower().count(txt) > 500:
            self.lbl_search_info.setText("There are more than 500 search results, press ENTER to search.")
            return

        self._find_text_in_results()

    def _find_text_in_results(self):
        frm_working_state = self.frm_working.isVisible()
        self.frm_working.setVisible(True)
        self.prg_working.setVisible(False)
        QCoreApplication.processEvents()
        QCoreApplication.processEvents()
        self.spin_find_go.setMaximum(self.txt_result.toPlainText().lower().count(self.txt_find.text().lower()))
        self.search_position = 0
        slider_position = self.txt_result.verticalScrollBar().value()
        txt = self.txt_find.text().lower()
        result_txt = self.txt_result.toPlainText().lower()
        cur = self.txt_result.textCursor()
        cf = QTextCharFormat()
        color = QColor()
        position = cur.position()

        color.setNamedColor("#1d1d1d")
        cf.setBackground(color)
        cur.select(QtGui.QTextCursor.Document)
        cur.mergeCharFormat(cf)
        cur.setPosition(0)

        if not txt:
            cur.setPosition(position)
            self.txt_result.setTextCursor(cur)
            self.lbl_search_info.setText("No search results.")
            self.txt_result.verticalScrollBar().setValue(slider_position)
            self.frm_working.setVisible(frm_working_state)
            self.abort_action = False
            return
        
        if result_txt.count(txt) > 500:
            self.txt_result.setTextCursor(cur)
            self.lbl_search_info.setText(f"Found {result_txt.count(txt)} results. A search with over 500 results is not marked in text.")
            self.frm_working.setVisible(frm_working_state)
            self.abort_action = False
            return
        
        if len(result_txt) > 150000:
            self.txt_result.setTextCursor(cur)
            self.lbl_search_info.setText(f"Found {result_txt.count(txt)} results. The search results are not marked because this operation on such a long document would take a long time.")
            self.frm_working.setVisible(frm_working_state)
            self.abort_action = False
            return

        
        pos = 0
        color.setNamedColor(self.MARKED_COLOR)
        cf.setBackground(color)
        
        self.prg_working.setVisible(True)
        self.prg_working.setValue(0)
        while True:
            if self.abort_action:
                QMessageBox.information(self, "Search aborted", "Search aborted by user", QMessageBox.Ok)
                break
            percent = int(pos / len(result_txt) * 100)
            if percent != self.prg_working.value():
                self.prg_working.setValue(percent)
                QCoreApplication.processEvents()

            pos = result_txt.find(txt, pos)
            if pos == -1:
                break
            cur.setPosition(pos)
            cur.movePosition(cur.Right, cur.KeepAnchor, len(txt))
            cur.mergeCharFormat(cf)
            pos += len(txt)
        
        cur.setPosition(position)
        self.txt_result.setTextCursor(cur)
        self.txt_result.verticalScrollBar().setValue(slider_position)
        self.lbl_search_info.setText(f"Found {result_txt.count(txt)} results.")
        self.frm_working.setVisible(frm_working_state)
        self.abort_action = False

    def _code_color_map(self, color_name: str = None) -> str:
        code = code_cls.Code()

        colors = {
            str(code.COMMENT): "#00aa00",
            str(code.BLOCK): "#0000ff",
            str(code.KEYWORD): "#00aaff",
            str(code.OPERATOR): "#c175ff",
            "equal": "#ffff00",
            "container": "#00aa00",
            "in_container": "#820000"
        }
        if color_name in colors:
            return colors[color_name]
        elif color_name is None:
            return colors
        else:
            return None

    def _html_color_map(self, color_name: str = None) -> str:
        colors = {
            "default": "#bdbdbd",
            "delim": "#ffffff",
            "tag": "#f0ffdd",
            "out_of_tag": "#ffff00",
            "slash": "#ff0000",
            "inactive": "#4b4b4b",
            "in_quota": "#884400",
            "in_brackets": "#ffd6c1",

            "doctype": "#ff0000",
            "html": "#aa00ff",
            "title": "#cf3eff",
            "meta": "#caca97",
            "name": "#dddda6",
            "content": "#aaaaff",
            "keywords": "#6faeff",
            "keyword": "#6faeff",
            "property": "#aa00ff",
            "type": "#ffb374",
            "website": "#e3d5ff",
            "url": "#5fbf00",
            "image": "#aaff7f",
            "noimage": "#82c160",
            "site": "#c1ac58",
            "link": "#aaffff",
            "rel": "#b4e3ff",
            "href": "#a5ffe6",
            "head": "#ff82d8",
            "header": "#da83ff",
            "div": "#00ffff",
            "class": "#aaffff",
            "a": "#aaff7f",
            "img": "#00ff00",
            "src": "#3cfcff",
            "alt": "#83c361",
            "nav": "#c376bc",
            "id": "#00ff00",
            "li": "#4eff26",
            "ul": "#aaff00",
            "option": "#443eff",
            "value": "#6ab2ff",
            "p": "#63ff52",
            "br": "#ff007f",
            "text": "#d3d39e",
            "javascript": "#e9ffc5",
            "script": "#c6ffc6",
            "debug": "#630095",
            "body": "#769544"
        }
        if color_name is None:
            return colors
        elif color_name.lower() in colors:
            return colors[color_name.lower()]
        else:
            return colors["default"]

    def mnu_file_new_triggered(self):
        if self.data_source and not self.data_source["saved"]:
            result = self.ask_to_save_project()
            if not result:
                return

        result = {
            "project": None,
            "selected": None,
            "type": None,
            "source": None,
            "text": None,
            "formated_text": None,
            "code": None,
            "project_filename": None,
            "saved": False
        }
        new_project.NewProject(self, result, app.clipboard())

        self.setWindowTitle("Rashomon")
        if result["selected"]:
            self.data_source = result
            self.script.load_data_source(self.data_source)
            self._create_new_project()

    def btn_change_source_click(self):
        if not self.data_source:
            QMessageBox.warning(self, "No project loaded", "Please load or create a project first")
            return
        
        result = {
            "project": None,
            "selected": None,
            "type": None,
            "source": None,
            "text": None,
            "formated_text": None,
            "code": None,
            "project_filename": None,
            "saved": False
        }
        new_project.NewProject(self, result, app.clipboard(), window_type="change")

        if result["selected"]:
            self._change_source(result)

    def _change_source(self, new_project_result: dict):
        if self.data_source is None:
            self.data_source = new_project_result
        else:
            self.data_source["selected"] = new_project_result["selected"]
            self.data_source["type"] = new_project_result["type"]
            self.data_source["source"] = new_project_result["source"]
            self.data_source["text"] = new_project_result["text"]
            self.data_source["formated_text"] = ""

        self.script.load_data_source(self.data_source)
        self.load_project()
        self.data_source["saved"] = False

    def _new_top_level_segment_code(self, segment_name: str = "Seg") -> str:
        result = f"""# Rashomon Code
BeginSegment ({segment_name})
    Parent = None
    Index = 0
EndSegment
"""
        return result
    
    def _create_new_project(self):
        self.data_source["code"] = self._new_top_level_segment_code()
        self.load_project()

    def _quick_format_html(self, html: str) -> str:
        if not html:
            return html
        
        html = html.replace("<", "\n<")
        html = html.replace(">", ">\n")
        
        html_clean = ""
        in_tag = False
        for line in html.splitlines():
            if line.startswith("<"):
                html_clean += line.replace("'", '"')
                in_tag = True
                if line.endswith(">"):
                    html_clean += "\n"
                    in_tag = False
                continue
            if in_tag:
                html_clean += " " + line.replace("'", '"')
            if line.endswith(">"):
                in_tag = False
                html_clean += "\n"
                continue

            if not in_tag:
                html_clean += HtmlLib.unescape(line) + "\n"

        html_clean = self.remove_extra_spaces(text=html_clean, only_remove_double="\n", remove_tabs=True)
        return html_clean

    def remove_extra_spaces(self, text: str, only_remove_double: list = None, remove_tabs: bool = True) -> str:
        if text is None:
            return None
        
        remove = [" ", "\n"]
        if only_remove_double:
            if isinstance(only_remove_double, str):
                remove = [only_remove_double]
            elif isinstance(only_remove_double, list) or isinstance(only_remove_double, tuple) or isinstance(only_remove_double, set):
                remove = [x for x in only_remove_double]
            else:
                raise ValueError("only_remove_double must be a string, list, tuple or set")

        while True:
            for item in remove:
                item_to_remove = item * 2
                item_to_replace_with = item
                text = text.replace(item_to_remove, item_to_replace_with)

            has_completed = True

            if remove_tabs:
                text = text.replace("\t", " ")
                if text.find("\t") != -1:
                    has_completed = False

            for item in remove:
                item_to_remove = item * 2
                if text.find(item_to_remove) != -1:
                    has_completed = False
            
            if has_completed:
                break

        return text.strip()

    def reload_source(self):
        frm_wortking_status = self.frm_working.isVisible()
        self.frm_working.setVisible(True)
        if self.data_source["selected"] == "file":
            try:
                with open(self.data_source["source"], 'r', encoding="utf-8") as file:
                    txt = file.read()
                self.data_source["text"] = txt
                # soup = bs(self.data_source["text"], 'html.parser')
                # formatted_text = soup.prettify()
                formatted_text = self._quick_format_html(self.data_source["text"])

                self.data_source["formated_text"] = formatted_text
            except Exception as e:
                QMessageBox.information(self, "Error", f"Error loading file: {e}\nSaved project data will be used instead!", QMessageBox.Ok)
                self.frm_working.setVisible(frm_wortking_status)
                return
        elif self.data_source["selected"] == "web":
            try:
                result_page = requests.get(self.data_source["source"])
                result_page.raise_for_status()
                result = result_page.text
                self.data_source["text"] = result
                # soup = bs(self.data_source["text"], 'html.parser')
                # formatted_text = soup.prettify()
                formatted_text = self._quick_format_html(self.data_source["text"])

                self.data_source["formated_text"] = formatted_text
            except Exception as e:
                QMessageBox.information(self, "Error", f"Error loading URL: {e}\nSaved project data will be used instead!", QMessageBox.Ok)
                self.frm_working.setVisible(frm_wortking_status)
                return
        self.frm_working.setVisible(frm_wortking_status)

    def load_project(self):
        self.script.load_data_source(self.data_source)
        if self.data_source["selected"] == "web":
            self.data_source["type"] = "html"
        else:
            if self.data_source["text"].strip().startswith("<!doctype html>"):
                self.data_source["type"] = "html"

        self.frm_working.setVisible(True)
        QCoreApplication.processEvents()

        if self.user_settings["general"]["reload_source_on_open"] and self.data_source["project_filename"] or not self.data_source["text"]:
            self.reload_source()

        if self.data_source["type"] == "html" and not self.data_source["formated_text"]:
            # soup = bs(self.data_source["text"], 'html.parser')
            # formatted_text = soup.prettify()
            formatted_text = self._quick_format_html(self.data_source["text"])
            self.data_source["formated_text"] = formatted_text

        self.lbl_data_src.setText(self.data_source["source"])
        self.refresh_tree()
        self.refresh_project()

    def refresh_project(self):
        self.frm_working.setVisible(True)
        QCoreApplication.processEvents()
        if not self.tree_seg.currentItem():
            return
        
        current_segment = self.tree_seg.currentItem().text(0)
        self.set_current_segment(segment_name=current_segment)
        
        if self.data_source["formated_text"]:
            self.txt_result.setPlainText(self.data_source["formated_text"])
        else:
            self.txt_result.setPlainText(self.data_source["text"])
        
        self.format_result_textbox()
        self.format_code_textbox(self.current_segment.code)
        self.frm_working.setVisible(False)

    def set_current_segment(self, segment_name: str = None):
        QCoreApplication.processEvents()
        # Check is segment_name valid
        current_segment = segment_name
        if current_segment is None:
            current_segment = self.tree_seg.currentItem().text()
        if current_segment not in self.script.get_all_segments(names_only=True):
            raise ValueError(f"Segment ({current_segment} is not valid segment name.)")

        # Set variable current_segment
        self.current_segment = self.script.segment(current_segment)
        
        # Set current segment, name and children if any
        self.lbl_curr.setText(self.current_segment.name)
        self.lst_cur_children.clear()
        for seg_name in self.script.get_segment_children(current_segment):
            self.lst_cur_children.addItem(seg_name.name)
        
        # Set parent segment name and children
        segment_parent = self.current_segment.parent
        if segment_parent not in self.script.get_all_segments(names_only=True):
            segment_parent = None
        
        self.lst_parent_children.clear()
        
        if segment_parent is None:
            self.lbl_parent.setText("Abstract Segment")
            for segment in self.script.get_all_segments():
                if segment.parent == None:
                    self.lst_parent_children.addItem(segment.name)
        else:
            self.lbl_parent.setText(segment_parent)
            for segment in self.script.get_all_segments():
                if segment.parent == segment_parent:
                    self.lst_parent_children.addItem(segment.name)
        for i in range(self.lst_parent_children.count()):
            if self.lst_parent_children.item(i).text() == self.current_segment.name:
                self.lst_parent_children.setCurrentItem(self.lst_parent_children.item(i))
                break

        # Set Code TextBox
        self.format_code_textbox(self.current_segment.code)

        # Set Rules list for current segment
        self._set_rules_list_from_code(self.current_segment.code)

    def _set_rules_list_from_code(self, code: str):
        self.lst_rules.clear()
        rules_list = self.current_segment.get_list_of_rules_for_GUI()
        for rule in rules_list:
            self.lst_rules.addItem(rule)

    def _log_incorect_len_text(self, txt_textbox: str, txt_data: str):
        with open("text_from_textbox.txt", "w", encoding="utf-8") as file:
            file.write(txt_textbox)
        with open("text_from_data.txt", "w", encoding="utf-8") as file:
            file.write(txt_data)

        txt = """There are some characters in the text that cannot be graphically displayed correctly in the textbox.
It is recommended to use the text displayed in the textbox in order for the graphic display to function properly.
This will not affect the accuracy of the data when using the "Rashomon" class.

If you want to check the differences in these two texts, you can do it by checking the files:
"text_from_textbox.txt"
"text_from_data.txt"

Do you want to use the text from the textbox instead of the original text?"""
        
        result = QMessageBox.question(self, "Unicode Chars", txt, QMessageBox.Yes|QMessageBox.No|QMessageBox.Cancel, QMessageBox.Yes)
        if result == QMessageBox.No:
            return
        
        self.data_source["formated_text"] = self.txt_result.toPlainText()

    def btn_tag_remove_click(self):
        self.frm_working.setVisible(True)
        QCoreApplication.processEvents()

        txt = self.txt_result.toPlainText()

        if self.data_source["formated_text"]:
            if txt != self.data_source["formated_text"]:
                self._log_incorect_len_text(txt, self.data_source["formated_text"])
        else:
            if txt != self.data_source["text"]:
                self._log_incorect_len_text(txt, self.data_source["text"])

        text_dict = self.script.get_segment_text(self.current_segment.name)

        pos = text_dict["start"]

        in_tag = False
        if pos > 0:
            if txt.find(">", pos) < txt.find("<", pos):
                in_tag = True

        char_map = []
        while pos <= text_dict["end"]:
            char = txt[pos:pos+1]
            if char == "<":
                in_tag = True
            if char == ">":
                char_map.append([pos, in_tag])
                in_tag = False
                pos += 1
                continue

            char_map.append([pos, in_tag])
            pos += 1

        cur = self.txt_result.textCursor()
        cur_pos = cur.position()
        slider_pos = self.txt_result.verticalScrollBar().value()

        cf_tag = QTextCharFormat()
        color_tag = QColor()
        color_tag.setNamedColor("#00005a")
        cf_tag.setForeground(color_tag)

        cf_text = QTextCharFormat()
        color_text = QColor()
        color_text.setNamedColor("#ffff00")
        cf_text.setForeground(color_text)

        if char_map:
            in_tag = char_map[0][1]
            old_pos = char_map[0][0]
        
        for i in char_map:
            if i[1] != in_tag:
                if not i[1]:
                    cur.setPosition(old_pos)
                    cur.movePosition(cur.Right, cur.KeepAnchor, i[0] - old_pos)
                    cur.setCharFormat(cf_tag)
                    old_pos = i[0]
                    in_tag = i[1]
                else:
                    cur.setPosition(old_pos)
                    cur.movePosition(cur.Right, cur.KeepAnchor, i[0] - old_pos)
                    cur.setCharFormat(cf_text)
                    old_pos = i[0]
                    in_tag = i[1]
        
        cur.setPosition(cur_pos)
        self.txt_result.setTextCursor(cur)
        self.txt_result.verticalScrollBar().setValue(slider_pos)
        self.frm_working.setVisible(False)
    
    def format_result_textbox(self):
        txt = self.txt_result.toPlainText()
        self.tree_seg.setDisabled(True)

        if self.data_source["formated_text"]:
            if txt != self.data_source["formated_text"]:
                self._log_incorect_len_text(txt, self.data_source["formated_text"])
        else:
            if txt != self.data_source["text"]:
                self._log_incorect_len_text(txt, self.data_source["text"])

        keywords = [x for x in self._html_color_map()]

        text_dict = self.script.get_segment_text(self.current_segment.name)

        fast_mode = False
        if text_dict["end"] - text_dict["start"] > 2000:
            if text_dict["end"] - text_dict["start"] >= len(txt):
                fast_mode = True
            else:
                fast_mode = False

        c = self.txt_result.textCursor()
        
        self._colorize_text(c, "", 0, use_color="DEFAULT", block_from=0, block_to=len(txt))
        self._colorize_text(c, "", 0, use_color="INACTIVE", block_from=0, block_to=text_dict["start"])
        self._colorize_text(c, "", 0, use_color="INACTIVE", block_from=text_dict["end"], block_to=len(txt))

        delim = " ()[]{}=:;\"'\n,.<>/?"
        delim_marker = "()=:;\"',.<>"

        self.prg_working.setVisible(True)

        pos = text_dict["start"]
        tag = False
        quota = False
        word = ""
        if fast_mode:
            text_html_obj = text_to_html_cls.TextToHtmlConverter(txt[text_dict["start"]:text_dict["end"]])
            text_html = text_html_obj.convertet_text()
            self.txt_result.setHtml(text_html)
            c.setPosition(0)
            self.txt_result.setTextCursor(c)
            self.prg_working.setVisible(False)
            self.tree_seg.setDisabled(False)
            return
        
        while pos < text_dict["end"]:
            if pos % (int(len(txt)/100)+1) == 0:
                self.prg_working.setValue(int(pos/(len(txt)+0.1)*100))
                QCoreApplication.processEvents()
                if self.abort_action:
                    c.setPosition(text_dict["end"])
                    self.txt_result.setTextCursor(c)
                    self.txt_result.ensureCursorVisible()
                    self.prg_working.setVisible(False)
                    self.abort_action = False
                    QMessageBox.critical(self, "User Abort", "Action aborted by User.\nNot completed !", QMessageBox.Ok)
                    self.tree_seg.setDisabled(False)
                    return

            i = txt[pos]
            if i == "<" and not quota:
                tag = True
                if word:
                    self._colorize_text(c, word, pos - len(word), use_color="OUT_OF_TAG")
                    word = ""
                self._colorize_text(c, i, pos, use_color="TAG")
                pos += 1
                continue
            if i == ">" and not quota:
                tag = False
                if word and not fast_mode:
                    self._colorize_text(c, word, pos - len(word))
                word = ""
                self._colorize_text(c, i, pos, use_color="TAG")
                pos += 1
                continue
            
            if fast_mode:
                word += i
                pos += 1
                continue
            
            if i == '"' and tag:
                if quota:
                    self._colorize_text(c, word, pos - len(word), use_color="IN_QUOTA")
                    word = ""
                    quota = False
                    self._colorize_text(c, i, pos, use_color="DELIM")
                    pos += 1
                    continue
                else:
                    quota = True
                    if word:
                        self._colorize_text(c, word, pos - len(word))
                        word = ""

                    self._colorize_text(c, i, pos, use_color="DELIM")
                    pos += 1
                    continue

            if quota or not tag:
                word += i
                pos += 1
                continue

            if i in delim:
                if word:
                    if word in keywords:
                        self._colorize_text(c, word, pos - len(word))
                    word = ""
                if i in delim_marker:
                    self._colorize_text(c, i, pos, use_color="DELIM")
                elif i == "/":
                    self._colorize_text(c, i, pos, use_color="SLASH")
                else:
                    self._colorize_text(c, i, pos)
                pos += 1
                continue

            word += i
            pos += 1
        
        c.setPosition(text_dict["end"])
        self.txt_result.setTextCursor(c)
        self.txt_result.ensureCursorVisible()
        self.prg_working.setVisible(False)
        self.tree_seg.setDisabled(False)

    def _colorize_text(self, cursor: QTextCursor, text: str, position: int, use_color: str = None, block_from: int = None, block_to: int = None):
        cf = QTextCharFormat()
        color = QColor()

        if use_color:
            color.setNamedColor(self._html_color_map(use_color))
        else:
            color.setNamedColor(self._html_color_map(text))
        cf.setForeground(color)

        if block_from is not None and block_to is not None:
            cursor.setPosition(block_from)
            cursor.movePosition(cursor.Right, cursor.KeepAnchor, block_to - block_from)
        else:
            cursor.setPosition(position)
            cursor.movePosition(cursor.Right, cursor.KeepAnchor, len(text))
        
        cursor.setCharFormat(cf)
        return

    def format_code_textbox(self, code: str):
        self._code_txtbox_protected = True
        self.txt_code.setPlainText(code)
        code_handler = code_cls.Code()
        line_start = 0
        found_command = False
        while True:
            if line_start >= len(code):
                break

            line_end = code.find("\n", line_start)
            if line_end == -1:
                line_end = len(code)

            line = code[line_start:line_end]

            if not line:
                line_start = line_end + 1
                continue
            
            found_command = False
            for command in code_handler.commands:
                command_obj: code_cls.AbstractCommand = command[1](line, 0, "", "")
                if command_obj.is_valid():
                    self._colorize_commands(command_obj.data.ColorMap, self.txt_code, line_start, self.old_txt_rule_cf)
                    found_command = True
                    break
            if not found_command:
                self._colorize_commands([[0, line_end - line_start, "#ff0000"]], self.txt_code, line_start, self.old_txt_rule_cf)

            line_start = line_end + 1
        self._code_txtbox_protected = False

    def _colorize_commands(self, color_map: list, textbox: QTextEdit, start_pos: int, old_cf: QTextCharFormat = None):
        cur = textbox.textCursor()
        cf = QTextCharFormat()
        for i in color_map:
            cur.setPosition(start_pos + i[0])
            cur.movePosition(cur.Right, cur.KeepAnchor, i[1] - i[0])
            color = QColor(i[2])
            cf.setForeground(color)
            cur.setCharFormat(cf)
        cur.setPosition(0)
        textbox.setTextCursor(cur)

        if old_cf:
            cur = textbox.textCursor()
            cur.setCharFormat(old_cf)
            textbox.setTextCursor(cur)

    def refresh_tree(self, set_current_segment_name: str = None):
        if not set_current_segment_name:
            if self.tree_seg.currentItem():
                set_current_segment_name = self.tree_seg.currentItem().text(0)

        self._tree_change_current_protected = True
        self.tree_seg.clear()
        
        if self.data_source is None:
            top_segments = None
        else:
            top_segments = self.script.get_top_segment_names()
        
        if not top_segments:
            self._tree_change_current_protected = False
            self.txt_code.setText("")
            self.txt_result.setText("")
            self.lst_cur_children.clear()
            self.lst_parent_children.clear()
            self.lbl_curr.setText("")
            self.lbl_parent.setText("Abstract Segment")
            return
        
        for seg_name in top_segments:
            self.tree_seg.addTopLevelItem(QTreeWidgetItem([seg_name]))

        if self.abort_action:
            QMessageBox.critical(self, "Abort", "Some Segments were not processed due to user interupt.", QMessageBox.Ok)
            self.abort_action = False
            return
            
        self.tree_seg.setCurrentItem(self.tree_seg.topLevelItem(0))

        self._tmp_total_segments = len(self.script.get_all_segments(names_only=True))
        self._tmp_segment_counter = 0
        progress_step = int(self._tmp_total_segments / 100) + 1

        frm_working_state = self.frm_working.isVisible()
        self.frm_working.setVisible(True)
        self.prg_working.setVisible(True)
        self.prg_working.setValue(0)

        for i in range(len(top_segments)):
            self._add_tree_items(self.tree_seg.topLevelItem(i), progress_step=progress_step)

        if set_current_segment_name:
            for i in range(self.tree_seg.invisibleRootItem().childCount()):
                item = self._set_current_tree_item(set_current_segment_name, self.tree_seg.topLevelItem(i))
                if item:
                    self.tree_seg.setCurrentItem(item)
                    break
        self._tree_change_current_protected = False
        if self.tree_seg.currentItem() is not None:
            self.tree_seg_current_changed(None, None)
        self.tree_seg.sortByColumn(0, Qt.AscendingOrder)
        self.frm_working.setVisible(frm_working_state)
            
    def _set_current_tree_item(self, set_current_item: str, start_with_item: QTreeWidgetItem):
        if start_with_item.text(0) == set_current_item:
            return start_with_item
        
        for idx in range(start_with_item.childCount()):
            item = self._set_current_tree_item(set_current_item=set_current_item, start_with_item=start_with_item.child(idx))
            if item:
                return item

    def _add_tree_items(self, item: QTreeWidgetItem, progress_step: int = 50):
        if self.abort_action:
            return
        self._tmp_segment_counter += 1
        if self._tmp_segment_counter % progress_step == 0:
            self.prg_working.setValue(int(self._tmp_segment_counter / self._tmp_total_segments * 100))
            app.processEvents()

        children = self.script.get_segment_children(item.text(0), names_only=True)
        if not children:
            return
        for child in children:
            child_item = QTreeWidgetItem()
            child_item.setText(0, child)
            item.addChild(child_item)
            if self.script.get_segment_children(child, names_only=True):
                self._add_tree_items(child_item, progress_step=progress_step)
            else:
                self._tmp_segment_counter += 1
                if self._tmp_segment_counter % progress_step == 0:
                    self.prg_working.setValue(int(self._tmp_segment_counter / self._tmp_total_segments * 100))
                    app.processEvents()

        item.setExpanded(True)

    def _struc(self, dictionary: dict) -> list:
        result = []
        self._struc_recurs(dictionary=dictionary, result=result)
        return result

    def _struc_recurs(self, dictionary: dict, result: list) -> None:
        if isinstance(dictionary, dict):
            for i in dictionary:
                result.append(i)
                if isinstance(dictionary[i], dict):
                    self._struc_recurs(dictionary[i], result)
        else:
            return

    def load_user_settings(self):
        if os.path.isfile("rashomon_user_settings.json"):
            with open("rashomon_user_settings.json", "r", encoding="utf-8") as file:
                loaded_settings = json.load(file)
            
            if self._struc(loaded_settings) == self._struc(self.user_settings):
                self.user_settings = loaded_settings
            else:
                QMessageBox.information(self, "User settings", "The structure of the user settings has been changed, the settings have been reset!", QMessageBox.Ok)
        else:
            QMessageBox.information(self, "User settings", "User settings file not found.\nDefault settings will be used.", QMessageBox.Ok)

        # Window geometry
        if self.user_settings["window"]["position"]["x"] is not None and self.user_settings["window"]["position"]["y"] is not None:
            self.move(self.user_settings["window"]["position"]["x"], self.user_settings["window"]["position"]["y"])
        if self.user_settings["window"]["size"]["width"] is not None and self.user_settings["window"]["size"]["height"] is not None:
            self.resize(self.user_settings["window"]["size"]["width"], self.user_settings["window"]["size"]["height"])

        if self.user_settings["separator"]["position"] is not None:
            self.line_sep.move(self.user_settings["separator"]["position"], self.line_sep.pos().y())

        # Code
        if self.user_settings["txt_code"]["font"]["name"] is not None:
            font = self.txt_code.font()
            font.setFamily(self.user_settings["txt_code"]["font"]["name"])
            self.txt_code.setFont(font)
        else:
            self.user_settings["txt_code"]["font"]["name"] = self.txt_code.font().family()

        if self.user_settings["txt_code"]["font"]["size"] is not None:
            font = self.txt_code.font()
            font.setPointSize(self.user_settings["txt_code"]["font"]["size"])
            self.txt_code.setFont(font)
        else:
            self.user_settings["txt_code"]["font"]["size"] = self.txt_code.font().pointSize()

        if self.user_settings["txt_code"]["bg_color"] is not None:
            self.txt_code.setStyleSheet(f"background-color: {self.user_settings['txt_code']['bg_color']};")
        else:
            self.user_settings["txt_code"]["bg_color"] = "#000000"

        if self.user_settings["txt_code"]["autocomplete"]["show"] is None:
            self.user_settings["txt_code"]["autocomplete"]["show"] = True

        if self.user_settings["txt_code"]["autocomplete"]["autoselect"] is None:
            self.user_settings["txt_code"]["autocomplete"]["autoselect"] = False

        # Result
        if self.user_settings["txt_result"]["font"]["name"] is not None:
            font = self.txt_result.font()
            font.setFamily(self.user_settings["txt_result"]["font"]["name"])
            self.txt_result.setFont(font)
        else:
            self.user_settings["txt_result"]["font"]["name"] = self.txt_result.font().family()

        if self.user_settings["txt_result"]["font"]["size"] is not None:
            font = self.txt_result.font()
            font.setPointSize(self.user_settings["txt_result"]["font"]["size"])
            self.txt_result.setFont(font)
        else:
            self.user_settings["txt_result"]["font"]["size"] = self.txt_result.font().pointSize()

        if self.user_settings["txt_result"]["bg_color"] is not None:
            self.txt_result.setStyleSheet(f"background-color: {self.user_settings['txt_result']['bg_color']};")
        else:
            self.user_settings["txt_result"]["bg_color"] = "#292929"

        # Segment
        if self.user_settings["tree_seg"]["font"]["name"] is not None:
            font = self.tree_seg.font()
            font.setFamily(self.user_settings["tree_seg"]["font"]["name"])
            self.tree_seg.setFont(font)
        else:
            self.user_settings["tree_seg"]["font"]["name"] = self.tree_seg.font().family()

        if self.user_settings["tree_seg"]["font"]["size"] is not None:
            font = self.tree_seg.font()
            font.setPointSize(self.user_settings["tree_seg"]["font"]["size"])
            self.tree_seg.setFont(font)
        else:
            self.user_settings["tree_seg"]["font"]["size"] = self.tree_seg.font().pointSize()

        # Other
        if self.user_settings["chk_apply_all"]["is_checked"] is not None:
            self.chk_apply_all.setChecked(self.user_settings["chk_apply_all"]["is_checked"])

        if self.user_settings["chk_apply_all_code"]["is_checked"] is not None:
            self.chk_apply_all_code.setChecked(self.user_settings["chk_apply_all_code"]["is_checked"])

    def close_event(self, a0):
        with open("rashomon_user_settings.json", "w", encoding="utf-8") as file:
            json.dump(self.user_settings, file, indent=2)
        if self.data_source and not self.data_source["saved"]:
            result = self.ask_to_save_project()
            if not result:
                a0.ignore()

    def _check_user_setting_structure(self, user_setting_structure: list = None, user_dict: dict = None):
        if user_setting_structure is None:
            user_setting_structure = self.USER_SETTINGS_STRUCTURE
        if user_dict is None:
            user_dict = self.user_settings
        
        for key in user_setting_structure:
            if key[0] not in user_dict:
                if key[1]:
                    user_dict[key[0]] = {}
                    self._check_user_setting_structure(key[1], user_dict[key[0]])
                else:
                    user_dict[key[0]] = None

    def resizeEvent(self, a0: QResizeEvent) -> None:
        self._resize_me()
        return super().resizeEvent(a0)
    
    def _resize_me(self):
        w = self.contentsRect().width()
        h = self.contentsRect().height()

        # Data Source Frame
        self.frm_data_src.resize(w - 20, self.frm_data_src.height())
        self.btn_change_source.move(self.frm_data_src.contentsRect().width() - 10 - self.btn_change_source.width(), self.btn_change_source.pos().y())
        self.lbl_data_src.resize(self.frm_data_src.contentsRect().width() - self.lbl_data_src.pos().x() - 30 - self.btn_change_source.width(), self.lbl_data_src.height())
        
        # Segment Frame
        self.frm_seg.resize(w - 20, self.frm_seg.height())
        self.txt_code.resize(self.frm_seg.contentsRect().width() - self.txt_code.pos().x() - 10, self.txt_code.height())

        # Delimiter Line
        self.line_sep.resize(self.line_sep.width(), h - self.line_sep.pos().y() - 45 - self.menuBar().height())

        # Segments Tree Widget
        self.tree_seg.resize(self.line_sep.pos().x() - 10, self.line_sep.height())

        # Find Frame
        self.frm_find.move(self.line_sep.pos().x() + self.line_sep.width(), self.frm_find.pos().y())
        self.frm_find.resize(w - self.frm_find.pos().x() - 10, self.frm_find.height())
        self.lbl_search_info.resize(self.frm_find.contentsRect().width() - self.lbl_search_info.pos().x() - 10, self.lbl_search_info.height())

        # Result TextBox
        self.txt_result.move(self.line_sep.pos().x() + self.line_sep.width(), self.txt_result.pos().y())
        self.txt_result.resize(w - self.txt_result.pos().x() - 10, h - self.txt_result.pos().y() - 45 - self.menuBar().height())

        # Tool Box (Segments Tree and Result TextBox)
        tree_tool_x = self.tree_seg.pos().x() + self.tree_seg.width() - self.frm_tree_seg_setup.width()
        if tree_tool_x < 0:
            tree_tool_x = 0
        self.frm_tree_seg_setup.move(tree_tool_x, self.tree_seg.pos().y() + self.tree_seg.height())
        
        result_tool_x = self.txt_result.pos().x() + self.txt_result.width() - self.frm_txt_result_setup.width()
        if result_tool_x < 0:
            result_tool_x = 0
        self.frm_txt_result_setup.move(result_tool_x, self.txt_result.pos().y() + self.txt_result.height())

        # Working frame
        frm_working_x = w - self.frm_working.width() - 10
        if frm_working_x < 0:
            frm_working_x = 0
        self.frm_working.move(frm_working_x, 10)

    def _setup_widgets(self):
        self.mnu_file_new: QAction = self.findChild(QAction, "mnu_file_new")
        self.mnu_file_open: QAction = self.findChild(QAction, "mnu_file_open")
        self.mnu_file_save: QAction = self.findChild(QAction, "mnu_file_save")
        self.mnu_file_save_as: QAction = self.findChild(QAction, "mnu_file_save_as")
        self.mnu_file_close: QAction = self.findChild(QAction, "mnu_file_close")
        self.mnu_file_export: QAction = self.findChild(QAction, "mnu_file_export")
        self.mnu_file_settings: QAction = self.findChild(QAction, "mnu_file_settings")
        self.mnu_file_exit: QAction = self.findChild(QAction, "mnu_file_exit")

        self.frm_data_src: QFrame = self.findChild(QFrame, "frm_data_src")
        self.lbl_data_src_mark: QLabel = self.findChild(QLabel, "lbl_data_src_mark")
        self.lbl_data_src: QLabel = self.findChild(QLabel, "lbl_data_src")
        self.btn_change_source: QPushButton = self.findChild(QPushButton, "btn_change_source")

        self.frm_seg: QFrame = self.findChild(QFrame, "frm_seg")
        self.lbl_parent_mark: QLabel = self.findChild(QLabel, "lbl_parent_mark")
        self.lbl_curr_mark: QLabel = self.findChild(QLabel, "lbl_curr_mark")
        self.lbl_parent: QLabel = self.findChild(QLabel, "lbl_parent")
        self.lbl_curr: QLabel = self.findChild(QLabel, "lbl_curr")
        self.lst_parent_children: QListWidget = self.findChild(QListWidget, "lst_parent_children")
        self.lst_cur_children: QListWidget = self.findChild(QListWidget, "lst_cur_children")
        
        self.frm_rule: QFrame = self.findChild(QFrame, "frm_rule")
        self.rbt_start: QRadioButton = self.findChild(QRadioButton, "rbt_start")
        self.rbt_end: QRadioButton = self.findChild(QRadioButton, "rbt_end")
        self.txt_rule_starts: QLineEdit = self.findChild(QLineEdit, "txt_rule_starts")
        self.txt_rule_ends: QLineEdit = self.findChild(QLineEdit, "txt_rule_ends")
        self.txt_rule_contain: QLineEdit = self.findChild(QLineEdit, "txt_rule_contain")
        self.btn_rule_add_starts: QPushButton = self.findChild(QPushButton, "btn_rule_add_starts")
        self.btn_rule_add_ends: QPushButton = self.findChild(QPushButton, "btn_rule_add_ends")
        self.btn_rule_add_contain: QPushButton = self.findChild(QPushButton, "btn_rule_add_contain")
        self.btn_rule_not_starts: QPushButton = self.findChild(QPushButton, "btn_rule_not_starts")
        self.btn_rule_not_ends: QPushButton = self.findChild(QPushButton, "btn_rule_not_ends")
        self.btn_rule_not_contain: QPushButton = self.findChild(QPushButton, "btn_rule_not_contain")
        self.lst_rules: QListWidget = self.findChild(QListWidget, "lst_rules")
        self.txt_rule_starts_with: QLineEdit = self.findChild(QLineEdit, "txt_rule_starts_with")
        self.txt_rule_ends_with: QLineEdit = self.findChild(QLineEdit, "txt_rule_ends_with")
        self.txt_rule_is_equal_to: QLineEdit = self.findChild(QLineEdit, "txt_rule_is_equal_to")

        self.btn_rule_add_is_equal_to: QPushButton = self.findChild(QPushButton, "btn_rule_add_is_equal_to")
        self.btn_rule_add_starts_with: QPushButton = self.findChild(QPushButton, "btn_rule_add_starts_with")
        self.btn_rule_add_ends_with: QPushButton = self.findChild(QPushButton, "btn_rule_add_ends_with")

        self.chk_apply_all: QCheckBox = self.findChild(QCheckBox, "chk_apply_all")
        self.chk_apply_all_code: QCheckBox = self.findChild(QCheckBox, "chk_apply_all_code")
        self.btn_apply_rule: QPushButton = self.findChild(QPushButton, "btn_apply_rule")
        self.txt_code: QTextEdit = self.findChild(QTextEdit, "txt_code")
        self.btn_apply_code: QPushButton = self.findChild(QPushButton, "btn_apply_code")
        self.btn_code_setup: QPushButton = self.findChild(QPushButton, "btn_code_setup")
        self.btn_code_zoom_in: QPushButton = self.findChild(QPushButton, "btn_code_zoom_in")
        self.btn_code_zoom_out: QPushButton = self.findChild(QPushButton, "btn_code_zoom_out")

        self.tree_seg: QTreeWidget = self.findChild(QTreeWidget, "tree_seg")
        self.txt_result: QTextEdit = self.findChild(QTextEdit, "txt_result")

        self.frm_tree_seg_setup: QFrame = self.findChild(QFrame, "frm_tree_seg_setup")
        self.btn_seg_setup: QPushButton = self.findChild(QPushButton, "btn_seg_setup")
        self.btn_seg_zoom_in: QPushButton = self.findChild(QPushButton, "btn_seg_zoom_in")
        self.btn_seg_zoom_out: QPushButton = self.findChild(QPushButton, "btn_seg_zoom_out")
        self.btn_seg_expand: QPushButton = self.findChild(QPushButton, "btn_seg_expand")
        self.btn_seg_collapse: QPushButton = self.findChild(QPushButton, "btn_seg_collapse")

        self.frm_txt_result_setup: QFrame = self.findChild(QFrame, "frm_txt_result_setup")
        self.btn_result_setup: QPushButton = self.findChild(QPushButton, "btn_result_setup")
        self.btn_result_zoom_in: QPushButton = self.findChild(QPushButton, "btn_result_zoom_in")
        self.btn_result_zoom_out: QPushButton = self.findChild(QPushButton, "btn_result_zoom_out")
        self.btn_tag_remove: QPushButton = self.findChild(QPushButton, "btn_tag_remove")

        self.line_sep: QFrame = self.findChild(QFrame, "line_sep")

        self.frm_working: QFrame = self.findChild(QFrame, "frm_working")
        self.prg_working: QProgressBar = self.findChild(QProgressBar, "prg_working")
        self.btn_abort: QPushButton = self.findChild(QPushButton, "btn_abort")

        self.frm_find: QFrame = self.findChild(QFrame, "frm_find")
        self.txt_find: QLineEdit = self.findChild(QLineEdit, "txt_find")
        self.btn_find_next: QPushButton = self.findChild(QPushButton, "btn_find_next")
        self.btn_find_prev: QPushButton = self.findChild(QPushButton, "btn_find_prev")
        self.lbl_search_info: QLabel = self.findChild(QLabel, "lbl_search_info")
        self.btn_find_go: QPushButton = self.findChild(QPushButton, "btn_find_go")
        self.spin_find_go: QSpinBox = self.findChild(QSpinBox, "spin_find_go")

        self.frm_info: QFrame = self.findChild(QFrame, "frm_info")

    def _setup_apperance(self):
        menubar_style = ""
        menubar_style += "QMenuBar::item:selected {" 
        menubar_style += "background-color: #26edff;"
        menubar_style += "}"

        menubar_style += "QMenuBar::item:hover {"
        menubar_style += "background-color: #a9b5ff;" 
        menubar_style += "}"

        menubar_style += "QMenu::item:selected {"
        menubar_style += "background-color: #2bb991;" 
        menubar_style += "}"


        self.setStyleSheet(menubar_style)
        self.frm_working.setVisible(False)
        self.frm_info.setVisible(False)
        self.tree_seg.setHeaderHidden(True)
        self.prg_working.setVisible(False)

        self.btn_rule_add_starts.setDisabled(True)
        self.btn_rule_add_ends.setDisabled(True)
        self.btn_rule_add_contain.setDisabled(True)
        
        self.btn_rule_add_is_equal_to.setDisabled(True)
        self.btn_rule_add_starts_with.setDisabled(True)
        self.btn_rule_add_ends_with.setDisabled(True)

        self.lst_rules.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_seg.setContextMenuPolicy(Qt.CustomContextMenu)
        self._create_context_menus()

        self.frm_autocomplete: QFrame = QFrame(self)
        self.lst_autocomplete: QListWidget = QListWidget(self.frm_autocomplete)
        self.lst_autocomplete.setStyleSheet("QListWidget::item:selected {background-color: #007a00;} QToolTip {background-color: #00003f; border: 1px solid yellow;}")
        
        self.frm_autocomplete.setVisible(False)

        self.lbl_pic = QLabel(self)
        self.lbl_pic.move(20,20)
        self.lbl_pic.resize(450, 350)
        self.lbl_pic.setFrameShape(1)
        self.lbl_pic.setLineWidth(3)
        self.lbl_pic.setAlignment(Qt.AlignCenter)
        self.lbl_pic.setStyleSheet("background-color: #00004b;")
        self.lbl_pic.setVisible(False)

    def _create_context_menus(self):
        # lst_rules menu
        self.mnu_lst_rules = QMenu(self)
        self.mnu_lst_rules_del_item = QAction("Delete Item", self)
        self.mnu_lst_rules_del_all = QAction("Delete ALL", self)
        self.mnu_lst_rules.addAction(self.mnu_lst_rules_del_item)
        self.mnu_lst_rules.addSeparator()
        self.mnu_lst_rules.addAction(self.mnu_lst_rules_del_all)

        # tree context menu
        self.mnu_tree = QMenu(self)
        self.mnu_tree_rename = QAction("Rename Segment", self)
        self.mnu_tree_del = QAction("Delete Segment", self)
        self.mnu_tree_add_top_level = QAction("Add Top Level Segment", self)
        self.mnu_tree.addAction(self.mnu_tree_rename)
        self.mnu_tree.addAction(self.mnu_tree_del)
        self.mnu_tree.addSeparator()
        self.mnu_tree.addAction(self.mnu_tree_add_top_level)

        


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RashomonGUI()
    window.show()
    sys.exit(app.exec_())


