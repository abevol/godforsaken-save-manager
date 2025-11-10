import requests
import tempfile
import os
import sys
import subprocess
import hashlib
import logging
from typing import Optional, Dict, Any

from ..common.constants import GITHUB_REPO, APP_VERSION
from ..i18n.translator import get_current_language

logger = logging.getLogger(__name__)


class Updater:
    """
    Handles application updates by checking for new releases on GitHub.
    """
    def __init__(self):
        self.api_url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
        self.latest_version_info: Optional[Dict[str, Any]] = None
        self.current_version = APP_VERSION

    def get_update_notes(self) -> str:
        """
        Extracts localized update notes from the latest version info.
        """
        if not self.latest_version_info:
            return ""

        notes = self.latest_version_info.get("notes", {})
        if isinstance(notes, str):  # For backward compatibility
            return notes
        
        app_lang = get_current_language()  # e.g., 'zh_CN' or 'en_US'
        lang_short = "zh" if app_lang and app_lang.startswith("zh") else "en"
        
        return notes.get(lang_short, notes.get("en", "No release notes available."))

    def check_for_update(self) -> Optional[Dict[str, Any]]:
        """
        Checks for the latest release and returns version info if it's newer.
        """
        try:
            response = requests.get(self.api_url, timeout=10)
            response.raise_for_status()
            data = response.json()
            latest_version = data["tag_name"].lstrip("v")

            if self._is_newer(latest_version, self.current_version):
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
                logger.info(f"Current version {self.current_version} is up to date.")

        except requests.RequestException as e:
            logger.error(f"Failed to check for updates: {e}")
        except (KeyError, StopIteration, ValueError):
            logger.error("Failed to parse release API response.")
        
        return None

    def _is_newer(self, new_version: str, current_version: str) -> bool:
        """
        Compares two version strings (e.g., "1.2.0" vs "1.1.0").
        """
        try:
            new_parts = list(map(int, new_version.split('.')))
            current_parts = list(map(int, current_version.split('.')))
            return new_parts > current_parts
        except ValueError:
            logger.warning(f"Could not compare versions '{new_version}' and '{current_version}'")
            return False

    def download_and_verify(self, progress_callback=None) -> Optional[str]:
        """
        Downloads the new executable, verifies its integrity, and returns the path.
        """
        if not self.latest_version_info:
            logger.error("No update information available to download.")
            return None

        exe_url = self.latest_version_info["url"]
        expected_sha256 = self.latest_version_info["sha256"]
        file_name = os.path.basename(exe_url)
        # Use a more specific name for the new executable
        target_path = os.path.join(tempfile.gettempdir(), f"GodForsakenSaveManager_new.exe")

        try:
            logger.info(f"Downloading update from {exe_url} to {target_path}...")
            with requests.get(exe_url, stream=True, timeout=60) as r:
                r.raise_for_status()
                total_size = int(r.headers.get('content-length', 0))
                downloaded_size = 0
                with open(target_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        if total_size > 0 and progress_callback:
                            progress = int((downloaded_size / total_size) * 100)
                            progress_callback(progress)
            
            logger.info("Download complete. Verifying file integrity...")
            if progress_callback:
                progress_callback(100) # Ensure it finishes at 100

            hasher = hashlib.sha256()
            with open(target_path, "rb") as f:
                buf = f.read(65536)
                while len(buf) > 0:
                    hasher.update(buf)
                    buf = f.read(65536)
            
            actual_sha256 = hasher.hexdigest()

            if actual_sha256.lower() != expected_sha256.lower().strip():
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

    def apply_update(self, new_exe_path: str):
        """
        Launches the new executable to perform the update and exits.
        Uses environment variables to pass information to the new process.
        """
        logger.info(f"Launching updater process with {new_exe_path}...")
        try:
            # Use environment variables to signal the new process to perform an update.
            # This is more reliable for Nuitka-built apps than command-line args.
            update_env = os.environ.copy()
            update_env["GFSM_DO_UPDATE"] = "1"
            update_env["GFSM_UPDATE_PID"] = str(os.getpid())
            update_env["GFSM_UPDATE_OLD_PATH"] = sys.executable
            
            subprocess.Popen([new_exe_path], env=update_env)
        except OSError as e:
            logger.error(f"Failed to launch new executable: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred while applying update: {e}")