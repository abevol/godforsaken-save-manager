import sys
from pathlib import Path


def get_base_path() -> Path:
    """
    Gets the base path for resource files.

    This function is designed to work both in development and within a
    Nuitka one-file bundle.
    """
    # Nuitka injects the '__compiled__' global. This is a reliable way to check
    # if we are running in a compiled state, as sys.frozen can be unreliable.
    if "__compiled__" in globals():
        # In a Nuitka bundle, we use the main module's path as an anchor.
        # The main script's file attribute should be available.
        main_file = getattr(sys.modules.get("__main__"), "__file__", None)
        if main_file is None:
            raise RuntimeError(
                "Cannot determine application path: __main__.__file__ is not set."
            )

        # In the bundle, main.py is at <temp_root>/godforsaken_save_manager/main.py
        # The assets (style.qss, resources/) are at <temp_root>.
        # So, we go up one level from the main script's directory.
        main_module_path = Path(main_file)
        return main_module_path.parent
    else:
        # Development mode: __main__ might not have __file__ when run via a
        # poetry script. Use the path of *this* file (paths.py) as a
        # reliable anchor.
        # This file is at: <project_root>/src/godforsaken_save_manager/common/paths.py
        # The return value is: <project_root>/src/godforsaken_save_manager
        return Path(__file__).parent.parent