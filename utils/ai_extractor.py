"""
KI-gestützte Extraktion von Konsumangaben aus Freitext (Explorationstext).

Ein Sachverständiger fügt die Schilderung des Trinkverhaltens an einem
Delikttag ein. Diese Komponente schickt den Text an Claude (Anthropic API)
und lässt die enthaltenen Angaben strukturiert herausfiltern:

* konsumierte Getränke (Art, Menge, Alkoholgehalt, Uhrzeit)
* Personendaten (sofern genannt: Geschlecht, Alter, Größe, Gewicht)
* die gemessene Blutalkoholkonzentration samt Entnahmezeitpunkt und Methode

Das Ergebnis wird in das vom Rechner erwartete Format normalisiert, sodass es
direkt in die Berechnung und den anschließenden Plausibilitätsabgleich gegen
den Messwert übernommen werden kann.

Hinweis: Es wird das offizielle Anthropic-SDK verwendet. Der API-Schlüssel
wird aus der Umgebungsvariablen ANTHROPIC_API_KEY gelesen.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

# Bevorzugtes Modell (gemäß Anthropic-Empfehlung das leistungsstärkste Opus).
MODEL = "claude-opus-4-8"

# Abhängigkeiten optional importieren, damit der Rechner auch ohne installiertes
# anthropic-/pydantic-Paket startet (die KI-Funktion ist dann nur deaktiviert).
try:
    import anthropic
    from pydantic import BaseModel, Field
    from typing import Literal
    AI_IMPORT_OK = True
except Exception:  # pragma: no cover - Importfehler nur ohne Paket
    AI_IMPORT_OK = False


# ---------------------------------------------------------------------------
# Strukturschema für die Extraktion (Structured Outputs)
# ---------------------------------------------------------------------------
if AI_IMPORT_OK:

    class PersonInfo(BaseModel):
        gender: Optional[Literal["männlich", "weiblich"]] = Field(
            None, description="Geschlecht, falls genannt")
        age: Optional[int] = Field(None, description="Alter in Jahren")
        height_cm: Optional[int] = Field(None, description="Körpergröße in cm")
        weight_kg: Optional[float] = Field(None, description="Körpergewicht in kg")
        drinking_habit: Optional[
            Literal["Abstinent", "Gelegentlich", "Regelmäßig", "Täglich"]
        ] = Field(None, description="Trinkgewohnheit, falls erkennbar")

    class DrinkInfo(BaseModel):
        name: str = Field(description="Bezeichnung des Getränks, z. B. 'Bier (Pils)'")
        volume_ml: float = Field(description="Menge EINES Getränks in Millilitern")
        alcohol_percent: float = Field(description="Alkoholgehalt in Volumenprozent")
        count: int = Field(1, description="Anzahl gleichartiger Getränke")
        datetime_iso: Optional[str] = Field(
            None,
            description=("Konsumzeitpunkt als ISO-8601 (YYYY-MM-DDTHH:MM). "
                         "Wenn nur eine Uhrzeit bekannt ist, trotzdem mit dem "
                         "Referenzdatum als vollständiges ISO-Datum angeben."))

    class Measurement(BaseModel):
        bac_per_mille: Optional[float] = Field(
            None, description="Gemessene BAK in Promille (‰)")
        datetime_iso: Optional[str] = Field(
            None, description="Entnahmezeitpunkt der Blutprobe als ISO-8601")
        method: Optional[str] = Field(
            None, description="Analysemethode, falls genannt (z. B. GC-FID)")

    class Extraction(BaseModel):
        person: PersonInfo
        drinks: List[DrinkInfo]
        measurement: Measurement
        summary: str = Field(
            description=("Kurze deutsche Zusammenfassung der getroffenen Annahmen "
                         "(z. B. angenommene Alkoholgehalte oder Mengen)."))


# ---------------------------------------------------------------------------
# Der "Prompt" für die Textanalyse
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """\
Du bist ein forensisch-toxikologischer Assistent. Deine Aufgabe ist es, aus \
einer frei formulierten Schilderung (Exploration) eines Beschuldigten/Probanden \
zum Alkoholkonsum an einem bestimmten Tag ALLE relevanten Angaben präzise und \
strukturiert herauszufiltern. Diese Angaben werden anschließend für eine \
Blutalkohol-Berechnung und einen Plausibilitätsabgleich gegen einen gemessenen \
Blutalkoholwert verwendet.

