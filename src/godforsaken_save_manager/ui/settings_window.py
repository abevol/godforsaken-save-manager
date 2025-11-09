
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QSpinBox,
    QCheckBox, QFileDialog, QHBoxLayout, QWidget, QComboBox
)
from PySide6.QtCore import Signal, Qt

from ..core import config_manager
from ..i18n.translator import t, get_translator, Language

class SettingsWindow(QDialog):
    settings_saved = Signal()
    language_changed = Signal(str)  # 语言改变信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t('ui.settings_window.title'))
        self.setMinimumWidth(600)
        self.setModal(True)
        self.config = config_manager.load_config()
        self.translator = get_translator()

        # Layouts
        self.main_layout = QVBoxLayout(self)
        self.form_widget = QWidget()
        self.form_widget.setObjectName("settings_form")
        self.form_layout = QFormLayout(self.form_widget)
        self.form_layout.setLabelAlignment(Qt.AlignRight)

        # Widgets
        self.game_save_path_edit = QLineEdit()
        self.game_save_path_edit.setObjectName("setting_line_edit")
        self.backup_root_path_edit = QLineEdit()
        self.backup_root_path_edit.setObjectName("setting_line_edit")
        self.max_history_spinbox = QSpinBox()
        self.max_history_spinbox.setRange(1, 999)
        self.restore_threshold_spinbox = QSpinBox()
        self.restore_threshold_spinbox.setRange(0, 9999)
        self.auto_launch_checkbox = QCheckBox(t('ui.settings_window.auto_launch_label'))

        # Language selection
        self.language_combo = QComboBox()
        self._setup_language_combo()

        # Path selection buttons
        self.game_save_path_button = QPushButton(t('ui.settings_window.select_button'))
        self.backup_root_path_button = QPushButton(t('ui.settings_window.select_button'))

        # Action buttons
        self.save_button = QPushButton(t('ui.settings_window.save_button'))
        self.save_button.setDefault(True)
        self.cancel_button = QPushButton(t('ui.settings_window.cancel_button'))

        # Setup UI
        self._setup_ui()
        self._connect_signals()
        self._load_settings()

    def _setup_language_combo(self):
        """设置语言选择下拉框"""
        # 添加自动检测选项
        auto_detect_text = t('config.language') + " (" + t('ui.settings_window.auto_detect') + ")"
        self.language_combo.addItem(auto_detect_text, None)

        # 添加可用语言
        available_languages = self.translator.get_available_languages()
        for lang_code, lang_name in available_languages.items():
            self.language_combo.addItem(lang_name, lang_code)

    def _setup_ui(self):
        # Path selectors with buttons
        game_save_path_layout = QHBoxLayout()
        game_save_path_layout.addWidget(self.game_save_path_edit)
        game_save_path_layout.addWidget(self.game_save_path_button)

        backup_path_layout = QHBoxLayout()
        backup_path_layout.addWidget(self.backup_root_path_edit)
        backup_path_layout.addWidget(self.backup_root_path_button)

        # Form
        self.form_layout.addRow(t('ui.settings_window.save_path_label'), game_save_path_layout)
        self.form_layout.addRow(t('ui.settings_window.backup_path_label'), backup_path_layout)
        self.form_layout.addRow(t('ui.settings_window.max_history_label'), self.max_history_spinbox)
        self.form_layout.addRow(t('ui.settings_window.restore_threshold_label'), self.restore_threshold_spinbox)
        self.form_layout.addRow(t('ui.settings_window.language_label'), self.language_combo)
        self.form_layout.addRow("", self.auto_launch_checkbox)

        # Buttons layout
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.save_button)
        buttons_layout.addWidget(self.cancel_button)

        self.main_layout.addWidget(self.form_widget)
        self.main_layout.addLayout(buttons_layout)

    def retranslate_ui(self):
        """Retranslates all the UI elements."""
        self.setWindowTitle(t('ui.settings_window.title'))
        self.auto_launch_checkbox.setText(t('ui.settings_window.auto_launch_label'))
        self.game_save_path_button.setText(t('ui.settings_window.select_button'))
        self.backup_root_path_button.setText(t('ui.settings_window.select_button'))
        self.save_button.setText(t('ui.settings_window.save_button'))
        self.cancel_button.setText(t('ui.settings_window.cancel_button'))

        # Update form labels
        self.form_layout.itemAt(0, QFormLayout.LabelRole).widget().setText(t('ui.settings_window.save_path_label'))
        self.form_layout.itemAt(1, QFormLayout.LabelRole).widget().setText(t('ui.settings_window.backup_path_label'))
        self.form_layout.itemAt(2, QFormLayout.LabelRole).widget().setText(t('ui.settings_window.max_history_label'))
        self.form_layout.itemAt(3, QFormLayout.LabelRole).widget().setText(t('ui.settings_window.restore_threshold_label'))
        self.form_layout.itemAt(4, QFormLayout.LabelRole).widget().setText(t('ui.settings_window.language_label'))

        # Update language combo box
        current_data = self.language_combo.currentData()
        self.language_combo.blockSignals(True)
        self.language_combo.clear()
        self._setup_language_combo()
        for i in range(self.language_combo.count()):
            if self.language_combo.itemData(i) == current_data:
                self.language_combo.setCurrentIndex(i)
                break
        self.language_combo.blockSignals(False)

    def _connect_signals(self):
        self.game_save_path_button.clicked.connect(self._select_game_save_path)
        self.backup_root_path_button.clicked.connect(self._select_backup_root_path)
        self.language_combo.currentIndexChanged.connect(self._on_language_changed)
        self.save_button.clicked.connect(self._save_and_close)
        self.cancel_button.clicked.connect(self.reject)

    def _load_settings(self):
        self.game_save_path_edit.setText(self.config.get("game_save_path", ""))
        self.backup_root_path_edit.setText(self.config.get("backup_root_path", ""))
        self.max_history_spinbox.setValue(self.config.get("max_history", 20))
        self.restore_threshold_spinbox.setValue(self.config.get("restore_confirm_threshold_minutes", 20))
        self.auto_launch_checkbox.setChecked(self.config.get("auto_launch_game", True))

        # 设置语言选择
        current_language = self.config.get("language")
        if current_language is None:
            # 自动检测
            self.language_combo.setCurrentIndex(0)
        else:
            # 查找对应语言
            for i in range(self.language_combo.count()):
                if self.language_combo.itemData(i) == current_language:
                    self.language_combo.setCurrentIndex(i)
                    break

    def _on_language_changed(self, index: int):
        """语言选择改变时的处理"""
        if index >= 0:
            selected_language = self.language_combo.itemData(index)
            # 实时切换语言
            self.translator.set_language(selected_language)
            self.retranslate_ui()
            self.language_changed.emit(selected_language or "")

    def _select_game_save_path(self):
        path = QFileDialog.getExistingDirectory(self, t('ui.file_dialog.select_game_save_title'), self.game_save_path_edit.text())
        if path:
            self.game_save_path_edit.setText(path)

    def _select_backup_root_path(self):
        path = QFileDialog.getExistingDirectory(self, t('ui.file_dialog.select_backup_title'), self.backup_root_path_edit.text())
        if path:
            self.backup_root_path_edit.setText(path)

    def _save_and_close(self):
        self.config["game_save_path"] = self.game_save_path_edit.text()
        self.config["backup_root_path"] = self.backup_root_path_edit.text()
        self.config["max_history"] = self.max_history_spinbox.value()
        self.config["restore_confirm_threshold_minutes"] = self.restore_threshold_spinbox.value()
        self.config["auto_launch_game"] = self.auto_launch_checkbox.isChecked()

        # 保存语言设置
        selected_language = self.language_combo.itemData(self.language_combo.currentIndex())
        self.config["language"] = selected_language

        config_manager.save_config(self.config)
        self.settings_saved.emit()
        self.accept()
