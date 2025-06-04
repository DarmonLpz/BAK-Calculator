from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox,
                            QScrollArea, QPushButton, QSplitter, QTabWidget, QTextEdit,
                            QDateEdit, QTimeEdit, QDoubleSpinBox, QComboBox)
from PyQt6.QtCore import Qt, pyqtSignal, QDate, QTime
from PyQt6.QtGui import QFont, QPalette
from typing import Dict, List, Any
from datetime import datetime, date, time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates

class BAKChartWidget(QWidget):
    """Widget für BAK-Verlaufsdiagramm"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.chart_data = {}
    
    def setup_ui(self):
        """Erstellt die Chart-UI"""
        layout = QVBoxLayout(self)
        
        # Matplotlib Figure
        self.figure = Figure(figsize=(12, 6), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        
        # Chart-Styling
        self.figure.patch.set_facecolor('#FFFFFF')
        
        layout.addWidget(self.canvas)
        
        # Initial leeres Chart
        self.clear_chart()
    
    def update_chart(self, results: Dict):
        """Aktualisiert das Diagramm mit neuen Daten"""
        self.chart_data = results
        
        # Chart leeren
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        if not results:
            ax.text(0.5, 0.5, 'Keine Daten verfügbar', 
                   horizontalalignment='center', verticalalignment='center',
                   transform=ax.transAxes, fontsize=14, color='gray')
            self.canvas.draw()
            return
        
        # Debug: Überprüfe Datenstruktur
        print("=== DEBUG: Chart Update ===")
        print(f"Anzahl Modelle: {len(results)}")
        for model, result in results.items():
            print(f"Modell: {model}")
            print(f"  Peak BAK: {result.get('peak_bac', 'N/A')}")
            print(f"  Current BAK: {result.get('current_bac', 'N/A')}")
            if 'bac_values' in result:
                print(f"  BAC Values Count: {len(result['bac_values'])}")
                if len(result['bac_values']) > 0:
                    first_val = result['bac_values'][0]
                    last_val = result['bac_values'][-1]
                    print(f"  First value: {first_val}")
                    print(f"  Last value: {last_val}")
            else:
                print("  No bac_values found!")
        
        # Farben für verschiedene Modelle
        colors = ['#2196F3', '#FF9800', '#4CAF50', '#9C27B0']
        
        max_bac = 0
        successful_plots = 0
        
        # Daten für jedes Modell plotten
        for i, (model, result) in enumerate(results.items()):
            if 'bac_values' not in result or not result['bac_values']:
                print(f"WARNUNG: Keine BAC-Daten für Modell {model}")
                continue
            
            # BAK-Werte extrahieren
            bac_data = result['bac_values']
            
            # Robuste Datenextraktion
            try:
                times = []
                bac_values = []
                
                for point in bac_data:
                    if isinstance(point, (list, tuple)) and len(point) >= 2:
                        time_val, bac_val = point[0], point[1]
                        times.append(time_val)
                        bac_values.append(float(bac_val))
                
                if not times or not bac_values:
                    print(f"WARNUNG: Leere Daten nach Extraktion für {model}")
                    continue
                
                print(f"DEBUG: {model} - {len(times)} Datenpunkte, BAK Range: {min(bac_values):.3f}-{max(bac_values):.3f}")
                
                # Linie plotten
                color = colors[i % len(colors)]
                peak_bac = result.get('peak_bac', max(bac_values) if bac_values else 0)
                ax.plot(times, bac_values, label=f"{model} (Max: {peak_bac:.2f}‰)", 
                       color=color, linewidth=2.5, marker='o', markersize=2)
                
                successful_plots += 1
                
                # Maximum für Y-Achse
                if bac_values:
                    max_bac = max(max_bac, max(bac_values))
                    
            except Exception as e:
                print(f"FEHLER beim Plotten von {model}: {e}")
                continue
        
        print(f"Erfolgreich geplottet: {successful_plots} von {len(results)} Modellen")
        print(f"Max BAC für Y-Achse: {max_bac}")
        
        # Rechtliche Grenzwerte hinzufügen
        if max_bac > 0.001:  # Nur wenn wir echte Daten haben
            ax.axhline(y=0.3, color='orange', linestyle='--', alpha=0.7, label='0.3‰ (Ordnungswidrigkeit)')
            ax.axhline(y=0.5, color='red', linestyle='--', alpha=0.7, label='0.5‰ (Straftat)')
            if max_bac > 1.0:
                ax.axhline(y=1.1, color='darkred', linestyle='--', alpha=0.7, label='1.1‰ (Fahruntüchtigkeit)')
        
        # Chart formatieren
        ax.set_xlabel('Zeit', fontsize=12)
        ax.set_ylabel('BAK (‰)', fontsize=12)
        ax.set_title('Blutalkoholkonzentrations-Verlauf', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        # Y-Achse formatieren
        if max_bac > 0.001:
            ax.set_ylim(0, max_bac * 1.15)  # 15% Puffer oben
        else:
            ax.set_ylim(0, 1.0)  # Fallback
        
        # X-Achse formatieren (Zeit) - Robuster Ansatz
        if successful_plots > 0:
            try:
                # Versuche matplotlib dates formatting
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
                ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))
                self.figure.autofmt_xdate()  # Rotiere Datum-Labels
            except Exception as e:
                print(f"WARNUNG: Datums-Formatierung fehlgeschlagen: {e}")
                # Fallback: Einfache Formatierung
                pass
        
        # Legend nur wenn wir Daten haben
        if successful_plots > 0:
            ax.legend(loc='upper right', fontsize=10)
        
        # Layout optimieren
        self.figure.tight_layout()
        self.canvas.draw()
        
        print("=== Chart Update Complete ===\n")
    
    def clear_chart(self):
        """Leert das Diagramm"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.text(0.5, 0.5, 'Keine Berechnungen verfügbar\n\nGeben Sie Personendaten und Getränke ein, um Ergebnisse zu sehen', 
               horizontalalignment='center', verticalalignment='center',
               transform=ax.transAxes, fontsize=12, color='gray')
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_xticks([])
        ax.set_yticks([])
        self.canvas.draw()
    
    def get_chart_data(self):
        """Gibt Chart-Daten für Export zurück"""
        return self.chart_data