Gehe sorgfältig und konservativ vor:

1. GETRÄNKE: Erfasse jedes alkoholische Getränk mit Art, Menge (ml für EIN \
   Getränk), Alkoholgehalt (Vol.-%) und Konsumzeitpunkt. Mehrere gleichartige \
   Getränke fasst du über das Feld "count" zusammen.
   - Übliche deutsche Maße: Maß Bier = 1000 ml, Halbe = 500 ml, \
     Glas/Pils = 300-500 ml, Glas Wein = 200 ml, Flasche Wein = 750 ml, \
     Sekt/Prosecco = 100 ml, Schnaps/Kurzer/Shot = 20-40 ml, Likör = 40 ml, \
     Cocktail = 200-300 ml.
   - Typische Alkoholgehalte, wenn nicht genannt: Bier 5 %, Weizen 5,4 %, \
     Wein 12 %, Sekt 11 %, Spirituosen 40 %, Likör 20 %. Solche Standardwerte \
     darfst du einsetzen und erwähnst sie in der Zusammenfassung.
   - Bei vagen Angaben ("ein paar", "einige") wähle eine plausible, eher \
     niedrige Anzahl und vermerke die Annahme.

2. PERSONENDATEN: Erfasse Geschlecht, Alter, Größe und Gewicht NUR wenn genannt. \
   Sonst null.

3. MESSWERT: Erfasse die gemessene Blutalkoholkonzentration (in ‰), den \
   Entnahmezeitpunkt der Blutprobe und die Analysemethode, falls im Text \
   enthalten. Sonst null.

4. ZEITEN: Wenn ein konkretes Datum fehlt, verwende als Referenzdatum {today}. \
   Gib Zeitpunkte immer als vollständiges ISO-8601 (YYYY-MM-DDTHH:MM) an. \
   Achte auf die zeitliche Reihenfolge: Konsum liegt vor der Blutentnahme; bei \
   Konsum über Mitternacht ggf. den Folgetag verwenden.

5. ERFINDE NICHTS. Was nicht aus dem Text hervorgeht und nicht über die oben \
   genannten Standardwerte sinnvoll ergänzbar ist, bleibt null. Halte in \
   "summary" kurz und auf Deutsch fest, welche Annahmen du getroffen hast.
