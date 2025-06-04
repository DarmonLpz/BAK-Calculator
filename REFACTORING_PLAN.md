# BAK-Calculator Refactoring Plan

## 🎯 Priorität 1: Kritische Verbesserungen (sofort)

### 1. Architektur aufteilen
```
bak_calculator/
├── main.py                 # Entry point
├── models/                 # Data models
│   ├── __init__.py
│   ├── person.py
│   ├── drink.py
│   └── settings.py
├── controllers/            # Business logic
│   ├── __init__.py
│   ├── calculation_controller.py  ✅ ERSTELLT
│   └── data_controller.py
├── ui/                     # User interface
│   ├── __init__.py
│   ├── main_window.py
│   ├── components/         # Reusable widgets
│   │   ├── __init__.py
│   │   ├── person_widget.py  ✅ ERSTELLT
│   │   ├── drinks_widget.py
│   │   └── results_widget.py
│   └── styles/
│       ├── __init__.py
│       └── theme_manager.py  ✅ ERSTELLT
├── utils/                  # Utilities
│   ├── __init__.py
│   ├── export_manager.py    ✅ ERSTELLT
│   ├── validation.py
│   └── database.py
└── resources/              # Assets
    ├── icons/
    ├── fonts/
    └── themes/
```

### 2. Design-Modus entfernen
- **Problem**: 500+ Zeilen für Widget-Positionierung
- **Lösung**: Standard Qt-Layouts verwenden
- **Geschätzter Aufwand**: 2 Stunden

### 3. Calculate-Methode optimieren
- **Problem**: 200+ Zeilen, wird zu oft aufgerufen
- **Lösung**: CalculationController verwenden ✅
- **Features**: Debouncing, Caching, Threading

## 🎨 Priorität 2: UI/UX-Verbesserungen (diese Woche)

### 1. Theme-System implementieren ✅
- Zentraler ThemeManager 
- Light/Dark/Auto Themes
- Konsistente Farben und Fonts

### 2. Komponentenbasierte UI
```python
# Statt 500 Zeilen in __init__:
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        self.person_widget = PersonDataWidget()
        self.drinks_widget = DrinksWidget()  
        self.results_widget = ResultsWidget()
        # ... Layout setup
```

### 3. Bessere Validierung
```python
class DataValidator:
    @staticmethod
    def validate_person(person_data):
        errors = []
        if person_data.age < 18:
            errors.append("Alter muss mindestens 18 Jahre betragen")
        return errors
```

## 📊 Priorität 3: Features & Funktionalität (nächste Woche)

### 1. Export-System implementieren ✅
- PDF-Reports mit Diagrammen
- CSV/Excel für Datenanalyse
- JSON für Datenarchivierung

### 2. Persistente Getränkedatenbank
```python
class DrinkDatabase:
    def __init__(self, db_path="drinks.db"):
        self.db = sqlite3.connect(db_path)
        self.create_tables()
    
    def add_drink(self, name, alcohol_content, volume):
        # SQLite implementation
    
    def get_drinks_by_category(self, category):
        # Return drinks from database
```

### 3. Bessere Datenvalidierung
- Eingabe-Validierung in Echtzeit
- Plausibilitätsprüfungen
- Benutzerfreundliche Fehlermeldungen

## 🚀 Priorität 4: Erweiterte Features (später)

### 1. Mehrsprachigkeit
```python
class LanguageManager:
    def __init__(self):
        self.load_translations()
    
    def tr(self, key):
        return self.translations.get(key, key)
```

### 2. Datenvisualisierung verbessern
- Interaktive Diagramme
- Mehrere Zeitachsen
- Vergleichsmodus

### 3. Erweiterte BAK-Modelle
- Zusätzliche wissenschaftliche Modelle
- Kalibrierung basierend auf Messwerten
- Unsicherheitsbänder

## 🔧 Implementierungsreihenfolge

### Woche 1: Grundlegende Architektur
1. ✅ CalculationController erstellen
2. ✅ PersonDataWidget erstellen  
3. ✅ ThemeManager erstellen
4. ✅ ExportManager erstellen
5. ⏳ Design-Modus entfernen
6. ⏳ UI in Komponenten aufteilen

### Woche 2: UI-Verbesserungen
1. Bessere Validierung
2. Fehlerbehandlung verbessern
3. Performance optimieren
4. Testing implementieren

### Woche 3: Features & Polish
1. Getränkedatenbank
2. Export-Funktionen finalisieren
3. Dokumentation
4. Bug-Fixes

## 📋 Sofortige TODOs

### Heute:
- [ ] ui_main.py aufteilen in Komponenten
- [ ] Design-Modus Code entfernen
- [ ] Neue Controller integrieren

### Diese Woche:
- [ ] Vollständige Validierung implementieren
- [ ] Error-Handling verbessern
- [ ] Tests schreiben
- [ ] Performance messen und optimieren

### Geschätzte Zeitersparnis nach Refactoring:
- **Entwicklungszeit**: -60% (modularer Code)
- **Bug-Fixing**: -70% (bessere Trennung)
- **Neue Features**: -50% (wiederverwendbare Komponenten)
- **Performance**: +200% (Caching, Threading)

## 🎯 Erfolgsmessung

### Vorher:
- 2335 Zeilen in einer Datei
- calculate() bei jeder Änderung
- Hardcodierte Getränke
- Kein Export
- Inkonsistente UI

### Nachher:
- Modulare Architektur
- Optimierte Berechnungen
- Persistente Datenbank
- Vollständige Export-Funktionen
- Einheitliches Design-System 