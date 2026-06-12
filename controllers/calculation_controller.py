"""
Controller für die BAK-Berechnung.

Vermittelt zwischen der GUI (liefert rohe Dictionaries) und der
Berechnungs-Engine (arbeitet mit typisierten Objekten). Enthält Debouncing
und einen einfachen Ergebnis-Cache, damit die GUI flüssig bleibt.
"""

import hashlib
import json
from datetime import datetime
from typing import Dict, List

from PyQt6.QtCore import QObject, pyqtSignal, QTimer

from models import (
    Person, Drink, CalculationSettings, Gender, BAKModel,
)
from calculations import BACCalculator


# Zuordnung GUI-Text -> Modell-Enum
MODEL_MAPPING = {
    'Widmark': BAKModel.WIDMARK,
    'Watson': BAKModel.WATSON,
    'Forrest': BAKModel.FORREST,
    'Seidl': BAKModel.SEIDL,
}

# Resorptionsdauer (Minuten) je Mahlzeit-Status für den Auto-Modus
MEAL_ABSORPTION_MINUTES = {
    'Nüchtern': 30,
    'Leichte Mahlzeit': 60,
    'Normale Mahlzeit': 90,
    'Schwere Mahlzeit': 120,
}

# Feste Resorptionsdauern aus dem Resorptionszeit-Combo
RESORPTION_PRESETS = {
    'Schnell (20 min)': 20,
    'Normal (45 min)': 45,
    'Langsam (90 min)': 90,
    'Sehr langsam (120 min)': 120,
}

# Trinkgewohnheit -> Multiplikator der Eliminationsrate (Enzyminduktion)
HABIT_FACTOR = {
    'Abstinent': 1.0,
    'Gelegentlich': 1.0,
    'Regelmäßig': 1.15,
    'Täglich': 1.30,
}


