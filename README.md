# ProtPeek

A Python desktop widget to load and display a rotating 3D protein structure from PDB codes or UniProt IDs.

## Features
- 200x200px always-on-top widget
- Enter PDB code (4 characters) or UniProt ID (6+ characters) and click play to load structure
- Supports both RCSB PDB and AlphaFold structures via UniProt IDs
- 3Dmol.js viewer for interactive protein visualization
- Slow clockwise rotation of the structure
- Multiple visualization styles: cartoon, ball and stick
- Close and edit code buttons after loading
- Info button in the top-right shows app details
- Single-file EXE build supported (PyInstaller)

## Requirements
- Python 3.8+
- PyQt5
- PyQtWebEngine
- requests

## Setup
1. Install dependencies:
   ```sh
   pip install PyQt5 PyQtWebEngine requests
   ```
2. Run the app:
   ```sh
   python main.py
   ```

## Build Single EXECUTABLE

### Windows
1. Run the build script:
   ```cmd
   build.bat
   ```
   The script will:
   - Create a virtual environment if it doesn't exist
   - Install all dependencies
   - Build the EXE using PyInstaller
   - Output the EXE to the `dist` folder

2. Manual build (if needed):
   ```cmd
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   pip install pyinstaller
   pyinstaller --onefile --noconsole --clean --name ProtPeek --add-data "3Dmol.js;." --collect-all PyQt5 --collect-all PyQt5.QtPlugins main.py
   ```

### Linux
1. Make the build script executable:
   ```bash
   chmod +x build.sh
   ```

2. Run the build script:
   ```bash
   ./build.sh
   ```
   The script will:
   - Create a virtual environment if it doesn't exist
   - Install all dependencies
   - Build the executable using PyInstaller
   - Output the executable to the `dist` folder

3. Manual build (if needed):
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   pip install pyinstaller
   pyinstaller --onefile --noconsole --clean --name ProtPeek --add-data "3Dmol.js:." --collect-all PyQt5 --collect-all PyQt5.QtPlugins main.py
   ```
   Note: Use `:` instead of `;` for `--add-data` separator on Linux.

## Usage
- Enter a **PDB code** (e.g., `1UBQ`) for structures from RCSB PDB
- Enter a **UniProt ID** (e.g., `Q92793`) for AlphaFold predicted structures
- Select visualization style (cartoon or ball and stick)
- Click play to load and view the structure

### Info button
Click the ℹ button in the top-right to display:

"A Python desktop widget to quickly load and display a rotating 3D protein structure from PDB codes or UniProt IDs.<br>Developed by Saurabh Gayali."

## Notes
- 3Dmol.js is required in the same directory as the executable for the viewer to work.
- The widget is always on top and positioned at the bottom-right of your screen.
- The application properly terminates all background processes when closed.
 - Build scripts will use icons from the `icons` folder when available (`.ico` on Windows, `.png` on Linux). If missing, builds will proceed without icons.

## Acknowledgements

This project uses **3Dmol.js** for interactive molecular visualization.

Rego, N., & Koes, D. (2015).  
*3Dmol.js: molecular visualization with WebGL.*  
Bioinformatics, 31(8), 1322–1324.  
https://doi.org/10.1093/bioinformatics/btu829

