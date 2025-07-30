"""
Widget für automatische Trinkprotokoll-Analyse mit Ollama
"""

import asyncio
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QTextEdit, QTableWidget, QTableWidgetItem,
                            QHeaderView, QMessageBox, QProgressBar, QGroupBox,
                            QSplitter, QFrame)
from PyQt6.QtCore import pyqtSignal, QThread, QTimer, Qt
from PyQt6.QtGui import QFont, QColor
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from utils.universal_analyzer import UniversalAnalyzer, DrinkingProtocol

class AnalysisWorker(QThread):
    """Worker-Thread für Ollama-Analyse"""
    
    analysis_complete = pyqtSignal(object)  # DrinkingProtocol oder None
    error_occurred = pyqtSignal(str)
    progress_updated = pyqtSignal(int)
    
    def __init__(self, text: str):
        super().__init__()
        self.text = text
        self.analyzer = UniversalAnalyzer()
    
    def run(self):
        """Führt Analyse in separatem Thread aus"""
        try:
            self.progress_updated.emit(10)
            
            # Event-Loop für asyncio erstellen
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            self.progress_updated.emit(30)
            
            # Prüfe Konfiguration
            if not self.analyzer.is_configured():
                self.error_occurred.emit("Kein API-Provider konfiguriert. Bitte gehen Sie zu Datei → Einstellungen.")
                return
            
            # Verbindung testen
            if not loop.run_until_complete(self.analyzer.test_connection()):
                provider_info = self.analyzer.get_provider_info()
                self.error_occurred.emit(f"API-Verbindung fehlgeschlagen ({provider_info}). Bitte überprüfen Sie die Einstellungen.")
                return
            
            self.progress_updated.emit(50)
            
            # Analyse durchführen
            protocol = loop.run_until_complete(self.analyzer.analyze_protocol(self.text))
            
            self.progress_updated.emit(90)
            
            if protocol:
                self.analysis_complete.emit(protocol)
            else:
                self.error_occurred.emit("Analyse fehlgeschlagen. Bitte überprüfen Sie den Text und versuchen Sie es erneut.")
            
            self.progress_updated.emit(100)
            
        except Exception as e:
            self.error_occurred.emit(f"Fehler bei der Analyse: {str(e)}")
        finally:
            if 'loop' in locals():
                loop.close()

class ProtocolAnalysisWidget(QWidget):
    """Widget für Trinkprotokoll-Analyse"""
    
    # Signal für Datenübertragung
    protocol_analyzed = pyqtSignal(object)  # DrinkingProtocol
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_protocol: Optional[DrinkingProtocol] = None
        self.analysis_worker: Optional[AnalysisWorker] = None
        
        self.setup_ui()
        self.connect_signals()
    
    def setup_ui(self):
        """Erstellt die UI-Komponenten"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel("🔍 KI-gestützte Protokoll-Analyse")
        title_label.setFont(QFont("Inter", 16, QFont.Weight.Bold))
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Status-Indikator
        self.status_label = QLabel("Bereit")
        self.status_label.setFont(QFont("Inter", 12))
        self.status_label.setStyleSheet("color: #4CAF50;")
        header_layout.addWidget(self.status_label)
        
        layout.addLayout(header_layout)
        
        # Splitter für Text und Vorschau
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Linke Seite: Eingabe
        input_group = QGroupBox("Trinkprotokoll eingeben")
        input_group.setFont(QFont("Inter", 14, QFont.Weight.Bold))
        input_layout = QVBoxLayout(input_group)
        
        # Beispiel-Text
        example_text = """Beispiel-Protokoll:
21.05.2024, 17:43 Uhr: Fahrlässigen Trunkenheit im Verkehr mit dem Fahrrad, (Blutalkoholgehalt mindestens 2,12 Promille zum Entnahmezeitpunkt 18:18 Uhr)

Wie kam es zur Tat?
"An dem Tag hatte meine Tochter Geburtstag und um 13:00 Uhr waren die ersten Gäste geladen. Ich habe dann ab 13:00 Uhr angefangen Alkohol zu trinken und bis ca. 17:30 Uhr insgesamt neun Bier (0,5 l) getrunken." """
        
        self.text_input = QTextEdit()
        self.text_input.setFont(QFont("Inter", 11))
        self.text_input.setPlaceholderText("Fügen Sie hier das Trinkprotokoll ein...")
        self.text_input.setMinimumHeight(200)
        self.text_input.setToolTip("""
