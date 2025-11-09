import requests
import tempfile
import os
import sys
import subprocess
import hashlib
import logging
from typing import Optional, Dict, Any

from ..common.constants import APP_VERSION, GITHUB_REPO

logger = logging.getLogger(__name__)

class Updater:
    """
    Handles application updates by checking for new releases on GitHub.
    """
    def __init__(self):
        self.api_url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
        self.latest_version_info: Optional[Dict[str, Any]] = None

    def check_for_update(self) -> Optional[Dict[str, Any]]:
        """
        Checks for the latest release and returns version info if it's newer.
        """
        try:
            response = requests.get(self.api_url, timeout=10)
            response.raise_for_status()
            data = response.json()
            latest_version = data["tag_name"].lstrip("v")

            # Simple version comparison, can be improved with packaging.version
            if self._is_newer(latest_version, APP_VERSION):
                logger.info(f"New version found: {latest_version}")
                asset = next((a for a in data["assets"] if a["name"] == "version.json"), None)
                if asset:
                    version_info_resp = requests.get(asset["browser_download_url"], timeout=10)
                    version_info_resp.raise_for_status()
                    self.latest_version_info = version_info_resp.json()
                    return self.latest_version_info
                else:
                    logger.warning("Release found, but version.json is missing.")
            else:
                logger.info(f"Current version {APP_VERSION} is up to date.")

        except requests.RequestException as e:
            logger.error(f"Failed to check for updates: {e}")
        except (KeyError, StopIteration):
            logger.error("Failed to parse release API response.")
        
        return None

    def _is_newer(self, new_version: str, current_version: str) -> bool:
        """
        Compares two version strings (e.g., "1.2.0" vs "1.1.0").
        """
        new_parts = list(map(int, new_version.split('.')))
        current_parts = list(map(int, current_version.split('.')))
        return new_parts > current_parts

    def download_and_verify(self) -> Optional[str]:
        """
        Downloads the new executable, verifies its integrity, and returns the path.
        """
        if not self.latest_version_info:
            logger.error("No update information available to download.")
            return None

        exe_url = self.latest_version_info["url"]
        expected_sha256 = self.latest_version_info["sha256"]
        file_name = os.path.basename(exe_url)
        target_path = os.path.join(tempfile.gettempdir(), f"new_{file_name}")

        try:
            logger.info(f"Downloading update from {exe_url} to {target_path}...")
            with requests.get(exe_url, stream=True, timeout=60) as r:
                r.raise_for_status()
                with open(target_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            
            logger.info("Download complete. Verifying file integrity...")
            hasher = hashlib.sha256()
            with open(target_path, "rb") as f:
                buf = f.read(65536)
                while len(buf) > 0:
                    hasher.update(buf)
                    buf = f.read(65536)
            
            actual_sha256 = hasher.hexdigest()

            if actual_sha256.lower() != expected_sha256.lower():
                logger.error(f"Checksum mismatch! Expected {expected_sha256}, got {actual_sha256}")
                os.remove(target_path)
                return None

            logger.info("Verification successful.")
            return target_path

        except requests.RequestException as e:
            logger.error(f"Failed to download update: {e}")
        except IOError as e:
            logger.error(f"File error during download/verification: {e}")

        return None

    def apply_update(self, exe_path: str):
        """
        Launches the new executable and exits the current application.
        """
        logger.info(f"Launching updated application at {exe_path}...")
        try:
            # Using Popen to detach the new process
            subprocess.Popen([exe_path], shell=True)
            logger.info("Exiting current application.")
            sys.exit(0)
        except OSError as e:
            logger.error(f"Failed to launch new executable: {e}")

def run_updater_task():
    """
    Entry point for the update check.
    """
    updater = Updater()
    update_info = updater.check_for_update()
    if update_info:
        # In a real GUI app, you would prompt the user here.
        # For this implementation, we proceed automatically.
        new_exe_path = updater.download_and_verify()
        if new_exe_path:
            updater.apply_update(new_exe_path)

if __name__ == "__main__":
    # For testing purposes
    logging.basicConfig(level=logging.INFO)
    run_updater_task()