class CalculationController(QObject):
    """Controller für BAK-Berechnungen mit Debouncing und Caching."""

    calculation_started = pyqtSignal()
    calculation_finished = pyqtSignal(dict)
    calculation_error = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        self.calculation_timer = QTimer()
        self.calculation_timer.setSingleShot(True)
        self.calculation_timer.timeout.connect(self._perform_calculation)

        self.calculation_cache: Dict[str, dict] = {}
        self.cache_limit = 50

        self.person_data = None
        self.drinks_data: List[Dict] = []
        self.settings_data = None

        self.calculator = BACCalculator()

    # ------------------------------------------------------------------ #
    # Eingaben
    # ------------------------------------------------------------------ #
    def set_person_data(self, data: Dict):
        self.person_data = data
        self._trigger_calculation()

    def set_drinks_data(self, data: List[Dict]):
        self.drinks_data = data
        self._trigger_calculation()

    def set_calculation_settings(self, data: Dict):
        self.settings_data = data
        self._trigger_calculation()

    def _trigger_calculation(self):
        self.calculation_timer.stop()
        self.calculation_timer.start(300)  # 300 ms Debounce

    # ------------------------------------------------------------------ #
    # Ablauf
    # ------------------------------------------------------------------ #
    def _perform_calculation(self):
        if not self._validate_data():
            # Keine vollständigen Daten -> leeres Ergebnis melden
            self.calculation_finished.emit({})
            return
        try:
            self.calculation_started.emit()
            cache_key = self._generate_cache_key()
            if cache_key in self.calculation_cache:
                self.calculation_finished.emit(self.calculation_cache[cache_key])
                return
            results = self._calculate_bac()
            self._update_cache(cache_key, results)
            self.calculation_finished.emit(results)
        except Exception as e:  # pragma: no cover - defensive
            import traceback
            traceback.print_exc()
            self.calculation_error.emit(str(e))

    def _validate_data(self) -> bool:
        if not self.person_data or not self.drinks_data or not self.settings_data:
            return False
        if not self.settings_data.get('models'):
            return False
        return True

    # ------------------------------------------------------------------ #
    # Umwandlung der GUI-Daten + Aufruf der Engine
    # ------------------------------------------------------------------ #
    def _calculate_bac(self) -> Dict:
        gender = (Gender.MALE
                  if self.person_data.get('gender') == 'Männlich'
                  else Gender.FEMALE)

        person = Person(
            gender=gender,
            age=int(self.person_data.get('age', 30)),
            height=int(self.person_data.get('height', 180)),
            weight=float(self.person_data.get('weight', 80)),
            body_fat=float(self.person_data.get('body_fat', 20)),
            drinking_habit=self.person_data.get('drinking_habit', 'Gelegentlich'),
        )

        drinks = [
            Drink(
                name=d['name'],
                volume=float(d['volume']),
                alcohol_content=float(d['alcohol_content']),
                time=d['time'],
            )
            for d in self.drinks_data
        ]

        models = [MODEL_MAPPING[m] for m in self.settings_data['models']
                  if m in MODEL_MAPPING]

        settings = CalculationSettings(
            models=models,
            elimination_rate=self._resolve_elimination_rate(gender),
            resorption_deficit=float(self.settings_data.get('resorption_deficit', 10)),
            absorption_minutes=self._resolve_absorption_minutes(),
            meal_status=self.settings_data.get('meal_status', 'Nüchtern'),
        )

        return self.calculator.calculate(person, drinks, settings, models)

    def _resolve_elimination_rate(self, gender: Gender) -> float:
        """Ermittelt die Eliminationsrate (‰/h) aus den GUI-Einstellungen."""
        choice = self.settings_data.get('elimination_rate', 'Normal (0.15 ‰/h)')

        if choice.startswith('Auto'):
            rate = 0.17 if gender == Gender.MALE else 0.15
            habit = self.person_data.get('drinking_habit', 'Gelegentlich')
            rate *= HABIT_FACTOR.get(habit, 1.0)
            return rate
        if choice.startswith('Niedrig'):
            return 0.10
        if choice.startswith('Normal'):
            return 0.15
        if choice.startswith('Hoch'):
            return 0.20
        if choice.startswith('Manuell'):
            return float(self.settings_data.get('manual_elimination_rate', 0.15))
        return 0.15

    def _resolve_absorption_minutes(self) -> float:
        """Ermittelt die Resorptionsdauer (min) aus den GUI-Einstellungen."""
        choice = self.settings_data.get('resorption_time',
                                        'Auto (abhängig von Mahlzeit)')
        if choice in RESORPTION_PRESETS:
            return RESORPTION_PRESETS[choice]
        # Auto: aus Mahlzeit-Status ableiten
        meal = self.settings_data.get('meal_status', 'Nüchtern')
        return MEAL_ABSORPTION_MINUTES.get(meal, 30)

    # ------------------------------------------------------------------ #
    # Cache
    # ------------------------------------------------------------------ #
    def _generate_cache_key(self) -> str:
        def convert(obj):
            if isinstance(obj, dict):
                return {k: convert(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [convert(i) for i in obj]
            if isinstance(obj, datetime):
                return obj.isoformat()
            return obj

        cache_data = convert({
            'person': self.person_data,
            'drinks': self.drinks_data,
            'settings': self.settings_data,
        })
        json_str = json.dumps(cache_data, sort_keys=True, default=str)
        return hashlib.md5(json_str.encode()).hexdigest()

    def _update_cache(self, key: str, results: Dict):
        if len(self.calculation_cache) >= self.cache_limit:
            oldest_key = next(iter(self.calculation_cache))
            del self.calculation_cache[oldest_key]
        self.calculation_cache[key] = results

    def get_cache_info(self) -> Dict:
        return {'size': len(self.calculation_cache), 'limit': self.cache_limit}

    def clear_cache(self):
        self.calculation_cache.clear()

    def force_calculation(self):
        self.calculation_timer.stop()
        self._perform_calculation()
