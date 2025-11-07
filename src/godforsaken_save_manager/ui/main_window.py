
import os
import subprocess
from pathlib import Path

from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QInputDialog, QLabel
)

from ..core import backup_manager, process_checker, config_manager
from .settings_window import SettingsWindow


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("神弃之地存档管理器 v1.0")
        self.setMinimumSize(800, 600)

        self.backup_manager = backup_manager.BackupManager()

        # Main widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        # Top buttons
        self.top_buttons_layout = QHBoxLayout()
        self.backup_button = QPushButton("备份当前存档")
        self.settings_button = QPushButton("设置")
        self.top_buttons_layout.addWidget(self.backup_button)
        self.top_buttons_layout.addStretch()
        self.top_buttons_layout.addWidget(self.settings_button)

        # History table
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(4)
        self.history_table.setHorizontalHeaderLabels(["时间", "备注", "", ""]) # Ops
        self.history_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.history_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.history_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.history_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.history_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.history_table.setSelectionBehavior(QTableWidget.SelectRows)

        # Status bar
        self.status_label = QLabel("就绪")
        self.statusBar().addWidget(self.status_label)

        # Assemble layout
        self.main_layout.addLayout(self.top_buttons_layout)
        self.main_layout.addWidget(self.history_table)

        # Connect signals
        self.backup_button.clicked.connect(self.manual_backup)
        self.settings_button.clicked.connect(self.open_settings)
        self.history_table.cellDoubleClicked.connect(self.edit_note_on_double_click)

        self.refresh_backup_list()

    def refresh_backup_list(self):
        self.status_label.setText("正在刷新备份列表...")
        self.backup_manager._reload_config() # Ensure config is fresh
        backups = self.backup_manager.list_backups()
        self.history_table.setRowCount(len(backups))

        for row, backup_entry in enumerate(backups):
            self.history_table.setItem(row, 0, QTableWidgetItem(backup_entry.timestamp))
            self.history_table.setItem(row, 1, QTableWidgetItem(backup_entry.note))

            # Restore button
            restore_btn = QPushButton("恢复")
            restore_btn.clicked.connect(lambda _, p=backup_entry.path: self.restore_backup(p))
            self.history_table.setCellWidget(row, 2, restore_btn)

            # Delete button
            delete_btn = QPushButton("删除")
            delete_btn.clicked.connect(lambda _, p=backup_entry.path: self.delete_backup(p))
            self.history_table.setCellWidget(row, 3, delete_btn)
        self.status_label.setText("就绪")

    @Slot()
    def manual_backup(self):
        if self._check_game_running():
            return

        note, ok = QInputDialog.getText(self, "创建备份", "请输入备注 (可选):")
        if ok:
            try:
                self.status_label.setText("正在备份...")
                timestamp = self.backup_manager.backup(note=note, auto=False)
                if timestamp:
                    QMessageBox.information(self, "成功", f"存档已备份至 {timestamp}")
                    self._maybe_launch_game()
                else:
                    QMessageBox.warning(self, "注意", "已存在相同时间戳的存档，本次未创建新备份。")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"备份失败: {e}")
            finally:
                self.refresh_backup_list()

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

    @Slot(int, int)
    def edit_note_on_double_click(self, row, column):
        if column == 1: # Note column
            timestamp_item = self.history_table.item(row, 0)
            if not timestamp_item:
                return
            
            timestamp = timestamp_item.text()
            current_note = self.history_table.item(row, 1).text()
            
            new_note, ok = QInputDialog.getText(self, "修改备注", "请输入新的备注:", text=current_note)
            
            if ok and new_note != current_note:
                config = config_manager.load_config()
                config["notes"][timestamp] = new_note
                config_manager.save_config(config)
                self.refresh_backup_list()

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
            reply = QMessageBox.question(
                self, "操作完成", "是否立即启动游戏？",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
            )
            if reply == QMessageBox.Yes:
                try:
                    # For Windows, use start command to open steam url
                    subprocess.run(["start", "steam://rungameid/3419290"], shell=True, check=True)
                except Exception as e:
                    QMessageBox.critical(self, "启动失败", f"无法启动游戏: {e}")
