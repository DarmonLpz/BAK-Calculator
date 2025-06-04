from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from typing import Dict, List, Optional
import threading
from datetime import datetime, timedelta
from models import Person, Drink, CalculationSettings, Gender, BAKModel, ResorptionMode
from calculations import BACCalculator

class CalculationController(QObject):
    """Controller für BAK-Berechnungen mit Optimierungen"""
    
    # Signale
    calculation_started = pyqtSignal()
    calculation_finished = pyqtSignal(dict)  # Ergebnisse
    calculation_error = pyqtSignal(str)  # Fehlermeldung
    
    def __init__(self):
        super().__init__()
        
        # Debounce Timer für verzögerte Berechnungen
        self.calculation_timer = QTimer()
        self.calculation_timer.setSingleShot(True)
        self.calculation_timer.timeout.connect(self._perform_calculation)
        
        # Cache für Berechnungen
        self.calculation_cache = {}
        self.cache_limit = 50
        
        # Aktuelle Daten
        self.person_data = None
        self.drinks_data = []
        self.settings_data = None
        
        # Calculator-Instanz
        self.calculator = BACCalculator()
    
    def set_person_data(self, data: Dict):
        """Setzt die Personendaten"""
        self.person_data = data
        self._trigger_calculation()
    
    def set_drinks_data(self, data: List[Dict]):
        """Setzt die Getränkedaten"""
        self.drinks_data = data
        self._trigger_calculation()
    
    def set_calculation_settings(self, data: Dict):
        """Setzt die Berechnungseinstellungen"""
        self.settings_data = data
        self._trigger_calculation()
    
    def _trigger_calculation(self):
        """Triggert eine verzögerte Berechnung (Debouncing)"""
        # Stoppe vorherigen Timer
        self.calculation_timer.stop()
        
        # Starte neuen Timer (300ms Verzögerung)
        self.calculation_timer.start(300)
    
    def _perform_calculation(self):
        """Führt die eigentliche Berechnung durch"""
        if not self._validate_data():
            return
        try:
            self.calculation_started.emit()
            cache_key = self._generate_cache_key()
            if cache_key in self.calculation_cache:
                results = self.calculation_cache[cache_key]
                self.calculation_finished.emit(results)
                return
            results = self._calculate_bac()
            self._update_cache(cache_key, results)
            self.calculation_finished.emit(results)
        except Exception as e:
            print(f"Berechnungsfehler: {e}")
            self.calculation_error.emit(str(e))
    
    def _validate_data(self) -> bool:
        """Validiert die Eingabedaten"""
        if not self.person_data:
            return False
        if not self.drinks_data:
            return False
        if not self.settings_data:
            return False
        if not self.settings_data.get('models'):
            return False
        return True
    
    def _calculate_bac(self) -> Dict:
        """Führt die BAK-Berechnung durch"""
        results = {}
        
        # Person-Objekt erstellen
        gender = Gender.MALE if self.person_data['gender'] == 'Männlich' else Gender.FEMALE
        person = Person(
            gender=gender,
            age=self.person_data['age'],
            height=self.person_data['height'],
            weight=self.person_data['weight'],
            body_fat=self.person_data.get('body_fat', 20)
        )
        
        # Drink-Objekte erstellen
        drinks = []
        for drink_data in self.drinks_data:
            drink = Drink(
                name=drink_data['name'],
                volume=drink_data['volume'],
                alcohol_content=drink_data['alcohol_content'],
                time=drink_data['time']
            )
            drinks.append(drink)
        
        # BAK-Modelle konvertieren
        model_mapping = {
            'Widmark': BAKModel.WIDMARK,
            'Watson': BAKModel.WATSON,
            'Forrest': BAKModel.FORREST,
            'Seidl': BAKModel.SEIDL
        }
        
        selected_models = []
        for model_name in self.settings_data['models']:
            if model_name in model_mapping:
                selected_models.append(model_mapping[model_name])
        
        # Resorption-Modus bestimmen
        resorption_mode = ResorptionMode.FASTING if self.settings_data.get('meal_status') == 'Nüchtern' else ResorptionMode.WITH_FOOD
        
        # Elimination-Rate bestimmen
        elimination_rate = 0.15  # Standard
        if self.settings_data.get('elimination_rate') == 'Auto (geschlechtsabhängig)':
            elimination_rate = 0.17 if gender == Gender.MALE else 0.15
        elif self.settings_data.get('manual_elimination_rate'):
            elimination_rate = float(self.settings_data['manual_elimination_rate'])
        
        # Settings-Objekt erstellen
        settings = CalculationSettings(
            models=selected_models,
            resorption_mode=resorption_mode,
            elimination_rate=elimination_rate
        )
        
        # Für jedes ausgewählte Modell berechnen
        for model in selected_models:
            try:
                # Da es keinen echten Calculator gibt, erstelle Mock-Ergebnisse
                result = self._mock_calculation(person, drinks, model)
                results[model.value] = result
            except Exception as e:
                print(f"Fehler bei Modell {model}: {e}")
                continue
        
        return results
    
    def _mock_calculation(self, person, drinks, model):
        """Realistische Berechnung mit Einzelgetränk-Abbau verschiedener BAK-Modelle"""
        
        # DEBUG: Alkoholmenge ausgeben
        total_alcohol = sum(drink.get_alcohol_grams() for drink in drinks)
        print(f"DEBUG: Gesamtalkohol für {model.value}: {total_alcohol:.1f}g")
        
        # Geschlechtsabhängige Grundwerte
        is_male = person.gender == Gender.MALE
        
        # Modell-spezifische r-Faktoren und Berechnungen
        if model == BAKModel.WIDMARK:
            # Klassische Widmark-Formel
            r_factor = 0.68 if is_male else 0.55
            elimination_rate = 0.15 if is_male else 0.13
            
        elif model == BAKModel.WATSON:
            # Watson-Modell mit Total Body Water
            if is_male:
                tbw = 2.447 - (0.09516 * person.age) + (0.1074 * person.height) + (0.3362 * person.weight)
            else:
                tbw = -2.097 + (0.1069 * person.height) + (0.2466 * person.weight)
            r_factor = tbw / person.weight
            elimination_rate = 0.16 if is_male else 0.14
            
        elif model == BAKModel.FORREST:
            # Forrest-Modell mit Alterskorrektur
            base_r = 0.68 if is_male else 0.55
            age_factor = max(0.5, 1 - 0.01 * max(0, person.age - 20))  # 1% Reduktion pro Jahr ab 20
            r_factor = base_r * age_factor
            elimination_rate = 0.17 if is_male else 0.15
            
        elif model == BAKModel.SEIDL:
            # Seidl-Modell mit BMI und Körperfett-Korrektur
            bmi = person.weight / ((person.height / 100) ** 2)
            bmi_factor = 1.0 + (bmi - 25) * 0.005  # Leichte BMI-Korrektur
            base_r = 0.70 if is_male else 0.58
            body_fat_factor = 1.0 - (person.body_fat - 20) * 0.01
            r_factor = base_r * bmi_factor * body_fat_factor
            elimination_rate = 0.18 if is_male else 0.16
            
        else:
            # Fallback: Widmark
            r_factor = 0.68 if is_male else 0.55
            elimination_rate = 0.15 if is_male else 0.13
        
        print(f"DEBUG: {model.value} - r_factor: {r_factor:.3f}, elimination_rate: {elimination_rate:.3f}‰/h")
        
        # Einzelgetränk-Berechnung mit separater Pharmakodynamik
        now = datetime.now()
        drink_contributions = []
        
        for i, drink in enumerate(drinks):
            drink_alcohol = drink.get_alcohol_grams()
            drink_time = drink.time
            
            # Einzelgetränk Peak-BAK
            drink_peak_bac = drink_alcohol / (person.weight * r_factor)
            
            # Resorptionszeit für dieses Getränk (30-60 Minuten je nach Typ)
            if drink_alcohol <= 10:  # Kleine Getränke
                resorption_time_hours = 0.5  # 30 Minuten
            elif drink_alcohol <= 20:  # Normale Getränke
                resorption_time_hours = 0.75  # 45 Minuten  
            else:  # Große/starke Getränke
                resorption_time_hours = 1.0  # 60 Minuten
            
            # Peak-Zeit für dieses Getränk
            drink_peak_time = drink_time + timedelta(hours=resorption_time_hours)
            
            print(f"DEBUG: Getränk {i+1}: {drink_alcohol:.1f}g → Peak {drink_peak_bac:.3f}‰ um {drink_peak_time.strftime('%H:%M')}")
            
            drink_contributions.append({
                'drink_index': i,
                'alcohol_grams': drink_alcohol,
                'consumption_time': drink_time,
                'peak_bac': drink_peak_bac,
                'peak_time': drink_peak_time,
                'resorption_hours': resorption_time_hours
            })
        
        # Gesamtverlauf berechnen: Summation aller Einzelkurven
        first_drink_time = min(drink.time for drink in drinks)
        last_drink_time = max(drink.time for drink in drinks)
        
        # BAK-Verlauf für Diagramm generieren (von 1h vor erstem bis 12h nach letztem Getränk)
        start_time = first_drink_time - timedelta(hours=1)
        end_time = max(now + timedelta(hours=6), last_drink_time + timedelta(hours=12))
        bac_values = []
        
        current_time = start_time
        time_step = timedelta(minutes=10)  # 10-Minuten-Schritte
        
        while current_time <= end_time:
            total_bac_at_time = 0.0
            
            # Summiere Beitrag aller Getränke zu diesem Zeitpunkt
            for contrib in drink_contributions:
                bac_contribution = self._calculate_single_drink_bac(
                    current_time, contrib, elimination_rate
                )
                total_bac_at_time += bac_contribution
            
            bac_values.append((current_time, total_bac_at_time))
            
            # Stoppe wenn BAK unter 0.001‰ ist und wir sind lange nach dem letzten Getränk
            if (total_bac_at_time <= 0.001 and 
                current_time > last_drink_time + timedelta(hours=2)):
                break
                
            current_time += time_step
        
        print(f"DEBUG: Generiert {len(bac_values)} BAK-Datenpunkte von {start_time.strftime('%H:%M')} bis {(start_time + timedelta(minutes=len(bac_values)*10)).strftime('%H:%M')}")
        
        # Aktuelle BAK und Peak-BAK berechnen
        current_bac = 0.0
        peak_bac = 0.0
        peak_time = None
        
        for time_point, bac_value in bac_values:
            if time_point <= now:
                current_bac = bac_value
            if bac_value > peak_bac:
                peak_bac = bac_value
                peak_time = time_point
        
        print(f"DEBUG: current_bac={current_bac}, now={now}, drinks={[d['consumption_time'] for d in drink_contributions]}")
        
        # Zeiten berechnen
        # Zeit bis unter 0.5‰
        time_to_05 = None
        time_to_00 = None
        
        for time_point, bac_value in bac_values:
            if time_point > now:
                if time_to_05 is None and bac_value <= 0.5:
                    time_to_05 = time_point
                if time_to_00 is None and bac_value <= 0.05:  # Praktisch nüchtern
                    time_to_00 = time_point
                    break
        
        # Detaillierte Berechnung für Dokumentation
        individual_contributions = []
        for contrib in drink_contributions:
            current_contrib_bac = self._calculate_single_drink_bac(now, contrib, elimination_rate)
            individual_contributions.append({
                'drink_number': contrib['drink_index'] + 1,
                'alcohol_grams': contrib['alcohol_grams'],
                'consumption_time': contrib['consumption_time'].strftime('%H:%M'),
                'peak_bac': contrib['peak_bac'],
                'peak_time': contrib['peak_time'].strftime('%H:%M'),
                'current_contribution': current_contrib_bac,
                'resorption_duration': contrib['resorption_hours']
            })
        
        return {
            'peak_bac': round(peak_bac, 3),
            'current_bac': round(current_bac, 3),
            'model': model.value,
            'alcohol_grams': round(total_alcohol, 1),
            'elimination_time': f"{(current_bac / elimination_rate):.1f} Stunden" if current_bac > 0 else "Bereits nüchtern",
            'peak_time': peak_time.strftime('%H:%M') if peak_time else "N/A",
            'time_to_03': time_to_05,
            'time_to_00': time_to_00,
            'elimination_rate': elimination_rate,
            'r_factor': round(r_factor, 3),
            'person_weight': person.weight,
            'body_fat_factor': round(1.0 - (person.body_fat - 20) * 0.01, 3),
            'bac_values': bac_values,  # Für Diagramm
            'individual_contributions': individual_contributions,  # Neue Einzelgetränk-Details
            'total_drinks': len(drinks),
            'calculation_details': {
                'zwischenschritt_1': f"Verteilungsvolumen = {person.weight} kg × {r_factor:.3f} = {person.weight * r_factor:.1f} L",
                'zwischenschritt_2': f"Gesamtalkohol = {total_alcohol:.1f} g (Summe aller Getränke)",
                'individual_peaks': f"{len(drinks)} Einzelgetränke mit separaten Resorptionskurven",
                'körperfett_korrektur': f"Körperfett-Faktor = {round(1.0 - (person.body_fat - 20) * 0.01, 3)}"
            }
        }

    def _calculate_single_drink_bac(self, current_time, drink_contrib, elimination_rate):
        """Berechnet den BAK-Beitrag eines einzelnen Getränks zu einem bestimmten Zeitpunkt"""
        consumption_time = drink_contrib['consumption_time']
        peak_time = drink_contrib['peak_time']
        peak_bac = drink_contrib['peak_bac']
        resorption_hours = drink_contrib['resorption_hours']
        
        if current_time < consumption_time:
            # Vor dem Konsumzeitpunkt: kein Beitrag
            return 0.0
        elif current_time <= peak_time:
            # Resorptionsphase - Linear ansteigend
            time_since_consumption = (current_time - consumption_time).total_seconds() / 3600
            progress = max(0.0, min(1.0, time_since_consumption / resorption_hours))
            return peak_bac * progress
        else:
            # Eliminationsphase - First-Order-Kinetik
            time_since_peak = (current_time - peak_time).total_seconds() / 3600
            bac_after_elimination = peak_bac - (elimination_rate * time_since_peak)
            return max(0.0, bac_after_elimination)
    
    def _generate_cache_key(self) -> str:
        """Generiert einen Cache-Schlüssel"""
        import hashlib
        import json
        def convert(obj):
            if isinstance(obj, dict):
                return {k: convert(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert(i) for i in obj]
            elif isinstance(obj, datetime):
                return obj.isoformat()
            return obj
        cache_data = {
            'person': self.person_data,
            'drinks': self.drinks_data,
            'settings': self.settings_data
        }
        cache_data = convert(cache_data)
        json_str = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(json_str.encode()).hexdigest()
    
    def _update_cache(self, key: str, results: Dict):
        """Aktualisiert den Cache"""
        # Cache-Limit prüfen
        if len(self.calculation_cache) >= self.cache_limit:
            # Ältesten Eintrag entfernen (FIFO)
            oldest_key = next(iter(self.calculation_cache))
            del self.calculation_cache[oldest_key]
        
        # Neuen Eintrag hinzufügen
        self.calculation_cache[key] = results
    
    def get_cache_info(self) -> Dict:
        """Gibt Cache-Informationen zurück"""
        return {
            'size': len(self.calculation_cache),
            'limit': self.cache_limit
        }
    
    def clear_cache(self):
        """Leert den Cache"""
        self.calculation_cache.clear()
    
    def force_calculation(self):
        """Erzwingt eine sofortige Berechnung"""
        self.calculation_timer.stop()
        self._perform_calculation()

    def calculate_bac_curve(self, drinks_data, weight, gender, height, age):
        """Berechnet die BAK-Kurve für alle Getränke"""
        if not drinks_data:
            return [], []
        
        # Sortiere Getränke nach Zeit
        sorted_drinks = sorted(drinks_data, key=lambda x: x['time'])
        
        # Extrahiere alle Zeitpunkte
        drink_times = [drink['time'] for drink in sorted_drinks]
        
        # Bestimme Start- und Endzeit
        start_time = min(drink_times)
        end_time = max(drink_times) + timedelta(hours=8)  # 8 Stunden nach dem letzten Getränk
        
        # Erstelle Zeitpunkte für die Kurve (alle 5 Minuten)
        time_points = []
        current_time = start_time
        while current_time <= end_time:
            time_points.append(current_time)
            current_time += timedelta(minutes=5)
        
        # Berechne BAK für jeden Zeitpunkt
        bac_values = []
        for current_time in time_points:
            total_bac = 0.0
            for drink in sorted_drinks:
                # Berechne BAK-Beitrag jedes Getränks
                drink_contrib = self._calculate_drink_contribution(drink, weight, gender, height, age)
                bac = self._calculate_single_drink_bac(current_time, drink_contrib, self.elimination_rate)
                total_bac += bac
            bac_values.append(total_bac)
        
        return time_points, bac_values, drink_times 