from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
                            QComboBox, QSpinBox, QDoubleSpinBox, QTimeEdit, QDateEdit, QGroupBox,
                            QMessageBox, QDialog, QDialogButtonBox)
from PyQt6.QtCore import pyqtSignal, QTime, QDate, Qt
from PyQt6.QtGui import QFont
from datetime import datetime, time, date, timedelta
from typing import List, Dict

class AddDrinkDialog(QDialog):
    """Dialog zum Hinzufügen von Getränken"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Getränk hinzufügen - BAK Calculator v2.0")
        self.setModal(True)
        self.setFixedSize(450, 400)  # Größer für besseres Layout
        
        # Getränke-Daten initialisieren
        self.drink_data = {
            "Bier (Pils)": {"volume": 500, "alcohol": 4.8},
            "Bier (Weizen)": {"volume": 500, "alcohol": 5.4},
            "Bier (Export)": {"volume": 500, "alcohol": 5.2},
            "Wein (Rot)": {"volume": 200, "alcohol": 12.5},
            "Wein (Weiß)": {"volume": 200, "alcohol": 11.5},
            "Sekt": {"volume": 100, "alcohol": 11.0},
            "Wodka": {"volume": 40, "alcohol": 40.0},
            "Whisky": {"volume": 40, "alcohol": 40.0},
            "Rum": {"volume": 40, "alcohol": 40.0},
            "Gin": {"volume": 40, "alcohol": 40.0},
            "Schnaps": {"volume": 20, "alcohol": 38.0},
            "Likör": {"volume": 40, "alcohol": 20.0},
            "Cocktail (Mojito)": {"volume": 250, "alcohol": 8.0},
            "Cocktail (Caipirinha)": {"volume": 200, "alcohol": 12.0},
            "Long Island Iced Tea": {"volume": 300, "alcohol": 18.0},
            "Benutzerdefiniert": {"volume": 500, "alcohol": 5.0}
        }
        
        self.setup_ui()
        self.load_default_drinks()
    
    def setup_ui(self):
        """Erstellt die Dialog-UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)  # Mehr Abstand zwischen Gruppen
        layout.setContentsMargins(20, 20, 20, 20)  # Größere Ränder
        
        # Getränke-Auswahl
        drink_group = QGroupBox("Getränk auswählen")
        drink_group.setFont(QFont("Inter", 13, QFont.Weight.Bold))
        drink_layout = QVBoxLayout(drink_group)
        drink_layout.setSpacing(10)  # Abstand zwischen Elementen
        
        # Vordefinierte Getränke
        predefined_layout = QHBoxLayout()
        predefined_layout.setSpacing(10)
        predefined_label = QLabel("Getränk:")
        predefined_label.setFont(QFont("Inter", 12))
        predefined_label.setMinimumWidth(120)  # Feste Breite für Labels
        predefined_label.setToolTip("""
<b>Alkoholgehalt verschiedener Getränketypen</b><br><br>
Standardisierte Alkoholgehalte nach EU-Verordnung 1169/2011:<br>
• <b>Bier:</b> 3.5-8.0% vol. (Deutschland: Ø 4.8%)<br>
• <b>Wein:</b> 8.5-15.0% vol. (Deutschland: Ø 11.5-13%)<br>
• <b>Spirituosen:</b> 15-80% vol. (Standard: 40%)<br><br>
<b>Wissenschaftliche Referenzen:</b><br>
• <a href="https://pubmed.ncbi.nlm.nih.gov/17234309/">Lachenmeier, D.W. (2007). Safety evaluation of ethyl carbamate in alcoholic beverages. Food Chem Toxicol 45:1016-1025</a><br>
• <a href="https://eur-lex.europa.eu/eli/reg/2011/1169/oj">EU-Verordnung 1169/2011 über die Information der Verbraucher über Lebensmittel</a>
        """)
        
        self.drink_combo = QComboBox()
        self.drink_combo.setFont(QFont("Inter", 12))
        self.drink_combo.currentTextChanged.connect(self.on_drink_changed)
        self.drink_combo.setMinimumHeight(35)  # Größere Höhe für bessere Usability
        self.drink_combo.setToolTip("""
<b>Getränkespezifische Pharmakodynamik</b><br><br>
Verschiedene Getränke haben unterschiedliche Resorptionskinetiken:<br>
• <b>Bier/Wein:</b> Langsamere Resorption durch Kohlenhydrate<br>
• <b>Spirituosen:</b> Schnelle Resorption, höhere Peak-BAK<br>
• <b>Cocktails:</b> Variable Resorption je nach Zuckern/Mixern<br><br>
<b>Kofaktoren:</b> CO₂ (Sekt) ↑ Resorptionsrate um 20-30%
        """)
        
        predefined_layout.addWidget(predefined_label)
        predefined_layout.addWidget(self.drink_combo)
        drink_layout.addLayout(predefined_layout)
        
        # Menge
        volume_layout = QHBoxLayout()
        volume_layout.setSpacing(10)
        volume_label = QLabel("Menge (ml):")
        volume_label.setFont(QFont("Inter", 12))
        volume_label.setMinimumWidth(120)  # Konsistente Label-Breite
        volume_label.setToolTip("""
<b>Volumetrische Alkoholberechnung</b><br><br>
Die Alkoholmenge berechnet sich:<br>
• <b>Ethanol (g) = Volumen (ml) × Vol% × 0.789 g/ml</b><br>
• <b>Dichte Ethanol:</b> 0.789 g/ml bei 20°C<br><br>
<b>Standardportionen:</b><br>
• <b>Bier:</b> 250-500ml (Deutschland: 300/500ml)<br>
• <b>Wein:</b> 125-200ml (Standard: 150ml)<br>
• <b>Spirituosen:</b> 20-40ml (Standard: 30ml)<br><br>
<b>Wissenschaftliche Referenz:</b><br>
• <a href="https://doi.org/10.1111/j.1530-0277.2006.00155.x">Brick, J. (2006). Standardization of alcohol calculations in research. Alcohol Clin Exp Res 30:1276-1287</a><br>
• <a href="https://www.oiml.org/">International Organization of Legal Metrology (OIML): Alcoholometry Tables</a>
        """)
        
        self.volume_spin = QSpinBox()
        self.volume_spin.setFont(QFont("Inter", 12))
        self.volume_spin.setRange(10, 2000)
        self.volume_spin.setValue(500)
        self.volume_spin.setSuffix(" ml")
        self.volume_spin.setMinimumHeight(35)  # Konsistente Höhe
        self.volume_spin.setToolTip("""
<b>Portionsgrößen und Alkoholmenge</b><br><br>
<b>Beispielrechnungen:</b><br>
• 500ml Bier (4.8%) = 18.9g Ethanol<br>
• 200ml Wein (12%) = 18.9g Ethanol<br>
• 40ml Vodka (40%) = 12.6g Ethanol<br><br>
<b>Eine Standardportion ≈ 10-20g Ethanol</b>
        """)
        
        volume_layout.addWidget(volume_label)
        volume_layout.addWidget(self.volume_spin)
        drink_layout.addLayout(volume_layout)
        
        # Alkoholgehalt
        alcohol_layout = QHBoxLayout()
        alcohol_layout.setSpacing(10)
        alcohol_label = QLabel("Alkoholgehalt (%):")
        alcohol_label.setFont(QFont("Inter", 12))
        alcohol_label.setMinimumWidth(120)  # Konsistente Label-Breite
        alcohol_label.setToolTip("""
<b>Alkoholgehalt-Bestimmung und -Deklaration</b><br><br>
<b>Messtechniken:</b><br>
• <b>Pyknometer:</b> Dichte-basiert, ±0.1% vol Genauigkeit<br>
• <b>Refraktometer:</b> Schnell, ±0.2% vol Genauigkeit<br>
• <b>Gaschromatographie:</b> Goldstandard, ±0.05% vol<br><br>
<b>Gesetzliche Toleranzen (EU):</b><br>
• <b>Bier:</b> ±0.5% vol erlaubt<br>
• <b>Wein:</b> ±0.8% vol erlaubt<br>
• <b>Spirituosen:</b> ±0.3% vol erlaubt<br><br>
<b>Wissenschaftliche Referenzen:</b><br>
• <a href="https://eur-lex.europa.eu/eli/reg/2009/606/oj">EG-Verordnung 606/2009 über die Kennzeichnung von Weinbauerzeugnissen</a><br>
• <a href="https://www.aoac.org/">AOAC Official Method 942.06: Alcohol by Volume in Distilled Spirits</a>
        """)
        
        self.alcohol_spin = QDoubleSpinBox()
        self.alcohol_spin.setFont(QFont("Inter", 12))
        self.alcohol_spin.setRange(0.0, 70.0)
        self.alcohol_spin.setDecimals(1)
        self.alcohol_spin.setValue(5.0)
        self.alcohol_spin.setSuffix(" %")
        self.alcohol_spin.setMinimumHeight(35)  # Konsistente Höhe
        self.alcohol_spin.setToolTip("""
<b>Alkoholgehalt-Klassifikation</b><br><br>
<b>Nach EU-Recht:</b><br>
• <b>Alkoholfrei:</b> <0.5% vol<br>
• <b>Alkoholarm:</b> 0.5-1.2% vol<br>
• <b>Bier:</b> 1.2-15% vol (typisch 3.5-8%)<br>
• <b>Wein:</b> 8.5-15% vol<br>
• <b>Spirituosen:</b> >15% vol (meist 40%)<br><br>
<b>Höchste natürliche Gärung:</b> ~16-18% vol (Hefen sterben ab)
        """)
        
        alcohol_layout.addWidget(alcohol_label)
        alcohol_layout.addWidget(self.alcohol_spin)
        drink_layout.addLayout(alcohol_layout)
        
        layout.addWidget(drink_group)
        
        # Zeit
        time_group = QGroupBox("Konsumzeit")
        time_group.setFont(QFont("Inter", 13, QFont.Weight.Bold))
        time_group.setToolTip("""
<b>Chronopharmakologie der Alkoholresorption</b><br><br>
Der Zeitpunkt des Alkoholkonsums beeinflusst die Pharmakodynamik:<br>
• <b>Tageszeit:</b> Circadiane Rhythmen der Leberfunktion<br>
• <b>Reihenfolge:</b> Sequenzielle vs. simultane Aufnahme<br>
• <b>Intervalle:</b> <30min → Summationseffekt, >2h → Eliminationseffekt<br><br>
<b>Wissenschaftliche Referenzen:</b><br>
• <a href="https://pubmed.ncbi.nlm.nih.gov/14977440/">Danel, T. et al. (2003). Chronobiology of ethanol: from chronokinetics to alcohol-related alterations of circadian rhythms. Chronobiol Int 20:947-973</a><br>
• <a href="https://pubmed.ncbi.nlm.nih.gov/30637619/">Jones, A.W. (2019). Forensic aspects of ethanol metabolism. Forensic Sci Med Pathol 15:298-316</a>
        """)
        time_layout = QVBoxLayout(time_group)
        time_layout.setSpacing(10)  # Abstand zwischen Elementen
        
        # Datum
        date_layout = QHBoxLayout()
        date_layout.setSpacing(10)
        date_label = QLabel("Datum:")
        date_label.setFont(QFont("Inter", 12))
        date_label.setMinimumWidth(120)  # Konsistente Label-Breite
        date_label.setToolTip("""
<b>Datum-spezifische Dokumentation</b><br><br>
<b>Forensische Relevanz:</b><br>
• Eindeutige Zuordnung zu Ereignissen<br>
• Rückrechnung zu spezifischen Zeitpunkten<br>
• Mehrtagessitzungen dokumentieren<br><br>
<b>Anwendungen:</b><br>
• Retrospektive BAK-Berechnung<br>
• Trinkprotokoll über mehrere Tage<br>
• Ereignis-basierte Dokumentation
        """)
        
        self.date_edit = QDateEdit()
        self.date_edit.setFont(QFont("Inter", 12))
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setDisplayFormat("dd.MM.yyyy")
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setMinimumHeight(35)  # Konsistente Höhe
        self.date_edit.setToolTip("""
<b>Datum für Konsumzeitpunkt</b><br><br>
<b>Standard:</b> Heutiges Datum<br>
<b>Anpassbar:</b> Vergangene/zukünftige Daten<br>
<b>Format:</b> TT.MM.JJJJ (deutsche Notation)<br><br>
<b>Kalender-Widget</b> verfügbar zum einfachen Auswählen
        """)
        
        date_layout.addWidget(date_label)
        date_layout.addWidget(self.date_edit)
        time_layout.addLayout(date_layout)
        
        # Uhrzeit
        time_selection_layout = QHBoxLayout()
        time_selection_layout.setSpacing(10)
        time_label = QLabel("Uhrzeit:")
        time_label.setFont(QFont("Inter", 12))
        time_label.setMinimumWidth(120)  # Konsistente Label-Breite
        time_label.setToolTip("""
<b>Resorptionskinetik und Timing</b><br><br>
<b>Resorptionszeiten:</b><br>
• <b>Nüchtern:</b> 15-45 min bis Peak-BAK<br>
• <b>Mit Nahrung:</b> 30-120 min bis Peak-BAK<br>
• <b>Langsam trinken:</b> Kontinuierliche Resorption<br><br>
<b>Eliminationsstart:</b> Sofort parallel zur Resorption<br>
<b>Peak-Zeit:</b> Wenn Resorption = Elimination<br><br>
<b>First-Pass-Metabolismus:</b> 15-25% bereits in Magen/Leber
        """)
        
        self.time_edit = QTimeEdit()
        self.time_edit.setFont(QFont("Inter", 12))
        self.time_edit.setTime(QTime.currentTime())
        self.time_edit.setDisplayFormat("HH:mm")
        self.time_edit.setMinimumHeight(35)  # Konsistente Höhe
        self.time_edit.setToolTip("""
<b>Zeitpunkt-spezifische Faktoren</b><br><br>
<b>Konsumzeit beeinflusst:</b><br>
• Resorptionsgeschwindigkeit<br>
• Peak-BAK Höhe und Zeitpunkt<br>
• Gesamteliminationsdauer<br><br>
<b>Forensische Relevanz:</b> Rückrechnung zur Tatzeit
        """)
        
        time_selection_layout.addWidget(time_label)
        time_selection_layout.addWidget(self.time_edit)
        time_layout.addLayout(time_selection_layout)
        
        layout.addWidget(time_group)
        
        # Abstand vor Buttons
        layout.addSpacing(10)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.setFont(QFont("Inter", 12))
        
        # Button-Styling
        ok_button = button_box.button(QDialogButtonBox.StandardButton.Ok)
        ok_button.setText("Hinzufügen")
        ok_button.setMinimumHeight(40)
        ok_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        cancel_button = button_box.button(QDialogButtonBox.StandardButton.Cancel)
        cancel_button.setText("Abbrechen")
        cancel_button.setMinimumHeight(40)
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #616161;
            }
        """)
        
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(button_box)
    
    def load_default_drinks(self):
        """Lädt vordefinierte Getränke"""
        for name, data in self.drink_data.items():
            self.drink_combo.addItem(name)
    
    def on_drink_changed(self):
        """Reagiert auf Getränke-Auswahl"""
        drink_name = self.drink_combo.currentText()
        if drink_name in self.drink_data:
            data = self.drink_data[drink_name]
            self.volume_spin.setValue(data["volume"])
            self.alcohol_spin.setValue(data["alcohol"])
    
    def get_drink_data(self):
        """Gibt die eingegebenen Getränke-Daten zurück"""
        qt = self.time_edit.time()
        qd = self.date_edit.date()
        
        time_obj = time(hour=qt.hour(), minute=qt.minute())
        date_obj = date(year=qd.year(), month=qd.month(), day=qd.day())
        datetime_obj = datetime.combine(date_obj, time_obj)
        
        return {
            'name': self.drink_combo.currentText(),
            'volume': self.volume_spin.value(),
            'alcohol_content': self.alcohol_spin.value(),
            'time': datetime_obj
        }

class DrinksWidget(QWidget):
    """Widget für die Getränkeverwaltung"""
    
    # Signal für Datenänderungen
    data_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.drinks_data = []
        self.setup_ui()
        self.connect_signals()
        # Initial Signal senden, falls Daten vorhanden sind
        if self.drinks_data:
            self.data_changed.emit()
    
    def setup_ui(self):
        """Erstellt die UI-Komponenten"""
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel("Konsumierte Getränke")
        title_label.setFont(QFont("Inter", 16, QFont.Weight.Bold))
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Buttons
        self.add_button = QPushButton("+ Getränk hinzufügen")
        self.add_button.setFont(QFont("Inter", 12))
        self.add_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        self.remove_button = QPushButton("Entfernen")
        self.remove_button.setFont(QFont("Inter", 12))
        self.remove_button.setEnabled(False)
        self.remove_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        
        self.clear_button = QPushButton("Alle löschen")
        self.clear_button.setFont(QFont("Inter", 12))
        self.clear_button.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #e68900;
            }
        """)
        
        header_layout.addWidget(self.add_button)
        header_layout.addWidget(self.remove_button)
        header_layout.addWidget(self.clear_button)
        
        layout.addLayout(header_layout)
        
        # Getränke-Tabelle
        self.drinks_table = QTableWidget()
        self.drinks_table.setFont(QFont("Inter", 11))
        self.setup_table()
        
        layout.addWidget(self.drinks_table)
        
        # Prominente Alkoholsumme direkt unter der Tabelle
        alcohol_summary_layout = QHBoxLayout()
        alcohol_summary_layout.setContentsMargins(10, 5, 10, 5)
        
        # Großer Alkoholsummen-Label
        self.alcohol_total_display = QLabel("Gesamtalkohol: 0.0 g")
        self.alcohol_total_display.setFont(QFont("Inter", 18, QFont.Weight.Bold))
        self.alcohol_total_display.setStyleSheet("""
            QLabel {
                color: #2196F3;
                background-color: #E3F2FD;
                border: 2px solid #2196F3;
                border-radius: 8px;
                padding: 10px 20px;
                margin: 5px 0px;
            }
        """)
        self.alcohol_total_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.alcohol_total_display.setToolTip("""
<b>Gesamtalkoholmenge in Gramm</b><br><br>
<b>Berechnung:</b> Volumen (ml) × Alkoholgehalt (%) × Dichte (0.8 g/ml)<br><br>
<b>Beispiel:</b> 500ml Bier (4.8%) = 500 × 0.048 × 0.8 = 19.2g Ethanol<br><br>
<b>Verwendung:</b> Diese Gesamtmenge wird für alle BAK-Berechnungen verwendet<br><br>
<b>Wissenschaftliche Referenz:</b><br>
• <a href="https://doi.org/10.1111/j.1530-0277.2006.00155.x">Brick, J. (2006). Standardization of alcohol calculations in research</a>
        """)
        
        alcohol_summary_layout.addWidget(self.alcohol_total_display)
        layout.addLayout(alcohol_summary_layout)
        
        # Zusammenfassung
        summary_group = QGroupBox("Zusammenfassung")
        summary_group.setFont(QFont("Inter", 14, QFont.Weight.Bold))
        summary_layout = QVBoxLayout(summary_group)
        
        # Gesamtalkohol
        self.total_alcohol_label = QLabel("Gesamtalkohol: 0.0 g")
        self.total_alcohol_label.setFont(QFont("Inter", 12, QFont.Weight.Bold))
        self.total_alcohol_label.setStyleSheet("color: #2196F3;")
        
        # Anzahl Getränke
        self.drink_count_label = QLabel("Anzahl Getränke: 0")
        self.drink_count_label.setFont(QFont("Inter", 12))
        
        # Zeitspanne
        self.time_span_label = QLabel("Zeitspanne: --")
        self.time_span_label.setFont(QFont("Inter", 12))
        
        summary_layout.addWidget(self.total_alcohol_label)
        summary_layout.addWidget(self.drink_count_label)
        summary_layout.addWidget(self.time_span_label)
        
        layout.addWidget(summary_group)
    
    def setup_table(self):
        """Konfiguriert die Getränke-Tabelle"""
        headers = ["Getränk", "Menge (ml)", "Alkohol (%)", "Datum", "Zeit", "Alkohol (g)"]
        self.drinks_table.setColumnCount(len(headers))
        self.drinks_table.setHorizontalHeaderLabels(headers)
        
        # Spaltenbreiten
        header = self.drinks_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Getränk
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)    # Menge
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)    # Alkohol %
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)    # Datum
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)    # Zeit
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)    # Alkohol g
        
        self.drinks_table.setColumnWidth(1, 100)  # Menge
        self.drinks_table.setColumnWidth(2, 100)  # Alkohol %
        self.drinks_table.setColumnWidth(3, 120)  # Datum
        self.drinks_table.setColumnWidth(4, 80)   # Zeit
        self.drinks_table.setColumnWidth(5, 100)  # Alkohol g
        
        # Stil
        self.drinks_table.setAlternatingRowColors(True)
        self.drinks_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.drinks_table.verticalHeader().setVisible(False)
        
        # Editierbarkeit aktivieren
        self.drinks_table.setEditTriggers(QTableWidget.EditTrigger.DoubleClicked | 
                                        QTableWidget.EditTrigger.EditKeyPressed)
        
        # Signal für Zellenänderungen
        self.drinks_table.cellChanged.connect(self.on_cell_changed)
    
    def connect_signals(self):
        """Verbindet alle Signale"""
        self.add_button.clicked.connect(self.add_drink)
        self.remove_button.clicked.connect(self.remove_selected_drink)
        self.clear_button.clicked.connect(self.clear_drinks)
        self.drinks_table.itemSelectionChanged.connect(self.on_selection_changed)
    
    def add_drink(self):
        """Öffnet Dialog zum Hinzufügen eines Getränks"""
        from datetime import datetime, timedelta
        dialog = AddDrinkDialog(self)
        # Setze Standardzeit auf jetzt minus 30 Minuten
        now_minus_30 = datetime.now() - timedelta(minutes=30)
        dialog.date_edit.setDate(QDate(now_minus_30.year, now_minus_30.month, now_minus_30.day))
        dialog.time_edit.setTime(QTime(now_minus_30.hour, now_minus_30.minute))
        if dialog.exec() == QDialog.DialogCode.Accepted:
            drink_data = dialog.get_drink_data()
            self.drinks_data.append(drink_data)
            self.update_table()
            self.update_summary()
            self.data_changed.emit()
    
    def remove_selected_drink(self):
        """Entfernt das ausgewählte Getränk"""
        current_row = self.drinks_table.currentRow()
        if current_row >= 0:
            reply = QMessageBox.question(
                self, "Getränk entfernen",
                "Möchten Sie das ausgewählte Getränk wirklich entfernen?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                del self.drinks_data[current_row]
                self.update_table()
                self.update_summary()
                self.data_changed.emit()
    
    def clear_drinks(self):
        """Löscht alle Getränke"""
        if self.drinks_data:
            reply = QMessageBox.question(
                self, "Alle Getränke löschen",
                "Möchten Sie wirklich alle Getränke löschen?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.drinks_data.clear()
                self.update_table()
                self.update_summary()
                self.data_changed.emit()
    
    def on_selection_changed(self):
        """Reagiert auf Änderung der Auswahl"""
        has_selection = len(self.drinks_table.selectedItems()) > 0
        self.remove_button.setEnabled(has_selection)
    
    def update_table(self):
        """Aktualisiert die Getränke-Tabelle"""
        # Signal temporär disconnecten um infinite loops zu vermeiden
        try:
            self.drinks_table.cellChanged.disconnect(self.on_cell_changed)
        except TypeError:
            pass
        
        self.drinks_table.setRowCount(len(self.drinks_data))
        
        for row, drink in enumerate(self.drinks_data):
            # Getränkename (editierbar)
            name_item = QTableWidgetItem(drink['name'])
            name_item.setFlags(name_item.flags() | Qt.ItemFlag.ItemIsEditable)
            self.drinks_table.setItem(row, 0, name_item)
            
            # Menge (editierbar)
            volume_item = QTableWidgetItem(f"{drink['volume']}")
            volume_item.setFlags(volume_item.flags() | Qt.ItemFlag.ItemIsEditable)
            volume_item.setToolTip("Doppelklick zum Bearbeiten der Menge")
            self.drinks_table.setItem(row, 1, volume_item)
            
            # Alkoholgehalt (editierbar)
            alcohol_item = QTableWidgetItem(f"{drink['alcohol_content']}")
            alcohol_item.setFlags(alcohol_item.flags() | Qt.ItemFlag.ItemIsEditable)
            alcohol_item.setToolTip("Doppelklick zum Bearbeiten des Alkoholgehalts")
            self.drinks_table.setItem(row, 2, alcohol_item)
            
            # Datum (editierbar)
            date_str = drink['time'].strftime('%d.%m.%Y')
            date_item = QTableWidgetItem(date_str)
            date_item.setFlags(date_item.flags() | Qt.ItemFlag.ItemIsEditable)
            date_item.setToolTip("Doppelklick zum Bearbeiten (Format: TT.MM.JJJJ)")
            self.drinks_table.setItem(row, 3, date_item)
            
            # Zeit (editierbar)
            time_str = drink['time'].strftime('%H:%M')
            time_item = QTableWidgetItem(time_str)
            time_item.setFlags(time_item.flags() | Qt.ItemFlag.ItemIsEditable)
            time_item.setToolTip("Doppelklick zum Bearbeiten (Format: HH:MM)")
            self.drinks_table.setItem(row, 4, time_item)
            
            # Alkohol in Gramm (nicht editierbar - automatisch berechnet)
            try:
                alcohol_grams = float(drink['volume']) * float(drink['alcohol_content']) / 100 * 0.789
            except Exception:
                alcohol_grams = 0.0
            alcohol_item = QTableWidgetItem(f"{alcohol_grams:.1f} g")
            alcohol_item.setFlags(alcohol_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            alcohol_item.setBackground(Qt.GlobalColor.lightGray)
            alcohol_item.setToolTip("Automatisch berechnet: Volumen × Alkohol% × 0.789")
            self.drinks_table.setItem(row, 5, alcohol_item)
        
        # Signal wieder connecten
        self.drinks_table.cellChanged.connect(self.on_cell_changed)
    
    def update_summary(self):
        """Aktualisiert die Zusammenfassung"""
        if not self.drinks_data:
            self.alcohol_total_display.setText("Gesamtalkohol: 0.0 g")
            self.total_alcohol_label.setText("Gesamtalkohol: 0.0 g")
            self.drink_count_label.setText("Anzahl Getränke: 0")
            self.time_span_label.setText("Zeitspanne: --")
            return
        
        # Gesamtalkohol berechnen
        total_alcohol = sum(
            drink['volume'] * (drink['alcohol_content'] / 100) * 0.8
            for drink in self.drinks_data
        )
        
        # Anzahl Getränke
        drink_count = len(self.drinks_data)
        
        # Zeitspanne berechnen
        if drink_count > 1:
            times = [drink['time'] for drink in self.drinks_data]
            min_time = min(times)
            max_time = max(times)
            time_span = max_time - min_time
            
            # Zeitspanne korrekt berechnen (auch über mehrere Tage)
            total_seconds = time_span.total_seconds()
            days = time_span.days
            hours = int(total_seconds // 3600) % 24
            minutes = int((total_seconds % 3600) // 60)
            
            if days > 0:
                time_span_text = f"{days}d {hours:02d}:{minutes:02d} Stunden"
            else:
                time_span_text = f"{hours:02d}:{minutes:02d} Stunden"
        else:
            time_span_text = "Einzelgetränk"
        
        # Labels aktualisieren
        self.alcohol_total_display.setText(f"Gesamtalkohol: {total_alcohol:.1f} g")
        self.total_alcohol_label.setText(f"Gesamtalkohol: {total_alcohol:.1f} g")
        self.drink_count_label.setText(f"Anzahl Getränke: {drink_count}")
        self.time_span_label.setText(f"Zeitspanne: {time_span_text}")
    
    def get_drinks_data(self) -> List[Dict]:
        """Gibt die aktuellen Getränke-Daten zurück (immer float für volume und alcohol_content, time als datetime)"""
        from datetime import datetime
        drinks = []
        for drink in self.drinks_data:
            d = drink.copy()
            # Korrigiere Typen
            try:
                d['volume'] = float(d['volume'])
            except Exception:
                d['volume'] = 0.0
            try:
                d['alcohol_content'] = float(d['alcohol_content'])
            except Exception:
                d['alcohol_content'] = 0.0
            # Zeitfeld sicherstellen
            if not isinstance(d['time'], datetime):
                # Versuche verschiedene Formate
                try:
                    d['time'] = datetime.strptime(d['time'], '%d.%m.%Y %H:%M')
                except Exception:
                    try:
                        d['time'] = datetime.fromisoformat(d['time'])
                    except Exception:
                        d['time'] = datetime.now()
            drinks.append(d)
        return drinks
    
    def set_drinks_data(self, data: List[Dict]):
        """Setzt die Getränke-Daten"""
        self.drinks_data = data.copy()
        self.update_table()
        self.update_summary()
    
    def add_default_drinks(self):
        """Fügt Standard-Getränke für Tests hinzu"""
        today = datetime.now().date()
        default_drinks = [
            {
                'name': 'Bier (Pils)',
                'volume': 500,
                'alcohol_content': 4.8,
                'time': datetime.combine(today, time(hour=20, minute=0))
            },
            {
                'name': 'Wein (Rot)',
                'volume': 200,
                'alcohol_content': 12.5,
                'time': datetime.combine(today, time(hour=21, minute=0))
            }
        ]
        
        self.drinks_data.extend(default_drinks)
        self.update_table()
        self.update_summary()
        self.data_changed.emit()

    def on_cell_changed(self, row, column):
        """Reagiert auf Änderung einer Zelle"""
        if row >= len(self.drinks_data):
            return
        
        # Signal temporär disconnecten (robust)
        try:
            self.drinks_table.cellChanged.disconnect(self.on_cell_changed)
        except TypeError:
            pass
        
        try:
            drink = self.drinks_data[row]
            
            if column == 0:  # Getränkename
                new_name = self.drinks_table.item(row, column).text().strip()
                if new_name:
                    drink['name'] = new_name
                else:
                    # Ungültiger Name - zurücksetzen
                    self.drinks_table.item(row, column).setText(drink['name'])
            
            elif column == 1:  # Menge
                try:
                    new_volume = float(self.drinks_table.item(row, column).text().replace(',', '.'))
                    if 0 < new_volume <= 5000:  # Sinnvolle Grenzen
                        drink['volume'] = new_volume
                    else:
                        raise ValueError("Volumen außerhalb des gültigen Bereichs")
                except ValueError:
                    # Ungültiger Wert - zurücksetzen
                    self.drinks_table.item(row, column).setText(str(drink['volume']))
                    QMessageBox.warning(self, "Ungültiger Wert", 
                                      "Bitte geben Sie ein gültiges Volumen zwischen 1 und 5000 ml ein.")
            
            elif column == 2:  # Alkoholgehalt
                try:
                    new_alcohol = float(self.drinks_table.item(row, column).text().replace(',', '.'))
                    if 0 <= new_alcohol <= 100:  # 0-100%
                        drink['alcohol_content'] = new_alcohol
                    else:
                        raise ValueError("Alkoholgehalt außerhalb des gültigen Bereichs")
                except ValueError:
                    # Ungültiger Wert - zurücksetzen
                    self.drinks_table.item(row, column).setText(str(drink['alcohol_content']))
                    QMessageBox.warning(self, "Ungültiger Wert", 
                                      "Bitte geben Sie einen gültigen Alkoholgehalt zwischen 0 und 100% ein.")
            
            elif column == 3:  # Datum
                try:
                    date_str = self.drinks_table.item(row, column).text().strip()
                    # Versuche verschiedene Formate
                    try:
                        new_date = datetime.strptime(date_str, '%d.%m.%Y').date()
                    except ValueError:
                        try:
                            new_date = datetime.strptime(date_str, '%d.%m.%y').date()
                        except ValueError:
                            new_date = datetime.strptime(date_str, '%d/%m/%Y').date()
                    
                    # Kombiniere mit bestehender Zeit
                    old_time = drink['time'].time()
                    drink['time'] = datetime.combine(new_date, old_time)
                    
                except ValueError:
                    # Ungültiges Datum - zurücksetzen
                    self.drinks_table.item(row, column).setText(drink['time'].strftime('%d.%m.%Y'))
                    QMessageBox.warning(self, "Ungültiges Datum", 
                                      "Bitte geben Sie ein gültiges Datum im Format TT.MM.JJJJ ein.")
            
            elif column == 4:  # Zeit
                try:
                    time_str = self.drinks_table.item(row, column).text().strip()
                    new_time = datetime.strptime(time_str, '%H:%M').time()
                    
                    # Kombiniere mit bestehendem Datum
                    old_date = drink['time'].date()
                    drink['time'] = datetime.combine(old_date, new_time)
                    
                except ValueError:
                    # Ungültige Zeit - zurücksetzen
                    self.drinks_table.item(row, column).setText(drink['time'].strftime('%H:%M'))
                    QMessageBox.warning(self, "Ungültige Zeit", 
                                      "Bitte geben Sie eine gültige Zeit im Format HH:MM ein.")
            
            # Tabelle und Zusammenfassung aktualisieren
            self.update_table()
            self.update_summary()
            # Typen für alle Getränke korrigieren
            from datetime import datetime
            for d in self.drinks_data:
                try:
                    d['volume'] = float(d['volume'])
                except Exception:
                    d['volume'] = 0.0
                try:
                    d['alcohol_content'] = float(d['alcohol_content'])
                except Exception:
                    d['alcohol_content'] = 0.0
                if not isinstance(d['time'], datetime):
                    try:
                        d['time'] = datetime.strptime(d['time'], '%d.%m.%Y %H:%M')
                    except Exception:
                        try:
                            d['time'] = datetime.fromisoformat(d['time'])
                        except Exception:
                            d['time'] = datetime.now()
            self.data_changed.emit()
            
        except Exception as e:
            print(f"Fehler beim Bearbeiten der Zelle: {e}")
        finally:
            # Signal wieder connecten
            self.drinks_table.cellChanged.connect(self.on_cell_changed) 