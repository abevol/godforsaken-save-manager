
import sys
import os
from PySide6.QtWidgets import QApplication

from godforsaken_save_manager.ui.main_window import MainWindow
from godforsaken_save_manager.core import config_manager

def main():
    """Main function to run the application."""
    # Ensure config file is created on first run
    config_manager.ensure_config_file_exists()

    app = QApplication(sys.argv)

    # Load stylesheet
    style_file = os.path.join(os.path.dirname(__file__), "ui/style.qss")
    if os.path.exists(style_file):
        with open(style_file, "r") as f:
            app.setStyleSheet(f.read())

    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