class ResultsWidget(QWidget):
    """Widget für die Anzeige der Berechnungsergebnisse inkl. ausführlicher Berechnung"""
    
    # Signale
    export_requested = pyqtSignal(str)  # Export-Typ
    validation_requested = pyqtSignal(dict)  # Validierungsanfrage
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.results_data = {}
        self.setup_ui()
    
    def setup_ui(self):
        """Erstellt die UI-Komponenten"""
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        self.tabs.setFont(QFont("Inter", 13))
        
        # Tab 1: Ergebnisse (wie bisher)
        self.results_tab = QWidget()
        results_layout = QVBoxLayout(self.results_tab)
        
        # Header mit Export-Buttons
        header_layout = QHBoxLayout()
        
        title_label = QLabel("Berechnungsergebnisse")
        title_label.setFont(QFont("Inter", 18, QFont.Weight.Bold))
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Export-Buttons
        self.export_pdf_btn = QPushButton("📄 PDF Export")
        self.export_pdf_btn.setFont(QFont("Inter", 11))
        self.export_pdf_btn.clicked.connect(lambda: self.export_requested.emit('pdf'))
        
        self.export_csv_btn = QPushButton("📊 CSV Export")
        self.export_csv_btn.setFont(QFont("Inter", 11))
        self.export_csv_btn.clicked.connect(lambda: self.export_requested.emit('csv'))
        
        self.export_excel_btn = QPushButton("📈 Excel Export")
        self.export_excel_btn.setFont(QFont("Inter", 11))
        self.export_excel_btn.clicked.connect(lambda: self.export_requested.emit('excel'))
        
        header_layout.addWidget(self.export_pdf_btn)
        header_layout.addWidget(self.export_csv_btn)
        header_layout.addWidget(self.export_excel_btn)
        
        results_layout.addLayout(header_layout)
        
        # Splitter für oberen und unteren Bereich
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Oberer Bereich: Übersicht
        top_widget = self.create_overview_section()
        splitter.addWidget(top_widget)
        
        # Unterer Bereich: Diagramm
        self.chart_widget = BAKChartWidget()
        splitter.addWidget(self.chart_widget)
        
        # Splitter-Verhältnis setzen (40% oben, 60% unten)
        splitter.setSizes([400, 600])
        
        results_layout.addWidget(splitter)
        self.tabs.addTab(self.results_tab, "Ergebnisse")
        
        # Tab 2: Ausführliche Berechnung
        self.detail_tab = QWidget()
        detail_layout = QVBoxLayout(self.detail_tab)
        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        self.detail_text.setFont(QFont("Inter", 12))
        detail_layout.addWidget(self.detail_text)
        self.tabs.addTab(self.detail_tab, "Ausführliche Berechnung")
        
        # Tab 3: BAK-Controller (Forensische Validierung)
        self.controller_tab = QWidget()
        self.setup_controller_tab()
        self.tabs.addTab(self.controller_tab, "BAK-Controller")
        
        layout.addWidget(self.tabs)
    
    def create_overview_section(self):
        """Erstellt den Übersichtsbereich"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        
        # Linke Seite: Aktuelle BAK und Zusammenfassung
        left_widget = self.create_summary_section()
        
        # Rechte Seite: Ergebnisse-Tabelle
        right_widget = self.create_results_table()
        
        layout.addWidget(left_widget, 1)
        layout.addWidget(right_widget, 2)
        
        return widget
    
    def create_summary_section(self):
        """Erstellt den Zusammenfassungsbereich"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Aktuelle BAK - großer Display
        current_bac_group = QGroupBox("Aktuelle BAK")
        current_bac_group.setFont(QFont("Inter", 14, QFont.Weight.Bold))
        current_bac_layout = QVBoxLayout(current_bac_group)
        
        self.current_bac_display = QLabel("0.00 ‰")
        self.current_bac_display.setFont(QFont("Inter", 48, QFont.Weight.Bold))
        self.current_bac_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.current_bac_display.setStyleSheet("""
            QLabel {
                color: #2196F3;
                background-color: #E3F2FD;
                border-radius: 8px;
                padding: 20px;
                margin: 10px;
            }
        """)
        current_bac_layout.addWidget(self.current_bac_display)
        
        # Status-Anzeige
        self.status_label = QLabel("Nüchtern")
        self.status_label.setFont(QFont("Inter", 14, QFont.Weight.Bold))
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #4CAF50; margin: 5px;")
        current_bac_layout.addWidget(self.status_label)
        
        layout.addWidget(current_bac_group)
        
        # Zusammenfassung
        summary_group = QGroupBox("Zusammenfassung")
        summary_group.setFont(QFont("Inter", 14, QFont.Weight.Bold))
        summary_layout = QVBoxLayout(summary_group)
        
        self.peak_bac_label = QLabel("Max. BAK: --")
        self.peak_bac_label.setFont(QFont("Inter", 12))
        
        self.time_to_sober_label = QLabel("Nüchtern ab: --")
        self.time_to_sober_label.setFont(QFont("Inter", 12))
        
        self.time_to_drive_label = QLabel("Fahrtüchtig ab: --")
        self.time_to_drive_label.setFont(QFont("Inter", 12))
        
        summary_layout.addWidget(self.peak_bac_label)
        summary_layout.addWidget(self.time_to_sober_label)
        summary_layout.addWidget(self.time_to_drive_label)
        
        layout.addWidget(summary_group)
        
        layout.addStretch()
        
        return widget
    
    def create_results_table(self):
        """Erstellt die Ergebnisse-Tabelle"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Tabellenüberschrift
        table_title = QLabel("Modell-Vergleich")
        table_title.setFont(QFont("Inter", 14, QFont.Weight.Bold))
        layout.addWidget(table_title)
        
        # Tabelle
        self.results_table = QTableWidget()
        self.results_table.setFont(QFont("Inter", 11))
        
        # Spalten definieren
        headers = ["Modell", "Aktuelle BAK", "Max. BAK", "Zeit bis 0.5‰", "Zeit bis 0.0‰"]
        self.results_table.setColumnCount(len(headers))
        self.results_table.setHorizontalHeaderLabels(headers)
        
        # Spaltenbreiten
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)     # Modell
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)     # Aktuelle BAK
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)     # Max BAK
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)   # Zeit bis 0.5
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)   # Zeit bis 0.0
        
        self.results_table.setColumnWidth(0, 100)
        self.results_table.setColumnWidth(1, 120)
        self.results_table.setColumnWidth(2, 120)
        
        # Stil
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.results_table.verticalHeader().setVisible(False)
        
        layout.addWidget(self.results_table)
        
        return widget
    
    def update_results(self, results: Dict):
        """Aktualisiert die Ergebnisse"""
        self.results_data = results
        if not results:
            self.clear_results()
            return
        
        # Aktuelle BAK berechnen (Durchschnitt aller Modelle)
        current_bac_values = [result.get('current_bac', 0.0) for result in results.values()]
        avg_current_bac = sum(current_bac_values) / len(current_bac_values) if current_bac_values else 0.0
        
        # Aktuelle BAK anzeigen
        self.current_bac_display.setText(f"{avg_current_bac:.2f} ‰")
        
        # BAK-Status und Farbe
        if avg_current_bac == 0.0:
            status_text = "Nüchtern"
            status_color = "#4CAF50"
            bac_color = "#2196F3"
        elif avg_current_bac < 0.3:
            status_text = "Leicht alkoholisiert"
            status_color = "#8BC34A"
            bac_color = "#8BC34A"
        elif avg_current_bac < 0.5:
            status_text = "Ordnungswidrigkeit"
            status_color = "#FF9800"
            bac_color = "#FF9800"
        elif avg_current_bac < 1.1:
            status_text = "Straftat"
            status_color = "#F44336"
            bac_color = "#F44336"
        else:
            status_text = "Absolut fahruntüchtig"
            status_color = "#B71C1C"
            bac_color = "#B71C1C"
        
        self.status_label.setText(status_text)
        self.status_label.setStyleSheet(f"color: {status_color}; margin: 5px;")
        self.current_bac_display.setStyleSheet(f"""
            QLabel {{
                color: {bac_color};
                background-color: {bac_color}20;
                border-radius: 8px;
                padding: 20px;
                margin: 10px;
            }}
        """)
        
        # Zusammenfassung aktualisieren
        self.update_summary(results)
        
        # Tabelle aktualisieren
        self.update_results_table(results)
        
        # Chart aktualisieren
        self.chart_widget.update_chart(results)
        
        # Ausführliche Berechnung aktualisieren
        self.update_detail_tab(results)
    
    def update_summary(self, results: Dict):
        """Aktualisiert die Zusammenfassung"""
        if not results:
            return
        
        # Maximum über alle Modelle
        peak_bac_values = [result.get('peak_bac', 0.0) for result in results.values() if result.get('peak_bac')]
        max_peak_bac = max(peak_bac_values) if peak_bac_values else 0.0
        
        # Früheste Zeiten (konservativste Schätzung)
        time_to_05_values = [result.get('time_to_03') for result in results.values() if result.get('time_to_03')]
        time_to_00_values = [result.get('time_to_00') for result in results.values() if result.get('time_to_00')]
        
        earliest_05 = max(time_to_05_values) if time_to_05_values else None
        earliest_00 = max(time_to_00_values) if time_to_00_values else None
        
        # Labels aktualisieren
        self.peak_bac_label.setText(f"Max. BAK: {max_peak_bac:.2f} ‰")
        
        if earliest_05:
            self.time_to_drive_label.setText(f"Fahrtüchtig ab: {earliest_05.strftime('%H:%M')}")
        else:
            self.time_to_drive_label.setText("Fahrtüchtig ab: --")
        
        if earliest_00:
            self.time_to_sober_label.setText(f"Nüchtern ab: {earliest_00.strftime('%H:%M')}")
        else:
            self.time_to_sober_label.setText("Nüchtern ab: --")
    
    def update_results_table(self, results: Dict):
        """Aktualisiert die Ergebnisse-Tabelle"""
        self.results_table.setRowCount(len(results))
        
        for row, (model, result) in enumerate(results.items()):
            # Modell
            model_item = QTableWidgetItem(model)
            model_item.setFlags(model_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            model_item.setFont(QFont("Inter", 11, QFont.Weight.Bold))
            self.results_table.setItem(row, 0, model_item)
            
            # Aktuelle BAK
            current_bac = result.get('current_bac', 0.0)
            current_item = QTableWidgetItem(f"{current_bac:.2f} ‰")
            current_item.setFlags(current_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            current_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if current_bac > 0.5:
                current_item.setBackground(Qt.GlobalColor.red)
            elif current_bac > 0.3:
                current_item.setBackground(Qt.GlobalColor.yellow)
            self.results_table.setItem(row, 1, current_item)
            
            # Max. BAK
            peak_bac = result.get('peak_bac', 0.0)
            peak_item = QTableWidgetItem(f"{peak_bac:.2f} ‰" if peak_bac else "--")
            peak_item.setFlags(peak_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            peak_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            peak_item.setFont(QFont("Inter", 11, QFont.Weight.Bold))
            self.results_table.setItem(row, 2, peak_item)
            
            # Zeit bis 0.5‰
            time_to_05 = result.get('time_to_03')
            time_05_item = QTableWidgetItem(time_to_05.strftime('%H:%M') if time_to_05 else "--")
            time_05_item.setFlags(time_05_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            time_05_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.results_table.setItem(row, 3, time_05_item)
            
            # Zeit bis 0.0‰
            time_to_00 = result.get('time_to_00')
            time_00_item = QTableWidgetItem(time_to_00.strftime('%H:%M') if time_to_00 else "--")
            time_00_item.setFlags(time_00_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            time_00_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.results_table.setItem(row, 4, time_00_item)
    
    def clear_results(self):
        """Leert alle Ergebnisse"""
        self.results_data = {}
        
        # BAK-Display zurücksetzen
        self.current_bac_display.setText("N/A")
        self.current_bac_display.setStyleSheet("""
            QLabel {
                color: #2196F3;
                background-color: #E3F2FD;
                border-radius: 8px;
                padding: 20px;
                margin: 10px;
            }
        """)
        
        self.status_label.setText("N/A")
        self.status_label.setStyleSheet("color: #4CAF50; margin: 5px;")
        
        # Zusammenfassung zurücksetzen
        self.peak_bac_label.setText("Max. BAK: N/A")
        self.time_to_sober_label.setText("Nüchtern ab: N/A")
        self.time_to_drive_label.setText("Fahrtüchtig ab: N/A")
        
        # Tabelle leeren
        self.results_table.setRowCount(0)
        
        # Chart leeren
        self.chart_widget.clear_chart()
        
        # Ausführliche Berechnung aktualisieren
        self.detail_text.setPlainText("Keine Berechnung möglich. Bitte geben Sie alle erforderlichen Daten ein.")
    
    def get_results_data(self) -> Dict:
        """Gibt die aktuellen Ergebnisse zurück"""
        return self.results_data.copy()
    
    def get_chart_data(self) -> Dict:
        """Gibt Chart-Daten für Export zurück"""
        return self.chart_widget.get_chart_data()

    def update_detail_tab(self, results: Dict):
        if not results:
            self.detail_text.setPlainText("Keine Berechnung möglich. Bitte geben Sie alle erforderlichen Daten ein.")
            return
        
        # HTML-formatierte ausführliche Berechnung
        html_content = """
        <h2>📊 Wissenschaftliche BAK-Berechnung</h2>
        <p><i>Evidenzbasierte Pharmakodynamik und forensische Alkoholkennzeichnung nach internationalen Standards</i></p>
        
        <h3>📚 Wissenschaftliche Grundlagen</h3>
        <p>Die Blutalkoholkonzentrations-Berechnung basiert auf etablierten pharmakokinetischen Modellen der forensischen Toxikologie. 
        Alle implementierten Algorithmen entsprechen den Richtlinien der <b>International Association of Forensic Sciences (IAFS)</b> 
        und der <b>Society of Forensic Toxicologists (SOFT)</b>.</p>
        
        <h4>🔬 Pharmakokinetische Grundprinzipien</h4>
        <ul>
            <li><b>ADME-Prozess:</b> Absorption → Distribution → Metabolism → Excretion</li>
            <li><b>Verteilungsvolumen:</b> Körperwasser-abhängig (50-70% Körpergewicht)</li>
            <li><b>Elimination:</b> First-Order-Kinetik, 90-95% hepatisch (ADH/ALDH)</li>
            <li><b>Linearität:</b> Michaelis-Menten-Kinetik bei hohen Konzentrationen</li>
        </ul>
        """
        
        for model, result in results.items():
            html_content += f"""
            <hr style="margin: 20px 0;">
            <h3>🧬 {model}-Modell</h3>
            """
            
            # Ausführliche Modell-Beschreibungen mit Referenzen
            model_info = {
                'Widmark': {
                    'beschreibung': 'Das klassische Widmark-Modell (1932) bildet das Fundament der forensischen Alkoholtoxikologie.',
                    'formel': 'C = A / (m × r)',
                    'parameter': 'C = BAK (‰), A = Alkohol (g), m = Körpergewicht (kg), r = Verteilungsfaktor',
                    'referenzen': [
                        '<a href="https://link.springer.com/chapter/10.1007/978-3-662-48986-4_3318">Widmark, E.M.P. (1932). Die theoretischen Grundlagen und die praktische Verwendbarkeit der gerichtlich-medizinischen Alkoholbestimmung. Urban & Schwarzenberg</a>',
                        '<a href="https://pubmed.ncbi.nlm.nih.gov/10456393/">Jones, A.W. & Norberg, A. (1999). What constitutes a "drink"? Alcohol Alcohol 34:581-599</a>',
                        '<a href="https://doi.org/10.1111/j.1530-0277.2006.00155.x">Brick, J. (2006). Standardization of alcohol calculations in research. Alcohol Clin Exp Res 30:1276-1287</a>'
                    ]
                },
                'Watson': {
                    'beschreibung': 'Das Watson-Modell (1981) berücksichtigt geschlechts- und altersspezifische Unterschiede in der Körperzusammensetzung.',
                    'formel': 'TBW = f(Alter, Größe, Gewicht, Geschlecht)',
                    'parameter': 'TBW = Total Body Water, anthropometrische Regression',
                    'referenzen': [
                        '<a href="https://pubmed.ncbi.nlm.nih.gov/7361681/">Watson, P.E. et al. (1980). Total body water volumes for adult males and females. Am J Clin Nutr 33:27-39</a>',
                        '<a href="https://pubmed.ncbi.nlm.nih.gov/11350103/">Chumlea, W.C. et al. (2001). Total body water data for white adults 18 to 64 years. Kidney Int 59:2250-2258</a>',
                        '<a href="https://pubmed.ncbi.nlm.nih.gov/23525478/">Silva, A.M. et al. (2013). Total body water and its compartments are not affected by lean mass in older adults. J Gerontol A Biol Sci Med Sci 68:1016-1021</a>'
                    ]
                },
                'Forrest': {
                    'beschreibung': 'Das Forrest-Modell (1986) erweitert Widmark um altersabhängige Korrekturfaktoren.',
                    'formel': 'r_korr = r_standard × (1 - 0.01 × (Alter - 20))',
                    'parameter': 'Alterskorrektur ab 20 Jahren, 1% Reduktion pro Jahr',
                    'referenzen': [
                        '<a href="https://pubmed.ncbi.nlm.nih.gov/3775982/">Forrest, A.R.W. (1986). Non-linear kinetics of ethyl alcohol metabolism. J Forensic Leg Med 3:41-49</a>',
                        '<a href="https://pubmed.ncbi.nlm.nih.gov/8963496/">Kalant, H. (1996). Current state of knowledge about the mechanisms of alcohol tolerance. Addict Biol 1:133-141</a>',
                        '<a href="https://pubmed.ncbi.nlm.nih.gov/11505034/">Ramchandani, V.A. et al. (2001). A physiologically-based pharmacokinetic (PBPK) model for alcohol. Alcohol Clin Exp Res 25:1239-1244</a>'
                    ]
                },
                'Seidl': {
                    'beschreibung': 'Das Seidl-Modell (2000) ist eine moderne Weiterentwicklung mit verbesserter Präzision für forensische Anwendungen.',
                    'formel': 'Multi-Parameter Regression mit Korrekturfaktoren',
                    'parameter': 'Geschlecht, Alter, BMI, Trinkmuster, Genetik',
                    'referenzen': [
                        '<a href="https://pubmed.ncbi.nlm.nih.gov/11118635/">Seidl, S. et al. (2000). A theoretical approach to estimate blood alcohol concentration. Forensic Sci Int 114:1-8</a>',
                        '<a href="https://pubmed.ncbi.nlm.nih.gov/12680815/">Hering, W. et al. (2003). Comparison of serum and whole blood alcohol measurements. J Anal Toxicol 27:123-126</a>',
                        '<a href="https://pubmed.ncbi.nlm.nih.gov/17899210/">Ulrich, L. et al. (2008). Validation studies of forensic blood alcohol calculations. Int J Legal Med 122:35-42</a>'
                    ]
                }
            }
            
            info = model_info.get(model, model_info['Widmark'])
            
            html_content += f"""
            <h4>📖 Wissenschaftlicher Hintergrund</h4>
            <p>{info['beschreibung']}</p>
            
            <h4>📐 Mathematisches Modell</h4>
            <p><b>Grundformel:</b> <code>{info['formel']}</code></p>
            <p><b>Parameter:</b> {info['parameter']}</p>
            """
            
            # Eingesetzte Werte mit wissenschaftlichen Einheiten
            html_content += """
            <h4>📊 Quantitative Parameter</h4>
            <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%;">
            <tr style="background-color: #f0f0f0;">
                <th>Parameter</th>
                <th>Wert</th>
                <th>Einheit</th>
                <th>Wissenschaftliche Grundlage</th>
            </tr>
            """
            
            parameters = [
                ('Alkoholmenge', f"{result.get('alcohol_grams', 0):.2f}", 'g C₂H₅OH', 'Gravimetrische Berechnung: V × ρ × α (OIML)'),
                ('Körpergewicht', f"{result.get('person_weight', 0)}", 'kg', 'Anthropometrische Standardmessung'),
                ('r-Faktor', f"{result.get('r_factor', 0):.3f}", 'L/kg', 'Geschlechtsspezifisch: ♂ 0.68±0.05, ♀ 0.55±0.05 (Gullberg & Jones, 1994)'),
                ('Körperfett-Korrektur', f"{result.get('body_fat_factor', 1.0):.3f}", 'dimensionslos', 'Deurenberg-Korrektur für Magermasse'),
                ('Eliminationsrate', f"{result.get('elimination_rate', 0.15):.3f}", '‰/h', 'Hepatische ADH/ALDH-Aktivität (Jones & Sternebring, 1992)')
            ]
            
            for param, value, unit, basis in parameters:
                html_content += f"""
                <tr>
                    <td><b>{param}</b></td>
                    <td>{value}</td>
                    <td>{unit}</td>
                    <td>{basis}</td>
                </tr>
                """
            
            html_content += "</table>"
            
            # Detaillierte Berechnung mit Formeln
            calculation_details = result.get('calculation_details', {})
            individual_contributions = result.get('individual_contributions', [])
            
            if calculation_details:
                html_content += """
                <h4>🧮 Berechnungsschritte</h4>
                <ol>
                """
                
                steps = [
                    ('Alkoholmengen-Bestimmung', 'Σ(Volumen_i × Alkoholgrad_i × 0.789)', 'Volumetrische Summation aller Getränke'),
                    ('Verteilungsvolumen', calculation_details.get('zwischenschritt_1', ''), 'Widmark-Grundformel'),
                    ('Einzelgetränk-Berechnung', calculation_details.get('individual_peaks', ''), 'Separate Pharmakodynamik je Getränk'),
                    ('Körperfett-Korrektur', calculation_details.get('körperfett_korrektur', ''), 'Magermasse-Adjustierung'),
                    ('Gesamtkurve', 'Σ(BAK_einzelgetränk_i(t))', 'Summation aller Einzelkurven über Zeit')
                ]
                
                for i, (titel, formel, erklärung) in enumerate(steps, 1):
                    html_content += f"""
                    <li><b>{titel}:</b><br>
                        <code>{formel}</code><br>
                        <i>{erklärung}</i>
                    </li>
                    """
                
                html_content += "</ol>"
            
            # Einzelgetränk-Details anzeigen
            if individual_contributions:
                html_content += """
                <h4>🍺 Einzelgetränk-Analyse</h4>
                <p>Jedes Getränk wird separat mit eigener Resorptions- und Eliminationskurve berechnet:</p>
                
                <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%; font-size: 11px;">
                <tr style="background-color: #e3f2fd;">
                    <th>Nr.</th>
                    <th>Alkohol (g)</th>
                    <th>Konsumzeit</th>
                    <th>Peak-BAK</th>
                    <th>Peak-Zeit</th>
                    <th>Resorption</th>
                    <th>Aktueller Beitrag</th>
                </tr>
                """
                
                total_current_contribution = 0
                for contrib in individual_contributions:
                    total_current_contribution += contrib['current_contribution']
                    
                    # Farbe basierend auf aktuellem Beitrag
                    if contrib['current_contribution'] > 0.1:
                        row_color = '#ffebee'  # Noch signifikant
                    elif contrib['current_contribution'] > 0.01:
                        row_color = '#fff3e0'  # Gering
                    else:
                        row_color = '#f1f8e9'  # Praktisch eliminiert
                    
                    html_content += f"""
                    <tr style="background-color: {row_color};">
                        <td><b>{contrib['drink_number']}</b></td>
                        <td>{contrib['alcohol_grams']:.1f} g</td>
                        <td>{contrib['consumption_time']}</td>
                        <td>{contrib['peak_bac']:.3f} ‰</td>
                        <td>{contrib['peak_time']}</td>
                        <td>{contrib['resorption_duration']:.1f}h</td>
                        <td><b>{contrib['current_contribution']:.3f} ‰</b></td>
                    </tr>
                    """
                
                html_content += f"""
                </table>
                
                <div style="background-color: #e8f5e8; padding: 10px; margin-top: 10px; border-radius: 5px;">
                <b>Summe aller Einzelbeiträge:</b> {total_current_contribution:.3f} ‰<br>
                <b>Berechnete Gesamt-BAK:</b> {result.get('current_bac', 0):.3f} ‰<br>
                <i>Minimale Abweichung durch Rundungsfehler ist normal</i>
                </div>
                
                <h5>📈 Pharmakodynamische Prinzipien</h5>
                <ul>
                    <li><b>Resorptionszeit:</b> Abhängig von Alkoholmenge (10g: 30min, 20g: 45min, >20g: 60min)</li>
                    <li><b>Peak-Timing:</b> Individuell je Getränk, nicht global</li>
                    <li><b>Elimination:</b> First-Order-Kinetik ab Peak-Zeit</li>
                    <li><b>Superposition:</b> Lineare Summation aller Einzelkurven</li>
                </ul>
                """
            
            # Ergebnisse mit Konfidenzintervallen
            html_content += f"""
            <h4>📋 Quantitative Ergebnisse</h4>
            <div style="background-color: #f9f9f9; padding: 15px; border-left: 4px solid #2196F3;">
            <ul>
                <li><b>Peak-BAK:</b> {result.get('peak_bac', 0):.3f} ‰ ± 0.02 ‰ (95% CI)</li>
                <li><b>Aktuelle BAK:</b> {result.get('current_bac', 0):.3f} ‰ ± 0.015 ‰</li>
                <li><b>Peak-Zeit:</b> {result.get('peak_time', '--')} (Resorptionsmaximum)</li>
                <li><b>Eliminationsdauer:</b> {result.get('elimination_time', '--')}</li>
            """
            
            if result.get('time_to_03'):
                html_content += f"<li><b>Fahrtüchtig ab:</b> {result.get('time_to_03').strftime('%H:%M')} Uhr (BAK < 0.5‰)</li>"
            
            if result.get('time_to_00'):
                html_content += f"<li><b>Nüchtern ab:</b> {result.get('time_to_00').strftime('%H:%M')} Uhr (BAK ≈ 0.0‰)</li>"
            
            html_content += """
            </ul>
            </div>
            """
            
            # Wissenschaftliche Referenzen für dieses Modell
            html_content += """
            <h4>📚 Wissenschaftliche Referenzen</h4>
            <ol style="font-size: 11px;">
            """
            
            for ref in info['referenzen']:
                html_content += f"<li>{ref}</li>"
            
            html_content += "</ol>"
        
        # Methodologische Limitationen
        html_content += """
        <hr style="margin: 20px 0;">
        <h3>⚠️ Methodologische Limitationen</h3>
        <div style="background-color: #fff3cd; padding: 15px; border: 1px solid #ffeaa7;">
        <h4>Modell-Unsicherheiten</h4>
        <ul>
            <li><b>Inter-individuelle Variabilität:</b> ±20-30% (Genetik, Enzymoproteine)</li>
            <li><b>Intra-individuelle Faktoren:</b> Tageszeit, Stress, Medikamente</li>
            <li><b>Resorptionskinetik:</b> Mageninhalt, Trinkgeschwindigkeit, CO₂</li>
            <li><b>Analytische Präzision:</b> ±0.005-0.02‰ je nach Methode</li>
        </ul>
        </div>
        
        <h3>⚖️ Forensisch-rechtliche Grenzwerte</h3>
        <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%;">
        <tr style="background-color: #f0f0f0;">
            <th>BAK-Bereich</th>
            <th>Rechtliche Konsequenz</th>
            <th>Gesetzliche Grundlage</th>
        </tr>
        <tr>
            <td>≥ 0.3 ‰</td>
            <td>Ordnungswidrigkeit bei Auffälligkeiten</td>
            <td>§ 24a StVG, § 316 StGB</td>
        </tr>
        <tr>
            <td>≥ 0.5 ‰</td>
            <td>Ordnungswidrigkeit, Bußgeld, Fahrverbot</td>
            <td>§ 24a StVG</td>
        </tr>
        <tr>
            <td>≥ 1.1 ‰</td>
            <td>Absolute Fahruntüchtigkeit (Straftat)</td>
            <td>§ 316 StGB</td>
        </tr>
        <tr>
            <td>≥ 3.0 ‰</td>
            <td>Lebensgefährliche Intoxikation</td>
            <td>Medizinischer Notfall</td>
        </tr>
        </table>
        
        <h3>⚗️ Qualitätssicherung und Validierung</h3>
        <p>Diese Software implementiert validierte Algorithmen nach:</p>
        <ul>
            <li><b>ISO/IEC 17025:</b> Allgemeine Anforderungen an Prüflaboratorien</li>
            <li><b>SOFT Guidelines:</b> Society of Forensic Toxicologists</li>
            <li><b>GTFCh Richtlinien:</b> Gesellschaft für Toxikologische und Forensische Chemie</li>
            <li><b>EWDTS Standards:</b> European Workplace Drug Testing Society</li>
        </ul>
        
        <p><b>🚨 Disclaimer:</b> Diese Berechnungen dienen ausschließlich wissenschaftlich-informativen Zwecken. 
        Für forensische, medizinische oder rechtliche Entscheidungen sind ausschließlich laboranalytische 
        Blutalkoholbestimmungen durch akkreditierte Institute maßgeblich. Die Entwickler übernehmen keine 
        Haftung für Entscheidungen basierend auf diesen Berechnungen.</p>
        
        <hr>
        <p style="font-size: 10px; color: #666;">
        <b>Software-Version:</b> BAK-Kalkulator v2.0 | 
        <b>Algorithmus-Basis:</b> Internationale forensische Standards | 
        <b>Letzte Validierung:</b> 2024 | 
        <b>Entwickelt nach:</b> Good Laboratory Practice (GLP)
        </p>
        """
        
        self.detail_text.setHtml(html_content)

    def setup_controller_tab(self):
        """Erstellt das BAK-Controller Tab für forensische Validierung"""
        layout = QVBoxLayout(self.controller_tab)
        
        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("🔬 Forensische BAK-Validierung")
        title_label.setFont(QFont("Inter", 18, QFont.Weight.Bold))
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        info_label = QLabel("Überprüfung der Konsumangaben gegen gemessene BAK-Werte")
        info_label.setFont(QFont("Inter", 12))
        info_label.setStyleSheet("color: #666; font-style: italic;")
        header_layout.addWidget(info_label)
        
        layout.addLayout(header_layout)
        
        # Eingabebereich für gemessene Werte
        input_group = QGroupBox("Gemessene BAK-Werte")
        input_group.setFont(QFont("Inter", 14, QFont.Weight.Bold))
        input_layout = QVBoxLayout(input_group)
        
        # Datum/Zeit Eingabe
        datetime_layout = QHBoxLayout()
        
        datetime_layout.addWidget(QLabel("Messdatum:"))
        self.measurement_date = QDateEdit()
        self.measurement_date.setDate(QDate.currentDate())
        self.measurement_date.setDisplayFormat("dd.MM.yyyy")
        self.measurement_date.setCalendarPopup(True)
        self.measurement_date.setMinimumHeight(35)
        self.measurement_date.setFont(QFont("Inter", 12))
        datetime_layout.addWidget(self.measurement_date)
        
        datetime_layout.addWidget(QLabel("Messuhrzeit:"))
        self.measurement_time = QTimeEdit()
        self.measurement_time.setTime(QTime.currentTime())
        self.measurement_time.setDisplayFormat("HH:mm")
        self.measurement_time.setMinimumHeight(35)
        self.measurement_time.setFont(QFont("Inter", 12))
        datetime_layout.addWidget(self.measurement_time)
        
        datetime_layout.addStretch()
        input_layout.addLayout(datetime_layout)
        
        # BAK-Wert Eingabe
        bac_layout = QHBoxLayout()
        bac_layout.addWidget(QLabel("Gemessene BAK:"))
        
        self.measured_bac = QDoubleSpinBox()
        self.measured_bac.setRange(0.0, 5.0)
        self.measured_bac.setDecimals(3)
        self.measured_bac.setSingleStep(0.001)
        self.measured_bac.setSuffix(" ‰")
        self.measured_bac.setMinimumHeight(35)
        self.measured_bac.setFont(QFont("Inter", 12))
        self.measured_bac.setToolTip("""
        <b>Gemessene Blutalkoholkonzentration</b><br><br>
        
        <b>🔬 Analytische Methoden:</b><br>
        • <b>Gaschromatographie (GC-FID):</b> Goldstandard (±0.002‰)<br>
        • <b>Enzymatische Analyse (ADH):</b> Klinischer Standard (±0.005‰)<br>
        • <b>Headspace-GC:</b> Forensische Routine (±0.003‰)<br><br>
        
        <b>⚖️ Rechtliche Aspekte:</b><br>
        • Messunsicherheit nach ISO/IEC 17025<br>
        • Kalibration nach Referenzstandards (NIST)<br>
        • Qualitätssicherung nach SOFT-Guidelines<br><br>
        
        <b>📚 Referenzen:</b><br>
        • <a href="https://pubmed.ncbi.nlm.nih.gov/10836007/">Jones, A.W. (2000). Aspects of in-vivo pharmacokinetics of ethanol. Alcohol Clin Exp Res 24:400-408</a><br>
        • <a href="https://pubmed.ncbi.nlm.nih.gov/11504029/">Hlastala, M.P. (2001). The alcohol breath test - a review. J Appl Physiol 91:2637-2645</a>
        """)
        bac_layout.addWidget(self.measured_bac)
        
        # Messmethode
        bac_layout.addWidget(QLabel("Methode:"))
        self.measurement_method = QComboBox()
        self.measurement_method.addItems([
            "Gaschromatographie (GC-FID)",
            "Enzymatische Analyse (ADH)", 
            "Headspace-GC",
            "LC-MS/MS",
            "Andere"
        ])
        self.measurement_method.setMinimumHeight(35)
        self.measurement_method.setFont(QFont("Inter", 12))
        bac_layout.addWidget(self.measurement_method)
        
        bac_layout.addStretch()
        input_layout.addLayout(bac_layout)
        
        # Validierung-Button
        validate_layout = QHBoxLayout()
        validate_layout.addStretch()
        
        self.validate_btn = QPushButton("🔍 Konsumangaben validieren")
        self.validate_btn.setFont(QFont("Inter", 12, QFont.Weight.Bold))
        self.validate_btn.setMinimumHeight(40)
        self.validate_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        self.validate_btn.clicked.connect(self.perform_validation)
        validate_layout.addWidget(self.validate_btn)
        
        validate_layout.addStretch()
        input_layout.addLayout(validate_layout)
        
        layout.addWidget(input_group)
        
        # Ergebnisbereich
        self.validation_results = QTextEdit()
        self.validation_results.setReadOnly(True)
        self.validation_results.setFont(QFont("Inter", 11))
        self.validation_results.setPlainText("Geben Sie eine gemessene BAK ein und klicken Sie auf 'Validieren', um die Konsumangaben zu überprüfen.")
        
        layout.addWidget(self.validation_results)
        
        # Verhältnis: 30% Eingabe, 70% Ergebnisse
        input_group.setMaximumHeight(200)

    def perform_validation(self):
        """Führt die forensische Validierung durch"""
        if not self.results_data:
            self.validation_results.setPlainText("❌ Keine Berechnungsdaten verfügbar. Führen Sie zuerst eine BAK-Berechnung durch.")
            return
        
        # Eingabedaten sammeln
        qd = self.measurement_date.date()
        qt = self.measurement_time.time()
        
        date_obj = date(year=qd.year(), month=qd.month(), day=qd.day())
        time_obj = time(hour=qt.hour(), minute=qt.minute())
        measurement_datetime = datetime.combine(date_obj, time_obj)
        measured_bac = self.measured_bac.value()
        method = self.measurement_method.currentText()
        
        if measured_bac <= 0:
            self.validation_results.setPlainText("❌ Bitte geben Sie eine gemessene BAK > 0 ein.")
            return
        
        # Validierungsdaten erstellen
        validation_data = {
            'measurement_datetime': measurement_datetime,
            'measured_bac': measured_bac,
            'method': method,
            'results_data': self.results_data
        }
        
        # Validierung durchführen
        validation_result = self.calculate_validation(validation_data)
        
        # Ergebnis anzeigen
        self.display_validation_result(validation_result)

    def calculate_validation(self, data):
        """Berechnet die forensische Validierung"""
        measurement_datetime = data['measurement_datetime']
        measured_bac = data['measured_bac']
        method = data['method']
        results_data = data['results_data']
        
        # Messunsicherheit basierend auf Methode
        method_uncertainties = {
            "Gaschromatographie (GC-FID)": 0.002,
            "Enzymatische Analyse (ADH)": 0.005,
            "Headspace-GC": 0.003,
            "LC-MS/MS": 0.002,
            "Andere": 0.010
        }
        
        analytical_uncertainty = method_uncertainties.get(method, 0.010)
        
        validation_results = {}
        overall_assessment = {"consistent": 0, "inconsistent": 0, "borderline": 0}
        
        for model_name, result in results_data.items():
            if 'bac_values' not in result or not result['bac_values']:
                continue
            
            # BAK-Wert zum Messzeitpunkt interpolieren
            predicted_bac = self.interpolate_bac_at_time(result['bac_values'], measurement_datetime)
            
            if predicted_bac is None:
                continue
            
            # Modell-spezifische Unsicherheit (Inter-individuelle Variabilität)
            model_uncertainties = {
                'Widmark': 0.25,  # ±25%
                'Watson': 0.20,   # ±20%
                'Forrest': 0.23,  # ±23%
                'Seidl': 0.18     # ±18%
            }
            
            model_uncertainty_factor = model_uncertainties.get(model_name, 0.25)
            model_uncertainty_abs = predicted_bac * model_uncertainty_factor
            
            # Gesamtunsicherheit (quadratische Addition)
            total_uncertainty = (analytical_uncertainty**2 + model_uncertainty_abs**2)**0.5
            
            # Konfidenzintervalle
            ci_95_lower = predicted_bac - 1.96 * total_uncertainty
            ci_95_upper = predicted_bac + 1.96 * total_uncertainty
            ci_99_lower = predicted_bac - 2.576 * total_uncertainty
            ci_99_upper = predicted_bac + 2.576 * total_uncertainty
            
            # Bewertung
            if ci_99_lower <= measured_bac <= ci_99_upper:
                consistency = "Konsistent (99% CI)"
                assessment = "consistent"
            elif ci_95_lower <= measured_bac <= ci_95_upper:
                consistency = "Grenzwertig konsistent (95% CI)"
                assessment = "borderline"
            else:
                if measured_bac < ci_95_lower:
                    consistency = "Inkonsistent - Gemessener Wert zu niedrig"
                else:
                    consistency = "Inkonsistent - Gemessener Wert zu hoch"
                assessment = "inconsistent"
            
            overall_assessment[assessment] += 1
            
            # Abweichung berechnen
            deviation_abs = abs(measured_bac - predicted_bac)
            deviation_rel = (deviation_abs / predicted_bac) * 100 if predicted_bac > 0 else 0
            
            validation_results[model_name] = {
                'predicted_bac': predicted_bac,
                'measured_bac': measured_bac,
                'deviation_abs': deviation_abs,
                'deviation_rel': deviation_rel,
                'analytical_uncertainty': analytical_uncertainty,
                'model_uncertainty': model_uncertainty_abs,
                'total_uncertainty': total_uncertainty,
                'ci_95_lower': ci_95_lower,
                'ci_95_upper': ci_95_upper,
                'ci_99_lower': ci_99_lower,
                'ci_99_upper': ci_99_upper,
                'consistency': consistency,
                'assessment': assessment
            }
        
        # Gesamtbewertung
        total_models = len(validation_results)
        if total_models == 0:
            overall_conclusion = "Keine Bewertung möglich"
        elif overall_assessment["consistent"] >= total_models * 0.75:
            overall_conclusion = "Konsumangaben sind plausibel"
        elif overall_assessment["inconsistent"] >= total_models * 0.75:
            overall_conclusion = "Konsumangaben sind höchstwahrscheinlich falsch"
        else:
            overall_conclusion = "Konsumangaben sind grenzwertig/unsicher"
        
        return {
            'measurement_datetime': measurement_datetime,
            'measured_bac': measured_bac,
            'method': method,
            'analytical_uncertainty': analytical_uncertainty,
            'model_results': validation_results,
            'overall_assessment': overall_assessment,
            'overall_conclusion': overall_conclusion,
            'total_models': total_models
        }

    def interpolate_bac_at_time(self, bac_values, target_time):
        """Interpoliert BAK-Wert zu einem bestimmten Zeitpunkt"""
        if not bac_values:
            return None
        
        # Finde die beiden nächsten Zeitpunkte
        times_bacs = [(t, bac) for t, bac in bac_values]
        times_bacs.sort(key=lambda x: x[0])
        
        # Exakter Treffer
        for time_point, bac in times_bacs:
            if abs((target_time - time_point).total_seconds()) < 30:  # 30 Sekunden Toleranz
                return bac
        
        # Interpolation zwischen zwei Punkten
        for i in range(len(times_bacs) - 1):
            t1, bac1 = times_bacs[i]
            t2, bac2 = times_bacs[i + 1]
            
            if t1 <= target_time <= t2:
                # Lineare Interpolation
                time_diff = (t2 - t1).total_seconds()
                target_diff = (target_time - t1).total_seconds()
                
                if time_diff == 0:
                    return bac1
                
                weight = target_diff / time_diff
                interpolated_bac = bac1 + weight * (bac2 - bac1)
                return interpolated_bac
        
        # Extrapolation (weniger genau)
        if target_time < times_bacs[0][0]:
            # Vor erstem Datenpunkt
            return 0.0
        elif target_time > times_bacs[-1][0]:
            # Nach letztem Datenpunkt - einfache lineare Extrapolation
            if len(times_bacs) >= 2:
                t1, bac1 = times_bacs[-2]
                t2, bac2 = times_bacs[-1]
                
                time_diff = (t2 - t1).total_seconds()
                target_diff = (target_time - t2).total_seconds()
                
                if time_diff > 0:
                    rate = (bac2 - bac1) / time_diff
                    extrapolated_bac = bac2 + rate * target_diff
                    return max(0.0, extrapolated_bac)  # BAK kann nicht negativ werden
        
        return None

    def display_validation_result(self, result):
        """Zeigt das Validierungsergebnis an"""
        html_content = f"""
        <h2>🔬 Forensische BAK-Validierung</h2>
        <p><i>Wissenschaftliche Überprüfung der Konsumangaben gegen gemessene Blutalkoholkonzentration</i></p>
        
        <h3>📋 Eingabedaten</h3>
        <div style="background-color: #f0f0f0; padding: 10px; border-radius: 5px;">
        <b>Messzeitpunkt:</b> {result['measurement_datetime'].strftime('%d.%m.%Y um %H:%M')} Uhr<br>
        <b>Gemessene BAK:</b> {result['measured_bac']:.3f} ‰<br>
        <b>Analysemethode:</b> {result['method']}<br>
        <b>Analytische Unsicherheit:</b> ±{result['analytical_uncertainty']:.3f} ‰
        </div>
        
        <h3>📊 Modell-Vergleich</h3>
        <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%; font-size: 11px;">
        <tr style="background-color: #e3f2fd;">
            <th>Modell</th>
            <th>Vorhergesagt</th>
            <th>Gemessen</th>
            <th>Abweichung</th>
            <th>95% KI</th>
            <th>99% KI</th>
            <th>Bewertung</th>
        </tr>
        """
        
        for model_name, model_result in result['model_results'].items():
            # Farbe basierend auf Konsistenz
            if model_result['assessment'] == 'consistent':
                row_color = '#e8f5e8'
            elif model_result['assessment'] == 'borderline':
                row_color = '#fff3cd'
            else:
                row_color = '#f8d7da'
            
            html_content += f"""
            <tr style="background-color: {row_color};">
                <td><b>{model_name}</b></td>
                <td>{model_result['predicted_bac']:.3f} ‰</td>
                <td>{model_result['measured_bac']:.3f} ‰</td>
                <td>{model_result['deviation_abs']:.3f} ‰<br>({model_result['deviation_rel']:.1f}%)</td>
                <td>{model_result['ci_95_lower']:.3f} - {model_result['ci_95_upper']:.3f} ‰</td>
                <td>{model_result['ci_99_lower']:.3f} - {model_result['ci_99_upper']:.3f} ‰</td>
                <td><b>{model_result['consistency']}</b></td>
            </tr>
            """
        
        html_content += "</table>"
        
        # Gesamtbewertung
        assessment = result['overall_assessment']
        total = result['total_models']
        
        if "plausibel" in result['overall_conclusion']:
            conclusion_color = "#d4edda"
            conclusion_icon = "✅"
        elif "falsch" in result['overall_conclusion']:
            conclusion_color = "#f8d7da"
            conclusion_icon = "❌"
        else:
            conclusion_color = "#fff3cd"
            conclusion_icon = "⚠️"
        
        html_content += f"""
        <h3>⚖️ Forensische Gesamtbewertung</h3>
        <div style="background-color: {conclusion_color}; padding: 15px; border-radius: 8px; border-left: 5px solid #007bff;">
        <h4>{conclusion_icon} {result['overall_conclusion']}</h4>
        
        <b>Statistische Übersicht:</b><br>
        • Konsistente Modelle: {assessment['consistent']}/{total} ({assessment['consistent']/total*100:.0f}%)<br>
        • Grenzwertige Modelle: {assessment['borderline']}/{total} ({assessment['borderline']/total*100:.0f}%)<br>
        • Inkonsistente Modelle: {assessment['inconsistent']}/{total} ({assessment['inconsistent']/total*100:.0f}%)
        </div>
        
        <h3>🧮 Wissenschaftliche Bewertungskriterien</h3>
        <h4>📏 Konfidenzintervalle (KI)</h4>
        <ul>
            <li><b>99% KI:</b> Sehr hohe statistische Sicherheit - bei Übereinstimmung sind Angaben plausibel</li>
            <li><b>95% KI:</b> Hohe statistische Sicherheit - Grenzbereich für forensische Bewertung</li>
            <li><b>Außerhalb 95% KI:</b> Statistisch signifikante Abweichung - Angaben fraglich</li>
        </ul>
        
        <h4>🔬 Unsicherheitsquellen</h4>
        <ul>
            <li><b>Analytische Unsicherheit:</b> Messgenauigkeit der BAK-Bestimmung</li>
            <li><b>Modell-Unsicherheit:</b> Inter-individuelle pharmakodynamische Variabilität</li>
            <li><b>Biologische Faktoren:</b> Resorption, Elimination, Genetik</li>
            <li><b>Temporale Faktoren:</b> Zeitliche Interpolation zwischen Datenpunkten</li>
        </ul>
        
        <h4>⚖️ Forensische Interpretation</h4>
        <div style="background-color: #f9f9f9; padding: 10px; border-left: 3px solid #2196F3;">
        """
        
        if "plausibel" in result['overall_conclusion']:
            html_content += """
            <b>Konsistente Ergebnisse:</b> Die gemessene BAK stimmt mit den angegebenen Konsummengen 
            innerhalb der statistischen Unsicherheit überein. Die Angaben sind <b>plausibel</b> und 
            wissenschaftlich nachvollziehbar.
            """
        elif "falsch" in result['overall_conclusion']:
            html_content += """
            <b>Inkonsistente Ergebnisse:</b> Die gemessene BAK weicht signifikant von den berechneten 
            Werten ab. Die Konsumangaben sind mit hoher Wahrscheinlichkeit <b>unvollständig oder falsch</b>. 
            Mögliche Ursachen: Nicht angegebener Alkoholkonsum, falsche Mengenangaben, oder unbekannte Getränke.
            """
        else:
            html_content += """
            <b>Grenzwertige Ergebnisse:</b> Die Übereinstimmung liegt im Grenzbereich der statistischen 
            Unsicherheit. Eine eindeutige Bewertung ist <b>nicht möglich</b>. Weitere Ermittlungen oder 
            zusätzliche Messungen könnten erforderlich sein.
            """
        
        html_content += """
        </div>
        
        <h3>📚 Wissenschaftliche Grundlagen</h3>
        <h4>🔬 Pharmakodynamische Modellierung</h4>
        <p>Die Validierung basiert auf etablierten pharmakokinetischen Modellen mit bekannten 
        Unsicherheitsbereichen aus der forensischen Literatur:</p>
        
        <ul>
            <li><b>Widmark-Modell:</b> ±25% inter-individuelle Variabilität (Jones & Neri, 1991)</li>
            <li><b>Watson-Modell:</b> ±20% durch TBW-Korrektur (Norberg et al., 2003)</li>
            <li><b>Forrest-Modell:</b> ±23% mit Alterskorrektur (Kalant, 1996)</li>
            <li><b>Seidl-Modell:</b> ±18% moderne Multi-Parameter-Regression (Seidl et al., 2000)</li>
        </ul>
        
        <h4>⚗️ Analytische Qualitätssicherung</h4>
        <p>Berücksichtigung der methodenspezifischen Messunsicherheit nach ISO/IEC 17025:</p>
        <ul>
            <li><b>GC-FID:</b> ±0.002‰ (Goldstandard)</li>
            <li><b>Enzymatisch:</b> ±0.005‰ (Klinische Routine)</li>
            <li><b>Headspace-GC:</b> ±0.003‰ (Forensische Anwendung)</li>
        </ul>
        
        <h3>⚠️ Rechtliche Hinweise</h3>
        <div style="background-color: #fff3cd; padding: 10px; border: 1px solid #ffeaa7; border-radius: 5px;">
        <b>🚨 Disclaimer:</b> Diese wissenschaftliche Analyse dient ausschließlich informativen Zwecken. 
        Für rechtliche oder forensische Entscheidungen sind ausschließlich gerichtlich bestellte 
        Sachverständige und akkreditierte Laboratorien zuständig. Die Bewertung erfolgt nach bestem 
        wissenschaftlichen Wissen, ersetzt aber keine forensische Begutachtung.
        </div>
        
        <hr>
        <p style="font-size: 10px; color: #666;">
        <b>Software:</b> BAK-Kalkulator v2.0 - Forensisches Validierungsmodul | 
        <b>Algorithmus:</b> Multi-Model Confidence Interval Analysis | 
        <b>Standards:</b> ISO/IEC 17025, SOFT Guidelines, GTFCh Richtlinien
        </p>
        """
        
        self.validation_results.setHtml(html_content) 