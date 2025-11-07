import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import List

from . import config_manager, file_operations, process_checker
from .backup_entry import BackupEntry
from ..common import constants, helpers


class BackupManager:
    def __init__(self):
        self.config = config_manager.load_config()

    def _reload_config(self):
        self.config = config_manager.load_config()

    def _save_config(self):
        config_manager.save_config(self.config)

    def list_backups(self) -> List[BackupEntry]:
        """Lists all manual and auto backups."""
        self._reload_config()
        backups = []
        manual_bak_path = Path(self.config["backup_root_path"])
        auto_bak_path = Path(self.config["auto_backup_root_path"])

        # Process manual backups
        if manual_bak_path.exists():
            for entry in manual_bak_path.iterdir():
                if entry.is_dir():
                    profile_mtime = file_operations.get_profile_timestamp(entry)
                    if profile_mtime:
                        note = self.config["notes"].get(entry.name, "")
                        backups.append(BackupEntry(
                            path=entry,
                            timestamp=entry.name,
                            note=note,
                            profile_mtime=profile_mtime,
                            auto=False
                        ))

        # Process auto backups
        if auto_bak_path.exists():
            for entry in auto_bak_path.iterdir():
                if entry.is_dir():
                    profile_mtime = file_operations.get_profile_timestamp(entry)
                    if profile_mtime:
                        note = self.config["notes"].get(entry.name, "")
                        backups.append(BackupEntry(
                            path=entry,
                            timestamp=entry.name,
                            note=note,
                            profile_mtime=profile_mtime,
                            auto=True
                        ))

        # Sort by profile modification time, descending
        backups.sort(key=lambda x: x.profile_mtime, reverse=True)
        return backups

    def backup(self, note: str = "", auto: bool = False) -> str | None:
        """Creates a new backup."""
        self._reload_config()
        game_save_path = Path(self.config["game_save_path"])

        if not game_save_path.exists():
            raise FileNotFoundError(f"Game save path not found: {game_save_path}")

        profile_mtime = file_operations.get_profile_timestamp(game_save_path)
        if not profile_mtime:
            raise FileNotFoundError(f"ProfileBrief.ssp not found in {game_save_path}")

        timestamp_str = helpers.format_timestamp(profile_mtime)

        if auto:
            backup_root = Path(self.config["auto_backup_root_path"])
            final_note = constants.AUTO_BACKUP_NOTE_PREFIX
        else:
            backup_root = Path(self.config["backup_root_path"])
            final_note = note

        target_backup_path = backup_root / timestamp_str

        # Check if a backup with the same timestamp already exists in the target location.
        # This provides independent deduplication for manual and auto backups.
        if target_backup_path.exists():
            print(f"Backup for timestamp {timestamp_str} already exists. Skipping.")
            return None

        # Perform the copy
        file_operations.copy_directory(game_save_path, target_backup_path)

        # Update config
        if final_note:
            self.config["notes"][timestamp_str] = final_note
        self.config["last_backup"] = str(target_backup_path)
        self._save_config()

        # Enforce max history
        self._enforce_max_history()
        return timestamp_str

    def restore(self, target_path: Path):
        """Restores a backup."""
        self._reload_config()
        game_save_path = Path(self.config["game_save_path"])

        if not target_path.exists():
            raise FileNotFoundError(f"Backup path not found: {target_path}")

        # Auto-backup before restoring
        current_profile_mtime = file_operations.get_profile_timestamp(game_save_path)
        if current_profile_mtime:
            timestamp_str = helpers.format_timestamp(current_profile_mtime)
            all_backups = self.list_backups()
            if not any(b.timestamp == timestamp_str for b in all_backups):
                self.backup(auto=True)

        # Perform the restore (remove and copy)
        if game_save_path.exists():
            file_operations.remove_directory(game_save_path)
        file_operations.copy_directory(target_path, game_save_path)

        # Update config
        self.config["last_backup"] = str(target_path)
        self._save_config()

    def delete(self, target_path: Path):
        """Deletes a backup."""
        if not target_path.exists() or not target_path.is_dir():
            raise FileNotFoundError(f"Backup path not found: {target_path}")

        timestamp_str = target_path.name
        file_operations.remove_directory(target_path)

        # Update config
        self._reload_config()
        if timestamp_str in self.config["notes"]:
            del self.config["notes"][timestamp_str]
        if self.config["last_backup"] == str(target_path):
            self.config["last_backup"] = ""
        self._save_config()

    def get_time_diff(self, target_path: Path) -> float:
        """Returns the time difference in minutes between a backup and the current save."""
        game_save_path = Path(self.config["game_save_path"])
        current_mtime = file_operations.get_profile_timestamp(game_save_path)
        backup_mtime = file_operations.get_profile_timestamp(target_path)

        if not current_mtime or not backup_mtime:
            return 0.0

        return abs((current_mtime - backup_mtime).total_seconds() / 60.0)

    def _enforce_max_history(self):
        """Deletes the oldest backups for each type if they exceed the configured limit."""
        self._reload_config()
        max_history = self.config.get("max_history", 30)
        all_backups = self.list_backups()

        manual_backups = [b for b in all_backups if not b.auto]
        auto_backups = [b for b in all_backups if b.auto]

        # Enforce for manual backups
        if len(manual_backups) > max_history:
            backups_to_delete = manual_backups[max_history:]
            for backup in backups_to_delete:
                print(f"Purging old manual backup: {backup.path}")
                self.delete(backup.path)

        # Enforce for auto backups
        if len(auto_backups) > max_history:
            backups_to_delete = auto_backups[max_history:]
            for backup in backups_to_delete:
                print(f"Purging old auto backup: {backup.path}")
                self.delete(backup.path)