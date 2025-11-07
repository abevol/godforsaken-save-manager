
import os
import subprocess
from pathlib import Path

import ctypes

from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QColor, QIcon
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QInputDialog, QLabel, QLineEdit,
    QGroupBox, QTabWidget, QFrame
)

from ..core import backup_manager, process_checker, config_manager
from .settings_window import SettingsWindow
from ..common.paths import get_base_path


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("神弃之地存档备份管理器 v1.0")

        # Use the robust path helper to find the icon
        # In dev, base_path is .../ui/
        # In prod, base_path is the temp _MEIPASS folder
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
        self.note_input.setPlaceholderText("存档备注")
        self.backup_button = QPushButton("备份当前存档")
        self.backup_button.setDefault(True)
        self.restore_last_button = QPushButton("恢复最近存档")
        self.settings_button = QPushButton("设置")
        self.top_buttons_layout.addWidget(self.backup_button)
        self.top_buttons_layout.addWidget(self.restore_last_button)
        self.top_buttons_layout.addStretch()
        self.top_buttons_layout.addWidget(self.settings_button)
        self.top_layout.addLayout(self.top_buttons_layout)
        self.top_layout.addWidget(self.note_input)

        # History section
        history_groupbox = QGroupBox("历史存档")
        history_layout = QVBoxLayout(history_groupbox)
        self.tab_widget = QTabWidget()
        history_layout.addWidget(self.tab_widget)

        # Manual backups tab
        self.manual_history_table = self._create_history_table()
        self.tab_widget.addTab(self.manual_history_table, "手动备份")

        # Auto backups tab
        self.auto_history_table = self._create_history_table()
        self.tab_widget.addTab(self.auto_history_table, "自动备份")

        # Status bar
        self.status_label = QLabel("就绪")
        self.statusBar().addWidget(self.status_label)

        # Assemble layout
        self.main_layout.addLayout(self.top_layout)
        self.main_layout.addWidget(history_groupbox)

        # Connect signals
        self.backup_button.clicked.connect(self.manual_backup)
        self.restore_last_button.clicked.connect(self.restore_last_backup)
        self.settings_button.clicked.connect(self.open_settings)
        self.manual_history_table.itemChanged.connect(self.save_note_from_item)
        self.auto_history_table.itemChanged.connect(self.save_note_from_item)

        self.refresh_backup_list()

    def _create_history_table(self) -> QTableWidget:
        table = QTableWidget()
        table.setFrameShape(QFrame.NoFrame)
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["时间", "备注", "", ""]) # Ops
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        return table

    def refresh_backup_list(self):
        self.status_label.setText("正在刷新备份列表...")
        self.backup_manager._reload_config() # Ensure config is fresh
        
        all_backups = self.backup_manager.list_backups()
        
        # I am assuming backup_entry has an 'auto' attribute.
        # This is a reasonable assumption given the `backup` method signature.
        manual_backups = [b for b in all_backups if not b.auto]
        auto_backups = [b for b in all_backups if b.auto]

        self._populate_history_table(self.manual_history_table, manual_backups)
        self._populate_history_table(self.auto_history_table, auto_backups)
        
        self.status_label.setText("就绪")

    def _populate_history_table(self, table: QTableWidget, backups: list):
        table.setRowCount(len(backups))
        for row, backup_entry in enumerate(backups):
            timestamp_item = QTableWidgetItem(backup_entry.timestamp)
            timestamp_item.setFlags(timestamp_item.flags() & ~Qt.ItemIsEditable)
            table.setItem(row, 0, timestamp_item)

            note_item = QTableWidgetItem(backup_entry.note)
            table.setItem(row, 1, note_item)

            # Restore button
            restore_btn = QPushButton("恢复")
            restore_btn.setObjectName("table_button")
            restore_btn.clicked.connect(lambda _, p=backup_entry.path: self.restore_backup(p))
            table.setCellWidget(row, 2, restore_btn)

            # Delete button
            delete_btn = QPushButton("删除")
            delete_btn.setObjectName("table_button")
            delete_btn.clicked.connect(lambda _, p=backup_entry.path: self.delete_backup(p))
            table.setCellWidget(row, 3, delete_btn)

    @Slot()
    def manual_backup(self):
        if self._check_game_running():
            return

        note = self.note_input.text()
        try:
            self.status_label.setText("正在备份...")
            # The `auto` parameter is explicitly set to False for manual backups.
            timestamp = self.backup_manager.backup(note=note, auto=False)
            if timestamp:
                QMessageBox.information(self, "成功", f"存档已备份至 {timestamp}")
                self.note_input.clear()
                self._maybe_launch_game()
            else:
                QMessageBox.warning(self, "注意", "已存在相同时间戳的存档，本次未创建新备份。")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"备份失败: {e}")
        finally:
            self.refresh_backup_list()

    @Slot()
    def restore_last_backup(self):
        if self._check_game_running():
            return

        last_backup_path_str = self.backup_manager.config.get("last_backup")
        if not last_backup_path_str:
            QMessageBox.warning(self, "错误", "没有找到最近的备份记录。")
            return

        last_backup_path = Path(last_backup_path_str)
        if not last_backup_path.exists():
            QMessageBox.warning(self, "错误", f"备份文件不存在: {last_backup_path}")
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
                self, "确认恢复",
                f"该存档创建于 {time_diff:.0f} 分钟前，远超于您设置的 {threshold} 分钟阈值。\n\n" \
                f"确定要恢复这个旧存档吗？",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply == QMessageBox.No:
                return

        try:
            self.status_label.setText(f"正在从 {backup_path.name} 恢复...")
            self.backup_manager.restore(backup_path)
            QMessageBox.information(self, "成功", f"已成功从 {backup_path.name} 恢复存档。")
            self._maybe_launch_game()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"恢复失败: {e}")
        finally:
            self.refresh_backup_list()

    @Slot(Path)
    def delete_backup(self, backup_path: Path):
        reply = QMessageBox.question(
            self, "确认删除", f"确定要永久删除备份 {backup_path.name} 吗？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                self.status_label.setText(f"正在删除 {backup_path.name}...")
                self.backup_manager.delete(backup_path)
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除失败: {e}")
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
                self.status_label.setText(f"备注已于 {timestamp} 保存.")



    @Slot()
    def open_settings(self):
        settings_dialog = SettingsWindow(self)
        settings_dialog.settings_saved.connect(self.refresh_backup_list)
        settings_dialog.exec()

    def _check_game_running(self) -> bool:
        if process_checker.is_game_running():
            QMessageBox.warning(self, "游戏正在运行", "请先关闭《神弃之地》(GodForsaken.exe) 再执行此操作。")
            return True
        return False

    def _maybe_launch_game(self):
        self.backup_manager._reload_config()
        if self.backup_manager.config.get("auto_launch_game", False):
            self._launch_game()
        else:
            reply = QMessageBox.question(
                self, "操作完成", "是否立即启动游戏？",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
            )
            if reply == QMessageBox.Yes:
                self._launch_game()

    def _launch_game(self):
        try:
            # For Windows, use start command to open steam url
            subprocess.run(["start", "steam://rungameid/3419290"], shell=True, check=True)
        except Exception as e:
            QMessageBox.critical(self, "启动失败", f"无法启动游戏: {e}")

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
