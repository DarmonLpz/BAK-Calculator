"""
OpenAI-Integration für automatische Trinkprotokoll-Analyse
"""

import json
import openai
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

class OpenAIAnalyzer:
    """Analysiert Trinkprotokolle mit OpenAI"""
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model = model
        self.client = openai.OpenAI(api_key=api_key)
        
        # System-Prompt für strukturierte Analyse
        self.system_prompt = """Du bist ein forensischer Alkoholexperte. Deine Aufgabe ist es, Trinkprotokolle zu analysieren und die Informationen in einem spezifischen JSON-Format zu extrahieren.

WICHTIG: Du MUSST IMMER im folgenden JSON-Format antworten, auch wenn die Informationen unvollständig sind. Verwende Standardwerte für fehlende Angaben.

ANALYSE-REGELN:
1. DATUM: Verwende das Datum der Blutentnahme
2. BEGINN: Erste Trinkzeit des relevanten Tages
3. ENDE: Letzte Trinkzeit des relevanten Tages
4. BLUTENTNAHME: Zeitpunkt der Blutentnahme
5. GETRÄNKE: Alle konsumierten Getränke als Array
6. GEMESSENER_BAK: Gemessener Blutalkoholgehalt

ZEITVERTEILUNG:
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
Input: "Freitag von 14:00 bis 18:00 Uhr: halbe Flasche Weinbrand"
Output: {
  "date": "2024-02-16",
  "start_time": "14:00",
  "end_time": "18:00", 
  "blood_test_time": "20:12",
  "measured_bac": 2.69,
  "drinks": [
    {"name": "Weinbrand", "volume_ml": 350, "quantity": 1, "alcohol_percent": 40, "distribution_start": "14:00", "distribution_end": "18:00"}
  ]
}"""

    async def analyze_protocol(self, text: str) -> Optional[DrinkingProtocol]:
        """Analysiert Trinkprotokoll mit OpenAI"""
        try:
            # Prompt erstellen
            prompt = self._create_prompt(text)
            
            # OpenAI API aufrufen
            response = await self._call_openai(prompt)
            
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
    
    async def _call_openai(self, prompt: str) -> Optional[str]:
        """Ruft OpenAI API auf"""
        try:
            # Asynchroner Aufruf über ThreadPoolExecutor
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, self._sync_openai_call, prompt)
            return response
            
        except Exception as e:
            logger.error(f"Fehler beim OpenAI API Aufruf: {e}")
            return None
    
    def _sync_openai_call(self, prompt: str) -> Optional[str]:
        """Synchroner OpenAI API Aufruf"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Niedrige Temperatur für konsistente Ausgaben
                max_tokens=1000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI API Fehler: {e}")
            return None
    
    def _parse_response(self, response: str) -> Optional[Dict]:
        """Parst JSON-Antwort und validiert"""
        try:
            # JSON aus Antwort extrahieren
            response = response.strip()
            
            # Debug: Zeige die Antwort
            logger.info(f"OpenAI Antwort: {response[:200]}...")
            
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
            # Datum parsen
            date = datetime.strptime(data['date'], '%Y-%m-%d').date()
            
            # Zeiten parsen
            start_time = datetime.strptime(data['start_time'], '%H:%M').time()
            end_time = datetime.strptime(data['end_time'], '%H:%M').time()
            blood_test_time = datetime.strptime(data['blood_test_time'], '%H:%M').time()
            
            # Datetime-Objekte erstellen
            start_datetime = datetime.combine(date, start_time)
            end_datetime = datetime.combine(date, end_time)
            blood_test_datetime = datetime.combine(date, blood_test_time)
            
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
                        
                        # Markiere für Zeitverteilung
                        drinks.append({
                            'name': name,
                            'volume': volume,
                            'quantity': quantity,
                            'alcohol_content': alcohol_percent,
                            'alcohol_grams': volume * (alcohol_percent / 100) * 0.789 * quantity,
                            'time': drink_datetime,
                            'distribution_start': datetime.combine(date, start_time),
                            'distribution_end': datetime.combine(date, end_time)
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
        """Testet die Verbindung zu OpenAI"""
        try:
            response = await self._call_openai("Test")
            return response is not None
        except Exception:
            return False 