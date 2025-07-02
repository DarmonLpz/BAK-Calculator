from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from typing import Dict, List, Optional
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
        
        # Trinkgewohnheiten für spätere Verwendung speichern
        drinking_habit = self.person_data.get('drinking_habit', 'Gelegentlich')
        
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
        
        # Elimination-Rate bestimmen (wird später modell-spezifisch überschrieben)
        elimination_setting = self.settings_data.get('elimination_rate', 'Auto (geschlechtsabhängig)')
        
        if elimination_setting == 'Auto (geschlechtsabhängig)':
            global_elimination_rate = 0.17 if gender == Gender.MALE else 0.15
        elif 'Niedrig (0.10' in elimination_setting:
            global_elimination_rate = 0.10
        elif 'Normal (0.15' in elimination_setting:
            global_elimination_rate = 0.15
        elif 'Hoch (0.20' in elimination_setting:
            global_elimination_rate = 0.20
        elif elimination_setting == 'Manuell':
            global_elimination_rate = float(self.settings_data.get('manual_elimination_rate', 0.15))
        else:
            global_elimination_rate = 0.15  # Standard
        
        # Settings-Objekt erstellen
        settings = CalculationSettings(
            models=selected_models,
            resorption_mode=resorption_mode,
            elimination_rate=global_elimination_rate
        )
        
        # Für jedes ausgewählte Modell berechnen
        for model in selected_models:
            try:
                # Da es keinen echten Calculator gibt, erstelle Mock-Ergebnisse
                result = self._mock_calculation(person, drinks, model, global_elimination_rate, drinking_habit)
                results[model.value] = result
            except Exception as e:
                print(f"Fehler bei Modell {model}: {e}")
                continue
        
        return results
    
    def _mock_calculation(self, person, drinks, model, user_elimination_rate, drinking_habit):
        """Realistische Berechnung mit GLOBALER Elimination (nicht pro Getränk)"""
        
        # DEBUG: Alkoholmenge ausgeben
        total_alcohol = sum(drink.get_alcohol_grams() for drink in drinks)
        # Gesamtalkohol berechnet: {total_alcohol:.1f}g
        
        # Geschlechtsabhängige Grundwerte
        is_male = person.gender == Gender.MALE
        
        # Modell-spezifische r-Faktoren und Berechnungen
        if model == BAKModel.WIDMARK:
            # Klassische Widmark-Formel
            r_factor = 0.68 if is_male else 0.55
            default_elimination = 0.15 if is_male else 0.13
            
        elif model == BAKModel.WATSON:
            # Watson-Modell mit Total Body Water
            if is_male:
                tbw = 2.447 - (0.09516 * person.age) + (0.1074 * person.height) + (0.3362 * person.weight)
            else:
                tbw = -2.097 + (0.1069 * person.height) + (0.2466 * person.weight)
            r_factor = tbw / person.weight
            default_elimination = 0.16 if is_male else 0.14
            
        elif model == BAKModel.FORREST:
            # Forrest-Modell mit Alterskorrektur
            base_r = 0.68 if is_male else 0.55
            age_factor = max(0.5, 1 - 0.01 * max(0, person.age - 20))  # 1% Reduktion pro Jahr ab 20
            r_factor = base_r * age_factor
            default_elimination = 0.17 if is_male else 0.15
            
        elif model == BAKModel.SEIDL:
            # Seidl-Modell mit BMI und Körperfett-Korrektur
            bmi = person.weight / ((person.height / 100) ** 2)
            bmi_factor = 1.0 + (bmi - 25) * 0.005  # Leichte BMI-Korrektur
            base_r = 0.70 if is_male else 0.58
            body_fat_factor = 1.0 - (person.body_fat - 20) * 0.01
            r_factor = base_r * bmi_factor * body_fat_factor
            default_elimination = 0.18 if is_male else 0.16
            
        else:
            # Fallback: Widmark
            r_factor = 0.68 if is_male else 0.55
            default_elimination = 0.15 if is_male else 0.13
        
        # GLOBALE Eliminationsrate bestimmen (Benutzervorgabe oder modellspezifisch)
        if self.settings_data.get('elimination_rate') == 'Auto (modellspezifisch)':
            global_elimination_rate = default_elimination
        else:
            global_elimination_rate = user_elimination_rate
        
        # Trinkgewohnheiten-Faktor anwenden (Enzyminduktion)
        habit_factor = self._get_drinking_habit_factor(drinking_habit)
        global_elimination_rate *= habit_factor
        
        # Debug: Faktoren: r={r_factor:.3f}, GLOBALE elimination={global_elimination_rate:.3f}‰/h
        
        # Einzelgetränk-Resorption berechnen (ohne individuelle Elimination)
        now = datetime.now()
        drink_contributions = []
        
        for i, drink in enumerate(drinks):
            drink_alcohol = drink.get_alcohol_grams()
            drink_time = drink.time
            
            # Einzelgetränk Peak-BAK (nur Resorption, keine Elimination)
            drink_peak_bac = drink_alcohol / (person.weight * r_factor)
            
            # Resorptionszeit basierend auf Benutzer-Einstellung
            base_resorption_hours = self._get_base_resorption_time()
            
            # Getränk-spezifische Anpassung
            if drink_alcohol <= 10:  # Kleine Getränke
                drink_factor = 0.8  # 20% schneller
            elif drink_alcohol <= 20:  # Normale Getränke
                drink_factor = 1.0  # Normal
            else:  # Große/starke Getränke
                drink_factor = 1.3  # 30% langsamer
            
            # Mahlzeiten-Effekt berücksichtigen
            meal_factor = self._get_meal_factor()
            
            # Finale Resorptionszeit
            resorption_time_hours = base_resorption_hours * drink_factor * meal_factor
            
            # Peak-Zeit für dieses Getränk
            drink_peak_time = drink_time + timedelta(hours=resorption_time_hours)
            
            # Resorptionsdefizit berücksichtigen (reduziert Peak-BAK)
            resorption_deficit = self.settings_data.get('resorption_deficit', 0) / 100.0
            adjusted_peak_bac = drink_peak_bac * (1.0 - resorption_deficit)
            
            # Getränk {i+1}: {drink_alcohol:.1f}g → Peak {adjusted_peak_bac:.3f}‰
            
            drink_contributions.append({
                'drink_index': i,
                'drink_name': drink.name,
                'alcohol_grams': drink_alcohol,
                'consumption_time': drink_time,
                'peak_bac': adjusted_peak_bac,
                'peak_time': drink_peak_time,
                'resorption_hours': resorption_time_hours
            })
        
        # GLOBALE BAK-Verlauf berechnen mit globaler Elimination
        first_drink_time = min(drink.time for drink in drinks)
        last_drink_time = max(drink.time for drink in drinks)
        
        # BAK-Verlauf für Diagramm generieren (von 1h vor erstem bis 12h nach letztem Getränk)
        start_time = first_drink_time - timedelta(hours=1)
        end_time = max(now + timedelta(hours=6), last_drink_time + timedelta(hours=12))
        bac_values = []
        
        current_time = start_time
        time_step = timedelta(minutes=10)  # 10-Minuten-Schritte
        
        while current_time <= end_time:
            # 1. Summiere alle Resorptionsbeiträge (ohne individuelle Elimination)
            total_resorption_bac = 0.0
            
            for contrib in drink_contributions:
                # Nur Resorption berechnen
                resorption_contrib = self._calculate_resorption_only(current_time, contrib)
                total_resorption_bac += resorption_contrib
            
            # 2. GLOBALE Elimination auf Gesamt-BAK anwenden
            # Finde den Zeitpunkt mit maximaler Resorption (globaler Peak)
            global_peak_time = None
            max_resorption = 0.0
            
            # Vereinfachte Peak-Ermittlung: Mittelwert aller Peak-Zeiten
            if drink_contributions:
                avg_peak_time = sum(contrib['peak_time'].timestamp() for contrib in drink_contributions) / len(drink_contributions)
                global_peak_time = datetime.fromtimestamp(avg_peak_time)
            else:
                global_peak_time = current_time
            
            # 3. Globale Elimination anwenden (nur nach dem globalen Peak)
            if current_time <= global_peak_time:
                # Vor/während Resorption: Keine Elimination
                final_bac = total_resorption_bac
            else:
                # Nach Peak: Globale Elimination auf Gesamt-BAK
                hours_since_peak = (current_time - global_peak_time).total_seconds() / 3600
                elimination_amount = global_elimination_rate * hours_since_peak
                final_bac = max(0.0, total_resorption_bac - elimination_amount)
            
            bac_values.append((current_time, final_bac))
            
            # Stoppe wenn BAK unter 0.001‰ ist und wir sind lange nach dem letzten Getränk
            if (final_bac <= 0.001 and 
                current_time > last_drink_time + timedelta(hours=2)):
                break
                
            current_time += time_step
        
        # Generiert {len(bac_values)} BAK-Datenpunkte mit GLOBALER Elimination
        
        # BAK-Messzeitpunkt basierend auf Benutzer-Auswahl bestimmen
        timing_mode = self.settings_data.get('timing_mode', '30 min nach letztem Konsum')
        
        # Standard-Zeitpunkt: Datum des letzten Getränks + 30 Minuten
        if drinks:
            last_drink_time = max(drink.time for drink in drinks)
            default_target_time = last_drink_time + timedelta(minutes=30)
        else:
            default_target_time = now
        
        target_time = default_target_time
        timing_description = "30 Min nach letztem Konsum"
        
        if timing_mode == "Jetzt (aktuell)":
            target_time = now
            timing_description = f"Aktueller Zeitpunkt ({target_time.strftime('%d.%m.%Y %H:%M')})"
        elif timing_mode == "30 min nach letztem Konsum":
            target_time = default_target_time
            timing_description = f"30 Min nach letztem Konsum ({target_time.strftime('%d.%m.%Y %H:%M')})"
        elif timing_mode == "Zeitpunkt höchster BAK":
            # Peak-Zeit wird aus bac_values bestimmt
            peak_bac_temp = 0.0
            peak_time_temp = default_target_time
            for time_point, bac_value in bac_values:
                if bac_value > peak_bac_temp:
                    peak_bac_temp = bac_value
                    peak_time_temp = time_point
            target_time = peak_time_temp
            timing_description = f"Zeitpunkt höchster BAK ({target_time.strftime('%d.%m.%Y %H:%M')})"
        elif timing_mode == "Benutzerdefiniert":
            custom_datetime_str = self.settings_data.get('custom_datetime', default_target_time.strftime('%d.%m.%Y %H:%M'))
            try:
                # Parsen der benutzerdefinierten Datum/Zeit
                target_time = datetime.strptime(custom_datetime_str, '%d.%m.%Y %H:%M')
                timing_description = f"Benutzerdefiniert ({target_time.strftime('%d.%m.%Y %H:%M')})"
            except ValueError:
                # Fallback auf Standard-Zeitpunkt bei ungültiger Eingabe
                target_time = default_target_time
                timing_description = f"Standard (Fehler bei Eingabe) ({target_time.strftime('%d.%m.%Y %H:%M')})"
        
        # BAK zum Zielzeitpunkt und Peak-BAK berechnen
        current_bac = 0.0
        peak_bac = 0.0
        peak_time = None
        
        for time_point, bac_value in bac_values:
            if time_point <= target_time:
                current_bac = bac_value
            if bac_value > peak_bac:
                peak_bac = bac_value
                peak_time = time_point
        
        # Aktuelle BAK berechnet: {current_bac:.3f}‰ (mit GLOBALER Elimination)
        
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
        
        # Detaillierte Berechnung für Dokumentation - mit globaler Elimination
        individual_contributions = []
        
        # Sortiere drink_contributions nach Konsumzeit
        sorted_contributions = sorted(drink_contributions, key=lambda x: x['consumption_time'])
        
        # Berechne anteilige Elimination für jedes Getränk
        total_resorption_at_target = sum(
            self._calculate_resorption_only(target_time, contrib) 
            for contrib in sorted_contributions
        )
        
        for i, contrib in enumerate(sorted_contributions):
            # Resorptionsbeitrag ohne Elimination
            resorption_contrib = self._calculate_resorption_only(target_time, contrib)
            
            # Anteilige globale Elimination berechnen
            if total_resorption_at_target > 0:
                contrib_ratio = resorption_contrib / total_resorption_at_target
                individual_elimination = (total_resorption_at_target - current_bac) * contrib_ratio
                final_contrib = max(0.0, resorption_contrib - individual_elimination)
            else:
                final_contrib = 0.0
            
            individual_contributions.append({
                'drink_number': i + 1,  # Neu nummerieren nach zeitlicher Reihenfolge
                'drink_name': contrib['drink_name'],  # Getränke-Name
                'original_index': contrib['drink_index'] + 1,  # Ursprüngliche Nummer beibehalten
                'alcohol_grams': contrib['alcohol_grams'],
                'consumption_time': contrib['consumption_time'].strftime('%H:%M'),
                'peak_bac': contrib['peak_bac'],
                'peak_time': contrib['peak_time'].strftime('%H:%M'),
                'current_contribution': final_contrib,  # Mit anteiliger globaler Elimination
                'resorption_duration': contrib['resorption_hours']
            })
        
        return {
            'peak_bac': round(peak_bac, 3),
            'current_bac': round(current_bac, 3),
            'bac_calculation_time': target_time,  # Zeitpunkt der BAK-Berechnung
            'timing_description': timing_description,  # Beschreibung des Messzeitpunkts
            'timing_mode': timing_mode,  # Gewählter Modus
            'model': model.value,
            'alcohol_grams': round(total_alcohol, 1),
            'elimination_time': f"{(current_bac / global_elimination_rate):.1f} Stunden" if current_bac > 0 else "Bereits nüchtern",
            'peak_time': peak_time.strftime('%H:%M') if peak_time else "N/A",
            'time_to_03': time_to_05,
            'time_to_00': time_to_00,
            'elimination_rate': global_elimination_rate,  # Globale Rate dokumentieren
            'r_factor': round(r_factor, 3),
            'person_weight': person.weight,
            'body_fat_factor': round(1.0 - (person.body_fat - 20) * 0.01, 3),
            'bac_values': bac_values,  # Für Diagramm
            'individual_contributions': individual_contributions,  # Mit globaler Elimination
            'total_drinks': len(drinks),
            'calculation_details': {
                'zwischenschritt_1': f"Verteilungsvolumen = {person.weight} kg × {r_factor:.3f} = {person.weight * r_factor:.1f} L",
                'zwischenschritt_2': f"Gesamtalkohol = {total_alcohol:.1f} g (Summe aller Getränke)",
                'individual_peaks': f"{len(drinks)} Einzelgetränke mit separaten Resorptionskurven",
                'körperfett_korrektur': f"Körperfett-Faktor = {round(1.0 - (person.body_fat - 20) * 0.01, 3)}",
                'messzeitpunkt': timing_description,  # Dokumentation des Messzeitpunkts
                'elimination_prinzip': f"GLOBALE Elimination: {global_elimination_rate:.3f} ‰/h auf Gesamt-BAK (nicht pro Getränk)"
            }
        }

    def _calculate_resorption_only(self, current_time, drink_contrib):
        """Berechnet nur den Resorptionsbeitrag eines Getränks (ohne Elimination)"""
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
            # Nach Peak: Vollständige Resorption erreicht (ohne individuelle Elimination)
            return peak_bac

    def _get_base_resorption_time(self) -> float:
        """Bestimmt die Basis-Resorptionszeit basierend auf Benutzer-Einstellung"""
        resorption_setting = self.settings_data.get('resorption_time', 'Normal (45 min)')
        
        if 'Schnell (30 min)' in resorption_setting:
            return 0.5  # 30 Minuten
        elif 'Normal (45 min)' in resorption_setting:
            return 0.75  # 45 Minuten
        elif 'Langsam (60 min)' in resorption_setting:
            return 1.0  # 60 Minuten
        else:
            return 0.75  # Standard: 45 Minuten
    
    def _get_meal_factor(self) -> float:
        """Bestimmt den Mahlzeiten-Faktor für Resorptionsverzögerung"""
        meal_status = self.settings_data.get('meal_status', 'Nüchtern')
        
        if meal_status == 'Nüchtern':
            return 1.0  # Keine Verzögerung
        elif meal_status == 'Leichte Mahlzeit':
            return 1.3  # 30% langsamer
        elif meal_status == 'Normale Mahlzeit':
            return 1.6  # 60% langsamer
        elif meal_status == 'Schwere Mahlzeit':
            return 2.0  # 100% langsamer (doppelt so lang)
        else:
            return 1.0  # Standard: nüchtern
    
    def _get_drinking_habit_factor(self, drinking_habit: str) -> float:
        """Bestimmt den Trinkgewohnheiten-Faktor für Enzyminduktion"""
        if drinking_habit == 'Abstinent':
            return 0.95  # 5% langsamere Elimination (weniger Enzyme)
        elif drinking_habit == 'Gelegentlich':
            return 1.0   # Standard-Elimination
        elif drinking_habit == 'Regelmäßig':
            return 1.2   # 20% schnellere Elimination (Enzyminduktion)
        elif drinking_habit == 'Täglich':
            return 1.4   # 40% schnellere Elimination (starke Enzyminduktion)
        else:
            return 1.0   # Standard

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
        """Berechnet die BAK-Kurve für alle Getränke mit GLOBALER Elimination"""
        if not drinks_data:
            return [], []
        
        # HINWEIS: Diese Methode ist veraltet und sollte durch die neue 
        # globale Elimination in _mock_calculation ersetzt werden.
        # Für Kompatibilität wird eine vereinfachte Version bereitgestellt.
        
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
        
        # Vereinfachte globale BAK-Berechnung
        bac_values = []
        global_elimination_rate = getattr(self, 'elimination_rate', 0.15)  # Fallback
        
        # Finde globalen Peak-Zeitpunkt (vereinfacht: 1 Stunde nach letztem Getränk)
        global_peak_time = max(drink_times) + timedelta(hours=1)
        
        for current_time in time_points:
            # Summiere alle Resorptionsbeiträge (ohne individuelle Elimination)
            total_resorption = 0.0
            
            for drink in sorted_drinks:
                # Vereinfachte Resorptionsberechnung
                if current_time >= drink['time']:
                    hours_since_drink = (current_time - drink['time']).total_seconds() / 3600
                    if hours_since_drink <= 1.0:  # Resorptionsphase
                        progress = min(1.0, hours_since_drink)
                        alcohol_grams = drink['volume'] * (drink['alcohol_content'] / 100) * 0.8
                        r_factor = 0.68 if gender == 'Männlich' else 0.55
                        drink_bac = (alcohol_grams / (weight * r_factor)) * progress
                        total_resorption += drink_bac
                    else:  # Nach Resorption: volle BAK
                        alcohol_grams = drink['volume'] * (drink['alcohol_content'] / 100) * 0.8
                        r_factor = 0.68 if gender == 'Männlich' else 0.55
                        drink_bac = alcohol_grams / (weight * r_factor)
                        total_resorption += drink_bac
            
            # Globale Elimination anwenden
            if current_time <= global_peak_time:
                final_bac = total_resorption
            else:
                hours_since_peak = (current_time - global_peak_time).total_seconds() / 3600
                elimination_amount = global_elimination_rate * hours_since_peak
                final_bac = max(0.0, total_resorption - elimination_amount)
            
            bac_values.append(final_bac)
        
        return time_points, bac_values, drink_times 