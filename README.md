# BAK Rechner

Ein wissenschaftlicher Blutalkohol-Kalkulator mit moderner PyQt6-GUI.

## Features

- Moderne, benutzerfreundliche Oberfläche
- **🤖 KI-Analyse von Explorationstexten**: Freitext einfügen → Claude filtert
  Getränke, Personendaten und den gemessenen BAK-Wert heraus, übernimmt sie
  automatisch und prüft die Plausibilität gegen den Messwert
- Verschiedene BAK-Berechnungsmodelle (Widmark, Watson, Forrest, Seidl)
- Berücksichtigung von Personendaten (Geschlecht, Alter, Größe, Gewicht)
- Getränkedatenbank mit vordefinierten Getränken
- Forensischer Plausibilitätsabgleich gegen gemessene Blutalkoholwerte
- Detaillierte BAK-Zeitverläufe und verständliche Auswertung
- Exportmöglichkeiten (schicke PDF, CSV, Excel)

## KI-Analyse einrichten

Die KI-Funktion nutzt die Anthropic-API (Modell Claude Opus 4.8). Dafür wird
ein API-Schlüssel benötigt:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

Ohne Schlüssel bleibt der Rechner voll nutzbar; nur der Tab „KI-Analyse" ist
dann deaktiviert und weist auf den fehlenden Schlüssel hin.

## Installation

1. Klonen Sie das Repository:
```bash
git clone https://github.com/ihr-username/bak-calculator.git
cd bak-calculator
```

2. Installieren Sie die Abhängigkeiten:
```bash
pip install -r requirements.txt
```

## Verwendung

Starten Sie die Anwendung mit:
```bash
python main.py
```

## Berechnungsmodelle

Die Anwendung unterstützt verschiedene wissenschaftliche Modelle zur BAK-Berechnung:

- **Widmark**: Klassisches Modell mit Verteilungsfaktor r
- **Watson**: Berücksichtigt Körperwasseranteil
- **Forrest**: Modifiziertes Widmark-Modell
- **Seidl**: Erweitertes Modell mit zusätzlichen Parametern

## Lizenz

MIT License 