from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QTabWidget, QLabel, QPushButton, QProgressBar,
                            QSplashScreen, QApplication, QMenuBar, QMenu, QToolBar,
                            QStatusBar, QMessageBox)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot
from PyQt6.QtGui import QFont, QPixmap, QAction, QIcon

from ui.components.person_widget import PersonDataWidget
from ui.components.drinks_widget import DrinksWidget
from ui.components.results_widget import ResultsWidget
from ui.components.calculation_settings_widget import CalculationSettingsWidget
from controllers.calculation_controller import CalculationController
from utils.export_manager import ExportManager
from ui.styles.theme_manager import theme_manager, Theme, FontManager
from datetime import datetime
import os

class MainWindow(QMainWindow):
    """Moderne BAK-Calculator Hauptfenster-Klasse"""
    
    def __init__(self):
        super().__init__()
        
        # Controller initialisieren
        self.calculation_controller = CalculationController()
        self.export_manager = ExportManager(self)
        
        # Setup
        self.setup_window()
        self.setup_ui()
        self.setup_connections()
        self.setup_theme()
        
        # Initialdaten an Controller übergeben
        self.on_person_data_changed()
        self.on_settings_data_changed()
        self.on_drinks_data_changed()
        
        # Lade gespeicherte Daten
        self.load_user_preferences()
        
        # Zeige Splash Screen
        self.show_splash_screen()
    
    def setup_window(self):
        """Konfiguriert das Hauptfenster"""
        self.setWindowTitle("BAK-Kalkulator v2.0 - Wissenschaftlicher Blutalkoholkonzentrations-Rechner")
        self.setMinimumSize(1400, 900)
        self.resize(1600, 1000)
        
        # Zentriere das Fenster
        screen = QApplication.primaryScreen().geometry()
        window_geometry = self.geometry()
        x = (screen.width() - window_geometry.width()) // 2
        y = (screen.height() - window_geometry.height()) // 2
        self.move(x, y)
    
    def setup_ui(self):
        """Erstellt die Benutzeroberfläche"""
        # Zentrales Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Hauptlayout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        self.create_header(main_layout)
        
        # Menu und Toolbar
        self.create_menu_bar()
        self.create_toolbar()
        
        # Hauptinhalt
        self.create_main_content(main_layout)
        
        # Status Bar
        self.create_status_bar()
    
    def create_header(self, parent_layout):
        """Erstellt den Header-Bereich"""
        header_widget = QWidget()
        header_widget.setFixedHeight(80)
        header_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2196F3, stop:1 #1976D2);
                border-bottom: 1px solid #1976D2;
            }
        """)
        
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(30, 0, 30, 0)
        
        # Logo und Titel
        title_section = QVBoxLayout()
        
        title_label = QLabel("BAK-Kalkulator")
        title_label.setFont(FontManager.get_font('h2', 'bold'))
        title_label.setStyleSheet("color: white;")
        
        subtitle_label = QLabel("Wissenschaftlicher Blutalkoholkonzentrations-Rechner")
        subtitle_label.setFont(FontManager.get_font('subtitle1'))
        subtitle_label.setStyleSheet("color: rgba(255, 255, 255, 0.8);")
        
        title_section.addWidget(title_label)
        title_section.addWidget(subtitle_label)
        title_section.addStretch()
        
        header_layout.addLayout(title_section)
        header_layout.addStretch()
        
        # Aktuelle BAK-Anzeige im Header
        self.current_bac_display = self.create_bac_display()
        header_layout.addWidget(self.current_bac_display)
        
        parent_layout.addWidget(header_widget)
    
    def create_bac_display(self):
        """Erstellt die aktuelle BAK-Anzeige"""
        bac_widget = QWidget()
        bac_widget.setFixedSize(200, 60)
        bac_widget.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
        """)
        
        layout = QVBoxLayout(bac_widget)
        layout.setContentsMargins(10, 5, 10, 5)
        
        title = QLabel("Aktuelle BAK")
        title.setFont(FontManager.get_font('caption'))
        title.setStyleSheet("color: rgba(255, 255, 255, 0.8);")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.bac_value_label = QLabel("0.00 ‰")
        self.bac_value_label.setFont(FontManager.get_font('h4', 'bold'))
        self.bac_value_label.setStyleSheet("color: white;")
        self.bac_value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(title)
        layout.addWidget(self.bac_value_label)
        
        return bac_widget
    
    def create_menu_bar(self):
        """Erstellt die Menüleiste"""
        menubar = self.menuBar()
        
        # Datei-Menü
        file_menu = menubar.addMenu('Datei')
        
        new_action = QAction('Neue Berechnung', self)
        new_action.setShortcut('Ctrl+N')
        new_action.triggered.connect(self.new_calculation)
        file_menu.addAction(new_action)
        
        file_menu.addSeparator()
        
        save_action = QAction('Speichern', self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_calculation)
        file_menu.addAction(save_action)
        
        load_action = QAction('Laden', self)
        load_action.setShortcut('Ctrl+O')
        load_action.triggered.connect(self.load_calculation)
        file_menu.addAction(load_action)
        
        file_menu.addSeparator()
        
        # Export-Untermenü
        export_menu = file_menu.addMenu('Exportieren')
        
        pdf_action = QAction('Als PDF...', self)
        pdf_action.triggered.connect(self.export_pdf)
        export_menu.addAction(pdf_action)
        
        csv_action = QAction('Als CSV...', self)
        csv_action.triggered.connect(self.export_csv)
        export_menu.addAction(csv_action)
        
        excel_action = QAction('Als Excel...', self)
        excel_action.triggered.connect(self.export_excel)
        export_menu.addAction(excel_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('Beenden', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Ansicht-Menü
        view_menu = menubar.addMenu('Ansicht')
        
        theme_menu = view_menu.addMenu('Theme')
        
        light_theme = QAction('Hell', self)
        light_theme.triggered.connect(lambda: theme_manager.set_theme(Theme.LIGHT))
        theme_menu.addAction(light_theme)
        
        dark_theme = QAction('Dunkel', self)
        dark_theme.triggered.connect(lambda: theme_manager.set_theme(Theme.DARK))
        theme_menu.addAction(dark_theme)
        
        auto_theme = QAction('System', self)
        auto_theme.triggered.connect(lambda: theme_manager.set_theme(Theme.AUTO))
        theme_menu.addAction(auto_theme)
        
        # Hilfe-Menü
        help_menu = menubar.addMenu('Hilfe')
        
        about_action = QAction('Über BAK-Kalkulator', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        help_action = QAction('Hilfe', self)
        help_action.setShortcut('F1')
        help_action.triggered.connect(self.show_help)
        help_menu.addAction(help_action)
    
    def create_toolbar(self):
        """Erstellt die Toolbar"""
        toolbar = self.addToolBar('Haupttoolbar')
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        
        # Neue Berechnung
        new_action = QAction('Neu', self)
        new_action.setToolTip('Neue Berechnung starten')
        new_action.triggered.connect(self.new_calculation)
        toolbar.addAction(new_action)
        
        toolbar.addSeparator()
        
        # Export-Aktionen
        pdf_action = QAction('PDF', self)
        pdf_action.setToolTip('Als PDF exportieren')
        pdf_action.triggered.connect(self.export_pdf)
        toolbar.addAction(pdf_action)
        
        csv_action = QAction('CSV', self)
        csv_action.setToolTip('Als CSV exportieren')
        csv_action.triggered.connect(self.export_csv)
        toolbar.addAction(csv_action)
        
        toolbar.addSeparator()
        
        # Theme-Umschalter
        theme_action = QAction('Theme', self)
        theme_action.setToolTip('Theme umschalten')
        theme_action.triggered.connect(self.toggle_theme)
        toolbar.addAction(theme_action)
    
    def create_main_content(self, parent_layout):
        """Erstellt den Hauptinhalt"""
        # Tab-Widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setFont(FontManager.get_font('subtitle2'))
        
        # Eingabe-Tab (Split-Layout)
        self.create_input_tab()
        
        # Ergebnisse-Tab
        self.results_widget = ResultsWidget()
        self.tab_widget.addTab(self.results_widget, "📊 Ergebnisse")
        
        parent_layout.addWidget(self.tab_widget)
    
    def create_input_tab(self):
        """Erstellt den Eingabe-Tab mit Split-Layout"""
        input_widget = QWidget()
        input_layout = QHBoxLayout(input_widget)
        input_layout.setSpacing(20)
        input_layout.setContentsMargins(20, 20, 20, 20)
        
        # Linke Seite: Personendaten (30%)
        self.person_widget = PersonDataWidget()
        self.person_widget.setMaximumWidth(400)
        input_layout.addWidget(self.person_widget, 0)
        
        # Mittlere Seite: Getränke (50%)
        self.drinks_widget = DrinksWidget()
        input_layout.addWidget(self.drinks_widget, 1)
        
        # Rechte Seite: Einstellungen (20%)
        self.settings_widget = CalculationSettingsWidget()
        self.settings_widget.setMaximumWidth(350)
        input_layout.addWidget(self.settings_widget, 0)
        
        self.tab_widget.addTab(input_widget, "⚙️ Eingabe")
    
    def create_status_bar(self):
        """Erstellt die Statusleiste"""
        status_bar = self.statusBar()
        
        # Standard-Nachricht
        status_bar.showMessage("Bereit für Berechnungen")
        
        # Progress Bar für Exporte
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumWidth(200)
        status_bar.addPermanentWidget(self.progress_bar)
        
        # Cache-Info
        self.cache_label = QLabel("Cache: 0/50")
        self.cache_label.setToolTip("Anzahl gecachter Berechnungen")
        status_bar.addPermanentWidget(self.cache_label)
    
    def setup_connections(self):
        """Verbindet alle Signale und Slots"""
        # Person Widget
        self.person_widget.data_changed.connect(self.on_person_data_changed)
        
        # Drinks Widget
        self.drinks_widget.data_changed.connect(self.on_drinks_data_changed)
        
        # Settings Widget
        self.settings_widget.data_changed.connect(self.on_settings_data_changed)
        
        # Calculation Controller
        self.calculation_controller.calculation_started.connect(self.on_calculation_started)
        self.calculation_controller.calculation_finished.connect(self.on_calculation_finished)
        self.calculation_controller.calculation_error.connect(self.on_calculation_error)
        
        # Export Manager
        self.export_manager.export_started.connect(self.on_export_started)
        self.export_manager.export_progress.connect(self.progress_bar.setValue)
        self.export_manager.export_finished.connect(self.on_export_finished)
        
        # Theme Manager
        theme_manager.theme_changed.connect(self.on_theme_changed)
    
    def setup_theme(self):
        """Wendet das aktuelle Theme an"""
        theme_manager.apply_theme()
    
    def show_splash_screen(self):
        """Zeigt einen Splash Screen beim Start"""
        # Einfacher Splash Screen (optional)
        splash_timer = QTimer()
        splash_timer.singleShot(100, lambda: self.statusBar().showMessage("BAK-Kalkulator geladen", 3000))
    
    # Slot-Methoden
    @pyqtSlot()
    def on_person_data_changed(self):
        """Reagiert auf Änderungen der Personendaten"""
        person_data = self.person_widget.get_person_data()
        self.calculation_controller.set_person_data(person_data)
    
    @pyqtSlot()
    def on_drinks_data_changed(self):
        """Reagiert auf Änderungen der Getränkedaten"""
        drinks_data = self.drinks_widget.get_drinks_data()
        self.calculation_controller.set_drinks_data(drinks_data)
    
    @pyqtSlot()
    def on_settings_data_changed(self):
        """Reagiert auf Änderungen der Berechnungseinstellungen"""
        settings_data = self.settings_widget.get_settings_data()
        self.calculation_controller.set_calculation_settings(settings_data)
    
    @pyqtSlot()
    def on_calculation_started(self):
        """Reagiert auf Beginn einer Berechnung"""
        self.statusBar().showMessage("Berechnung läuft...")
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
    
    @pyqtSlot(dict)
    def on_calculation_finished(self, results):
        """Reagiert auf abgeschlossene Berechnung"""
        self.statusBar().showMessage("Berechnung abgeschlossen", 3000)
        QApplication.restoreOverrideCursor()
        
        # Ergebnisse an Results Widget weiterleiten
        self.results_widget.update_results(results)
        
        # Aktuelle BAK im Header aktualisieren
        self.update_current_bac_display(results)
        
        # Cache-Info aktualisieren
        cache_info = self.calculation_controller.get_cache_info()
        self.cache_label.setText(f"Cache: {cache_info['size']}/{cache_info['limit']}")
    
    @pyqtSlot(str)
    def on_calculation_error(self, error_message):
        """Reagiert auf Berechnungsfehler"""
        self.statusBar().showMessage(f"Fehler: {error_message}", 5000)
        QApplication.restoreOverrideCursor()
        
        QMessageBox.warning(self, "Berechnungsfehler", 
                          f"Bei der Berechnung ist ein Fehler aufgetreten:\n\n{error_message}")
    
    @pyqtSlot()
    def on_export_started(self):
        """Reagiert auf Export-Start"""
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.statusBar().showMessage("Export läuft...")
    
    @pyqtSlot(bool, str)
    def on_export_finished(self, success, message):
        """Reagiert auf Export-Ende"""
        self.progress_bar.setVisible(False)
        self.statusBar().showMessage(message, 5000)
    
    @pyqtSlot(str)
    def on_theme_changed(self, theme_name):
        """Reagiert auf Theme-Änderung"""
        self.statusBar().showMessage(f"Theme geändert: {theme_name}", 2000)
    
    def update_current_bac_display(self, results):
        """Aktualisiert die aktuelle BAK-Anzeige"""
        if not results:
            self.bac_value_label.setText("0.00 ‰")
            return
        
        # Nimm den ersten verfügbaren Wert
        first_model = next(iter(results.keys()))
        current_bac = results[first_model].get('current_bac', 0.0)
        
        self.bac_value_label.setText(f"{current_bac:.2f} ‰")
        
        # Farbkodierung basierend auf BAK-Wert
        if current_bac == 0.0:
            color = "white"
        elif current_bac < 0.5:
            color = "#4CAF50"  # Grün
        elif current_bac < 1.1:
            color = "#FF9800"  # Orange
        else:
            color = "#F44336"  # Rot
        
        self.bac_value_label.setStyleSheet(f"color: {color};")
    
    # Menu-Aktionen
    def new_calculation(self):
        """Startet eine neue Berechnung"""
        reply = QMessageBox.question(self, "Neue Berechnung", 
                                   "Möchten Sie eine neue Berechnung starten? Aktuelle Daten gehen verloren.",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            self.person_widget.set_default_values()
            self.drinks_widget.clear_drinks()
            self.settings_widget.set_default_values()
            self.results_widget.clear_results()
            self.bac_value_label.setText("0.00 ‰")
            self.statusBar().showMessage("Neue Berechnung gestartet", 2000)
    
    def save_calculation(self):
        """Speichert die aktuelle Berechnung"""
        # TODO: Implementierung der Speicher-Funktion
        self.statusBar().showMessage("Speicher-Funktion wird implementiert...", 3000)
    
    def load_calculation(self):
        """Lädt eine gespeicherte Berechnung"""
        # TODO: Implementierung der Lade-Funktion
        self.statusBar().showMessage("Lade-Funktion wird implementiert...", 3000)
    
    def export_pdf(self):
        """Exportiert als PDF"""
        data = self.gather_export_data()
        self.export_manager.export_to_pdf(data)
    
    def export_csv(self):
        """Exportiert als CSV"""
        data = self.gather_export_data()
        self.export_manager.export_to_csv(data)
    
    def export_excel(self):
        """Exportiert als Excel"""
        data = self.gather_export_data()
        self.export_manager.export_to_excel(data)
    
    def gather_export_data(self):
        """Sammelt alle Daten für den Export"""
        return {
            'person_data': self.person_widget.get_person_data(),
            'drinks_data': self.drinks_widget.get_drinks_data(),
            'settings_data': self.settings_widget.get_settings_data(),
            'results': self.results_widget.get_results_data(),
            'chart_data': self.results_widget.get_chart_data()
        }
    
    def toggle_theme(self):
        """Wechselt zwischen Hell- und Dunkel-Theme"""
        current_theme = theme_manager.current_theme
        if current_theme == Theme.LIGHT:
            theme_manager.set_theme(Theme.DARK)
        else:
            theme_manager.set_theme(Theme.LIGHT)
    
    def show_about(self):
        """Zeigt Info-Dialog"""
        QMessageBox.about(self, "Über BAK-Kalkulator",
                         """
                         <h3>BAK-Kalkulator v2.0</h3>
                         <p>Wissenschaftlicher Blutalkoholkonzentrations-Rechner</p>
                         <p>Mit modernster PyQt6-Technologie entwickelt</p>
                         
                         <p><b>Features:</b></p>
                         <ul>
                         <li>Vier wissenschaftliche Berechnungsmodelle</li>
                         <li>Moderne Benutzeroberfläche</li>
                         <li>PDF/CSV/Excel Export</li>
                         <li>Hell/Dunkel Themes</li>
                         <li>Caching und Performance-Optimierung</li>
                         </ul>
                         
                         <p><b>Disclaimer:</b> Nur für Informationszwecke!</p>
                         """)
    
    def show_help(self):
        """Zeigt Hilfe-Dialog"""
        QMessageBox.information(self, "Hilfe",
                              """
                              <h3>Hilfe - BAK-Kalkulator</h3>
                              
                              <p><b>Verwendung:</b></p>
                              <ol>
                              <li>Geben Sie Ihre Personendaten ein</li>
                              <li>Fügen Sie konsumierte Getränke hinzu</li>
                              <li>Passen Sie die Berechnungseinstellungen an</li>
                              <li>Betrachten Sie die Ergebnisse im Ergebnisse-Tab</li>
                              <li>Exportieren Sie bei Bedarf als PDF/CSV/Excel</li>
                              </ol>
                              
                              <p><b>Tastenkürzel:</b></p>
                              <ul>
                              <li>Strg+N: Neue Berechnung</li>
                              <li>Strg+S: Speichern</li>
                              <li>Strg+O: Laden</li>
                              <li>F1: Diese Hilfe</li>
                              </ul>
                              """)
    
    def load_user_preferences(self):
        """Lädt Benutzereinstellungen"""
        # TODO: Implementierung
        pass
    
    def save_user_preferences(self):
        """Speichert Benutzereinstellungen"""
        # TODO: Implementierung
        pass
    
    def closeEvent(self, event):
        """Behandelt das Schließen des Fensters"""
        self.save_user_preferences()
        event.accept()
    
    def update_bac_plot(self):
        """Aktualisiert die BAK-Kurve"""
        drinks_data = self.drinks_widget.get_drinks_data()
        if not drinks_data:
            return
        
        # Hole Personendaten
        weight = self.person_widget.get_weight()
        gender = self.person_widget.get_gender()
        height = self.person_widget.get_height()
        age = self.person_widget.get_age()
        
        # Berechne BAK-Kurve
        times, bac_values, drink_times = self.calculation_controller.calculate_bac_curve(
            drinks_data, weight, gender, height, age
        )
        
        # Zeichne Kurve
        self.bac_plot_widget.plot_bac_curve(times, bac_values, drink_times) 