#!/usr/bin/env python3
"""
BAK-Kalkulator v2.0
Wissenschaftlicher Blutalkoholkonzentrations-Rechner

Modernisiert mit PyQt6, modularem Design und optimierter Performance.
"""

import sys
import os
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QIcon

# Import der neuen modularen UI
from ui.main_window import MainWindow
from ui.styles.theme_manager import theme_manager

def setup_application():
    """Konfiguriert die Anwendung"""
    app = QApplication(sys.argv)
    
    # App-Metadaten
    app.setApplicationName("BAK-Kalkulator")
    app.setApplicationVersion("2.0")
    app.setOrganizationName("BAK Calculator Team")
    app.setApplicationDisplayName("BAK-Kalkulator v2.0")
    
    # Icon setzen (falls verfügbar)
    try:
        icon_path = os.path.join(os.path.dirname(__file__), 'resources', 'icons', 'app_icon.png')
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))
    except:
        pass  # Kein Icon verfügbar
    
    return app

def main():
    """Hauptfunktion"""
    try:
        # Anwendung erstellen
        app = setup_application()
        
        # Theme-System initialisieren
        theme_manager.apply_theme()
        
        # Hauptfenster erstellen
        window = MainWindow()
        
        # Fenster anzeigen
        window.show()
        
        # Startup-Message
        QTimer.singleShot(1000, lambda: print("🚀 BAK-Kalkulator v2.0 erfolgreich gestartet!"))
        
        # Event-Loop starten
        return app.exec()
        
    except Exception as e:
        # Kritischer Fehler beim Start
        error_msg = f"Kritischer Fehler beim Start der Anwendung:\n\n{str(e)}"
        
        try:
            QMessageBox.critical(None, "Startfehler", error_msg)
        except:
            print(f"KRITISCHER FEHLER: {error_msg}")
        
        return 1

if __name__ == "__main__":
    # Anwendung starten
    exit_code = main()
    sys.exit(exit_code) 