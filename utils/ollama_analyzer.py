"""
Ollama-Integration für automatische Trinkprotokoll-Analyse
"""

import json
import aiohttp
import asyncio
from datetime import datetime, time
from typing import Dict, List, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class DrinkingProtocol:
    """Struktur für analysierte Trinkprotokolle"""
    date: datetime
    start_time: datetime
    end_time: datetime
    blood_test_time: datetime
    drinks: List[Dict]
    total_alcohol_grams: float
    measured_bac: float
    source_text: str

class OllamaAnalyzer:
    """Analysiert Trinkprotokolle mit Ollama"""
    
    def __init__(self, model_name: str = "llama3.1", base_url: str = "http://localhost:11434"):
        self.model = model_name
        self.base_url = base_url
        self.timeout = 30
        
        # System-Prompt für strukturierte Analyse
        self.system_prompt = """Du bist ein forensischer Alkoholexperte. Deine Aufgabe ist es, Trinkprotokolle zu analysieren und die Informationen in einem spezifischen JSON-Format zu extrahieren.

WICHTIG: Du MUSST IMMER im folgenden JSON-Format antworten, auch wenn die Informationen unvollständig sind. Verwende Standardwerte für fehlende Angaben.

ANALYSE-REGELN:
1. DATUM: Verwende das Datum der Blutentnahme
2. BEGINN: Erste Trinkzeit (kann am Vortag sein!)
3. ENDE: Letzte Trinkzeit vor der Messung
4. BLUTENTNAHME: Zeitpunkt der Blutentnahme (MUSS nach dem Trinken liegen!)
5. GETRÄNKE: Alle konsumierten Getränke als Array
6. GEMESSENER_BAK: Gemessener Blutalkoholgehalt

MEHRTÄGIGER KONSUM:
- Bei Konsum über mehrere Tage: Verwende das DATUM der MESSUNG
- Konsum-BEGINN kann am Vortag liegen (z.B. 25.11. 19:00 Uhr)
- Konsum-ENDE ist vor der Messung (z.B. 26.11. Mittagszeit)
- Messung ist am aktuellen Tag (z.B. 26.11. 19:56 Uhr)
- Bei "am nächsten Tag" oder "über Nacht": Konsum geht bis zum nächsten Tag
- Bei "Mittagszeit": Verwende 12:00 Uhr
- Bei "Abend": Verwende 19:00 Uhr

VERSCHIEDENE KONSUMTAGE:
- Bei "Donnerstag... Freitag...": Separate Konsumtage erkennen
- Jeder Tag hat eigene Getränke und Zeiten
- WICHTIG: Verwende das DATUM der MESSUNG für alle Getränke
- Zeitangaben wie "Donnerstagabend" → 19:00 Uhr (Messdatum)
- Zeitangaben wie "Freitagmorgen" → 09:00 Uhr (Messdatum)
- Zeitangaben wie "nach dem Mittagessen" → 13:00 Uhr (Messdatum)
- Bei verschiedenen Tagen: Verwende spezifische Zeiten für einzelne Getränke
- Bei Zeiträumen: Verwende distribution_start/end

ZEITVERTEILUNG:
- WICHTIG: Konsumzeiten müssen VOR dem Messzeitpunkt liegen!
- Bei "ab X Uhr bis Y Uhr" verteile Getränke gleichmäßig in diesem Zeitraum
- Bei Zeitangaben wie "von 14:00 bis 18:00 Uhr" werden die Getränke automatisch gleichmäßig verteilt
- Bei spezifischen Zeitangaben (z.B. "um 19:00 Uhr") wird diese Zeit verwendet
- Bei unklaren Zeitangaben wird die Startzeit verwendet

ERFORDERLICHES JSON-FORMAT:
{
  "date": "2024-02-16",
  "start_time": "14:00",
  "end_time": "18:00", 
  "blood_test_time": "20:12",
  "measured_bac": 2.69,
  "drinks": [
    {
      "name": "Weinbrand", 
      "volume_ml": 700, 
      "quantity": 1, 
      "alcohol_percent": 40,
      "distribution_start": "14:00",
      "distribution_end": "18:00"
    }
  ]
}

STANDARDWERTE:
- Bier: 4.8% Alkohol, 500ml
- Wein: 12% Alkohol, 200ml  
- Weinbrand/Cognac: 40% Alkohol, 700ml
- Wodka/Gin: 40% Alkohol, 700ml
- Whisky: 40% Alkohol, 700ml

BEISPIEL-ANALYSE:
Input: "16.02.2024, 19:20 Uhr: Fahrlässige Straßenverkehrsgefährdung durch Trunkenheit (Blutalkoholgehalt mindestens 2,69 Promille; Blutentnahmezeitpunkt: 20:12 Uhr), es kam zum Unfall. Wie kam es zur Tat? „Am Donnerstag war ich beim Arzt, ich wurde krankgeschrieben und ich habe dann 2 Flaschen Weinbrand gekauft. Ich habe dann Donnerstagabend ab 19:00 oder 20:00 Uhr eine Flasche von diesem Weinbrand (0,7 l) getrunken. Freitagmorgen bin ich aufgestanden und habe dann nach dem Mittagessen die zweite Flasche angefangen und dann bis ca. 18:00 Uhr die halbe Flasche getrunken.""
Output: {
  "date": "2024-02-16",
  "start_time": "19:00",
  "end_time": "18:00", 
  "blood_test_time": "20:12",
  "measured_bac": 2.69,
  "drinks": [
    {"name": "Weinbrand", "volume_ml": 700, "quantity": 1, "alcohol_percent": 40, "drink_time": "19:00"},
    {"name": "Weinbrand", "volume_ml": 350, "quantity": 1, "alcohol_percent": 40, "distribution_start": "13:00", "distribution_end": "18:00"}
  ]
}"""

    async def analyze_protocol(self, text: str) -> Optional[DrinkingProtocol]:
        """Analysiert Trinkprotokoll mit Ollama"""
        try:
            # Prompt erstellen
            prompt = self._create_prompt(text)
            
            # Ollama API aufrufen
            response = await self._call_ollama(prompt)
            
            if not response:
                return None
            
            # JSON parsen
            data = self._parse_response(response)
            
            if not data:
                return None
            
            # In DrinkingProtocol konvertieren
            return self._convert_to_protocol(data, text)
            
        except Exception as e:
            logger.error(f"Fehler bei der Protokoll-Analyse: {e}")
            return None
    
    def _create_prompt(self, text: str) -> str:
        """Erstellt strukturierten Prompt"""
        return f"{self.system_prompt}\n\nTrinkprotokoll:\n{text}\n\nJSON-Antwort:"
    
    async def _call_ollama(self, prompt: str) -> Optional[str]:
        """Ruft Ollama API auf"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                payload = {
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # Niedrige Temperatur für konsistente Ausgaben
                        "top_p": 0.9
                    }
                }
                
                async with session.post(f"{self.base_url}/api/generate", json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("response", "")
                    else:
                        logger.error(f"Ollama API Fehler: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Fehler beim Ollama API Aufruf: {e}")
            return None
    
    def _parse_response(self, response: str) -> Optional[Dict]:
        """Parst JSON-Antwort und validiert"""
        try:
            # JSON aus Antwort extrahieren
            response = response.strip()
            
            # Debug: Zeige die Antwort
            logger.info(f"Ollama Antwort: {response[:200]}...")
            
            # Versuche verschiedene JSON-Formate zu finden
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                logger.error("Kein JSON in der Antwort gefunden")
                logger.error(f"Vollständige Antwort: {response}")
                return None
            
            json_str = response[json_start:json_end]
            logger.info(f"Extrahierter JSON: {json_str}")
            
            data = json.loads(json_str)
            
            # Validierung
            required_fields = ['date', 'start_time', 'end_time', 'blood_test_time', 'measured_bac', 'drinks']
            missing_fields = []
            for field in required_fields:
                if field not in data:
                    missing_fields.append(field)
            
            if missing_fields:
                logger.error(f"Fehlende Felder: {missing_fields}")
                logger.error(f"Verfügbare Felder: {list(data.keys())}")
                return None
            
            logger.info(f"Erfolgreich geparst: {data}")
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON Parse Fehler: {e}")
            logger.error(f"Problematischer JSON-String: {json_str if 'json_str' in locals() else 'N/A'}")
            return None
        except Exception as e:
            logger.error(f"Fehler beim Parsen der Antwort: {e}")
            return None
    
    def _convert_to_protocol(self, data: Dict, source_text: str) -> DrinkingProtocol:
        """Konvertiert JSON-Daten in DrinkingProtocol"""
        try:
            # Datum parsen (Datum der Messung)
            date = datetime.strptime(data['date'], '%Y-%m-%d').date()
            
            # Zeiten parsen
            start_time = datetime.strptime(data['start_time'], '%H:%M').time()
            end_time = datetime.strptime(data['end_time'], '%H:%M').time()
            blood_test_time = datetime.strptime(data['blood_test_time'], '%H:%M').time()
            
            # Datetime-Objekte erstellen
            # Bei mehreren Tage dauerndem Konsum: Start kann am Vortag sein
            start_datetime = datetime.combine(date, start_time)
            end_datetime = datetime.combine(date, end_time)
            blood_test_datetime = datetime.combine(date, blood_test_time)
            
            # Prüfe auf mehreren Tage dauernden Konsum (Ende vor Start am gleichen Tag)
            if end_time < start_time:
                # Konsum geht über Nacht - Ende ist am nächsten Tag
                from datetime import timedelta
                end_datetime = datetime.combine(date + timedelta(days=1), end_time)
            
            # Getränke verarbeiten
            drinks = []
            total_alcohol = 0.0
            
            for drink_data in data['drinks']:
                # Standardwerte für fehlende Felder
                name = drink_data.get('name', 'Unbekanntes Getränk')
                volume = drink_data.get('volume_ml', 500)
                quantity = drink_data.get('quantity', 1)
                alcohol_percent = drink_data.get('alcohol_percent', 4.8)
                
                # Zeitverteilung verarbeiten
                distribution_start = drink_data.get('distribution_start')
                distribution_end = drink_data.get('distribution_end')
                drink_time_str = drink_data.get('drink_time')
                
                if distribution_start and distribution_end:
                    # Zeitverteilung über einen Zeitraum
                    try:
                        start_time = datetime.strptime(distribution_start, '%H:%M').time()
                        end_time = datetime.strptime(distribution_end, '%H:%M').time()
                        drink_datetime = datetime.combine(date, start_time)  # Startzeit als Referenz
                        
                        # Prüfe auf mehreren Tage dauernden Konsum
                        distribution_start_dt = datetime.combine(date, start_time)
                        distribution_end_dt = datetime.combine(date, end_time)
                        
                        if end_time < start_time:
                            # Konsum geht über Nacht - Ende ist am nächsten Tag
                            from datetime import timedelta
                            distribution_end_dt = datetime.combine(date + timedelta(days=1), end_time)
                        
                        # Markiere für Zeitverteilung
                        drinks.append({
                            'name': name,
                            'volume': volume,
                            'quantity': quantity,
                            'alcohol_content': alcohol_percent,
                            'alcohol_grams': volume * (alcohol_percent / 100) * 0.789 * quantity,
                            'time': drink_datetime,
                            'distribution_start': distribution_start_dt,
                            'distribution_end': distribution_end_dt
                        })
                        total_alcohol += volume * (alcohol_percent / 100) * 0.789 * quantity
                        continue
                        
                    except Exception as e:
                        logger.error(f"Fehler beim Parsen der Zeitverteilung: {e}")
                
                # Spezifische Trinkzeit oder Fallback
                if drink_time_str:
                    try:
                        drink_time = datetime.strptime(drink_time_str, '%H:%M').time()
                        drink_datetime = datetime.combine(date, drink_time)
                    except:
                        drink_datetime = start_datetime
                else:
                    drink_datetime = start_datetime
                
                # Alkoholmenge berechnen
                alcohol_grams = volume * (alcohol_percent / 100) * 0.789 * quantity
                total_alcohol += alcohol_grams
                
                drinks.append({
                    'name': name,
                    'volume': volume,
                    'quantity': quantity,
                    'alcohol_content': alcohol_percent,
                    'alcohol_grams': alcohol_grams,
                    'time': drink_datetime
                })
            
            return DrinkingProtocol(
                date=start_datetime,
                start_time=start_datetime,
                end_time=end_datetime,
                blood_test_time=blood_test_datetime,
                drinks=drinks,
                total_alcohol_grams=total_alcohol,
                measured_bac=data['measured_bac'],
                source_text=source_text
            )
            
        except Exception as e:
            logger.error(f"Fehler bei der Konvertierung: {e}")
            raise
    
    async def test_connection(self) -> bool:
        """Testet die Verbindung zu Ollama"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.get(f"{self.base_url}/api/tags") as response:
                    return response.status == 200
        except Exception:
            return False 