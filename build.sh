#!/bin/bash
echo "================================"
echo "Building Executable with PyInstaller"
echo "================================"
echo

# Check if venv exists, create if not
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to create virtual environment"
        exit 1
    fi
    echo "Virtual environment created successfully."
    echo
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to activate virtual environment"
    exit 1
fi

# Install/upgrade dependencies
echo "Installing dependencies..."
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pyinstaller
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    exit 1
fi
echo

# Build the executable using PyInstaller
echo "Building executable..."
# Detect icon in icons folder (.png)
ICON_PATH=""
if [ -f "icons/icon.png" ]; then
    ICON_PATH="icons/icon.png"
else
    FIRST_PNG=$(ls icons/*.png 2>/dev/null | head -n 1)
    if [ -n "$FIRST_PNG" ]; then
        ICON_PATH="$FIRST_PNG"
    else
        echo "WARNING: No .png icon found in icons folder. Proceeding without icon."
    fi
fi

if [ -n "$ICON_PATH" ]; then
    ADD_ICON="--icon $ICON_PATH"
else
    ADD_ICON=""
fi

# Detect UPX for compression (optional)
if command -v upx >/dev/null 2>&1; then
    UPX_DIR="$(dirname "$(command -v upx)")"
    ADD_UPX="--upx-dir \"$UPX_DIR\""
    echo "Using UPX at: $UPX_DIR"
else
    ADD_UPX=""
    echo "WARNING: UPX not found in PATH. Build will proceed without UPX compression."
fi

python -m pyinstaller \
  --onefile \
  --noconsole \
  --clean \
    --name ProtPeek \
    $ADD_ICON \
    $ADD_UPX \
  --add-data "3Dmol.js:." \
  --collect-all PyQt5 \
  --collect-all PyQt5.QtPlugins \
  main.py

if [ $? -ne 0 ]; then
    echo "ERROR: Build failed"
    exit 1
fi

echo
echo "================================"
echo "Build finished successfully!"
echo "Executable is in the dist folder"
echo "================================"
