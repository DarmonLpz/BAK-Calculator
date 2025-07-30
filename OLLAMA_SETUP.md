# 🔍 Ollama-Integration für Protokoll-Analyse

## Übersicht

Die BAK-Calculator v2.0 unterstützt jetzt **KI-gestützte Protokoll-Analyse** mit Ollama. Diese Funktion ermöglicht es, Trinkprotokolle aus Gerichtsakten, Polizeiberichten oder anderen Dokumenten automatisch zu analysieren und in die Getränke-Tabelle zu übertragen.

## 🚀 Installation von Ollama

### Windows
1. Besuchen Sie [ollama.ai](https://ollama.ai)
2. Laden Sie den Windows-Installer herunter
3. Führen Sie die Installation aus
4. Starten Sie Ollama über das Startmenü oder die Kommandozeile

### macOS
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

### Linux
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

## 📥 Modell herunterladen

Nach der Installation laden Sie ein geeignetes Modell herunter:

```bash
# Empfohlenes Modell (deutsch, gut für strukturierte Ausgaben)
ollama pull llama3.1:8b

# Alternative Modelle
ollama pull mistral:7b
ollama pull phi3:mini
```

## 🔧 Konfiguration

### Standard-Konfiguration
Die Anwendung ist standardmäßig für folgende Einstellungen konfiguriert:
- **URL**: `http://localhost:11434`
- **Modell**: `llama3.1:8b`
- **Timeout**: 30 Sekunden

### Anpassung der Einstellungen
Falls Sie andere Einstellungen verwenden möchten, können Sie diese in `utils/ollama_analyzer.py` anpassen:

```python
class OllamaAnalyzer:
    def __init__(self, model_name: str = "llama3.1:8b", base_url: str = "http://localhost:11434"):
        self.model = model_name
        self.base_url = base_url
        self.timeout = 30
```

## 🎯 Verwendung

### 1. Ollama starten
Stellen Sie sicher, dass Ollama läuft:
```bash
ollama serve
```

### 2. Protokoll-Analyse öffnen
1. Starten Sie die BAK-Calculator Anwendung
2. Klicken Sie auf den Tab **"🔍 Explorations-Eingabe"**

### 3. Text eingeben
- Fügen Sie das Trinkprotokoll in das Textfeld ein
- Oder klicken Sie auf **"Beispiel laden"** für ein Demo-Protokoll

### 4. Analyse starten
- Klicken Sie auf **"🔍 Mit Ollama analysieren"**
- Die Analyse läuft im Hintergrund und zeigt den Fortschritt an

### 5. Ergebnisse überprüfen
- Die Vorschau zeigt die extrahierten Daten
- Überprüfen Sie Datum, Zeiten, Getränke und Mengen

### 6. In App übertragen
- Klicken Sie auf **"📋 In App übertragen"**
- Die Daten werden automatisch in die Getränke-Tabelle übernommen

## 📋 Unterstützte Protokoll-Formate

### Gerichtsprotokolle
```
21.05.2024, 17:43 Uhr: Fahrlässigen Trunkenheit im Verkehr mit dem Fahrrad, 
(Blutalkoholgehalt mindestens 2,12 Promille zum Entnahmezeitpunkt 18:18 Uhr)

Wie kam es zur Tat?
"An dem Tag hatte meine Tochter Geburtstag und um 13:00 Uhr waren die ersten Gäste geladen. 
Ich habe dann ab 13:00 Uhr angefangen Alkohol zu trinken und bis ca. 17:30 Uhr 
insgesamt neun Bier (0,5 l) getrunken."
```

### Polizeiberichte
```
Zeitpunkt der Blutentnahme: 18:18 Uhr
Gemessener BAK: 2,12 Promille

Konsumzeitraum: 13:00 - 17:30 Uhr
Getränke: 9 Bier à 0,5 Liter
```

### Selbstauskünfte
```
Ich habe von 13:00 bis 17:30 Uhr getrunken:
- 9 Bier (500ml, 4,8%)
- 2 Gläser Wein (200ml, 12%)
Blutentnahme war um 18:18 Uhr mit 2,12 Promille.
```

## 🔍 Automatische Erkennung

Die KI erkennt automatisch:

### ✅ Datum und Zeiten
- Konsumbeginn und -ende
- Blutentnahme-Zeitpunkt
- Verschiedene Datumsformate

### ✅ Getränke und Mengen
- Getränketypen (Bier, Wein, Spirituosen)
- Volumen (ml, Liter)
- Anzahl der Getränke
- Alkoholgehalt (falls angegeben)

### ✅ BAK-Werte
- Gemessene Blutalkoholkonzentration
- Verschiedene Einheiten (Promille, %)

### ✅ Standardwerte
Bei unklaren Angaben werden Standardwerte verwendet:
- **Bier**: 4.8% Alkohol, 500ml
- **Wein**: 12% Alkohol, 200ml  
- **Spirituosen**: 40% Alkohol, 40ml

## ⚠️ Fehlerbehebung

### Ollama nicht erreichbar
```
Fehler: Ollama ist nicht erreichbar
```
**Lösung:**
1. Prüfen Sie, ob Ollama läuft: `ollama list`
2. Starten Sie Ollama: `ollama serve`
3. Prüfen Sie die URL: `http://localhost:11434`

### Modell nicht gefunden
```
Fehler: Modell nicht verfügbar
```
**Lösung:**
1. Laden Sie das Modell herunter: `ollama pull llama3.1:8b`
2. Prüfen Sie verfügbare Modelle: `ollama list`

### Analyse fehlgeschlagen
```
Fehler: Analyse fehlgeschlagen
```
**Lösung:**
1. Überprüfen Sie den Text auf Vollständigkeit
2. Stellen Sie sicher, dass Datum und Zeiten enthalten sind
3. Versuchen Sie es mit einem anderen Modell

## 🔧 Erweiterte Konfiguration

### Eigene Prompts
Sie können die Prompts in `utils/ollama_analyzer.py` anpassen:

```python
self.system_prompt = """Ihr eigener Prompt hier..."""
```

### Verschiedene Modelle
Testen Sie verschiedene Modelle für bessere Ergebnisse:

```python
# Für deutsche Texte
analyzer = OllamaAnalyzer(model_name="llama3.1:8b")

# Für schnelle Analysen
analyzer = OllamaAnalyzer(model_name="phi3:mini")

# Für komplexe Protokolle
analyzer = OllamaAnalyzer(model_name="mistral:7b")
```

## 📊 Performance-Tipps

### Optimale Modell-Größe
- **8B Modelle**: Gute Balance zwischen Geschwindigkeit und Genauigkeit
- **7B Modelle**: Schneller, ausreichend für einfache Protokolle
- **Mini Modelle**: Sehr schnell, für einfache Fälle geeignet

### Hardware-Anforderungen
- **Minimum**: 8GB RAM, 4GB VRAM
- **Empfohlen**: 16GB RAM, 8GB VRAM
- **Optimal**: 32GB RAM, 16GB VRAM

## 🔒 Datenschutz

### Lokale Verarbeitung
- Alle Analysen laufen **lokal** auf Ihrem Computer
- **Keine Daten** werden an externe Server gesendet
- **Vollständige Kontrolle** über Ihre Daten

### Keine Speicherung
- Analysierte Protokolle werden **nicht gespeichert**
- Nur die extrahierten Getränke-Daten werden übertragen
- **Vollständige Anonymität** gewährleistet

## 🆘 Support

Bei Problemen mit der Ollama-Integration:

1. **Prüfen Sie die Ollama-Dokumentation**: [ollama.ai/docs](https://ollama.ai/docs)
2. **Testen Sie Ollama direkt**: `ollama run llama3.1:8b`
3. **Überprüfen Sie die Logs**: Schauen Sie in die Konsole für Fehlermeldungen
4. **Kontaktieren Sie den Support**: Bei spezifischen Problemen

---

**Hinweis**: Die KI-gestützte Analyse ist ein Hilfsmittel und ersetzt nicht die fachliche Überprüfung der Ergebnisse. Bitte überprüfen Sie alle extrahierten Daten vor der Verwendung in rechtlichen oder medizinischen Kontexten. 