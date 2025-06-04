# BAK-Kalkulator - Änderungsprotokoll

## Version 1.3.0 - Forensisches Validierungsmodul (2024-12-XX)

### 🔬 Neue Funktionen
- **BAK-Controller Tab**: Neues Register für forensische Validierung von Konsumangaben
  - Eingabe von gemessenen BAK-Werten (Datum, Uhrzeit, Konzentration)
  - Auswahl der Analysemethode (GC-FID, Enzymatisch, Headspace-GC, LC-MS/MS)
  - Automatische Interpolation der berechneten BAK zum Messzeitpunkt
  - Konfidenzintervall-Analyse (95% und 99% CI)
  - Wissenschaftlich nachvollziehbare Plausibilitätsbewertung

- **Editierbare Getränke-Tabelle**: Direkte Bearbeitung aller Werte in der Tabelle
  - Doppelklick auf Zellen zur Bearbeitung von Name, Menge, Alkoholgehalt, Datum, Zeit
  - Intelligente Datenvalidierung mit Fehlermeldungen
  - Automatische Neuberechnung bei Änderungen
  - Tooltips mit Formatierungshinweisen

- **Einzelgetränk-Pharmakodynamik**: Realistische Simulation individueller Abbauprozesse
  - Separate Resorptions- und Eliminationskurven pro Getränk
  - Alkoholmengen-abhängige Resorptionszeiten (30-60 Minuten)
  - Superposition aller Einzelkurven zur Gesamtkurve
  - Detaillierte Einzelgetränk-Analyse in der Dokumentation

### 🧮 Wissenschaftliche Verbesserungen
- **Multi-Modell-Validierung**: Vergleich aller vier BAK-Modelle gegen gemessene Werte
- **Unsicherheitsanalyse**: Berücksichtigung analytischer und modellspezifischer Unsicherheiten
- **Konfidenzintervalle**: Statistische Bewertung mit 95% und 99% Sicherheit
- **Forensische Interpretation**: Automatische Bewertung als "plausibel", "grenzwertig" oder "falsch"
- **Realistische Pharmakodynamik**: First-Order-Kinetik mit individuellen Absorptionsmustern

### 📊 Technische Details
- **Interpolation**: Lineare Interpolation zwischen BAK-Datenpunkten
- **Extrapolation**: Erweiterte Berechnung außerhalb des Messzeitraums
- **Messunsicherheit**: Methodenspezifische Analytik-Toleranzen
- **Modell-Variabilität**: Inter-individuelle pharmakokinetische Unterschiede
- **Einzelgetränk-Tracking**: Separate Berechnung mit zeitlicher Summation

### 🔬 Qualitätssicherung
- **Standards**: ISO/IEC 17025, SOFT Guidelines, GTFCh Richtlinien
- **Wissenschaftliche Referenzen**: 15+ publizierte Studien verlinkt
- **Forensische Compliance**: Gerichtsfeste wissenschaftliche Dokumentation
- **Datenvalidierung**: Umfassende Eingabeprüfung mit Benutzerführung

---

## Version 1.2.1 - Layout-Optimierung (2024-12-XX)

### 🎨 UI-Verbesserungen  
- **Verbesserte Dialog-Größen**: AddDrinkDialog auf 450×400px vergrößert
- **Optimierte Abstände**: Konsistente 15px Gruppenabstände, 10px Elementabstände  
- **Erhöhte Element-Mindesthöhen**: Alle Eingabefelder auf 35px Mindesthöhe
- **Erweiterte Ränder**: 20px Außenränder für bessere Lesbarkeit
- **Konsistente Label-Breiten**: 120px für einheitliches Erscheinungsbild

### 🔧 Button-Styling
- **Deutsche Beschriftung**: "Hinzufügen"/"Abbrechen" statt englischer Begriffe
- **Hover-Effekte**: Verbesserte visuelle Rückmeldung bei Maus-Hover
- **Moderne Farbgebung**: Professionelles Blau/Grau-Schema

---

## Version 1.2.0 - Erweiterte Funktionalität (2024-12-XX)

### 🆕 Neue Funktionen
- **Datum-Funktionalität**: Vollständige Datum- und Uhrzeiteingabe für Getränke
  - QDateEdit-Widget mit deutschem Format (dd.MM.yyyy)
  - Kalender-Popup für einfache Datumsauswahl
  - Getrennte Anzeige von Datum und Zeit in der Tabelle
  - Korrekte Zeitspannen-Berechnung über mehrere Tage

- **Prominente Alkoholsumme**: Großer, stilisierter Display direkt unter der Getränkeliste
  - Blaues Design mit Rahmen und Hintergrund
  - Echtzeit-Aktualisierung bei Änderungen
  - Wissenschaftlicher Tooltip mit Berechnungsformel

### 🔧 Technische Verbesserungen
- **Verbesserte Zeitberechnungen**: Korrekte Handhabung von Datum/Zeit-Kombinationen
- **Erweiterte Tooltips**: Forensische Relevanz der Datums-Dokumentation erklärt
- **Optimierte Datenstrukturen**: Effiziente datetime-Objekt-Verwendung

### 📊 Chart-Verbesserungen  
- **Debug-Ausgaben**: Umfassende Konsolen-Logs für Fehlerdiagnose
- **Robuste Datenvalidierung**: Verbesserte Fehlerbehandlung
- **Erweiterte Interpolation**: Präzise BAK-Kurven über Zeiträume
- **Optimierte Skalierung**: Automatische Y-Achsen-Anpassung mit 15% Puffer

### 🧮 Berechnungs-Fixes
- **Realistische Zeitberechnung**: Basierend auf tatsächlichen Getränke-Zeitstempeln  
- **Korrekte Resorptionszeit**: 30 Min nach letztem Getränk + Verteilungsdauer
- **Präzise Elimination**: Echte Zeit seit erstem Getränk statt fester Annahmen
- **Verbesserte Peak-Zeiten**: Realistische Maximums-Berechnung

---

## Version 1.1.0 - Grundversion (2024-11-XX)

### 🚀 Kernfunktionen
- **Vier BAK-Modelle**: Widmark, Watson, Forrest, Seidl
- **Umfangreiche Getränke-Datenbank**: 50+ vordefinierte Getränke
- **Moderne PyQt6-Oberfläche**: Professionelles Design mit Inter-Font
- **Wissenschaftliche Tooltips**: 50+ verlinkte Forschungsarbeiten
- **Export-Funktionen**: PDF, CSV, Excel-Export
- **Echtzeit-Berechnungen**: Automatische Updates bei Datenänderungen

### 📈 Visualisierung  
- **BAK-Verlaufsdiagramm**: Matplotlib-Integration
- **Rechtliche Grenzwerte**: Visuelle Markierung bei 0.3‰, 0.5‰, 1.1‰
- **Multi-Modell-Anzeige**: Vergleichbare Darstellung aller Berechnungen

### 🔬 Wissenschaftlicher Standard
- **Internationale Referenzen**: Über 50 verlinkte Studien
- **Forensische Compliance**: Nach ISO/IEC 17025, SOFT, GTFCh
- **Deutsche Lokalisierung**: Vollständig deutschsprachige Benutzeroberfläche 