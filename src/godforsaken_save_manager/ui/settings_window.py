
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QSpinBox,
    QCheckBox, QFileDialog, QHBoxLayout, QWidget
)
from PySide6.QtCore import Signal

from ..core import config_manager

class SettingsWindow(QDialog):
    settings_saved = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setModal(True)
        self.config = config_manager.load_config()

        # Layouts
        self.main_layout = QVBoxLayout(self)
        self.form_layout = QFormLayout()

        # Widgets
        self.game_save_path_edit = QLineEdit()
        self.backup_root_path_edit = QLineEdit()
        self.max_history_spinbox = QSpinBox()
        self.max_history_spinbox.setRange(1, 999)
        self.restore_threshold_spinbox = QSpinBox()
        self.restore_threshold_spinbox.setRange(0, 9999)
        self.auto_launch_checkbox = QCheckBox("恢复/备份后自动启动游戏")

        # Path selection buttons
        self.game_save_path_button = QPushButton("选择")
        self.backup_root_path_button = QPushButton("选择")

        # Action buttons
        self.save_button = QPushButton("保存设置")
        self.cancel_button = QPushButton("取消")

        # Setup UI
        self._setup_ui()
        self._connect_signals()
        self._load_settings()

    def _setup_ui(self):
        # Path selectors with buttons
        game_save_path_layout = QHBoxLayout()
        game_save_path_layout.addWidget(self.game_save_path_edit)
        game_save_path_layout.addWidget(self.game_save_path_button)

        backup_path_layout = QHBoxLayout()
        backup_path_layout.addWidget(self.backup_root_path_edit)
        backup_path_layout.addWidget(self.backup_root_path_button)

        # Form
        self.form_layout.addRow("存档路径:", game_save_path_layout)
        self.form_layout.addRow("备份路径:", backup_path_layout)
        self.form_layout.addRow("最大历史数量:", self.max_history_spinbox)
        self.form_layout.addRow("恢复确认阈值(分钟):", self.restore_threshold_spinbox)
        self.form_layout.addRow("", self.auto_launch_checkbox)

        # Buttons layout
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.save_button)
        buttons_layout.addWidget(self.cancel_button)

        self.main_layout.addLayout(self.form_layout)
        self.main_layout.addLayout(buttons_layout)

    def _connect_signals(self):
        self.game_save_path_button.clicked.connect(self._select_game_save_path)
        self.backup_root_path_button.clicked.connect(self._select_backup_root_path)
        self.save_button.clicked.connect(self._save_and_close)
        self.cancel_button.clicked.connect(self.reject)

    def _load_settings(self):
        self.game_save_path_edit.setText(self.config.get("game_save_path", ""))
        self.backup_root_path_edit.setText(self.config.get("backup_root_path", ""))
        self.max_history_spinbox.setValue(self.config.get("max_history", 20))
        self.restore_threshold_spinbox.setValue(self.config.get("restore_confirm_threshold_minutes", 20))
        self.auto_launch_checkbox.setChecked(self.config.get("auto_launch_game", True))

    def _select_game_save_path(self):
        path = QFileDialog.getExistingDirectory(self, "选择游戏存档路径", self.game_save_path_edit.text())
        if path:
            self.game_save_path_edit.setText(path)

    def _select_backup_root_path(self):
        path = QFileDialog.getExistingDirectory(self, "选择备份根路径", self.backup_root_path_edit.text())
        if path:
            self.backup_root_path_edit.setText(path)

    def _save_and_close(self):
        self.config["game_save_path"] = self.game_save_path_edit.text()
        self.config["backup_root_path"] = self.backup_root_path_edit.text()
        # Auto backup path is derived from backup path
        self.config["auto_backup_root_path"] = self.backup_root_path_edit.text().replace("_my_bak", "_auto_bak")
        self.config["max_history"] = self.max_history_spinbox.value()
        self.config["restore_confirm_threshold_minutes"] = self.restore_threshold_spinbox.value()
        self.config["auto_launch_game"] = self.auto_launch_checkbox.isChecked()

        config_manager.save_config(self.config)
        self.settings_saved.emit()
        self.accept()
