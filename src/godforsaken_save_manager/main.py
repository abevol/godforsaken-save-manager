
import sys
from PySide6.QtWidgets import QApplication

from godforsaken_save_manager.ui.main_window import MainWindow
from godforsaken_save_manager.core import config_manager

def main():
    """Main function to run the application."""
    # Ensure config file is created on first run
    config_manager.ensure_config_file_exists()

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
