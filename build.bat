@echo off
rem ==============================================================================
rem Build script for GodForsaken Save Manager
rem ==============================================================================
rem This script compiles the Python application into a single executable file
rem using Nuitka. Ensure you have run 'poetry install' before executing this.

echo Generating version file...
call poetry run python docs/scripts/prepare_build.py
echo.

echo Building GodForsakenSaveManager.exe...

call poetry run nuitka ^
  --standalone ^
  --onefile ^
  --windows-console-mode=disable ^
  --windows-icon-from-ico="src/godforsaken_save_manager/resources/app.ico" ^
  --enable-plugin=pyside6 ^
  --include-data-dir=src/godforsaken_save_manager/resources=resources ^
  --include-data-dir=src/godforsaken_save_manager/ui/styles=ui/styles ^
  --include-data-dir=src/godforsaken_save_manager/i18n/langs=i18n/langs ^
  --output-dir=build ^
  --output-filename=GodForsakenSaveManager.exe ^
  src/godforsaken_save_manager/main.py

if %errorlevel% equ 0 (
  echo.
  echo Build successful!
  echo The executable can be found in the project root directory as GodForsakenSaveManager.exe
) else (
  echo.
  echo Build failed.
)

pause