<b>KI-gestützte Protokoll-Analyse</b><br><br>
<b>Unterstützte Formate:</b><br>
• Gerichtsprotokolle<br>
• Polizeiberichte<br>
• Selbstauskünfte<br>
• Medizinische Berichte<br><br>
<b>Automatisch erkannt werden:</b><br>
• Datum und Zeiten<br>
• Getränke und Mengen<br>
• Gemessene BAK-Werte<br>
• Konsumzeiträume<br><br>
<b>Hinweis:</b> Ollama muss lokal installiert und gestartet sein.
        """)
        
        input_layout.addWidget(self.text_input)
        
        # Button-Layout
        button_layout = QHBoxLayout()
        
        self.load_example_button = QPushButton("Beispiel laden")
        self.load_example_button.setFont(QFont("Inter", 12))
        self.load_example_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        
        self.analyze_button = QPushButton("🔍 Mit Ollama analysieren")
        self.analyze_button.setFont(QFont("Inter", 12, QFont.Weight.Bold))
        self.analyze_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        
        button_layout.addWidget(self.load_example_button)
        button_layout.addStretch()
        button_layout.addWidget(self.analyze_button)
        
        input_layout.addLayout(button_layout)
        
        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        input_layout.addWidget(self.progress_bar)
        
        splitter.addWidget(input_group)
        
        # Rechte Seite: Vorschau
        preview_group = QGroupBox("Analyse-Vorschau")
        preview_group.setFont(QFont("Inter", 14, QFont.Weight.Bold))
        preview_layout = QVBoxLayout(preview_group)
        
        # Zusammenfassung
        self.summary_label = QLabel("Keine Analyse verfügbar")
        self.summary_label.setFont(QFont("Inter", 12))
        self.summary_label.setStyleSheet("""
            QLabel {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 6px;
                padding: 10px;
            }
        """)
        preview_layout.addWidget(self.summary_label)
        
        # Getränke-Tabelle
        self.drinks_table = QTableWidget()
        self.drinks_table.setFont(QFont("Inter", 11))
        self.setup_drinks_table()
        preview_layout.addWidget(self.drinks_table)
        
        # Übertragen-Button
        self.transfer_button = QPushButton("📋 In App übertragen")
        self.transfer_button.setFont(QFont("Inter", 12, QFont.Weight.Bold))
        self.transfer_button.setEnabled(False)
        self.transfer_button.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #e68900;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        preview_layout.addWidget(self.transfer_button)
        
        splitter.addWidget(preview_group)
        
        # Splitter-Verhältnis
        splitter.setSizes([400, 500])
        
        layout.addWidget(splitter)
    
    def setup_drinks_table(self):
        """Konfiguriert die Getränke-Vorschau-Tabelle"""
        headers = ["Getränk", "Anzahl", "Menge (ml)", "Alkohol (%)", "Alkohol (g)"]
        self.drinks_table.setColumnCount(len(headers))
        self.drinks_table.setHorizontalHeaderLabels(headers)
        
        # Spaltenbreiten
        header = self.drinks_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Getränk
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)    # Anzahl
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)    # Menge
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)    # Alkohol %
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)    # Alkohol g
        
        self.drinks_table.setColumnWidth(1, 60)   # Anzahl
        self.drinks_table.setColumnWidth(2, 100)  # Menge
        self.drinks_table.setColumnWidth(3, 100)  # Alkohol %
        self.drinks_table.setColumnWidth(4, 100)  # Alkohol g
        
        # Stil
        self.drinks_table.setAlternatingRowColors(True)
        self.drinks_table.verticalHeader().setVisible(False)
        self.drinks_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    
    def connect_signals(self):
        """Verbindet alle Signale"""
        self.load_example_button.clicked.connect(self.load_example)
        self.analyze_button.clicked.connect(self.start_analysis)
        self.transfer_button.clicked.connect(self.transfer_to_app)
    
    def load_example(self):
        """Lädt Beispiel-Protokoll"""
        example_text = """21.05.2024, 17:43 Uhr: Fahrlässigen Trunkenheit im Verkehr mit dem Fahrrad, (Blutalkoholgehalt mindestens 2,12 Promille zum Entnahmezeitpunkt 18:18 Uhr)

