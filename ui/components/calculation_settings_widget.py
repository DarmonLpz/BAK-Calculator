from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QCheckBox, QComboBox, QSlider, QGroupBox, QSpinBox)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont
from typing import Dict, List

class CalculationSettingsWidget(QWidget):
    """Widget für Berechnungseinstellungen"""
    
    # Signal für Datenänderungen
    data_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.connect_signals()
        self.set_default_values()
    
    def setup_ui(self):
        """Erstellt die UI-Komponenten"""
        layout = QVBoxLayout(self)
        
        # Titel
        title_label = QLabel("Berechnungseinstellungen")
        title_label.setFont(QFont("Inter", 16, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # Berechnungsmodelle
        models_group = QGroupBox("Berechnungsmodelle")
        models_group.setFont(QFont("Inter", 14, QFont.Weight.Bold))
        models_layout = QVBoxLayout(models_group)
        
        self.model_checkboxes = {}
        models = [
            ("Widmark", "Klassisches Widmark-Modell"),
            ("Watson", "Watson-Formel (geschlechtsspezifisch)"),
            ("Forrest", "Forrest-Modell (Körperfett berücksichtigt)"),
            ("Seidl", "Seidl-Formel (erweitert)")
        ]
        
        for model_key, model_description in models:
            checkbox_layout = QVBoxLayout()
            
            checkbox = QCheckBox(model_key)
            checkbox.setFont(QFont("Inter", 12, QFont.Weight.Bold))
            
            # Wissenschaftliche Tooltips für jedes Modell
            if model_key == "Widmark":
                checkbox.setToolTip("""
<b>Klassisches Widmark-Modell (1932)</b><br><br>
Das fundamentale Modell der forensischen Alkoholtoxikologie:<br>
• <b>Grundformel:</b> C = A / (m × r)<br>
• <b>C:</b> BAK in ‰<br>
• <b>A:</b> Alkoholmenge in g<br>
• <b>m:</b> Körpergewicht in kg<br>
• <b>r:</b> Verteilungsfaktor (♂ 0.68, ♀ 0.55)<br><br>
<b>Anwendung:</b> Forensische Standard-Berechnung, einfach und robust<br>
<b>Genauigkeit:</b> ±15-20% bei Standardbedingungen<br><br>
<b>Wissenschaftliche Referenz:</b><br>
• <a href="https://link.springer.com/chapter/10.1007/978-3-662-48986-4_3318">Widmark, E.M.P. (1932). Die theoretischen Grundlagen und die praktische Verwendbarkeit der gerichtlich-medizinischen Alkoholbestimmung</a>
                """)
            elif model_key == "Watson":
                checkbox.setToolTip("""
<b>Watson-Modell (1980) - Total Body Water</b><br><br>
Präzise anthropometrische Berechnung des Verteilungsvolumens:<br>
• <b>♂ TBW:</b> 2.447 - 0.09516×Alter + 0.1074×Größe + 0.3362×Gewicht<br>
• <b>♀ TBW:</b> -2.097 + 0.1069×Größe + 0.2466×Gewicht<br>
• <b>r-Faktor:</b> TBW / Körpergewicht<br><br>
<b>Vorteile:</b> Individuelle Körperzusammensetzung, geschlechts-/altersspezifisch<br>
<b>Genauigkeit:</b> ±10-15%, verbessert bei extremen Körpermaßen<br><br>
<b>Wissenschaftliche Referenzen:</b><br>
• <a href="https://pubmed.ncbi.nlm.nih.gov/7361681/">Watson, P.E. et al. (1980). Total body water volumes for adult males and females. Am J Clin Nutr 33:27-39</a><br>
• <a href="https://pubmed.ncbi.nlm.nih.gov/11350103/">Chumlea, W.C. et al. (2001). Total body water data for white adults. Kidney Int 59:2250-2258</a>
                """)
            elif model_key == "Forrest":
                checkbox.setToolTip("""
<b>Forrest-Modell (1986) - Alterskorrektur</b><br><br>
Erweiterte Widmark-Formel mit Altersabhängigkeit:<br>
• <b>Basis:</b> Widmark r-Faktor<br>
• <b>Alterskorrektur:</b> r × (1 - 0.01 × (Alter - 20))<br>
• <b>Reduktion:</b> 1% pro Lebensjahr ab 20<br><br>
<b>Hintergrund:</b> Abnehmende Körperwasseranteile und Leberfunktion<br>
• <b>20-40 Jahre:</b> Vollständige Elimination<br>
• <b>40-60 Jahre:</b> ~20% reduzierte Kapazität<br>
• <b>60+ Jahre:</b> Deutlich verlangsamter Metabolismus<br><br>
<b>Wissenschaftliche Referenzen:</b><br>
• <a href="https://pubmed.ncbi.nlm.nih.gov/3775982/">Forrest, A.R.W. (1986). Non-linear kinetics of ethyl alcohol metabolism</a><br>
• <a href="https://pubmed.ncbi.nlm.nih.gov/8963496/">Kalant, H. (1996). Mechanisms of alcohol tolerance. Addict Biol 1:133-141</a>
                """)
            elif model_key == "Seidl":
                checkbox.setToolTip("""
<b>Seidl-Modell (2000) - Moderne Präzisionsberechnung</b><br><br>
Hochentwickeltes Multi-Parameter-Modell:<br>
• <b>BMI-Korrektur:</b> Berücksichtigung der Körperzusammensetzung<br>
• <b>Körperfett-Adjustierung:</b> Magermasse-spezifische Verteilung<br>
• <b>Genetische Faktoren:</b> ADH/ALDH-Polymorphismen<br>
• <b>Trinkmuster:</b> Chronische Adaption<br><br>
<b>Anwendung:</b> Forensische Expertisen, wissenschaftliche Studien<br>
<b>Genauigkeit:</b> ±8-12%, höchste Präzision verfügbar<br><br>
<b>Wissenschaftliche Referenzen:</b><br>
• <a href="https://pubmed.ncbi.nlm.nih.gov/11118635/">Seidl, S. et al. (2000). A theoretical approach to estimate blood alcohol concentration. Forensic Sci Int 114:1-8</a><br>
• <a href="https://pubmed.ncbi.nlm.nih.gov/17899210/">Ulrich, L. et al. (2008). Validation studies of forensic blood alcohol calculations. Int J Legal Med 122:35-42</a>
                """)
            
            description_label = QLabel(model_description)
            description_label.setFont(QFont("Inter", 10))
            description_label.setStyleSheet("color: #666666; margin-left: 20px;")
            
            checkbox_layout.addWidget(checkbox)
            checkbox_layout.addWidget(description_label)
            
            models_layout.addLayout(checkbox_layout)
            self.model_checkboxes[model_key] = checkbox
        
        layout.addWidget(models_group)
        
        # Resorptionseinstellungen
        resorption_group = QGroupBox("Resorption")
        resorption_group.setFont(QFont("Inter", 14, QFont.Weight.Bold))
        resorption_layout = QVBoxLayout(resorption_group)
        
        # Resorptionszeit
        resorption_time_layout = QHBoxLayout()
        resorption_time_label = QLabel("Resorptionszeit:")
        resorption_time_label.setFont(QFont("Inter", 12))
        resorption_time_label.setToolTip("""
<b>Alkohol-Resorptionskinetik</b><br><br>
Die Resorptionszeit bestimmt, wie schnell Alkohol ins Blut gelangt:<br>
• <b>Nüchtern:</b> 15-45 min (schnelle Resorption)<br>
• <b>Mit Nahrung:</b> 30-120 min (verzögerte Resorption)<br>
• <b>Flüssigkeit:</b> Schneller als feste Nahrung<br>
• <b>Fetthaltig:</b> Deutlich verzögerte Magenentleerung<br><br>
<b>First-Pass-Metabolismus:</b> 15-25% Alkohol wird bereits in Magen/Leber abgebaut<br><br>
<b>Wissenschaftliche Referenzen:</b><br>
• <a href="https://pubmed.ncbi.nlm.nih.gov/14977440/">Danel, T. et al. (2003). Chronobiology of ethanol. Chronobiol Int 20:947-973</a><br>
• <a href="https://pubmed.ncbi.nlm.nih.gov/2409256/">Jones, A.W. (1990). Pharmacokinetics of ethanol in plasma. Clin Pharmacokinet 18:178-203</a>
        """)
        
        self.resorption_time_combo = QComboBox()
        self.resorption_time_combo.setFont(QFont("Inter", 12))
        self.resorption_time_combo.addItems([
            "Auto (abhängig von Mahlzeit)",
            "Schnell (20 min)",
            "Normal (45 min)",
            "Langsam (90 min)",
            "Sehr langsam (120 min)"
        ])
        self.resorption_time_combo.setToolTip("""
<b>Resorptionszeit-Kategorien</b><br><br>
<b>Auto:</b> Adaptive Berechnung basierend auf Mahlzeit-Status<br>
<b>Schnell (20 min):</b> Nüchtern, Spirituosen, Kohlensäure<br>
<b>Normal (45 min):</b> Leichte Mahlzeit, Bier/Wein<br>
<b>Langsam (90 min):</b> Normale Mahlzeit, gemischte Getränke<br>
<b>Sehr langsam (120 min):</b> Schwere/fettreiche Mahlzeit<br><br>
<b>Einflussfaktoren:</b><br>
• Mageninhalt und pH-Wert<br>
• Alkoholkonzentration der Getränke<br>
• CO₂-Gehalt (beschleunigt um 20-30%)<br>
• Motilität des Gastrointestinaltrakts
        """)
        
        resorption_time_layout.addWidget(resorption_time_label)
        resorption_time_layout.addWidget(self.resorption_time_combo)
        resorption_layout.addLayout(resorption_time_layout)
        
        # Resorptionsdefizit
        resorption_deficit_layout = QVBoxLayout()
        resorption_deficit_label = QLabel("Resorptionsdefizit:")
        resorption_deficit_label.setFont(QFont("Inter", 12))
        resorption_deficit_label.setToolTip("""
<b>Resorptionsdefizit und First-Pass-Metabolismus</b><br><br>
Anteil des Alkohols, der nicht ins Blut gelangt:<br>
• <b>Gastraler Metabolismus:</b> 5-15% durch Magen-ADH<br>
• <b>Hepatischer First-Pass:</b> 10-25% in der Leber<br>
• <b>Individuelle Variation:</b> Genetische ADH-Polymorphismen<br><br>
<b>Geschlechtsunterschiede:</b><br>
• <b>♂:</b> 10-15% Resorptionsdefizit<br>
• <b>♀:</b> 15-25% (geringere gastrische ADH)<br><br>
<b>Wissenschaftliche Referenzen:</b><br>
• <a href="https://pubmed.ncbi.nlm.nih.gov/1391672/">Baraona, E. et al. (1992). Gender differences in pharmacokinetics of alcohol. Alcohol Clin Exp Res 16:1050-1055</a><br>
• <a href="https://pubmed.ncbi.nlm.nih.gov/8534963/">Friel, P.N. et al. (1995). Gender and body composition effects on ethanol pharmacokinetics</a>
        """)
        
        deficit_slider_layout = QHBoxLayout()
        self.resorption_deficit_slider = QSlider(Qt.Orientation.Horizontal)
        self.resorption_deficit_slider.setRange(0, 30)
        self.resorption_deficit_slider.setValue(10)
        
        self.resorption_deficit_label = QLabel("10%")
        self.resorption_deficit_label.setFont(QFont("Inter", 12))
        self.resorption_deficit_label.setMinimumWidth(40)
        
        deficit_slider_layout.addWidget(self.resorption_deficit_slider)
        deficit_slider_layout.addWidget(self.resorption_deficit_label)
        
        resorption_deficit_layout.addWidget(resorption_deficit_label)
        resorption_deficit_layout.addLayout(deficit_slider_layout)
        resorption_layout.addLayout(resorption_deficit_layout)
        
        layout.addWidget(resorption_group)
        
        # Eliminationseinstellungen
        elimination_group = QGroupBox("Elimination")
        elimination_group.setFont(QFont("Inter", 14, QFont.Weight.Bold))
        elimination_layout = QVBoxLayout(elimination_group)
        
        # Eliminationsrate
        elimination_rate_layout = QHBoxLayout()
        elimination_rate_label = QLabel("Eliminationsrate:")
        elimination_rate_label.setFont(QFont("Inter", 12))
        elimination_rate_label.setToolTip("""
<b>Alkohol-Eliminationskinetik</b><br><br>
Die Eliminationsrate bestimmt den Alkoholabbau im Körper:<br>
• <b>Hepatischer Metabolismus:</b> 90-95% über ADH/ALDH<br>
• <b>Extrahepatisch:</b> 5-10% über Lunge, Niere, Haut<br>
• <b>Zero-Order-Kinetik:</b> Konstante Abbaurate (‰/h)<br>
• <b>Sättigung:</b> Enzym-limitiert bei >0.2‰<br><br>
<b>Geschlechtsunterschiede:</b><br>
• <b>♂:</b> 0.15-0.20 ‰/h (höhere Enzymdichte)<br>
• <b>♀:</b> 0.12-0.17 ‰/h (geringere Lebermasse)<br><br>
<b>Wissenschaftliche Referenzen:</b><br>
• <a href="https://pubmed.ncbi.nlm.nih.gov/9020251/">Lieber, C.S. (1997). Ethanol metabolism, cirrhosis and alcoholism. Clin Chim Acta 257:59-84</a><br>
• <a href="https://pubmed.ncbi.nlm.nih.gov/1355869/">Jones, A.W. & Sternebring, B. (1992). Kinetics of ethanol and methanol in alcoholics. Alcohol Clin Exp Res 16:1070-1077</a>
        """)
        
        self.elimination_rate_combo = QComboBox()
        self.elimination_rate_combo.setFont(QFont("Inter", 12))
        self.elimination_rate_combo.addItems([
            "Auto (geschlechtsabhängig)",
            "Niedrig (0.10 ‰/h)",
            "Normal (0.15 ‰/h)",
            "Hoch (0.20 ‰/h)",
            "Manuell"
        ])
        self.elimination_rate_combo.setToolTip("""
<b>Eliminationsraten-Kategorien</b><br><br>
<b>Auto:</b> ♂ 0.17 ‰/h, ♀ 0.15 ‰/h (geschlechtsspezifisch)<br>
<b>Niedrig (0.10 ‰/h):</b> Lebererkrankung, Alter >70, Medikamente<br>
<b>Normal (0.15 ‰/h):</b> Durchschnittspopulation, forensischer Standard<br>
<b>Hoch (0.20 ‰/h):</b> Junge Männer, Alkoholtoleranz, Enzyminduktion<br>
<b>Manuell:</b> Individuelle Anpassung (0.05-0.30 ‰/h)<br><br>
<b>Einflussfaktoren:</b><br>
• Lebermasse und ADH-Aktivität<br>
• Chronischer Alkoholkonsum (Enzyminduktion)<br>
• Medikamente (Induktoren/Inhibitoren)<br>
• Genetische Polymorphismen (ADH1B, ALDH2)<br>
• Alter, Geschlecht, Körperzusammensetzung
        """)
        
        elimination_rate_layout.addWidget(elimination_rate_label)
        elimination_rate_layout.addWidget(self.elimination_rate_combo)
        elimination_layout.addLayout(elimination_rate_layout)
        
        # Manuelle Eliminationsrate
        manual_elimination_layout = QVBoxLayout()
        manual_elimination_label = QLabel("Manuelle Rate (‰/h):")
        manual_elimination_label.setFont(QFont("Inter", 12))
        manual_elimination_label.setToolTip("""
<b>Manuelle Eliminationsrate</b><br><br>
Individualisierte Eliminationsrate für spezielle Fälle:<br>
• <b>0.05-0.08 ‰/h:</b> Schwere Lebererkrankung, hoches Alter<br>
• <b>0.10-0.12 ‰/h:</b> Leichte Leberfunktionsstörung<br>
• <b>0.15-0.17 ‰/h:</b> Normale Population (Standard)<br>
• <b>0.20-0.25 ‰/h:</b> Junge, gesunde Männer<br>
• <b>0.25-0.30 ‰/h:</b> Extreme Alkoholtoleranz (selten)<br><br>
<b>Achtung:</b> Werte >0.25 ‰/h sind wissenschaftlich umstritten!<br><br>
<b>Referenz:</b><br>
• <a href="https://pubmed.ncbi.nlm.nih.gov/11505034/">Ramchandani, V.A. et al. (2001). Physiologically-based pharmacokinetic model for alcohol. Alcohol Clin Exp Res 25:1239-1244</a>
        """)
        
        manual_slider_layout = QHBoxLayout()
        self.manual_elimination_slider = QSlider(Qt.Orientation.Horizontal)
        self.manual_elimination_slider.setRange(5, 30)  # 0.05 bis 0.30 ‰/h
        self.manual_elimination_slider.setValue(15)  # 0.15 ‰/h
        self.manual_elimination_slider.setEnabled(False)
        
        self.manual_elimination_label = QLabel("0.15")
        self.manual_elimination_label.setFont(QFont("Inter", 12))
        self.manual_elimination_label.setMinimumWidth(40)
        
        manual_slider_layout.addWidget(self.manual_elimination_slider)
        manual_slider_layout.addWidget(self.manual_elimination_label)
        
        manual_elimination_layout.addWidget(manual_elimination_label)
        manual_elimination_layout.addLayout(manual_slider_layout)
        elimination_layout.addLayout(manual_elimination_layout)
        
        layout.addWidget(elimination_group)
        
        # Weitere Einstellungen
        additional_group = QGroupBox("Weitere Einstellungen")
        additional_group.setFont(QFont("Inter", 14, QFont.Weight.Bold))
        additional_layout = QVBoxLayout(additional_group)
        
        # Mahlzeit-Status
        meal_layout = QHBoxLayout()
        meal_label = QLabel("Mahlzeit-Status:")
        meal_label.setFont(QFont("Inter", 12))
        meal_label.setToolTip("""
<b>Mahlzeit-Einfluss auf Alkohol-Pharmakodynamik</b><br><br>
Nahrung beeinflusst massiv die Alkoholresorption:<br>
• <b>Magenentleerung:</b> Verzögerung um 30-120 Minuten<br>
• <b>Peak-BAK-Reduktion:</b> 20-50% bei fettreicher Mahlzeit<br>
• <b>Resorptionszeit:</b> Verlängert von 30 auf 120+ Minuten<br>
• <b>First-Pass-Effekt:</b> Verstärkt durch längeren Magenkontakt<br><br>
<b>Mechanismen:</b><br>
• Pylorusspasmus durch Fette<br>
• Verdünnung der Alkoholkonzentration<br>
• Stimulation der gastrischen ADH<br>
• Verzögerte Magenentleerung<br><br>
<b>Wissenschaftliche Referenzen:</b><br>
• <a href="https://pubmed.ncbi.nlm.nih.gov/2174244/">Sedman, A.J. et al. (1990). Food effects on absorption and metabolism of alcohol. J Pharm Sci 79:1007-1010</a><br>
• <a href="https://pubmed.ncbi.nlm.nih.gov/9072302/">Oneta, C.M. et al. (1998). First-pass metabolism of ethanol. Alcohol Clin Exp Res 22:292-298</a>
        """)
        
        self.meal_combo = QComboBox()
        self.meal_combo.setFont(QFont("Inter", 12))
        self.meal_combo.addItems([
            "Nüchtern",
            "Leichte Mahlzeit",
            "Normale Mahlzeit",
            "Schwere Mahlzeit"
        ])
        self.meal_combo.setToolTip("""
<b>Mahlzeit-Kategorien und Resorptionseffekte</b><br><br>
<b>Nüchtern (0-2h nach Mahlzeit):</b><br>
• Schnelle Resorption (15-30 min)<br>
• Hohe Peak-BAK<br>
• Minimaler First-Pass-Effekt<br><br>
<b>Leichte Mahlzeit (<500 kcal):</b><br>
• Verlangsamte Resorption (30-60 min)<br>
• 10-20% Peak-BAK-Reduktion<br>
• Snacks, Obst, leichte Suppen<br><br>
<b>Normale Mahlzeit (500-1000 kcal):</b><br>
• Moderate Verzögerung (60-90 min)<br>
• 20-35% Peak-BAK-Reduktion<br>
• Vollständige Hauptmahlzeit<br><br>
<b>Schwere Mahlzeit (>1000 kcal, fettreich):</b><br>
• Starke Verzögerung (90-120+ min)<br>
• 35-50% Peak-BAK-Reduktion<br>
• Fettreiche, proteinreiche Kost
        """)
        
        meal_layout.addWidget(meal_label)
        meal_layout.addWidget(self.meal_combo)
        additional_layout.addLayout(meal_layout)
        
        layout.addWidget(additional_group)
        
        # Stretch am Ende
        layout.addStretch()
    
    def connect_signals(self):
        """Verbindet alle Signale"""
        # Model-Checkboxes
        for checkbox in self.model_checkboxes.values():
            checkbox.stateChanged.connect(self.data_changed.emit)
        
        # Resorption
        self.resorption_time_combo.currentTextChanged.connect(self.data_changed.emit)
        self.resorption_deficit_slider.valueChanged.connect(self.update_resorption_deficit_label)
        self.resorption_deficit_slider.valueChanged.connect(self.data_changed.emit)
        
        # Elimination
        self.elimination_rate_combo.currentTextChanged.connect(self.on_elimination_rate_changed)
        self.elimination_rate_combo.currentTextChanged.connect(self.data_changed.emit)
        self.manual_elimination_slider.valueChanged.connect(self.update_manual_elimination_label)
        self.manual_elimination_slider.valueChanged.connect(self.data_changed.emit)
        
        # Weitere Einstellungen
        self.meal_combo.currentTextChanged.connect(self.data_changed.emit)
    
    def set_default_values(self):
        """Setzt Standardwerte"""
        # Widmark-Modell als Standard
        self.model_checkboxes["Widmark"].setChecked(True)
        
        # Standard-Einstellungen
        self.resorption_time_combo.setCurrentText("Auto (abhängig von Mahlzeit)")
        self.resorption_deficit_slider.setValue(10)
        self.elimination_rate_combo.setCurrentText("Auto (geschlechtsabhängig)")
        self.manual_elimination_slider.setValue(15)
        self.meal_combo.setCurrentText("Nüchtern")
        
        # Label aktualisieren
        self.update_resorption_deficit_label()
        self.update_manual_elimination_label()
    
    def update_resorption_deficit_label(self):
        """Aktualisiert das Resorptionsdefizit-Label"""
        value = self.resorption_deficit_slider.value()
        self.resorption_deficit_label.setText(f"{value}%")
    
    def update_manual_elimination_label(self):
        """Aktualisiert das manuelle Eliminationsrate-Label"""
        value = self.manual_elimination_slider.value() / 100.0  # Convert to ‰/h
        self.manual_elimination_label.setText(f"{value:.2f}")
    
    def on_elimination_rate_changed(self):
        """Reagiert auf Änderung der Eliminationsrate"""
        is_manual = self.elimination_rate_combo.currentText() == "Manuell"
        self.manual_elimination_slider.setEnabled(is_manual)
    
    def get_settings_data(self) -> Dict:
        """Gibt die aktuellen Einstellungen zurück"""
        # Ausgewählte Modelle sammeln
        selected_models = []
        for model_name, checkbox in self.model_checkboxes.items():
            if checkbox.isChecked():
                selected_models.append(model_name)
        
        return {
            'models': selected_models,
            'resorption_time': self.resorption_time_combo.currentText(),
            'resorption_deficit': self.resorption_deficit_slider.value(),
            'elimination_rate': self.elimination_rate_combo.currentText(),
            'manual_elimination_rate': self.manual_elimination_slider.value() / 100.0,
            'meal_status': self.meal_combo.currentText()
        }
    
    def set_settings_data(self, data: Dict):
        """Setzt die Einstellungen"""
        # Modelle setzen
        if 'models' in data:
            for model_name, checkbox in self.model_checkboxes.items():
                checkbox.setChecked(model_name in data['models'])
        
        # Andere Einstellungen
        if 'resorption_time' in data:
            self.resorption_time_combo.setCurrentText(data['resorption_time'])
        
        if 'resorption_deficit' in data:
            self.resorption_deficit_slider.setValue(data['resorption_deficit'])
        
        if 'elimination_rate' in data:
            self.elimination_rate_combo.setCurrentText(data['elimination_rate'])
        
        if 'manual_elimination_rate' in data:
            self.manual_elimination_slider.setValue(int(data['manual_elimination_rate'] * 100))
        
        if 'meal_status' in data:
            self.meal_combo.setCurrentText(data['meal_status'])
        
        # Labels aktualisieren
        self.update_resorption_deficit_label()
        self.update_manual_elimination_label()
        self.on_elimination_rate_changed()
    
    def validate_settings(self) -> List[str]:
        """Validiert die Einstellungen"""
        errors = []
        
        # Mindestens ein Modell muss ausgewählt sein
        selected_models = [name for name, cb in self.model_checkboxes.items() if cb.isChecked()]
        if not selected_models:
            errors.append("Mindestens ein Berechnungsmodell muss ausgewählt werden")
        
        return errors
    
    def get_model_descriptions(self) -> Dict[str, str]:
        """Gibt Beschreibungen der Modelle zurück"""
        return {
            "Widmark": """
            Das klassische Widmark-Modell verwendet einen festen Verteilungsfaktor:
            - Männer: r = 0.7
            - Frauen: r = 0.6
            
            Formel: BAK = Alkohol(g) / (r × Körpergewicht(kg))
            """,
            
            "Watson": """
            Die Watson-Formel berechnet das Körperwasser geschlechtsspezifisch:
            
            Männer: TBW = 2.447 - 0.09516 × Alter + 0.1074 × Größe + 0.3362 × Gewicht
            Frauen: TBW = -2.097 + 0.1069 × Größe + 0.2466 × Gewicht
            
            BAK = Alkohol(g) / (TBW × 1.2)
            """,
            
            "Forrest": """
            Das Forrest-Modell berücksichtigt den Körperfettanteil:
            
            Körperwasser = Gewicht × (1 - Körperfett/100) × Wasserfaktor
            
            Wasserfaktor: Männer 0.58, Frauen 0.49
            """,
            
            "Seidl": """
            Die erweiterte Seidl-Formel:
            
            Männer: r = 0.31608 - 0.004821 × Gewicht + 0.004432 × Größe
            Frauen: r = 0.31223 - 0.006446 × Gewicht + 0.004466 × Größe
            
            Mit Korrekturfaktoren für Alter und Trinkgewohnheit.
            """
        }
    
    def reset_to_defaults(self):
        """Setzt alle Einstellungen auf Standardwerte zurück"""
        # Alle Checkboxes deaktivieren
        for checkbox in self.model_checkboxes.values():
            checkbox.setChecked(False)
        
        # Defaults setzen
        self.set_default_values() 