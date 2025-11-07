import shutil
from datetime import datetime
from pathlib import Path

from godforsaken_save_manager.common.constants import PROFILE_BRIEF_FILE_NAME


def copy_directory(src: Path, dst: Path):
    """Recursively copies a directory."""
    if not dst.parent.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dst)

def remove_directory(path: Path):
    """Recursively removes a directory."""
    if path.exists() and path.is_dir():
        shutil.rmtree(path)

def get_profile_timestamp(path: Path) -> datetime | None:
    """Gets the modification time of the profile brief file."""
    profile_file = path / PROFILE_BRIEF_FILE_NAME
    if not profile_file.is_file():
        return None
    return datetime.fromtimestamp(profile_file.stat().st_mtime)
