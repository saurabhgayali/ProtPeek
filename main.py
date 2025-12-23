
import sys
import requests
import tempfile
import os
import atexit
from PyQt5 import QtCore, QtGui, QtWidgets, QtWebEngineWidgets

HTML_TEMPLATE = """
<html style='background: transparent; overflow: hidden; width:200px; height:200px;'>
    <head>
        <meta name='viewport' content='width=200, height=200, initial-scale=1.0, user-scalable=no'>
        <style>
            html, body { background: transparent !important; margin:0; padding:0; overflow:hidden; width:200px; height:200px; }
            #container { width:200px; height:200px; background: transparent !important; overflow:hidden; }
            ::-webkit-scrollbar { display: none; }
        </style>
    </head>
    <body style='background: transparent;'>
        <div id='container'></div>
        <script src="../3Dmol.js"></script>
        <script>
            let viewer = $3Dmol.createViewer('container', {backgroundColor: 'rgba(0,0,0,0)'});
            let pdbData = `{pdb}`;
            viewer.addModel(pdbData, 'pdb');
            let style = '{style}';
            if(style === 'cartoon') {
                viewer.setStyle({}, {cartoon: {color: 'spectrum'}});
            } else if(style === 'gaussian' || style === 'surface') {
                viewer.setStyle({}, {cartoon: {color: 'spectrum'}});
                viewer.addSurface($3Dmol.SurfaceType.VDW, {opacity:0.8, color:'white'});
            } else if(style === 'ballstick') {
                viewer.setStyle({}, {stick: {radius:0.2}, sphere: {scale:0.3}});
            } else {
                viewer.setStyle({}, {cartoon: {color: 'spectrum'}});
            }
            viewer.zoomTo();
            viewer.render();
            function rotate() {
                viewer.rotate(0.09);
                viewer.render();
                requestAnimationFrame(rotate);
            }
            rotate();
        </script>
    </body>
</html>
"""

class ProteinWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Protein 3D Widget")
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.FramelessWindowHint | QtCore.Qt.Tool)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setFixedSize(200, 210)
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 21, 0, 0)  # Leave 21px at top for buttons
        
        # Track temp files for cleanup
        self.temp_files = []
        self.input = QtWidgets.QLineEdit(self)
        self.input.setPlaceholderText("PDB/UniProt ID")
        self.input.setGeometry(20, 90, 120, 20)
        self.input.show()
        self.playBtn = QtWidgets.QPushButton("▶", self)
        self.playBtn.setGeometry(140, 90, 40, 20)
        self.playBtn.clicked.connect(self.load_pdb)
        self.playBtn.show()
        self.styleDropdown = QtWidgets.QComboBox(self)
        self.styleDropdown.addItems(["cartoon", "ball and stick"])
        self.styleDropdown.setGeometry(20, 110, 160, 20)
        self.styleDropdown.show()
        # Remove from layout, use absolute positioning for initial form
        self.webview = None
        self.loadingLabel = QtWidgets.QLabel("", self)
        self.loadingLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.loadingLabel.setFixedSize(100, 30)
        self.loadingLabel.setStyleSheet("background:rgba(255,255,255,0.7);border-radius:8px;font-size:12px;")
        self.loadingLabel.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.loadingLabel.setContentsMargins(0, 0, 0, 0)
        self.loadingLabel.hide()
        self.layout.addWidget(self.loadingLabel, alignment=QtCore.Qt.AlignCenter)
        # Buttons in top 21px
        self.closeBtn = QtWidgets.QPushButton("✕", self)
        self.closeBtn.setFixedSize(24, 21)
        self.closeBtn.move(170, 0)
        self.closeBtn.clicked.connect(self.close)
        self.closeBtn.setStyleSheet("background:#FFC000;color:black;font-weight:bold;border:none;border-radius:10px;")
        self.closeBtn.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, False)
        self.closeBtn.raise_()
        self.closeBtn.show()
        # Info button (top bar)
        self.infoBtn = QtWidgets.QPushButton("ℹ", self)
        self.infoBtn.setFixedSize(24, 21)
        self.infoBtn.move(110, 0)
        self.infoBtn.clicked.connect(self.show_info)
        self.infoBtn.setStyleSheet("background:#FFC000;color:black;font-weight:bold;border:none;border-radius:10px;")
        self.infoBtn.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, False)
        self.infoBtn.raise_()
        self.infoBtn.show()
        self.editBtn = QtWidgets.QPushButton("✎", self)
        self.editBtn.setFixedSize(24, 21)
        self.editBtn.move(140, 0)
        self.editBtn.clicked.connect(self.edit_code)
        self.editBtn.setStyleSheet("background:#FFC000;color:black;font-weight:bold;border:none;border-radius:10px;")
        self.editBtn.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, False)
        self.editBtn.raise_()
        self.editBtn.hide()
        self.move_to_bottom_right()
        QtWidgets.QApplication.instance().primaryScreen().geometryChanged.connect(self.move_to_bottom_right)

        # Remove manual geometry and use layout for vertical stacking
        self.layout.setContentsMargins(0, 21, 0, 0)
        self.layout.setSpacing(0)
        # Ensure app quits when widget is closed
        self.destroyed.connect(QtWidgets.QApplication.quit)

    def closeEvent(self, event):
        """Override close event to properly cleanup WebEngine"""
        self.cleanup_temp_files()
        if self.webview:
            self.webview.page().deleteLater()
            self.webview.deleteLater()
            self.webview = None
        QtWidgets.QApplication.quit()
        event.accept()
    
    def cleanup_temp_files(self):
        """Clean up all temporary HTML files"""
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception:
                pass
        self.temp_files.clear()

    def move_to_bottom_right(self):
        screen = QtWidgets.QApplication.primaryScreen().availableGeometry()
        x = screen.x() + screen.width() - self.width() - 10
        y = screen.y() + screen.height() - self.height() - 10
        self.move(x, y)

    def load_pdb(self):
        code = self.input.text().strip()
        if not code:
            return
        style = self.styleDropdown.currentText()
        # Map dropdown to 3Dmol.js style
        if style == "ball and stick":
            style_js = "ballstick"
        else:
            style_js = style
        
        # Detect if it's a PDB code (4 chars) or UniProt ID (6+ chars)
        if len(code) == 4:
            # PDB code from RCSB
            url = f"https://files.rcsb.org/download/{code}.pdb"
            source = "PDB"
            self.loadingLabel.setText(f"Loading {source}...")
            self.loadingLabel.show()
            QtWidgets.QApplication.processEvents()
            try:
                r = requests.get(url)
                r.raise_for_status()
                pdb = r.text
            except Exception as e:
                self.loadingLabel.setText("")
                self.loadingLabel.hide()
                QtWidgets.QMessageBox.critical(self, "Error", f"Failed to load {source}: {e}")
                return
        else:
            # UniProt ID from AlphaFold - use API first
            source = "AlphaFold"
            self.loadingLabel.setText(f"Fetching {source} API...")
            self.loadingLabel.show()
            QtWidgets.QApplication.processEvents()
            try:
                # First, get the PDB URL from AlphaFold API
                api_url = f"https://alphafold.ebi.ac.uk/api/prediction/{code}"
                r = requests.get(api_url)
                r.raise_for_status()
                data = r.json()
                
                if not data or len(data) == 0:
                    raise ValueError("No prediction found for this UniProt ID")
                
                pdb_url = data[0].get('pdbUrl')
                if not pdb_url:
                    raise ValueError("PDB URL not found in API response")
                
                # Now download the actual PDB file
                self.loadingLabel.setText(f"Loading {source} PDB...")
                QtWidgets.QApplication.processEvents()
                r = requests.get(pdb_url)
                r.raise_for_status()
                pdb = r.text
            except Exception as e:
                self.loadingLabel.setText("")
                self.loadingLabel.hide()
                QtWidgets.QMessageBox.critical(self, "Error", f"Failed to load {source}: {e}")
                return
        
        self.show_structure(pdb, style_js)

    def show_structure(self, pdb, style):
        if self.webview:
            self.webview.page().deleteLater()
            self.layout.removeWidget(self.webview)
            self.webview.deleteLater()
            self.webview = None
        html = HTML_TEMPLATE.replace('{pdb}', pdb.replace('`', '\\`')).replace('{style}', style)
        
        # Create temp folder if it doesn't exist
        temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        
        fd, temp_html_path = tempfile.mkstemp(suffix='.html', dir=temp_dir)
        
        # Track temp file for cleanup
        self.temp_files.append(temp_html_path)
        
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(html)
        self.webview = QtWebEngineWidgets.QWebEngineView(self)
        self.webview.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        self.webview.setStyleSheet("background: transparent;")
        self.webview.page().setBackgroundColor(QtCore.Qt.transparent)
        profile = self.webview.page().profile()
        profile.setPersistentCookiesPolicy(QtWebEngineWidgets.QWebEngineProfile.NoPersistentCookies)
        profile.setHttpCacheType(QtWebEngineWidgets.QWebEngineProfile.NoCache)
        self.webview.page().featurePermissionRequested.connect(self.deny_feature_permission)
        self.webview.load(QtCore.QUrl.fromLocalFile(temp_html_path))
        self.webview.loadFinished.connect(self.check_3dmol_loaded)
        self.layout.addWidget(self.webview)
        self.input.hide()
        self.playBtn.hide()
        self.styleDropdown.hide()
        self.loadingLabel.hide()
        self.setFixedSize(200, 210)
        self.webview.setFixedSize(200, 200)
        # Buttons in top 21px
        self.closeBtn.raise_()
        self.closeBtn.show()
        self.infoBtn.raise_()
        self.infoBtn.show()
        self.editBtn.raise_()
        self.editBtn.show()

    def deny_feature_permission(self, url, feature):
        self.webview.page().setFeaturePermission(url, feature, QtWebEngineWidgets.QWebEnginePage.PermissionDeniedByUser)

    def check_3dmol_loaded(self):
        js = "typeof $3Dmol !== 'undefined'"
        def handle(result):
            if not result:
                QtWidgets.QMessageBox.critical(self, "Error", "3Dmol.js not loaded. Please ensure 3Dmol.js is in the app directory and not blocked by antivirus.")
        self.webview.page().runJavaScript(js, handle)

    def edit_code(self):
        if self.webview:
            self.webview.page().deleteLater()
            self.layout.removeWidget(self.webview)
            self.webview.deleteLater()
            self.webview = None
        # Restore initial layout positions and sizes
        self.input.setGeometry(20, 90, 120, 20)
        self.playBtn.setGeometry(140, 90, 40, 20)
        self.styleDropdown.setGeometry(20, 110, 160, 20)
        self.input.show()
        self.playBtn.show()
        self.styleDropdown.show()
        # Buttons in top 21px
        self.closeBtn.raise_()
        self.closeBtn.show()
        self.infoBtn.raise_()
        self.infoBtn.show()
        self.editBtn.raise_()
        self.editBtn.hide()

    def show_info(self):
        msg = QtWidgets.QMessageBox(self)
        msg.setIcon(QtWidgets.QMessageBox.Information)
        msg.setWindowTitle("About ProtPeek")
        msg.setTextFormat(QtCore.Qt.RichText)
        msg.setText(
            "A Python desktop widget to quickly load and display a rotating 3D protein structure from PDB codes or UniProt IDs.<br>"
            "Developed by Saurabh Gayali."
        )
        # Keep dialog lightweight and on top similar to the widget
        msg.setWindowFlags(msg.windowFlags() | QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.Tool)
        msg.exec_()

def main():
    # Enable High DPI scaling (important for widgets on modern displays)
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)

    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)

    # Create and show the widget
    widget = ProteinWidget()
    
    # Register cleanup function to run on exit
    atexit.register(widget.cleanup_temp_files)
    
    widget.show()

    # Ensure all processes terminate on exit
    exit_code = app.exec_()
    
    # Force cleanup
    widget.cleanup_temp_files()
    del widget
    del app
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()