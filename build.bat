@echo off
setlocal EnableExtensions EnableDelayedExpansion

echo =====================================
echo  ProtPeek - Windows Build Script
echo =====================================
echo.

REM -------------------------------------------------
REM Resolve project root (directory of this script)
REM -------------------------------------------------
set "ROOT=%~dp0"

REM -------------------------------------------------
REM Virtual environment setup
REM -------------------------------------------------
if not exist "%ROOT%.venv" (
    echo Creating virtual environment...
    python -m venv "%ROOT%.venv"
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
)

echo Activating virtual environment...
call "%ROOT%.venv\Scripts\activate.bat"
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

echo Installing dependencies...
python -m pip install --upgrade pip
python -m pip install -r "%ROOT%requirements.txt"
python -m pip install pyinstaller
if errorlevel 1 (
    echo ERROR: Dependency installation failed
    pause
    exit /b 1
)

echo.

REM -------------------------------------------------
REM Detect Windows icon (.ico) for executable
REM -------------------------------------------------
set "ICON_PATH="

if exist "%ROOT%\icons\icon.ico" (
    set "ICON_PATH=%ROOT%icons\icon.ico"
) else (
    for %%f in ("%ROOT%assets\icons\*.ico") do (
        set "ICON_PATH=%%f"
        goto :icon_found
    )
)
:icon_found

if defined ICON_PATH (
    echo Using EXE icon: %ICON_PATH%
    set "ICON_ARG=--icon=%ICON_PATH%"
) else (
    echo WARNING: No .ico icon found. Building without EXE icon.
    set "ICON_ARG="
)

echo.

REM -------------------------------------------------
REM Detect UPX for executable compression (optional)
REM -------------------------------------------------
set "UPX_ARG="
set "UPX_EXE="
for /f "delims=" %%u in ('where upx 2^>nul') do (
    set "UPX_EXE=%%u"
    goto :upx_found
)
:upx_found
if defined UPX_EXE (
    for %%d in ("%UPX_EXE%") do set "UPX_DIR=%%~dpd"
    echo Using UPX at: %UPX_EXE%
    set "UPX_ARG=--upx-dir=\"%UPX_DIR%\""
) else (
    echo WARNING: UPX not found in PATH. Build will proceed without UPX compression.
)

echo.

REM -------------------------------------------------
REM Build with PyInstaller
REM -------------------------------------------------
echo Building executable...

python -m PyInstaller ^
  --onefile ^
  --noconsole ^
  --clean ^
  --name ProtPeek ^
  %ICON_ARG% ^
  %UPX_ARG% ^
  --upx-exclude "vcruntime140.dll" ^
  --add-data "3Dmol.js;." ^
  --add-data "icons\icon.png;icons" ^
  --collect-all PyQt5 ^
  --collect-all PyQt5.QtPlugins ^
  main.py

if errorlevel 1 (
    echo.
    echo ERROR: Build failed
    pause
    exit /b 1
)

echo.
echo =====================================
echo  Build completed successfully!
echo  Output: dist\ProtPeek.exe
echo =====================================
echo.
pause
