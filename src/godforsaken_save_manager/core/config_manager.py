import json
import os
from pathlib import Path

from godforsaken_save_manager.common.constants import CONFIG_FILE_NAME

GAME_PROFILE_DIR = Path(os.path.expandvars("%USERPROFILE%")) / "AppData" / "LocalLow" / "InsightStudio" / "GodForsakenRelease"
DEFAULT_BACKUP_ROOT_PATH = GAME_PROFILE_DIR / "game_save_my_bak"

def get_config_file_path(backup_root_path: str | None = None) -> Path:
    """获取配置文件路径，位于备份根目录下"""
    backup_root = Path(backup_root_path) if backup_root_path else DEFAULT_BACKUP_ROOT_PATH
    return backup_root / CONFIG_FILE_NAME


DEFAULTS = {
    "game_save_path": str(GAME_PROFILE_DIR / "game_save"),
    "backup_root_path": str(DEFAULT_BACKUP_ROOT_PATH),
    "last_backup": "",
    "max_history": 30,
    "restore_confirm_threshold_minutes": 20,
    "auto_launch_game": True,
    "notes": {}
}

def ensure_config_file_exists():
    """Ensures the config file exists with default values if not present."""
    config_file = get_config_file_path()
    if not config_file.is_file():
        save_config({})

def load_config() -> dict:
    """Loads the configuration from backup_manager_config.json, returning defaults if it doesn't exist."""
    config_file = get_config_file_path()
    if not config_file.is_file():
        return ensure_defaults({})

    with open(config_file, 'r', encoding='utf-8') as f:
        try:
            config = json.load(f)
        except json.JSONDecodeError:
            config = {}
    return ensure_defaults(config)

def save_config(config: dict):
    """Saves the configuration to backup_manager_config.json, creating the directory if needed."""
    full_config = ensure_defaults(config)
    backup_root_path = Path(full_config["backup_root_path"])
    backup_root_path.mkdir(parents=True, exist_ok=True)

    config_file = backup_root_path / CONFIG_FILE_NAME
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(full_config, f, indent=4, ensure_ascii=False)

def ensure_defaults(config: dict) -> dict:
    """Ensures the given config has all default values."""
    defaults_copy = DEFAULTS.copy()
    defaults_copy.update(config)
    if not isinstance(defaults_copy.get("notes"), dict):
        defaults_copy["notes"] = {}
    return defaults_copy