Wie kam es zur Tat?
"An dem Tag hatte meine Tochter Geburtstag und um 13:00 Uhr waren die ersten Gäste geladen. Ich habe dann ab 13:00 Uhr angefangen Alkohol zu trinken und bis ca. 17:30 Uhr insgesamt neun Bier (0,5 l) getrunken." """
        
        self.text_input.setPlainText(example_text)
    
    def start_analysis(self):
        """Startet die Protokoll-Analyse"""
        text = self.text_input.toPlainText().strip()
        
        if not text:
            QMessageBox.warning(self, "Eingabe erforderlich", 
                              "Bitte geben Sie ein Trinkprotokoll ein.")
            return
        
        # UI-Status aktualisieren
        self.analyze_button.setEnabled(False)
        self.analyze_button.setText("🔍 Analysiere...")
        self.status_label.setText("Analysiere...")
        self.status_label.setStyleSheet("color: #FF9800;")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Worker starten
        self.analysis_worker = AnalysisWorker(text)
        self.analysis_worker.analysis_complete.connect(self.on_analysis_complete)
        self.analysis_worker.error_occurred.connect(self.on_analysis_error)
        self.analysis_worker.progress_updated.connect(self.progress_bar.setValue)
        self.analysis_worker.finished.connect(self.on_analysis_finished)
        
        self.analysis_worker.start()
    
    def on_analysis_complete(self, protocol: DrinkingProtocol):
        """Reagiert auf erfolgreiche Analyse"""
        self.current_protocol = protocol
        self.update_preview(protocol)
        
        self.status_label.setText("Analyse erfolgreich")
        self.status_label.setStyleSheet("color: #4CAF50;")
        self.transfer_button.setEnabled(True)
    
    def on_analysis_error(self, error_message: str):
        """Reagiert auf Analyse-Fehler"""
        QMessageBox.critical(self, "Analyse-Fehler", error_message)
        
        self.status_label.setText("Fehler")
        self.status_label.setStyleSheet("color: #f44336;")
    
    def on_analysis_finished(self):
        """Reagiert auf Beendigung der Analyse"""
        self.analyze_button.setEnabled(True)
        self.analyze_button.setText("🔍 Mit Ollama analysieren")
        self.progress_bar.setVisible(False)
    
    def update_preview(self, protocol: DrinkingProtocol):
        """Aktualisiert die Vorschau mit den analysierten Daten"""
        # Zusammenfassung
        summary_text = f"""
<b>📅 Datum:</b> {protocol.date.strftime('%d.%m.%Y')}<br>
<b>⏰ Konsumzeitraum:</b> {protocol.start_time.strftime('%H:%M')} - {protocol.end_time.strftime('%H:%M')}<br>
<b>🩸 Blutentnahme:</b> {protocol.blood_test_time.strftime('%H:%M')}<br>
<b>📊 Gemessene BAK:</b> {protocol.measured_bac:.2f} ‰<br>
<b>🍺 Gesamtalkohol:</b> {protocol.total_alcohol_grams:.1f} g<br>
<b>🥤 Anzahl Getränke:</b> {len(protocol.drinks)}
        """
        
        self.summary_label.setText(summary_text)
        
        # Getränke-Tabelle
        self.drinks_table.setRowCount(len(protocol.drinks))
        
        for row, drink in enumerate(protocol.drinks):
            # Getränkename
            name_item = QTableWidgetItem(drink['name'])
            self.drinks_table.setItem(row, 0, name_item)
            
            # Anzahl
            quantity_item = QTableWidgetItem(str(drink['quantity']))
            quantity_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.drinks_table.setItem(row, 1, quantity_item)
            
            # Menge
            volume_item = QTableWidgetItem(str(drink['volume']))
            volume_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.drinks_table.setItem(row, 2, volume_item)
            
            # Alkoholgehalt
            alcohol_item = QTableWidgetItem(f"{drink['alcohol_content']:.1f}")
            alcohol_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.drinks_table.setItem(row, 3, alcohol_item)
            
            # Alkohol in Gramm
            grams_item = QTableWidgetItem(f"{drink['alcohol_grams']:.1f}")
            grams_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            grams_item.setBackground(QColor(200, 230, 255))  # Hervorhebung
            self.drinks_table.setItem(row, 4, grams_item)
    
    def transfer_to_app(self):
        """Überträgt die analysierten Daten in die Hauptanwendung"""
        if not self.current_protocol:
            return
        
        # Signal senden
        self.protocol_analyzed.emit(self.current_protocol)
        
        # Bestätigung
        QMessageBox.information(self, "Übertragung erfolgreich", 
                              "Die analysierten Daten wurden erfolgreich in die Getränke-Tabelle übertragen!")
        
        # UI zurücksetzen
        self.transfer_button.setEnabled(False)
        self.current_protocol = None 