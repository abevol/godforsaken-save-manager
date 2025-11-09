@echo off
setlocal enabledelayedexpansion

:: Use environment variables to dynamically set paths
set "SOURCE_PATH=%USERPROFILE%\AppData\LocalLow\InsightStudio\GodForsakenRelease\game_save"
set "DEST_PATH=%USERPROFILE%\AppData\LocalLow\InsightStudio\GodForsakenRelease\game_save_my_bak"

:: Check if source folder exists
if not exist "%SOURCE_PATH%" (
    echo Error: Source folder "%SOURCE_PATH%" does not exist!
    pause
    exit /b 1
)

:: Create destination folder if it doesn't exist
if not exist "%DEST_PATH%" (
    mkdir "%DEST_PATH%"
    if %errorlevel% neq 0 (
        echo Error: Failed to create destination folder "%DEST_PATH%"
        pause
        exit /b 1
    )
)

:: Copy folder, automatically overwrite same-name files
echo Copying from "%SOURCE_PATH%" to "%DEST_PATH%"...
xcopy "%SOURCE_PATH%\*" "%DEST_PATH%\*" /E /H /Y /R

:: Check if copy was successful
if %errorlevel% equ 0 (
    echo Copy completed successfully!
) else (
    echo An error occurred during copying!
    pause
    exit /b %errorlevel%
)

endlocal

start steam://rungameid/3419290

:: Press any key to continue (optional)
:: pause
