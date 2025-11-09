
import sys
import ctypes
import os
import time
import shutil
import subprocess
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette

from godforsaken_save_manager.ui.main_window import MainWindow
from godforsaken_save_manager.core import config_manager
from godforsaken_save_manager.common.paths import get_base_path
from godforsaken_save_manager.common.constants import APP_VERSION

def handle_update():
    """
    Handles the second stage of the update process.
    This code runs when the new executable is launched with '--perform-update'.
    """
    if len(sys.argv) > 2 and sys.argv[1] == '--perform-update':
        old_exe_path = sys.argv[2]
        # Give the old process time to terminate gracefully
        time.sleep(2)
        try:
            # The new executable is sys.executable. We move it to replace the old one.
            shutil.move(sys.executable, old_exe_path)
            # Relaunch the application from its original path
            subprocess.Popen([old_exe_path])
        except Exception as e:
            # If something goes wrong, we can't do much, but this might help debugging.
            # In a real-world app, you might want to show a message box.
            print(f"FATAL: Failed to apply update. {e}")
        finally:
            # Exit the temporary updater process
            sys.exit(0)

def main():
    """Main function to run the application."""
    # First thing: handle the update process if applicable
    handle_update()

    # Set AppUserModelID to ensure the taskbar icon is correct, especially in dev.
    # This should be a unique string for the application.
    my_app_id = f'dev.jason.godforsaken-save-manager.{APP_VERSION}'
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
        style_file = base_path / "ui" / "styles" / f"{theme}.qss"

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
