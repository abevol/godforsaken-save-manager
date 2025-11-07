import json
import os
from pathlib import Path

CONFIG_DIR = Path(os.path.expandvars("%USERPROFILE%")) / "AppData" / "LocalLow" / "InsightStudio" / "GodForsakenRelease"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULTS = {
    "game_save_path": str(CONFIG_DIR / "game_save"),
    "backup_root_path": str(CONFIG_DIR / "game_save_my_bak"),
    "auto_backup_root_path": str(CONFIG_DIR / "game_save_auto_bak"),
    "last_backup": "",
    "max_history": 30,
    "restore_confirm_threshold_minutes": 20,
    "auto_launch_game": True,
    "notes": {}
}

def ensure_config_file_exists():
    """Ensures the config file exists with default values if not present."""
    if not CONFIG_FILE.is_file():
        save_config({})

def load_config() -> dict:
    """Loads the configuration from config.json, returning defaults if it doesn't exist."""
    if not CONFIG_FILE.is_file():
        return ensure_defaults({})
    
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        try:
            config = json.load(f)
        except json.JSONDecodeError:
            config = {}
    return ensure_defaults(config)

def save_config(config: dict):
    """Saves the configuration to config.json, creating the directory if needed."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    full_config = ensure_defaults(config)
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(full_config, f, indent=4, ensure_ascii=False)

def ensure_defaults(config: dict) -> dict:
    """Ensures the given config has all default values."""
    defaults_copy = DEFAULTS.copy()
    defaults_copy.update(config)
    if not isinstance(defaults_copy.get("notes"), dict):
        defaults_copy["notes"] = {}
    return defaults_copy