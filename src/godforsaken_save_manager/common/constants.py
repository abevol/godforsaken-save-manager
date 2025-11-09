def _get_version() -> str:
    """
    Gets the version number, prioritizing the development environment.
    It first tries to read pyproject.toml (for development).
    As a fallback, it imports from the build-time generated _version.py (for packaged apps).
    """
    try:
        # Prioritize reading from pyproject.toml for development mode
        import tomllib
        from pathlib import Path
        pyproject_path = Path(__file__).parent.parent.parent.parent / "pyproject.toml"
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
        return data["tool"]["poetry"]["version"]
    except (ImportError, FileNotFoundError, KeyError):
        # Fallback for packaged apps
        try:
            from .._version import __version__
            return __version__
        except ImportError:
            # Final fallback if everything fails
            return "0.0.0-unknown"

APP_VERSION = _get_version()


CONFIG_FILE_NAME = "backup_manager_config.json"
PROFILE_BRIEF_FILE_NAME = "ProfileBrief.ssp"
GAME_MUTEX_NAME = "n-GOD-FORSAKEN-GodForsaken-exe-SingleInstanceMutex-Default"
DATETIME_FORMAT = "%Y-%m-%d_%H-%M-%S"
GITHUB_REPO = "abevol/godforsaken-save-manager"
