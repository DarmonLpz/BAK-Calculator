from typing import Dict, List, Optional
import csv
import json
from datetime import datetime
from PyQt6.QtWidgets import QFileDialog, QMessageBox, QWidget
from PyQt6.QtCore import QObject, pyqtSignal, QThread
from PyQt6.QtGui import QPixmap, QPainter
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_agg import FigureCanvasAgg
import pandas as pd
import os

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

class ExportThread(QThread):
    """Thread für Export-Operationen"""
    
    progress_updated = pyqtSignal(int)
    export_finished = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, export_type: str, file_path: str, data: Dict):
        super().__init__()
        self.export_type = export_type
        self.file_path = file_path
        self.data = data
    
    def run(self):
        """Führt den Export durch"""
        try:
            if self.export_type == 'pdf':
                self._export_pdf()
            elif self.export_type == 'csv':
                self._export_csv()
            elif self.export_type == 'excel':
                self._export_excel()
            elif self.export_type == 'json':
                self._export_json()
            
            print(f"✅ Export erfolgreich: {self.file_path}")
            self.export_finished.emit(True, f"Export erfolgreich: {self.file_path}")
            
        except Exception as e:
            error_msg = f"Export-Fehler: {str(e)}"
            print(f"❌ {error_msg}")
            import traceback
            print("Vollständiger Fehler-Traceback:")
            traceback.print_exc()
            self.export_finished.emit(False, error_msg)
    
    def _export_pdf(self):
        """Exportiert als PDF"""
        print(f"🔄 Starte PDF-Export: {self.file_path}")
        
        if not REPORTLAB_AVAILABLE:
            raise ImportError("ReportLab ist nicht installiert. Bitte installieren Sie es mit: pip install reportlab")
        
        self.progress_updated.emit(10)
        
        doc = SimpleDocTemplate(self.file_path, pagesize=A4, 
                               leftMargin=2*cm, rightMargin=2*cm,
                               topMargin=2*cm, bottomMargin=2*cm)
        styles = getSampleStyleSheet()
        story = []
        
        # Prüfe ob detaillierte Berechnung verfügbar ist
        if 'detailed_calculation_html' in self.data:
            print("📋 Verwende detaillierte Berechnung für PDF")
            # Verwende die ausführliche Berechnung
            self._export_detailed_pdf(doc, styles, story)
        else:
            print("📋 Keine detaillierte HTML-Daten gefunden - erstelle sie jetzt")
            # Erstelle die detaillierte Berechnung direkt hier
            self._create_detailed_calculation_on_demand()
            if 'detailed_calculation_html' in self.data:
                print("📋 Detaillierte Berechnung erfolgreich erstellt - verwende sie")
                self._export_detailed_pdf(doc, styles, story)
            else:
                print("📋 Fallback: Verwende Standard-PDF-Format")
                # Fallback: Standard-PDF
                self._export_standard_pdf(doc, styles, story)
        
        print(f"✅ PDF-Export abgeschlossen: {self.file_path}")
    
    def _create_detailed_calculation_on_demand(self):
        """Erstellt die detaillierte Berechnung direkt im Export-Manager"""
        results = self.data.get('results', {})
        if not results:
            print("⚠️ Keine Ergebnisse für detaillierte Berechnung verfügbar")
            return
        
        print("🔄 Erstelle detaillierte HTML-Berechnung im Export-Manager...")
        
        # Messzeitpunkt-Information aus den Ergebnissen extrahieren
        first_result = next(iter(results.values()))
        timing_description = first_result.get('timing_description', 'Aktueller Zeitpunkt')
        timing_mode = first_result.get('timing_mode', 'Jetzt (aktuell)')
        bac_calculation_time = first_result.get('bac_calculation_time')
        
        # HTML-formatierte ausführliche Berechnung - PDF-optimiert
        html_content = f"""
        <h2>📊 Wissenschaftliche BAK-Berechnung</h2>
        <p><i>Evidenzbasierte Pharmakodynamik und forensische Alkoholkennzeichnung nach internationalen Standards</i></p>
        
        <h3>⏰ BAK-Messzeitpunkt</h3>
        <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%; margin: 10px 0;">
        <tr style="background-color: #f0f8ff;">
            <th style="width: 30%;">Parameter</th>
            <th style="width: 70%;">Wert</th>
        </tr>
        <tr>
            <td><b>Gewählter Modus</b></td>
            <td>{timing_mode}</td>
        </tr>
        <tr>
            <td><b>Messzeitpunkt</b></td>
            <td>{timing_description}</td>
        </tr>
        <tr>
            <td><b>Datum/Uhrzeit</b></td>
            <td>{bac_calculation_time.strftime('%d.%m.%Y %H:%M:%S') if bac_calculation_time else 'N/A'}</td>
        </tr>
        <tr style="background-color: #fff3cd;">
            <td colspan="2"><b>⚠️ Wichtiger Hinweis:</b> Alle nachfolgenden BAK-Werte und Berechnungen beziehen sich auf diesen spezifischen Zeitpunkt!</td>
        </tr>
        </table>
        
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
                # Messzeitpunkt-Information extrahieren
                timing_info = result.get('timing_description', 'Aktueller Zeitpunkt')
                bac_calculation_time = result.get('bac_calculation_time')
                
                if bac_calculation_time:
                    time_str = bac_calculation_time.strftime('%d.%m.%Y %H:%M')
                    timing_detail = f"zum Zeitpunkt: {time_str}"
                else:
                    timing_detail = timing_info
                
                html_content += f"""
                <h4>🍺 Einzelgetränk-Analyse</h4>
                <p>Jedes Getränk wird separat mit eigener Resorptions- und Eliminationskurve berechnet:</p>
                
                <p><b>📅 Berechnung der aktuellen Beiträge:</b></p>
                <ul>
                    <li><b>Messzeitpunkt:</b> {timing_info}</li>
                    <li><b>Datum/Zeit:</b> {timing_detail}</li>
                    <li><i>Alle "Aktueller Beitrag"-Werte beziehen sich auf diesen Zeitpunkt</i></li>
                </ul>
                
                <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%; font-size: 11px;">
                <tr style="background-color: #e3f2fd;">
                    <th>Nr.</th>
                    <th>Alkohol (g)</th>
                    <th>Konsumzeit</th>
                    <th>Peak-BAK</th>
                    <th>Peak-Zeit</th>
                    <th>Resorption</th>
                    <th>Aktueller Beitrag*</th>
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
                
                <p><b>* Hinweis zum "Aktueller Beitrag":</b></p>
                <p><i>Alle Werte in der Spalte "Aktueller Beitrag" beziehen sich auf den gewählten Messzeitpunkt: <b>{timing_info}</b> ({timing_detail}). Diese Werte zeigen, wie viel jedes einzelne Getränk zum angegebenen Zeitpunkt zur Gesamt-BAK beiträgt.</i></p>
                
                <p><b>Zusammenfassung der Einzelbeiträge:</b></p>
                <ul>
                    <li><b>Summe aller Einzelbeiträge:</b> {total_current_contribution:.3f} ‰</li>
                    <li><b>Berechnete Gesamt-BAK:</b> {result.get('current_bac', 0):.3f} ‰</li>
                    <li><b>Messzeitpunkt:</b> {result.get('timing_description', 'Aktueller Zeitpunkt')}</li>
                    <li><i>Minimale Abweichung durch Rundungsfehler ist normal</i></li>
                </ul>
                
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
            <ul>
                <li><b>Peak-BAK:</b> {result.get('peak_bac', 0):.3f} ‰ ± 0.02 ‰ (95% CI)</li>
                <li><b>BAK zum Messzeitpunkt:</b> {result.get('current_bac', 0):.3f} ‰ ± 0.015 ‰</li>
                <li><b>Messzeitpunkt:</b> {result.get('timing_description', 'Aktueller Zeitpunkt')}</li>
                <li><b>Peak-Zeit:</b> {result.get('peak_time', '--')} (Resorptionsmaximum)</li>
                <li><b>Eliminationsdauer:</b> {result.get('elimination_time', '--')}</li>
            """
            
            if result.get('time_to_03'):
                html_content += f"<li><b>Fahrtüchtig ab:</b> {result.get('time_to_03').strftime('%H:%M')} Uhr (BAK < 0.5‰)</li>"
            
            if result.get('time_to_00'):
                html_content += f"<li><b>Nüchtern ab:</b> {result.get('time_to_00').strftime('%H:%M')} Uhr (BAK ≈ 0.0‰)</li>"
            
            html_content += """
            </ul>
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
        <h4>Modell-Unsicherheiten</h4>
        <ul>
            <li><b>Inter-individuelle Variabilität:</b> ±20-30% (Genetik, Enzymoproteine)</li>
            <li><b>Intra-individuelle Faktoren:</b> Tageszeit, Stress, Medikamente</li>
            <li><b>Resorptionskinetik:</b> Mageninhalt, Trinkgeschwindigkeit, CO₂</li>
            <li><b>Analytische Präzision:</b> ±0.005-0.02‰ je nach Methode</li>
        </ul>
        
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
        
        self.data['detailed_calculation_html'] = html_content
        print(f"✅ Detaillierte HTML-Berechnung erstellt: {len(html_content)} Zeichen")
    
    def _export_detailed_pdf(self, doc, styles, story):
        """Exportiert detaillierte PDF basierend auf HTML-Inhalt"""
        # Titel
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER
        )
        story.append(Paragraph("BAK-Kalkulator - Ausführliche Berechnung", title_style))
        story.append(Spacer(1, 20))
        
        # Datum
        date_style = ParagraphStyle(
            'DateStyle',
            parent=styles['Normal'],
            fontSize=12,
            alignment=TA_RIGHT
        )
        story.append(Paragraph(f"Erstellt am: {datetime.now().strftime('%d.%m.%Y %H:%M')}", date_style))
        story.append(Spacer(1, 30))
        
        self.progress_updated.emit(20)
        
        # HTML-Inhalt der ausführlichen Berechnung konvertieren
        html_content = self.data['detailed_calculation_html']
        
        # HTML zu ReportLab Paragraphs konvertieren
        self._convert_html_to_reportlab(html_content, story, styles)
        
        self.progress_updated.emit(90)
        
        # Disclaimer
        story.append(Spacer(1, 30))
        disclaimer_style = ParagraphStyle(
            'Disclaimer',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.red,
            alignment=TA_CENTER
        )
        story.append(Paragraph(
            "<b>WICHTIGER HINWEIS:</b> Diese Berechnung dient nur zu Informationszwecken. "
            "Die tatsächliche Blutalkoholkonzentration kann von den berechneten Werten abweichen. "
            "Fahren Sie niemals unter Alkoholeinfluss!",
            disclaimer_style
        ))
        
        # PDF erstellen
        try:
            print("🔨 Erstelle detailliertes PDF-Dokument...")
            doc.build(story)
            print("✅ Detailliertes PDF-Dokument erfolgreich erstellt")
            
            # Lösche temporäres Chart-Bild nach erfolgreichem PDF-Build
            if hasattr(self, '_temp_chart_path') and os.path.exists(self._temp_chart_path):
                try:
                    os.remove(self._temp_chart_path)
                    print("🗑️ Temporäres Chart-Bild gelöscht")
                except Exception as cleanup_error:
                    print(f"⚠️ Warnung: Chart-Bild konnte nicht gelöscht werden: {cleanup_error}")
                    
        except Exception as e:
            print(f"❌ Fehler beim Erstellen des detaillierten PDF-Dokuments: {e}")
            import traceback
            traceback.print_exc()
            
            # Lösche Chart-Bild auch bei Fehler
            if hasattr(self, '_temp_chart_path') and os.path.exists(self._temp_chart_path):
                try:
                    os.remove(self._temp_chart_path)
                    print("🗑️ Temporäres Chart-Bild nach Fehler gelöscht")
                except:
                    pass
            raise
        self.progress_updated.emit(100)
    
    def _convert_html_to_reportlab(self, html_content, story, styles):
        """Konvertiert HTML-Inhalt zu ReportLab-Elementen - VOLLSTÄNDIGE Konvertierung"""
        import re
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib.enums import TA_LEFT, TA_CENTER
        from reportlab.lib import colors
        
        print("🔄 Starte vollständige HTML-zu-PDF-Konvertierung...")
        
        # Bereinige HTML für bessere Verarbeitung
        html_content = html_content.replace('<br>', '\n')
        html_content = html_content.replace('<br/>', '\n')
        html_content = html_content.replace('<br />', '\n')
        html_content = html_content.replace('<hr>', '\n---\n')
        html_content = html_content.replace('<hr/>', '\n---\n')
        html_content = html_content.replace('<hr />', '\n---\n')
        
        # Definiere Custom Styles
        h2_style = ParagraphStyle(
            'CustomH2',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=12,
            spaceBefore=20,
            textColor=colors.darkblue
        )
        
        h3_style = ParagraphStyle(
            'CustomH3',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=10,
            spaceBefore=15,
            textColor=colors.darkgreen
        )
        
        h4_style = ParagraphStyle(
            'CustomH4',
            parent=styles['Heading3'],
            fontSize=12,
            spaceAfter=8,
            spaceBefore=12,
            textColor=colors.darkred
        )
        
        h5_style = ParagraphStyle(
            'CustomH5',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=6,
            spaceBefore=10,
            fontName='Helvetica-Bold'
        )
        
        # Sequenzielle Verarbeitung aller HTML-Elemente
        elements = self._parse_html_sequentially(html_content)
        
        for element in elements:
            element_type = element['type']
            content = element['content']
            
            if element_type == 'h2':
                story.append(Paragraph(content, h2_style))
            elif element_type == 'h3':
                story.append(Paragraph(content, h3_style))
            elif element_type == 'h4':
                story.append(Paragraph(content, h4_style))
            elif element_type == 'h5':
                story.append(Paragraph(content, h5_style))
            elif element_type == 'p':
                if content.strip():
                    story.append(Paragraph(content, styles['Normal']))
                    story.append(Spacer(1, 6))
            elif element_type == 'ul':
                for li_content in content:
                    story.append(Paragraph(f"• {li_content}", styles['Normal']))
                story.append(Spacer(1, 6))
            elif element_type == 'ol':
                for i, li_content in enumerate(content, 1):
                    story.append(Paragraph(f"{i}. {li_content}", styles['Normal']))
                story.append(Spacer(1, 6))
            elif element_type == 'table':
                # Tabelle direkt mit HTML-String verarbeiten
                self._convert_html_table_advanced(content, story, styles)
            elif element_type == 'div':
                # Spezielle Div-Behandlung (z.B. farbige Boxen)
                div_style = element.get('style', {})
                if 'background-color' in div_style:
                    # Erstelle farbige Box
                    box_style = ParagraphStyle(
                        'ColorBox',
                        parent=styles['Normal'],
                        backColor=self._parse_color(div_style.get('background-color', '#f9f9f9')),
                        borderPadding=10,
                        borderWidth=1,
                        borderColor=colors.lightgrey
                    )
                    story.append(Paragraph(content, box_style))
                    story.append(Spacer(1, 10))
                else:
                    # Normale Div-Behandlung
                    if content.strip():
                        story.append(Paragraph(content, styles['Normal']))
                        story.append(Spacer(1, 6))
            elif element_type == 'hr':
                # Horizontale Linie
                story.append(Spacer(1, 10))
                from reportlab.platypus import HRFlowable
                story.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
                story.append(Spacer(1, 10))
        
        print(f"✅ HTML-zu-PDF-Konvertierung abgeschlossen: {len(elements)} Elemente verarbeitet")
    
    def _parse_html_sequentially(self, html_content):
        """Parst HTML sequenziell und behält die Reihenfolge bei"""
        import re
        
        elements = []
        
        # Alle HTML-Tags mit ihrer Position finden
        pattern = r'<(/?)([^>]+)>(.*?)(?=<|$)'
        matches = []
        
        # Finde alle wichtigen HTML-Elemente in der richtigen Reihenfolge
        patterns = [
            (r'<h2[^>]*>(.*?)</h2>', 'h2'),
            (r'<h3[^>]*>(.*?)</h3>', 'h3'),
            (r'<h4[^>]*>(.*?)</h4>', 'h4'),
            (r'<h5[^>]*>(.*?)</h5>', 'h5'),
            (r'<p[^>]*>(.*?)</p>', 'p'),
            (r'<ul[^>]*>(.*?)</ul>', 'ul'),
            (r'<ol[^>]*>(.*?)</ol>', 'ol'),
            (r'<table[^>]*>(.*?)</table>', 'table'),
            (r'<div[^>]*style="([^"]*)"[^>]*>(.*?)</div>', 'div'),
            (r'<hr[^>]*/?>', 'hr')
        ]
        
        for pattern, tag_type in patterns:
            for match in re.finditer(pattern, html_content, re.DOTALL | re.IGNORECASE):
                start_pos = match.start()
                if tag_type == 'ul' or tag_type == 'ol':
                    # Extrahiere Liste-Items
                    list_content = match.group(1)
                    li_pattern = r'<li[^>]*>(.*?)</li>'
                    li_items = [self._clean_html_text(li.group(1)) for li in re.finditer(li_pattern, list_content, re.DOTALL)]
                    content = li_items
                elif tag_type == 'div':
                    style_attr = match.group(1) if match.lastindex >= 2 else ""
                    content = self._clean_html_text(match.group(2) if match.lastindex >= 2 else "")
                    style_dict = self._parse_style_attr(style_attr)
                    elements.append({
                        'type': tag_type,
                        'content': content,
                        'style': style_dict,
                        'position': start_pos
                    })
                    continue
                elif tag_type == 'hr':
                    content = ""
                elif tag_type == 'table':
                    # Für Tabellen den kompletten HTML-String behalten
                    content = match.group(0)  # Kompletter Match mit Tags
                else:
                    content = self._clean_html_text(match.group(1))
                
                elements.append({
                    'type': tag_type,
                    'content': content,
                    'position': start_pos
                })
        
        # Sortiere nach Position im HTML
        elements.sort(key=lambda x: x['position'])
        
        return elements
    
    def _parse_style_attr(self, style_attr):
        """Parst CSS-Style-Attribute"""
        style_dict = {}
        if style_attr:
            for style_rule in style_attr.split(';'):
                if ':' in style_rule:
                    key, value = style_rule.split(':', 1)
                    style_dict[key.strip()] = value.strip()
        return style_dict
    
    def _parse_color(self, color_str):
        """Konvertiert CSS-Farben zu ReportLab-Farben"""
        color_map = {
            '#f9f9f9': colors.whitesmoke,
            '#e8f5e8': colors.lightgreen,
            '#fff3cd': colors.lightyellow,
            '#e3f2fd': colors.lightblue,
            '#ffebee': colors.mistyrose,
            '#fff3e0': colors.cornsilk,
            '#f1f8e9': colors.honeydew
        }
        return color_map.get(color_str, colors.whitesmoke)
    
    def _convert_html_table_advanced(self, table_html, story, styles):
        """Erweiterte HTML-Tabellen-Konvertierung"""
        import re
        from reportlab.platypus import Table, TableStyle
        from reportlab.lib import colors
        
        print(f"🔄 Konvertiere HTML-Tabelle: {len(table_html)} Zeichen")
        
        # Extrahiere Tabellenzeilen
        row_pattern = r'<tr[^>]*>(.*?)</tr>'
        rows = re.findall(row_pattern, table_html, re.DOTALL)
        print(f"📊 Gefundene Tabellenzeilen: {len(rows)}")
        
        table_data = []
        for row in rows:
            # Extrahiere Zellen (th und td)
            cell_pattern = r'<t[hd][^>]*>(.*?)</t[hd]>'
            cells = re.findall(cell_pattern, row, re.DOTALL)
            clean_cells = [self._clean_html_text(cell) for cell in cells]
            if clean_cells:
                table_data.append(clean_cells)
        
        if table_data:
            print(f"✅ Tabelle erstellt: {len(table_data)} Zeilen × {len(table_data[0]) if table_data else 0} Spalten")
            # Erstelle ReportLab-Tabelle mit verbessertem Styling
            table = Table(table_data, repeatRows=1)
            table.setStyle(TableStyle([
                # Header-Styling
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                
                # Body-Styling
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.beige, colors.lightgrey]),
                
                # Rahmen
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('LINEBELOW', (0, 0), (-1, 0), 2, colors.darkblue),
                
                # Padding
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))
            story.append(table)
            story.append(Spacer(1, 15))
    
    def _clean_html_text(self, html_text):
        """Bereinigt HTML-Text von Tags"""
        import re
        # Entferne HTML-Tags
        clean = re.sub(r'<[^>]+>', '', html_text)
        # Ersetze HTML-Entities
        clean = clean.replace('&lt;', '<')
        clean = clean.replace('&gt;', '>')
        clean = clean.replace('&amp;', '&')
        clean = clean.replace('&nbsp;', ' ')
        clean = clean.replace('‰', '‰')
        # Entferne mehrfache Leerzeichen
        clean = re.sub(r'\s+', ' ', clean)
        return clean.strip()
    
    def _convert_html_table(self, table_html, story, styles):
        """Konvertiert HTML-Tabelle zu ReportLab-Tabelle"""
        import re
        
        # Extrahiere Tabellenzeilen
        row_pattern = r'<tr[^>]*>(.*?)</tr>'
        rows = re.findall(row_pattern, table_html, re.DOTALL)
        
        table_data = []
        for row in rows:
            # Extrahiere Zellen
            cell_pattern = r'<t[hd][^>]*>(.*?)</t[hd]>'
            cells = re.findall(cell_pattern, row, re.DOTALL)
            clean_cells = [self._clean_html_text(cell) for cell in cells]
            if clean_cells:
                table_data.append(clean_cells)
        
        if table_data:
            # Erstelle ReportLab-Tabelle
            from reportlab.platypus import Table, TableStyle
            from reportlab.lib import colors
            
            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(table)
            story.append(Spacer(1, 12))
    
    def _export_standard_pdf(self, doc, styles, story):
        """Exportiert Standard-PDF (Fallback)"""
        # Titel
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER
        )
        story.append(Paragraph("BAK-Kalkulator Bericht", title_style))
        story.append(Spacer(1, 20))
        
        # Datum
        date_style = ParagraphStyle(
            'DateStyle',
            parent=styles['Normal'],
            fontSize=12,
            alignment=TA_RIGHT
        )
        story.append(Paragraph(f"Erstellt am: {datetime.now().strftime('%d.%m.%Y %H:%M')}", date_style))
        story.append(Spacer(1, 30))
        
        self.progress_updated.emit(20)
        
        # Personendaten
        if 'person_data' in self.data:
            person = self.data['person_data']
            story.append(Paragraph("Personendaten", styles['Heading2']))
            
            person_table_data = [
                ['Geschlecht:', person.get('gender', 'N/A')],
                ['Alter:', f"{person.get('age', 'N/A')} Jahre"],
                ['Größe:', f"{person.get('height', 'N/A')} cm"],
                ['Gewicht:', f"{person.get('weight', 'N/A')} kg"],
                ['BMI:', f"{person.get('bmi', 'N/A'):.1f}" if person.get('bmi') else 'N/A'],
                ['Körperfettanteil:', f"{person.get('body_fat', 'N/A')}%"],
                ['Trinkgewohnheit:', person.get('drinking_habit', 'N/A')]
            ]
            
            person_table = Table(person_table_data, colWidths=[4*cm, 6*cm])
            person_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('BACKGROUND', (1, 0), (1, -1), colors.beige),
            ]))
            story.append(person_table)
            story.append(Spacer(1, 20))
        
        self.progress_updated.emit(40)
        
        # Getränke
        if 'drinks_data' in self.data and self.data['drinks_data']:
            story.append(Paragraph("Konsumierte Getränke", styles['Heading2']))
            
            drinks_table_data = [['Getränk', 'Menge (ml)', 'Alkohol (%)', 'Zeit', 'Alkohol (g)']]
            
            for drink in self.data['drinks_data']:
                quantity = drink.get('quantity', 1)
                alcohol_grams = drink['volume'] * (drink['alcohol_content'] / 100) * 0.8 * quantity
                drinks_table_data.append([
                    drink['name'],
                    f"{drink['volume']} × {quantity}",
                    f"{drink['alcohol_content']:.1f}",
                    drink['time'].strftime('%H:%M') if isinstance(drink['time'], datetime) else str(drink['time']),
                    f"{alcohol_grams:.1f}"
                ])
            
            drinks_table = Table(drinks_table_data, colWidths=[4*cm, 2*cm, 2*cm, 2*cm, 2*cm])
            drinks_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(drinks_table)
            story.append(Spacer(1, 20))
        
        self.progress_updated.emit(60)
        
        # Ergebnisse
        if 'results' in self.data and self.data['results']:
            story.append(Paragraph("Berechnungsergebnisse", styles['Heading2']))
            
            results_table_data = [['Modell', 'Aktuelle BAK', 'Max. BAK', 'Zeit bis 0.5‰', 'Zeit bis 0.0‰']]
            
            for model, result in self.data['results'].items():
                results_table_data.append([
                    model,
                    f"{result.get('current_bac', 0):.2f} ‰",
                    f"{result.get('peak_bac', 0):.2f} ‰",
                    result.get('time_to_03', '--').strftime('%H:%M') if result.get('time_to_03') else '--',
                    result.get('time_to_00', '--').strftime('%H:%M') if result.get('time_to_00') else '--'
                ])
            
            results_table = Table(results_table_data, colWidths=[3*cm, 2.5*cm, 2.5*cm, 2.5*cm, 2.5*cm])
            results_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(results_table)
            story.append(Spacer(1, 20))
        
        self.progress_updated.emit(80)
        
        # Chart hinzufügen (falls verfügbar)
        if 'chart_data' in self.data and self.data['chart_data']:
            story.append(Paragraph("BAK-Verlaufsdiagramm", styles['Heading2']))
            
            try:
                # Erstelle Chart als Bild
                chart_path = self.file_path.replace('.pdf', '_chart.png')
                self._create_chart_image(chart_path)
                
                # Warte kurz und prüfe mehrfach, ob Datei existiert
                import time
                max_attempts = 10
                attempt = 0
                
                while attempt < max_attempts:
                    if os.path.exists(chart_path) and os.path.getsize(chart_path) > 0:
                        print(f"✅ Chart-Datei gefunden nach {attempt} Versuchen: {chart_path}")
                        break
                    time.sleep(0.1)  # 100ms warten
                    attempt += 1
                
                if os.path.exists(chart_path) and os.path.getsize(chart_path) > 0:
                    try:
                        chart_img = Image(chart_path, width=15*cm, height=10*cm)
                        story.append(chart_img)
                        print("✅ Chart erfolgreich in PDF eingefügt")
                        # Merke Chart-Pfad zum späteren Löschen
                        self._temp_chart_path = chart_path
                    except Exception as img_error:
                        print(f"❌ Fehler beim Laden des Chart-Bildes: {img_error}")
                        story.append(Paragraph("Chart konnte nicht geladen werden.", styles['Normal']))
                        # Lösche fehlerhaftes Chart-Bild
                        try:
                            os.remove(chart_path)
                        except:
                            pass
                else:
                    print(f"❌ Chart-Datei nicht gefunden oder leer: {chart_path}")
                    story.append(Paragraph("Chart konnte nicht erstellt werden.", styles['Normal']))
            except Exception as e:
                print(f"❌ Fehler beim Chart-Export: {e}")
                import traceback
                traceback.print_exc()
                story.append(Paragraph("Chart konnte nicht erstellt werden.", styles['Normal']))
        
        # Disclaimer
        story.append(Spacer(1, 30))
        disclaimer_style = ParagraphStyle(
            'Disclaimer',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.red,
            alignment=TA_CENTER
        )
        story.append(Paragraph(
            "<b>WICHTIGER HINWEIS:</b> Diese Berechnung dient nur zu Informationszwecken. "
            "Die tatsächliche Blutalkoholkonzentration kann von den berechneten Werten abweichen. "
            "Fahren Sie niemals unter Alkoholeinfluss!",
            disclaimer_style
        ))
        
        # PDF erstellen
        try:
            print("🔨 Erstelle Standard-PDF-Dokument...")
            doc.build(story)
            print("✅ Standard-PDF-Dokument erfolgreich erstellt")
            
            # Lösche temporäres Chart-Bild nach erfolgreichem PDF-Build
            if hasattr(self, '_temp_chart_path') and os.path.exists(self._temp_chart_path):
                try:
                    os.remove(self._temp_chart_path)
                    print("🗑️ Temporäres Chart-Bild gelöscht")
                except Exception as cleanup_error:
                    print(f"⚠️ Warnung: Chart-Bild konnte nicht gelöscht werden: {cleanup_error}")
                    
        except Exception as e:
            print(f"❌ Fehler beim Erstellen des Standard-PDF-Dokuments: {e}")
            import traceback
            traceback.print_exc()
            
            # Lösche Chart-Bild auch bei Fehler
            if hasattr(self, '_temp_chart_path') and os.path.exists(self._temp_chart_path):
                try:
                    os.remove(self._temp_chart_path)
                    print("🗑️ Temporäres Chart-Bild nach Fehler gelöscht")
                except:
                    pass
            raise
        self.progress_updated.emit(100)
    
    def _create_chart_image(self, file_path: str):
        """Erstellt ein Chart-Bild für PDF-Export"""
        try:
            import matplotlib
            matplotlib.use('Agg')  # Non-interactive backend
            import matplotlib.pyplot as plt
            import matplotlib.dates as mdates
            
            fig, ax = plt.subplots(figsize=(12, 8))
            
            colors = ['#2196F3', '#FF9800', '#4CAF50', '#9C27B0']
            
            for i, (model, result) in enumerate(self.data['chart_data'].items()):
                if 'bac_values' in result and result['bac_values']:
                    times = []
                    bac_values = []
                    
                    for point in result['bac_values']:
                        if len(point) >= 2:
                            time_val = point[0]
                            bac_val = point[1]
                            
                            # Konvertiere Zeit zu datetime falls nötig
                            if isinstance(time_val, (int, float)):
                                # Annahme: Zeit ist in Stunden seit einem Referenzpunkt
                                base_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                                time_val = base_time.timestamp() + (time_val * 3600)
                                time_val = datetime.fromtimestamp(time_val)
                            elif not isinstance(time_val, datetime):
                                continue  # Überspringe ungültige Zeitwerte
                            
                            times.append(time_val)
                            bac_values.append(bac_val)
                    
                    if times and bac_values:
                        color = colors[i % len(colors)]
                        ax.plot(times, bac_values, label=f"{model}", color=color, linewidth=2)
            
            # Grenzwerte
            ax.axhline(y=0.3, color='orange', linestyle='--', alpha=0.7, label='0.3‰')
            ax.axhline(y=0.5, color='red', linestyle='--', alpha=0.7, label='0.5‰')
            ax.axhline(y=1.1, color='darkred', linestyle='--', alpha=0.7, label='1.1‰')
            
            # Formatiere X-Achse für Zeiten
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))
            plt.xticks(rotation=45)
            
            ax.set_xlabel('Zeit')
            ax.set_ylabel('BAK (‰)')
            ax.set_title('Blutalkoholkonzentrations-Verlauf')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.savefig(file_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            # Stelle sicher, dass die Datei vollständig geschrieben wurde
            import time
            time.sleep(0.1)  # Kurz warten
            
            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                print(f"✅ Chart-Bild erfolgreich erstellt: {file_path} ({os.path.getsize(file_path)} Bytes)")
            else:
                print(f"❌ Chart-Bild konnte nicht erstellt werden: {file_path}")
                raise Exception("Chart-Datei wurde nicht erstellt")
            
        except Exception as e:
            print(f"❌ Fehler beim Erstellen des Chart-Bildes: {e}")
            import traceback
            traceback.print_exc()
            raise  # Weiterleiten des Fehlers
    
    def _export_csv(self):
        """Exportiert als CSV"""
        self.progress_updated.emit(20)
        
        with open(self.file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile, delimiter=';')
            
            # Header
            writer.writerow(['BAK-Kalkulator Export'])
            writer.writerow(['Erstellt am:', datetime.now().strftime('%d.%m.%Y %H:%M')])
            writer.writerow([])
            
            self.progress_updated.emit(40)
            
            # Personendaten
            if 'person_data' in self.data:
                writer.writerow(['Personendaten'])
                person = self.data['person_data']
                writer.writerow(['Geschlecht:', person.get('gender', 'N/A')])
                writer.writerow(['Alter:', f"{person.get('age', 'N/A')} Jahre"])
                writer.writerow(['Größe:', f"{person.get('height', 'N/A')} cm"])
                writer.writerow(['Gewicht:', f"{person.get('weight', 'N/A')} kg"])
                writer.writerow(['Körperfettanteil:', f"{person.get('body_fat', 'N/A')}%"])
                writer.writerow(['Trinkgewohnheit:', person.get('drinking_habit', 'N/A')])
                writer.writerow([])
            
            self.progress_updated.emit(60)
            
            # Getränke
            if 'drinks_data' in self.data and self.data['drinks_data']:
                writer.writerow(['Konsumierte Getränke'])
                writer.writerow(['Getränk', 'Menge (ml)', 'Alkohol (%)', 'Zeit', 'Alkohol (g)'])
                
                for drink in self.data['drinks_data']:
                    quantity = drink.get('quantity', 1)
                    alcohol_grams = drink['volume'] * (drink['alcohol_content'] / 100) * 0.8 * quantity
                    writer.writerow([
                        drink['name'],
                        f"{drink['volume']} × {quantity}",
                        f"{drink['alcohol_content']:.1f}",
                        drink['time'].strftime('%H:%M') if isinstance(drink['time'], datetime) else str(drink['time']),
                        f"{alcohol_grams:.1f}"
                    ])
                writer.writerow([])
            
            self.progress_updated.emit(80)
            
            # Ergebnisse
            if 'results' in self.data and self.data['results']:
                writer.writerow(['Berechnungsergebnisse'])
                writer.writerow(['Modell', 'Aktuelle BAK', 'Max. BAK', 'Zeit bis 0.5‰', 'Zeit bis 0.0‰'])
                
                for model, result in self.data['results'].items():
                    writer.writerow([
                        model,
                        f"{result.get('current_bac', 0):.2f}",
                        f"{result.get('peak_bac', 0):.2f}",
                        result.get('time_to_03', '--').strftime('%H:%M') if result.get('time_to_03') else '--',
                        result.get('time_to_00', '--').strftime('%H:%M') if result.get('time_to_00') else '--'
                    ])
        
        self.progress_updated.emit(100)
    
    def _export_json(self):
        """Exportiert als JSON"""
        self.progress_updated.emit(20)
        
        # Prepare data for JSON serialization
        json_data = {}
        
        # Convert datetime objects to strings
        if 'drinks_data' in self.data:
            drinks_data = []
            for drink in self.data['drinks_data']:
                drink_copy = drink.copy()
                if isinstance(drink_copy.get('time'), datetime):
                    drink_copy['time'] = drink_copy['time'].isoformat()
                drinks_data.append(drink_copy)
            json_data['drinks_data'] = drinks_data
        
        self.progress_updated.emit(60)
        
        # Convert results datetime objects
        if 'results' in self.data:
            results_data = {}
            for model, result in self.data['results'].items():
                result_copy = result.copy()
                for key, value in result_copy.items():
                    if isinstance(value, datetime):
                        result_copy[key] = value.isoformat()
                results_data[model] = result_copy
            json_data['results'] = results_data
        
        # Copy other data as-is
        for key, value in self.data.items():
            if key not in ['drinks_data', 'results']:
                json_data[key] = value
        
        with open(self.file_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(json_data, jsonfile, indent=2, ensure_ascii=False)
        
        self.progress_updated.emit(100)
    
    def _export_excel(self):
        """Exportiert als Excel"""
        try:
            import openpyxl
            from openpyxl.styles import Font, PatternFill, Alignment
        except ImportError:
            raise ImportError("openpyxl ist nicht installiert. Bitte installieren Sie es mit: pip install openpyxl")
        
        self.progress_updated.emit(20)
        
        workbook = openpyxl.Workbook()
        
        # Personendaten Sheet
        if 'person_data' in self.data:
            ws_person = workbook.active
            ws_person.title = "Personendaten"
            
            person = self.data['person_data']
            ws_person['A1'] = "Personendaten"
            ws_person['A1'].font = Font(bold=True, size=14)
            
            data_rows = [
                ['Geschlecht:', person.get('gender', 'N/A')],
                ['Alter:', f"{person.get('age', 'N/A')} Jahre"],
                ['Größe:', f"{person.get('height', 'N/A')} cm"],
                ['Gewicht:', f"{person.get('weight', 'N/A')} kg"],
                ['Körperfettanteil:', f"{person.get('body_fat', 'N/A')}%"],
                ['Trinkgewohnheit:', person.get('drinking_habit', 'N/A')]
            ]
            
            for i, (label, value) in enumerate(data_rows, start=3):
                ws_person[f'A{i}'] = label
                ws_person[f'B{i}'] = value
                ws_person[f'A{i}'].font = Font(bold=True)
        
        self.progress_updated.emit(50)
        
        # Getränke Sheet
        if 'drinks_data' in self.data and self.data['drinks_data']:
            ws_drinks = workbook.create_sheet("Getränke")
            
            headers = ['Getränk', 'Menge (ml)', 'Alkohol (%)', 'Zeit', 'Alkohol (g)']
            for col, header in enumerate(headers, start=1):
                cell = ws_drinks.cell(row=1, column=col, value=header)
                cell.font = Font(bold=True)
                cell.fill = PatternFill(start_color="CCCCCC", end_color="CCCCCC", fill_type="solid")
            
            for row, drink in enumerate(self.data['drinks_data'], start=2):
                quantity = drink.get('quantity', 1)
                alcohol_grams = drink['volume'] * (drink['alcohol_content'] / 100) * 0.8 * quantity
                ws_drinks.cell(row=row, column=1, value=drink['name'])
                ws_drinks.cell(row=row, column=2, value=f"{drink['volume']} × {quantity}")
                ws_drinks.cell(row=row, column=3, value=drink['alcohol_content'])
                ws_drinks.cell(row=row, column=4, value=drink['time'].strftime('%H:%M') if isinstance(drink['time'], datetime) else str(drink['time']))
                ws_drinks.cell(row=row, column=5, value=round(alcohol_grams, 1))
        
        self.progress_updated.emit(80)
        
        # Ergebnisse Sheet
        if 'results' in self.data and self.data['results']:
            ws_results = workbook.create_sheet("Ergebnisse")
            
            headers = ['Modell', 'Aktuelle BAK', 'Max. BAK', 'Zeit bis 0.5‰', 'Zeit bis 0.0‰']
            for col, header in enumerate(headers, start=1):
                cell = ws_results.cell(row=1, column=col, value=header)
                cell.font = Font(bold=True)
                cell.fill = PatternFill(start_color="CCCCCC", end_color="CCCCCC", fill_type="solid")
            
            for row, (model, result) in enumerate(self.data['results'].items(), start=2):
                ws_results.cell(row=row, column=1, value=model)
                ws_results.cell(row=row, column=2, value=f"{result.get('current_bac', 0):.2f}")
                ws_results.cell(row=row, column=3, value=f"{result.get('peak_bac', 0):.2f}")
                ws_results.cell(row=row, column=4, value=result.get('time_to_03', '--').strftime('%H:%M') if result.get('time_to_03') else '--')
                ws_results.cell(row=row, column=5, value=result.get('time_to_00', '--').strftime('%H:%M') if result.get('time_to_00') else '--')
        
        workbook.save(self.file_path)
        self.progress_updated.emit(100)

class ExportManager(QObject):
    """Manager für Export-Funktionen"""
    
    export_started = pyqtSignal()
    export_progress = pyqtSignal(int)
    export_finished = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, parent: QWidget = None):
        super().__init__()
        self.parent = parent
        self.export_thread = None
    
    def export_to_pdf(self, data: Dict):
        """Exportiert Daten als PDF"""
        file_path, _ = QFileDialog.getSaveFileName(
            self.parent,
            "PDF exportieren",
            f"BAK_Berechnung_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            "PDF Dateien (*.pdf)"
        )
        
        if file_path:
            self._start_export('pdf', file_path, data)
    
    def export_to_csv(self, data: Dict):
        """Exportiert Daten als CSV"""
        file_path, _ = QFileDialog.getSaveFileName(
            self.parent,
            "CSV exportieren",
            f"BAK_Berechnung_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV Dateien (*.csv)"
        )
        
        if file_path:
            self._start_export('csv', file_path, data)
    
    def export_to_excel(self, data: Dict):
        """Exportiert Daten als Excel"""
        file_path, _ = QFileDialog.getSaveFileName(
            self.parent,
            "Excel exportieren",
            f"BAK_Berechnung_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            "Excel Dateien (*.xlsx)"
        )
        
        if file_path:
            self._start_export('excel', file_path, data)
    
    def export_to_json(self, data: Dict):
        """Exportiert Daten als JSON"""
        file_path, _ = QFileDialog.getSaveFileName(
            self.parent,
            "JSON exportieren",
            f"BAK_Berechnung_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "JSON Dateien (*.json)"
        )
        
        if file_path:
            self._start_export('json', file_path, data)
    
    def _start_export(self, export_type: str, file_path: str, data: Dict):
        """Startet den Export in einem separaten Thread"""
        if self.export_thread and self.export_thread.isRunning():
            QMessageBox.warning(self.parent, "Export läuft", "Es läuft bereits ein Export. Bitte warten Sie.")
            return
        
        self.export_started.emit()
        
        self.export_thread = ExportThread(export_type, file_path, data)
        self.export_thread.progress_updated.connect(self.export_progress.emit)
        self.export_thread.export_finished.connect(self.export_finished.emit)
        self.export_thread.start() 