"""


# ---------------------------------------------------------------------------
# Verfügbarkeit
# ---------------------------------------------------------------------------
def ai_status() -> Tuple[bool, str]:
    """Prüft, ob die KI-Analyse einsatzbereit ist.

    Rückgabe: (verfügbar, Hinweistext)
    """
    if not AI_IMPORT_OK:
        return False, ("Das Paket 'anthropic' ist nicht installiert. "
                       "Installieren Sie es mit: pip install anthropic")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return False, ("Kein API-Schlüssel gefunden. Setzen Sie die "
                       "Umgebungsvariable ANTHROPIC_API_KEY mit Ihrem "
                       "Anthropic-API-Schlüssel.")
    return True, f"Bereit (Modell: {MODEL})"


# ---------------------------------------------------------------------------
# Hauptfunktion (blockierend – im Hintergrund-Thread aufrufen)
# ---------------------------------------------------------------------------
def run_extraction(text: str, reference_date: Optional[datetime] = None) -> dict:
    """Extrahiert Konsumangaben aus Freitext und normalisiert sie.

    Wirft eine Exception bei Fehlern (fehlendes Paket/Key, API-Fehler,
    Verweigerung). Der Aufrufer fängt diese ab.
    """
    ok, msg = ai_status()
    if not ok:
        raise RuntimeError(msg)

    if not text or not text.strip():
        raise ValueError("Bitte geben Sie einen Text zur Analyse ein.")

    ref = reference_date or datetime.now()
    client = anthropic.Anthropic()

    response = client.messages.parse(
        model=MODEL,
        max_tokens=4096,
        system=SYSTEM_PROMPT.format(today=ref.strftime("%Y-%m-%d")),
        messages=[{"role": "user", "content": text}],
        output_format=Extraction,
    )

    if response.stop_reason == "refusal":
        raise RuntimeError("Die Analyse wurde vom Modell aus Sicherheitsgründen "
                           "abgelehnt.")

    extraction: "Extraction" = response.parsed_output
    if extraction is None:
        raise RuntimeError("Es konnten keine strukturierten Daten extrahiert werden.")

    return _normalize(extraction, ref)


# ---------------------------------------------------------------------------
# Normalisierung -> vom Rechner erwartetes Format
# ---------------------------------------------------------------------------
def _normalize(extraction, reference_date: datetime) -> dict:
    # Referenzdatum für Getränke ohne Datum: Messdatum, sonst übergebenes Datum
    measure_dt = _parse_dt(extraction.measurement.datetime_iso, reference_date)
    drink_ref = measure_dt or reference_date

    # ---- Personendaten ----
    person = {}
    p = extraction.person
    if p.gender:
        person["gender"] = "Männlich" if p.gender == "männlich" else "Weiblich"
    if p.age:
        person["age"] = int(p.age)
    if p.height_cm:
        person["height"] = int(p.height_cm)
    if p.weight_kg:
        person["weight"] = float(p.weight_kg)
    if p.drinking_habit:
        person["drinking_habit"] = p.drinking_habit

    # ---- Getränke (count expandieren) ----
    drinks = []
    for d in extraction.drinks:
        dt = _parse_dt(d.datetime_iso, drink_ref)
        if dt is None:
            # Ohne Zeitangabe: auf 20:00 des Referenztages setzen (editierbar)
            dt = drink_ref.replace(hour=20, minute=0, second=0, microsecond=0)
        count = max(1, int(d.count or 1))
        for i in range(count):
            drinks.append({
                "name": d.name,
                "volume": float(d.volume_ml),
                "alcohol_content": float(d.alcohol_percent),
                # gleichartige Getränke um je 15 min versetzen
                "time": dt + timedelta(minutes=15 * i),
            })
    drinks.sort(key=lambda x: x["time"])

    # ---- Messwert ----
    measurement = {
        "datetime": measure_dt,
        "bac": (float(extraction.measurement.bac_per_mille)
                if extraction.measurement.bac_per_mille is not None else None),
        "method": _map_method(extraction.measurement.method),
    }

    return {
        "person": person,
        "drinks": drinks,
        "measurement": measurement,
        "summary": extraction.summary or "",
    }


def _parse_dt(value: Optional[str], reference: datetime) -> Optional[datetime]:
    """Robustes Parsen verschiedener Datums-/Zeitformate."""
    if not value:
        return None
    value = value.strip()
    # ISO 8601
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        pass
    for fmt in ("%d.%m.%Y %H:%M", "%d.%m.%Y", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    # Nur Uhrzeit -> mit Referenzdatum kombinieren
    for fmt in ("%H:%M", "%H:%M:%S"):
        try:
            t = datetime.strptime(value, fmt).time()
            return reference.replace(hour=t.hour, minute=t.minute,
                                     second=0, microsecond=0)
        except ValueError:
            continue
    return None


def _map_method(method: Optional[str]) -> Optional[str]:
    """Bildet einen freien Methodentext auf die Auswahlliste der GUI ab."""
    if not method:
        return None
    m = method.lower()
    if "gc" in m and "fid" in m:
        return "Gaschromatographie (GC-FID)"
    if "headspace" in m or "hs-gc" in m:
        return "Headspace-GC"
    if "adh" in m or "enzym" in m:
        return "Enzymatische Analyse (ADH)"
    if "lc-ms" in m or "lcms" in m or "massensp" in m:
        return "LC-MS/MS"
    if "gc" in m or "chromatograph" in m:
        return "Gaschromatographie (GC-FID)"
    return "Andere"
