from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QComboBox, QSpinBox, QDoubleSpinBox, QSlider, QGroupBox)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont

class PersonDataWidget(QWidget):
    """Widget für die Eingabe von Personendaten"""
    
    # Signale für Datenänderungen
    data_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.connect_signals()
        self.set_default_values()
    
    def setup_ui(self):
        """Erstellt die UI-Komponenten"""
        layout = QVBoxLayout(self)
        
        # Grunddaten
        basic_group = QGroupBox("Grunddaten")
        basic_group.setFont(QFont("Inter", 14, QFont.Weight.Bold))
        basic_layout = QVBoxLayout(basic_group)
        
        # Geschlecht
        gender_layout = QHBoxLayout()
        gender_label = QLabel("Geschlecht:")
        gender_label.setFont(QFont("Inter", 12))
        gender_label.setToolTip("""
<b>Geschlechtsabhängige Pharmakodynamik</b><br><br>
Die Blutalkoholkonzentration ist stark geschlechtsabhängig aufgrund unterschiedlicher:<br>
• <b>Körperwasseranteile:</b> ♂ 60-70%, ♀ 50-60% (Watson et al., 1980)<br>
• <b>Verteilungsräume:</b> r-Faktor ♂ 0.68-0.70, ♀ 0.55-0.60<br>
• <b>Eliminationsraten:</b> ♂ 0.17±0.02‰/h, ♀ 0.15±0.02‰/h<br><br>
<b>Wissenschaftliche Referenzen:</b><br>
• <a href="https://pubmed.ncbi.nlm.nih.gov/7361681/">Watson, P.E. et al. (1980). Total body water volumes for adult males and females estimated from simple anthropometric measurements. Am J Clin Nutr 33:27-39</a><br>
• <a href="https://pubmed.ncbi.nlm.nih.gov/8534963/">Friel, P.N. et al. (1995). The influence of gender and body composition on the pharmacokinetics of ethanol. Alcohol Clin Exp Res 19:1095-1099</a>
        """)
        
        self.gender_combo = QComboBox()
        self.gender_combo.setFont(QFont("Inter", 12))
        self.gender_combo.addItems(["Männlich", "Weiblich"])
        self.gender_combo.setToolTip("""
<b>Pharmakokinetische Geschlechtsunterschiede</b><br><br>
<b>Männlich:</b> Höherer Körperwasseranteil, größerer Verteilungsraum, schnellere Elimination<br>
<b>Weiblich:</b> Geringerer Körperwasseranteil, kleinerer Verteilungsraum, langsamere Elimination<br><br>
Dieser Unterschied beruht auf hormonellen und anatomischen Faktoren (Baraona et al., 2001)
        """)
        
        gender_layout.addWidget(gender_label)
        gender_layout.addWidget(self.gender_combo)
        basic_layout.addLayout(gender_layout)
        
        # Alter
        age_layout = QHBoxLayout()
        age_label = QLabel("Alter:")
        age_label.setFont(QFont("Inter", 12))
        age_label.setToolTip("""
<b>Altersabhängige Pharmakokinetik</b><br><br>
Mit zunehmendem Alter ändern sich:<br>
• <b>Körperzusammensetzung:</b> ↓ Magermasse, ↑ Fettanteil<br>
• <b>Körperwasseranteil:</b> ↓ 0.3-0.4% pro Jahr ab 30<br>
• <b>Leberfunktion:</b> ↓ Alkoholdehydrogenase-Aktivität<br>
• <b>Elimination:</b> ↓ ~10% pro Dekade ab 40 Jahren<br><br>
<b>Wissenschaftliche Referenzen:</b><br>
• <a href="https://pubmed.ncbi.nlm.nih.gov/858867/">Vestal, R.E. et al. (1977). Aging and ethanol metabolism. Clin Pharmacol Ther 21:343-354</a><br>
• <a href="https://pubmed.ncbi.nlm.nih.gov/1550274/">Dufour, M.C. et al. (1992). Twenty-year trends in cirrhosis mortality. Alcohol Health Res World 16:67-83</a>
        """)
        
        self.age_spin = QSpinBox()
        self.age_spin.setFont(QFont("Inter", 12))
        self.age_spin.setRange(16, 99)
        self.age_spin.setValue(30)
        self.age_spin.setSuffix(" Jahre")
        self.age_spin.setToolTip("""
<b>Alterskorrelierte BAK-Faktoren</b><br><br>
<b>18-30 Jahre:</b> Optimale Eliminationsrate<br>
<b>30-50 Jahre:</b> Leichte Reduktion der Leberfunktion<br>
<b>50+ Jahre:</b> Deutlich reduzierte Alkoholtoleranz<br><br>
Forrest-Modell berücksichtigt Alterskorrektur: r-Faktor × (1 - 0.01 × (Alter - 20))
        """)
        
        age_layout.addWidget(age_label)
        age_layout.addWidget(self.age_spin)
        basic_layout.addLayout(age_layout)
        
        # Körpergröße
        height_layout = QHBoxLayout()
        height_label = QLabel("Körpergröße:")
        height_label.setFont(QFont("Inter", 12))
        height_label.setToolTip("""
<b>Anthropometrische Verteilungsvolumen-Berechnung</b><br><br>
Die Körpergröße ist essentiell für Watson-Modell:<br>
• <b>Total Body Water (TBW):</b> Funktion von Größe, Gewicht, Alter<br>
• <b>Männer:</b> TBW = 2.447 - 0.09516×Alter + 0.1074×Größe + 0.3362×Gewicht<br>
• <b>Frauen:</b> TBW = -2.097 + 0.1069×Größe + 0.2466×Gewicht<br><br>
<b>Wissenschaftliche Referenz:</b><br>
• <a href="https://pubmed.ncbi.nlm.nih.gov/7361681/">Watson, P.E. et al. (1980). Total body water volumes for adult males and females estimated from simple anthropometric measurements. Am J Clin Nutr 33:27-39</a>
        """)
        
        self.height_spin = QSpinBox()
        self.height_spin.setFont(QFont("Inter", 12))
        self.height_spin.setRange(140, 220)
        self.height_spin.setValue(180)
        self.height_spin.setSuffix(" cm")
        self.height_spin.setToolTip("""
<b>Körpergröße in der BAK-Berechnung</b><br><br>
Zusammen mit Gewicht bestimmt die Größe das Verteilungsvolumen für Ethanol.<br>
Größere Personen haben i.d.R. niedrigere BAK-Werte bei gleicher Alkoholmenge.
        """)
        
        height_layout.addWidget(height_label)
        height_layout.addWidget(self.height_spin)
        basic_layout.addLayout(height_layout)
        
        # Körpergewicht
        weight_layout = QHBoxLayout()
        weight_label = QLabel("Körpergewicht:")
        weight_label.setFont(QFont("Inter", 12))
        weight_label.setToolTip("""
<b>Verteilungsvolumen und Pharmakodynamik</b><br><br>
Das Körpergewicht ist der wichtigste Faktor in der Widmark-Formel:<br>
• <b>BAK = A / (m × r)</b> wobei m = Körpergewicht<br>
• <b>Lineare Korrelation:</b> Doppeltes Gewicht = halbe BAK<br>
• <b>Berücksichtigung:</b> Magermasse vs. Fettmasse wichtig<br><br>
<b>Kritische Werte:</b><br>
• <b><50kg:</b> Erhöhtes Risiko für Intoxikation<br>
• <b>>120kg:</b> Mögliche Unterschätzung der BAK<br><br>
<b>Wissenschaftliche Referenz:</b><br>
• <a href="https://link.springer.com/chapter/10.1007/978-3-662-48986-4_3318">Widmark, E.M.P. (1932). Die theoretischen Grundlagen und die praktische Verwendbarkeit der gerichtlich-medizinischen Alkoholbestimmung. Urban & Schwarzenberg, Berlin</a>
        """)
        
        self.weight_spin = QDoubleSpinBox()
        self.weight_spin.setFont(QFont("Inter", 12))
        self.weight_spin.setRange(40.0, 200.0)
        self.weight_spin.setValue(80.0)
        self.weight_spin.setDecimals(1)
        self.weight_spin.setSuffix(" kg")
        self.weight_spin.setToolTip("""
<b>Gewichtsabhängige BAK-Berechnung</b><br><br>
Jedes zusätzliche Kilogramm Körpergewicht reduziert die BAK um ~1.4% bei Männern und ~1.7% bei Frauen.<br><br>
<b>Beispiel:</b> 10g Alkohol bei 70kg ♂ → 0.20‰, bei 80kg ♂ → 0.18‰
        """)
        
        weight_layout.addWidget(weight_label)
        weight_layout.addWidget(self.weight_spin)
        basic_layout.addLayout(weight_layout)
        
        layout.addWidget(basic_group)
        
        # Erweiterte Optionen
        advanced_group = QGroupBox("Erweiterte Optionen")
        advanced_group.setFont(QFont("Inter", 14, QFont.Weight.Bold))
        advanced_layout = QVBoxLayout(advanced_group)
        
        # Körperfettanteil
        body_fat_layout = QHBoxLayout()
        body_fat_label = QLabel("Körperfettanteil:")
        body_fat_label.setFont(QFont("Inter", 12))
        body_fat_label.setToolTip("""
<b>Körperfettanteil und Alkoholverteilung</b><br><br>
Der Körperfettanteil beeinflusst die BAK erheblich:<br>
• <b>Fettgewebe:</b> Hydrophob, niedrige Alkoholaufnahme<br>
• <b>Magermasse:</b> Höherer Wasseranteil, höhere Alkoholverteilung<br>
• <b>Korrektur:</b> r-Faktor × (1 - 0.01 × (KFA - 20%))<br><br>
<b>Normwerte:</b><br>
• <b>♂ Sportler:</b> 6-13%, <b>Fit:</b> 14-17%, <b>Durchschnitt:</b> 18-24%<br>
• <b>♀ Sportler:</b> 16-20%, <b>Fit:</b> 21-24%, <b>Durchschnitt:</b> 25-31%<br><br>
<b>Wissenschaftliche Referenzen:</b><br>
• <a href="https://pubmed.ncbi.nlm.nih.gov/3219734/">Kvist, H. et al. (1988). Total and visceral adipose-tissue volumes derived from measurements with computed tomography. Am J Clin Nutr 48:1351-1361</a><br>
• <a href="https://pubmed.ncbi.nlm.nih.gov/12760098/">Norberg, A. et al. (2003). Role of variability in explaining ethanol pharmacokinetics. Alcohol Clin Exp Res 27:1-8</a>
        """)
        
        self.body_fat_slider = QSlider()
        self.body_fat_slider.setOrientation(Qt.Orientation.Horizontal)
        self.body_fat_slider.setRange(5, 50)
        self.body_fat_slider.setValue(20)
        self.body_fat_slider.setToolTip("""
<b>Körperfettanteil-Bestimmung</b><br><br>
<b>Messmethoden:</b><br>
• <b>Bioelektrische Impedanz:</b> ±3-5% Genauigkeit<br>
• <b>DEXA-Scan:</b> Goldstandard, ±1-2% Genauigkeit<br>
• <b>Caliper:</b> ±3-4% Genauigkeit bei korrekter Anwendung<br><br>
<b>Einfluss auf BAK:</b> ±0.02-0.05‰ pro 5% KFA-Unterschied
        """)
        
        self.body_fat_label_value = QLabel("20%")
        self.body_fat_label_value.setFont(QFont("Inter", 12, QFont.Weight.Bold))
        self.body_fat_label_value.setMinimumWidth(40)
        
        self.body_fat_slider.valueChanged.connect(
            lambda v: self.body_fat_label_value.setText(f"{v}%")
        )
        
        body_fat_layout.addWidget(body_fat_label)
        body_fat_layout.addWidget(self.body_fat_slider)
        body_fat_layout.addWidget(self.body_fat_label_value)
        advanced_layout.addLayout(body_fat_layout)
        
        # Trinkgewohnheiten
        habit_layout = QHBoxLayout()
        habit_label = QLabel("Trinkgewohnheiten:")
        habit_label.setFont(QFont("Inter", 12))
        habit_label.setToolTip("""
<b>Alkoholtoleranz und Enzyminduktion</b><br><br>
Regelmäßiger Alkoholkonsum führt zu metabolischen Anpassungen:<br>
• <b>Enzyminduktion:</b> ↑ Alkoholdehydrogenase (ADH), ↑ MEOS<br>
• <b>Elimination:</b> ↑ 20-40% bei chronischem Konsum<br>
• <b>Neurotolerance:</b> Reduzierte ZNS-Empfindlichkeit<br><br>
<b>Kategorien nach WHO/AUDIT:</b><br>
• <b>Abstinent:</b> 0g/Tag<br>
• <b>Gelegentlich:</b> <10g/Tag (♀), <20g/Tag (♂)<br>
• <b>Regelmäßig:</b> 10-40g/Tag (♀), 20-60g/Tag (♂)<br>
• <b>Problematisch:</b> >40g/Tag (♀), >60g/Tag (♂)<br><br>
<b>Wissenschaftliche Referenzen:</b><br>
• <a href="https://pubmed.ncbi.nlm.nih.gov/9020251/">Lieber, C.S. (1997). Ethanol metabolism, cirrhosis and alcoholism. Clin Chim Acta 257:59-84</a><br>
• <a href="https://doi.org/10.1016/j.cld.2012.08.002">Cederbaum, A.I. (2012). Alcohol metabolism. Clin Liver Dis 16:667-685</a>
        """)
        
        self.habit_combo = QComboBox()
        self.habit_combo.setFont(QFont("Inter", 12))
        self.habit_combo.addItems([
            "Abstinent", "Gelegentlich", "Regelmäßig", "Täglich"
        ])
        self.habit_combo.setCurrentText("Gelegentlich")
        self.habit_combo.setToolTip("""
<b>Trinkgewohnheiten und Metabolismus</b><br><br>
<b>Abstinent:</b> Normale Enzymaktivität, Standardeliminationsrate<br>
<b>Gelegentlich:</b> Geringe Toleranz, Standardrate<br>
<b>Regelmäßig:</b> Leichte Enzyminduktion, +10-20% Eliminationsrate<br>
<b>Täglich:</b> Starke Enzyminduktion, +20-40% Eliminationsrate<br><br>
<b>Achtung:</b> Erhöhte Toleranz bedeutet nicht geringere Gefahr!
        """)
        
        habit_layout.addWidget(habit_label)
        habit_layout.addWidget(self.habit_combo)
        advanced_layout.addLayout(habit_layout)
        
        layout.addWidget(advanced_group)
        
        # BMI-Anzeige
        bmi_group = QGroupBox("Body Mass Index (BMI)")
        bmi_group.setFont(QFont("Inter", 12, QFont.Weight.Bold))
        bmi_group.setToolTip("""
<b>BMI und Alkoholverteilung</b><br><br>
Der BMI korreliert mit der Körperzusammensetzung:<br>
• <b>BMI <18.5:</b> Untergewicht, höhere BAK-Gefahr<br>
• <b>BMI 18.5-25:</b> Normalgewicht, Standardberechnung<br>
• <b>BMI 25-30:</b> Übergewicht, mögliche Unterschätzung<br>
• <b>BMI >30:</b> Adipositas, Körperfettkorrektur nötig<br><br>
<b>Limitation:</b> BMI unterscheidet nicht zwischen Muskel- und Fettmasse!<br><br>
<b>Wissenschaftliche Referenz:</b><br>
• <a href="https://pubmed.ncbi.nlm.nih.gov/1957828/">Deurenberg, P. et al. (1991). Body mass index and percent body fat: a meta-analysis among different ethnic groups. Am J Clin Nutr 54:623-630</a>
        """)
        
        bmi_layout = QVBoxLayout(bmi_group)
        
        self.bmi_display = QLabel("BMI: 24.7 (Normalgewicht)")
        self.bmi_display.setFont(QFont("Inter", 14, QFont.Weight.Bold))
        self.bmi_display.setStyleSheet("color: #4CAF50;")
        self.bmi_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.bmi_display.setToolTip("""
<b>BMI-Interpretation nach WHO</b><br><br>
• <b><16.0:</b> Starkes Untergewicht<br>
• <b>16.0-18.4:</b> Untergewicht<br>
• <b>18.5-24.9:</b> Normalgewicht<br>
• <b>25.0-29.9:</b> Übergewicht<br>
• <b>30.0-34.9:</b> Adipositas Grad I<br>
• <b>35.0-39.9:</b> Adipositas Grad II<br>
• <b>≥40.0:</b> Adipositas Grad III
        """)
        
        bmi_layout.addWidget(self.bmi_display)
        layout.addWidget(bmi_group)
    
    def connect_signals(self):
        """Verbindet alle Signale"""
        self.gender_combo.currentTextChanged.connect(self.data_changed.emit)
        self.age_spin.valueChanged.connect(self.data_changed.emit)
        self.height_spin.valueChanged.connect(self.data_changed.emit)
        self.weight_spin.valueChanged.connect(self.data_changed.emit)
        self.weight_spin.valueChanged.connect(self.update_bmi)
        self.height_spin.valueChanged.connect(self.update_bmi)
        self.body_fat_slider.valueChanged.connect(self.update_body_fat_label)
        self.body_fat_slider.valueChanged.connect(self.data_changed.emit)
        self.habit_combo.currentTextChanged.connect(self.data_changed.emit)
    
    def set_default_values(self):
        """Setzt Standardwerte"""
        self.gender_combo.setCurrentText("Männlich")
        self.age_spin.setValue(30)
        self.height_spin.setValue(180)
        self.weight_spin.setValue(80.0)
        self.body_fat_slider.setValue(20)
        self.habit_combo.setCurrentText("Gelegentlich")
        self.update_bmi()
        self.update_body_fat_label()
    
    def update_bmi(self):
        """Berechnet und aktualisiert den BMI"""
        try:
            weight = self.weight_spin.value()
            height = self.height_spin.value() / 100.0
            if height > 0 and weight > 0:
                bmi = weight / (height * height)
                
                # BMI-Kategorien mit Beschreibung
                if bmi < 16.0:
                    category = "Starkes Untergewicht"
                    color = "#F44336"  # Rot
                elif bmi < 18.5:
                    category = "Untergewicht"
                    color = "#FF9800"  # Orange
                elif bmi < 25.0:
                    category = "Normalgewicht"
                    color = "#4CAF50"  # Grün
                elif bmi < 30.0:
                    category = "Übergewicht"
                    color = "#FF9800"  # Orange
                elif bmi < 35.0:
                    category = "Adipositas Grad I"
                    color = "#F44336"  # Rot
                elif bmi < 40.0:
                    category = "Adipositas Grad II"
                    color = "#D32F2F"  # Dunkelrot
                else:
                    category = "Adipositas Grad III"
                    color = "#B71C1C"  # Sehr dunkelrot
                
                self.bmi_display.setText(f"BMI: {bmi:.1f} ({category})")
                self.bmi_display.setStyleSheet(f"color: {color};")
            else:
                self.bmi_display.setText("BMI: -- (Ungültige Eingabe)")
                self.bmi_display.setStyleSheet("color: #666666;")
        except (ValueError, ZeroDivisionError, OverflowError) as e:
            self.bmi_display.setText("BMI: -- (Berechnungsfehler)")
            self.bmi_display.setStyleSheet("color: #666666;")
    
    def update_body_fat_label(self):
        """Aktualisiert die Körperfettanteil-Anzeige"""
        value = self.body_fat_slider.value()
        self.body_fat_label_value.setText(f"{value}%")
    
    def get_person_data(self):
        """Gibt die aktuellen Personendaten zurück"""
        return {
            'gender': self.gender_combo.currentText(),
            'age': self.age_spin.value(),
            'height': self.height_spin.value(),
            'weight': self.weight_spin.value(),
            'body_fat': self.body_fat_slider.value(),
            'drinking_habit': self.habit_combo.currentText()
        }
    
    def set_person_data(self, data):
        """Setzt die Personendaten"""
        if 'gender' in data:
            self.gender_combo.setCurrentText(data['gender'])
        if 'age' in data:
            self.age_spin.setValue(data['age'])
        if 'height' in data:
            self.height_spin.setValue(data['height'])
        if 'weight' in data:
            self.weight_spin.setValue(data['weight'])
        if 'body_fat' in data:
            self.body_fat_slider.setValue(data['body_fat'])
        if 'drinking_habit' in data:
            self.habit_combo.setCurrentText(data['drinking_habit'])
    
    def validate_data(self):
        """Validiert die eingegebenen Daten"""
        errors = []
        
        if self.age_spin.value() < 18:
            errors.append("Alter muss mindestens 18 Jahre betragen")
        
        if self.height_spin.value() < 140:
            errors.append("Größe muss mindestens 140 cm betragen")
        
        if self.weight_spin.value() < 40:
            errors.append("Gewicht muss mindestens 40 kg betragen")
        
        return errors 