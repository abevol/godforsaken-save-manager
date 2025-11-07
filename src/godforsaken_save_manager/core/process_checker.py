import psutil

from godforsaken_save_manager.common.constants import GAME_EXECUTABLE_NAME


def is_game_running() -> bool:
    """Checks if the game process is currently running."""
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] == GAME_EXECUTABLE_NAME:
            return True
    return False
