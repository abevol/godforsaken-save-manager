import win32event
import win32api
import pywintypes

from godforsaken_save_manager.common.constants import GAME_MUTEX_NAME


def is_game_running() -> bool:
    """Checks if the game process is currently running by checking for a mutex."""
    try:
        mutex_handle = win32event.OpenMutex(win32event.SYNCHRONIZE, False, GAME_MUTEX_NAME)
        if mutex_handle:
            win32api.CloseHandle(mutex_handle)
            return True
    except pywintypes.error as e:
        # ERROR_FILE_NOT_FOUND (2) means the mutex doesn't exist.
        if e.winerror == 2:
            return False
        raise  # Re-raise other errors
    return False
