
import sys
import ctypes
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette

from godforsaken_save_manager.ui.main_window import MainWindow
from godforsaken_save_manager.core import config_manager
from godforsaken_save_manager.common.paths import get_base_path

def main():
    """Main function to run the application."""
    # Set AppUserModelID to ensure the taskbar icon is correct, especially in dev.
    # This should be a unique string for the application.
    my_app_id = 'dev.jason.godforsaken-save-manager.1.0'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(my_app_id)

    # Ensure config file is created on first run
    config_manager.ensure_config_file_exists()

    app = QApplication(sys.argv)

    def load_stylesheet():
        """Loads the appropriate stylesheet based on the system theme."""
        base_path = get_base_path()
        # Detect if the theme is light or dark
        # A lightness value < 128 is generally considered dark
        is_dark_theme = app.palette().color(QPalette.ColorRole.Window).lightness() < 128
        theme = "dark" if is_dark_theme else "light"
        style_file = base_path / "styles" / f"{theme}.qss"

        if style_file.exists():
            with open(style_file, "r", encoding="utf-8") as f:
                stylesheet = f.read()
            app.setStyleSheet(stylesheet)

    # Load initial stylesheet and connect to theme changes
    load_stylesheet()
    app.paletteChanged.connect(load_stylesheet)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
