
import os
import subprocess
from pathlib import Path
import logging

import ctypes

from PySide6.QtCore import Qt, Slot, QTimer, QThread, Signal
from PySide6.QtGui import QColor, QIcon
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QInputDialog, QLabel, QLineEdit,
    QGroupBox, QTabWidget, QFrame
)

from ..core import backup_manager, process_checker, config_manager
from ..core.updater import Updater
from .settings_window import SettingsWindow
from ..common.paths import get_base_path
from ..i18n.translator import t, get_translator, init_translator

logger = logging.getLogger(__name__)


class UpdateWorker(QThread):
    """
    Worker thread to check for updates in the background.
    """
    update_found = Signal(dict)
    no_update = Signal()
    error = Signal(str)

    def __init__(self, updater: Updater):
        super().__init__()
        self.updater = updater

    def run(self):
        try:
            update_info = self.updater.check_for_update()
            if update_info:
                self.update_found.emit(update_info)
            else:
                self.no_update.emit()
        except Exception as e:
            logger.error(f"Update check failed in worker thread: {e}")
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # 初始化翻译器
        config = config_manager.load_config()
        language = config.get("language")
        init_translator(language)

        self.translator = get_translator()
        self.updater = Updater()
        self._init_ui()
        self.check_for_updates()

    def _init_ui(self):
        """初始化UI"""
        self.setWindowTitle(t('ui.main_window.title'))

        # Use the robust path helper to find the icon
        base_path = get_base_path()
        icon_path = base_path / "resources" / "app.ico"
        self.setWindowIcon(QIcon(str(icon_path)))

        self.setMinimumSize(800, 600)

        self.backup_manager = backup_manager.BackupManager()

        # Main widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        # Top layout
        self.top_layout = QVBoxLayout()
        self.top_buttons_layout = QHBoxLayout()
        self.note_input = QLineEdit()
        self.note_input.setObjectName("note_input_main")
        self.note_input.setPlaceholderText(t('ui.main_window.note_placeholder'))
        self.backup_button = QPushButton(t('ui.main_window.backup_button'))
        self.backup_button.setDefault(True)
        self.restore_last_button = QPushButton(t('ui.main_window.restore_last_button'))
        self.settings_button = QPushButton(t('ui.main_window.settings_button'))
        self.top_buttons_layout.addWidget(self.backup_button)
        self.top_buttons_layout.addWidget(self.restore_last_button)
        self.top_buttons_layout.addStretch()
        self.top_buttons_layout.addWidget(self.settings_button)
        self.top_layout.addLayout(self.top_buttons_layout)
        self.top_layout.addWidget(self.note_input)

        # History section
        history_groupbox = QGroupBox(t('ui.main_window.history_group'))
        history_layout = QVBoxLayout(history_groupbox)
        self.tab_widget = QTabWidget()
        history_layout.addWidget(self.tab_widget)

        # Manual backups tab
        self.manual_history_table = self._create_history_table()
        self.tab_widget.addTab(self.manual_history_table, t('ui.main_window.manual_backup_tab'))

        # Auto backups tab
        self.auto_history_table = self._create_history_table()
        self.tab_widget.addTab(self.auto_history_table, t('ui.main_window.auto_backup_tab'))

        # Message bubble
        self.message_bubble = QLabel()
        self.message_bubble.setObjectName("message_bubble")
        self.message_bubble.setVisible(False)
        self.message_bubble.setAlignment(Qt.AlignCenter)
        self.message_bubble.setWordWrap(True)
        self.message_bubble_timer = QTimer()
        self.message_bubble_timer.setSingleShot(True)
        self.message_bubble_timer.timeout.connect(self.hide_message_bubble)

        # Status bar
        self.status_label = QLabel(t('ui.main_window.status_ready'))
        self.status_label.setObjectName("status_label")
        self.statusBar().addWidget(self.status_label)

        # Assemble layout
        self.main_layout.addLayout(self.top_layout)
        self.main_layout.addWidget(history_groupbox)
        self.main_layout.addWidget(self.message_bubble)

        # Connect signals
        self.backup_button.clicked.connect(self.manual_backup)
        self.restore_last_button.clicked.connect(self.restore_last_backup)
        self.settings_button.clicked.connect(self.open_settings)
        self.manual_history_table.itemChanged.connect(self.save_note_from_item)
        self.auto_history_table.itemChanged.connect(self.save_note_from_item)

        self.refresh_backup_list()

    def check_for_updates(self):
        self.status_label.setText(t('ui.main_window.status_checking_update'))
        self.update_thread = QThread()
        self.update_worker = UpdateWorker(self.updater)
        self.update_worker.moveToThread(self.update_thread)

        self.update_thread.started.connect(self.update_worker.run)
        self.update_worker.finished.connect(self.update_thread.quit)
        self.update_worker.finished.connect(self.update_worker.deleteLater)
        self.update_thread.finished.connect(self.update_thread.deleteLater)

        self.update_worker.update_found.connect(self.on_update_found)
        self.update_worker.no_update.connect(self.on_no_update)
        self.update_worker.error.connect(self.on_update_error)

        self.update_thread.start()

    @Slot(dict)
    def on_update_found(self, info):
        version = info.get('version', 'N/A')
        notes = info.get('notes', t('ui.dialogs.update_no_notes'))
        reply = QMessageBox.information(
            self,
            t('ui.dialogs.update_available_title'),
            t('ui.dialogs.update_available_message', version=version, notes=notes),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )

        if reply == QMessageBox.Yes:
            self.status_label.setText(t('ui.main_window.status_downloading_update'))
            # This will block the UI, a second worker thread would be better for production
            new_exe_path = self.updater.download_and_verify()
            if new_exe_path:
                self.updater.apply_update(new_exe_path)
            else:
                QMessageBox.critical(self, t('ui.dialogs.error'), t('ui.dialogs.update_failed'))
                self.status_label.setText(t('ui.main_window.status_ready'))

    @Slot()
    def on_no_update(self):
        self.status_label.setText(t('ui.main_window.status_up_to_date'))
        # Hide the message after a few seconds
        QTimer.singleShot(5000, lambda: self.status_label.setText(t('ui.main_window.status_ready')))

    @Slot(str)
    def on_update_error(self, error_message):
        self.status_label.setText(t('ui.main_window.status_update_error'))
        logger.error(f"Update check error: {error_message}")
        # Hide the message after a few seconds
        QTimer.singleShot(5000, lambda: self.status_label.setText(t('ui.main_window.status_ready')))

    def _create_history_table(self) -> QTableWidget:
        table = QTableWidget()
        table.setFrameShape(QFrame.NoFrame)
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels([
            t('ui.main_window.table_headers.time'),
            t('ui.main_window.table_headers.note'),
            t('ui.main_window.table_headers.restore'),
            t('ui.main_window.table_headers.delete')
        ])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        return table

    def refresh_backup_list(self):
        self.status_label.setText(t('ui.main_window.status_refreshing'))
        self.backup_manager._reload_config() # Ensure config is fresh

        all_backups = self.backup_manager.list_backups()

        # I am assuming backup_entry has an 'auto' attribute.
        # This is a reasonable assumption given the `backup` method signature.
        manual_backups = [b for b in all_backups if not b.auto]
        auto_backups = [b for b in all_backups if b.auto]

        self._populate_history_table(self.manual_history_table, manual_backups)
        self._populate_history_table(self.auto_history_table, auto_backups)

        self.status_label.setText(t('ui.main_window.status_ready'))

    def _populate_history_table(self, table: QTableWidget, backups: list):
        table.setRowCount(len(backups))
        for row, backup_entry in enumerate(backups):
            timestamp_item = QTableWidgetItem(backup_entry.timestamp)
            timestamp_item.setFlags(timestamp_item.flags() & ~Qt.ItemIsEditable)
            table.setItem(row, 0, timestamp_item)

            note_item = QTableWidgetItem(backup_entry.note)
            table.setItem(row, 1, note_item)

            # Restore button
            restore_btn = QPushButton(t('ui.main_window.table_headers.restore'))
            restore_btn.setObjectName("table_button")
            restore_btn.clicked.connect(lambda _, p=backup_entry.path: self.restore_backup(p))
            table.setCellWidget(row, 2, restore_btn)

            # Delete button
            delete_btn = QPushButton(t('ui.main_window.table_headers.delete'))
            delete_btn.setObjectName("table_button")
            delete_btn.clicked.connect(lambda _, p=backup_entry.path: self.delete_backup(p))
            table.setCellWidget(row, 3, delete_btn)

    @Slot()
    def manual_backup(self):
        if self._check_game_running():
            return

        note = self.note_input.text()
        try:
            self.status_label.setText(t('ui.main_window.status_backuping'))
            # The `auto` parameter is explicitly set to False for manual backups.
            timestamp = self.backup_manager.backup(note=note, auto=False)
            if timestamp:
                self.show_message_bubble(t('ui.dialogs.backup_success', timestamp=timestamp))
                self.note_input.clear()
                self._maybe_launch_game()
            else:
                QMessageBox.warning(self, t('ui.dialogs.warning'), t('ui.dialogs.backup_exists_message'))
        except Exception as e:
            QMessageBox.critical(self, t('ui.dialogs.error'), t('ui.dialogs.backup_failed', error=e))
        finally:
            self.refresh_backup_list()

    @Slot()
    def restore_last_backup(self):
        if self._check_game_running():
            return

        last_backup_path_str = self.backup_manager.config.get("last_backup")
        if not last_backup_path_str:
            QMessageBox.warning(self, t('ui.dialogs.error'), t('ui.dialogs.no_recent_backup'))
            return

        last_backup_path = Path(last_backup_path_str)
        if not last_backup_path.exists():
            QMessageBox.warning(self, t('ui.dialogs.error'), t('ui.dialogs.backup_not_found', path=last_backup_path))
            return

        self.restore_backup(last_backup_path)

    @Slot(Path)
    def restore_backup(self, backup_path: Path):
        if self._check_game_running():
            return

        # Confirmation for old backups
        time_diff = self.backup_manager.get_time_diff(backup_path)
        threshold = self.backup_manager.config.get("restore_confirm_threshold_minutes", 20)
        if time_diff > threshold:
            reply = QMessageBox.question(
                self, t('ui.dialogs.confirm_restore'),
                t('ui.dialogs.confirm_restore_message', minutes=f"{time_diff:.0f}", threshold=threshold),
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply == QMessageBox.No:
                return

        try:
            self.status_label.setText(t('ui.main_window.status_restoring', path=backup_path.name))
            self.backup_manager.restore(backup_path)
            self.show_message_bubble(t('ui.dialogs.restore_success', backup_name=backup_path.name))
            self._maybe_launch_game()
        except Exception as e:
            QMessageBox.critical(self, t('ui.dialogs.error'), t('ui.dialogs.restore_failed', error=e))
        finally:
            self.refresh_backup_list()

    @Slot(Path)
    def delete_backup(self, backup_path: Path):
        reply = QMessageBox.question(
            self, t('ui.dialogs.confirm_delete'),
            t('ui.dialogs.confirm_delete_message', backup_name=backup_path.name),
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                self.status_label.setText(t('ui.main_window.status_deleting', path=backup_path.name))
                self.backup_manager.delete(backup_path)
            except Exception as e:
                QMessageBox.critical(self, t('ui.dialogs.error'), t('ui.dialogs.delete_failed', error=e))
            finally:
                self.refresh_backup_list()

    @Slot(QTableWidgetItem)
    def save_note_from_item(self, item):
        if item.column() == 1: # Note column
            table = item.tableWidget()
            if not table:
                return
            row = item.row()
            timestamp_item = table.item(row, 0)
            if not timestamp_item:
                return

            timestamp = timestamp_item.text()
            new_note = item.text()

            config = config_manager.load_config()
            if config["notes"].get(timestamp) != new_note:
                config["notes"][timestamp] = new_note
                config_manager.save_config(config)
                self.status_label.setText(t('ui.dialogs.note_saved', timestamp=timestamp))

    def show_message_bubble(self, message: str, duration_ms: int = 5000):
        """Show a message bubble that auto-hides after duration_ms"""
        self.message_bubble.setText(message)
        self.message_bubble.setVisible(True)
        self.message_bubble_timer.stop()
        self.message_bubble_timer.start(duration_ms)

    def hide_message_bubble(self):
        """Hide the message bubble"""
        self.message_bubble.setVisible(False)
        self.message_bubble_timer.stop()

    @Slot()
    def open_settings(self):
        settings_dialog = SettingsWindow(self)
        settings_dialog.settings_saved.connect(self.refresh_backup_list)
        settings_dialog.language_changed.connect(self._on_language_changed)
        settings_dialog.exec()

    def _on_language_changed(self, language_code: str):
        """语言改变时的处理"""
        self._retranslate_ui()



    def _retranslate_ui(self):
        """重新翻译UI"""
        self.setWindowTitle(t('ui.main_window.title'))
        self.note_input.setPlaceholderText(t('ui.main_window.note_placeholder'))
        self.backup_button.setText(t('ui.main_window.backup_button'))
        self.restore_last_button.setText(t('ui.main_window.restore_last_button'))
        self.settings_button.setText(t('ui.main_window.settings_button'))

        # 重新设置表格标题
        headers = [
            t('ui.main_window.table_headers.time'),
            t('ui.main_window.table_headers.note'),
            t('ui.main_window.table_headers.restore'),
            t('ui.main_window.table_headers.delete')
        ]
        self.manual_history_table.setHorizontalHeaderLabels(headers)
        self.auto_history_table.setHorizontalHeaderLabels(headers)

        # 重新设置标签页标题
        self.tab_widget.setTabText(0, t('ui.main_window.manual_backup_tab'))
        self.tab_widget.setTabText(1, t('ui.main_window.auto_backup_tab'))

        # 重新设置历史存档组标题
        # 找到QGroupBox并重新设置标题
        for i in range(self.main_layout.count()):
            widget = self.main_layout.itemAt(i).widget()
            if isinstance(widget, QGroupBox):
                widget.setTitle(t('ui.main_window.history_group'))
                break

        self.status_label.setText(t('ui.main_window.status_ready'))
        self.refresh_backup_list()

    def _check_game_running(self) -> bool:
        if process_checker.is_game_running():
            QMessageBox.warning(self, t('ui.dialogs.game_running'), t('ui.dialogs.game_running_message'))
            return True
        return False

    def _maybe_launch_game(self):
        self.backup_manager._reload_config()
        if self.backup_manager.config.get("auto_launch_game", False):
            self._launch_game()
        else:
            reply = QMessageBox.question(
                self, t('ui.dialogs.operation_complete'), t('ui.dialogs.launch_game_question'),
                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
            )
            if reply == QMessageBox.Yes:
                self._launch_game()

    def _launch_game(self):
        try:
            # For Windows, use start command to open steam url
            subprocess.run(["start", "steam://rungameid/3419290"], shell=True, check=True)
        except Exception as e:
            QMessageBox.critical(self, t('ui.dialogs.launch_failed'), t('ui.dialogs.launch_failed', error=e))

    @staticmethod
    def get_windows_accent_color():
        try:
            dwm = ctypes.windll.dwmapi
            color = ctypes.c_uint()
            dwm.DwmGetColorizationColor(ctypes.byref(color), None)
            rgb = color.value & 0xFFFFFF
            return QColor((rgb >> 16) & 0xFF, (rgb >> 8) & 0xFF, rgb & 0xFF)
        except (AttributeError, OSError):
            # Fallback for non-Windows or if DWM API is not available
            return None
