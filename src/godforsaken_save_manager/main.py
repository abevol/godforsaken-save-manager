
import sys
import ctypes
import os
import time
import shutil
import subprocess
import tempfile # Added this import
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette

from godforsaken_save_manager.ui.main_window import MainWindow
from godforsaken_save_manager.core import config_manager
from godforsaken_save_manager.common.paths import get_base_path
from godforsaken_save_manager.common.constants import APP_VERSION

import psutil
import logging
import traceback

def handle_update():
    """
    Handles the second stage of the update process by checking environment variables.
    This code runs when the new executable is launched by the old one.
    It waits for the parent process to exit, then replaces the old executable.
    """
    if os.environ.get("GFSM_DO_UPDATE") == "1":
        # --- Updater Logging Setup ---
        # Switch back to file-based logging, as console may not be visible.
        log_file = os.path.join(tempfile.gettempdir(), "updater_log.txt")
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            filename=log_file,
            filemode='w'
        )
        logger = logging.getLogger(__name__)
        # --- End Logging Setup ---

        logger.info("Updater process started (triggered by environment variable).")
        try:
            pid = int(os.environ.get("GFSM_UPDATE_PID", "0"))
            old_exe_path = os.environ.get("GFSM_UPDATE_OLD_PATH")
            new_exe_path = sys.executable

            # Unset env vars to prevent loops
            del os.environ["GFSM_DO_UPDATE"]
            if "GFSM_UPDATE_PID" in os.environ: del os.environ["GFSM_UPDATE_PID"]
            if "GFSM_UPDATE_OLD_PATH" in os.environ: del os.environ["GFSM_UPDATE_OLD_PATH"]

            if not pid or not old_exe_path:
                raise ValueError("Missing required update environment variables.")

            logger.info(f"PID to wait for: {pid}")
            logger.info(f"Old executable path: {old_exe_path}")
            logger.info(f"New executable path: {new_exe_path}")

            # 1. Wait for the main process to exit
            logger.info(f"Waiting for parent process {pid} to terminate...")
            try:
                parent = psutil.Process(pid)
                parent.wait(timeout=15)
                logger.info(f"Parent process {pid} terminated.")
            except psutil.NoSuchProcess:
                logger.warning(f"Parent process {pid} already terminated.")
            except (psutil.TimeoutExpired, psutil.AccessDenied) as e:
                logger.warning(f"Could not wait for parent process: {e}. Proceeding after a delay.")
                time.sleep(3)

            # 2. Replace the old executable with the new one
            backup_path = old_exe_path + ".bak"
            logger.info(f"Backup path: {backup_path}")

            if os.path.exists(backup_path):
                logger.info(f"Removing existing backup file: {backup_path}")
                os.remove(backup_path)

            try:
                # Rename the old exe to a backup
                if os.path.exists(old_exe_path):
                    logger.info(f"Renaming {old_exe_path} to {backup_path}")
                    os.rename(old_exe_path, backup_path)
                
                # Copy the new exe to the original path by streaming
                logger.info(f"Attempting to copy {new_exe_path} to {old_exe_path}")
                try:
                    with open(new_exe_path, 'rb') as f_new, open(old_exe_path, 'wb') as f_old:
                        shutil.copyfileobj(f_new, f_old)
                    logger.info("File copy successful.")
                except Exception as copy_error:
                    logger.error("--- FILE COPY FAILED ---")
                    logger.error(f"Error during copy: {copy_error}")
                    logger.error(traceback.format_exc())
                    raise copy_error

                # 3. Relaunch the application from its original path
                logger.info(f"Relaunching application from {old_exe_path}")
                subprocess.Popen([old_exe_path])

            except Exception as e:
                logger.error(f"FATAL: Failed to apply update. Error: {e}")
                logger.error(traceback.format_exc())
                if os.path.exists(backup_path):
                    logger.info(f"Attempting to restore backup from {backup_path}")
                    os.rename(backup_path, old_exe_path)
                ctypes.windll.user32.MessageBoxW(0, f"Failed to apply update. Check updater_log.txt.\nError: {e}", "Update Failed", 0x10 | 0x1000)

        except Exception as e:
            logger.error(f"FATAL: An unexpected error occurred during update. Error: {e}")
            logger.error(traceback.format_exc())
            ctypes.windll.user32.MessageBoxW(0, f"An unexpected error occurred. Check updater_log.txt.\nError: {e}", "Update Error", 0x10 | 0x1000)
        finally:
            logger.info("Updater process finished.")
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
