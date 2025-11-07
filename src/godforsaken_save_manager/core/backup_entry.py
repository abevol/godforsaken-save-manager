from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class BackupEntry:
    path: Path
    timestamp: str  # "2025-11-06_18-30-47"
    note: str
    profile_mtime: datetime
