"""
UI Components für BAK-Kalkulator v2.0

Wiederverwendbare UI-Widgets:
- PersonDataWidget: Eingabe von Personendaten
- DrinksWidget: Getränkeverwaltung
- CalculationSettingsWidget: Berechnungseinstellungen
- ResultsWidget: Ergebnisanzeige mit Charts
"""

from .person_widget import PersonDataWidget
from .drinks_widget import DrinksWidget
from .calculation_settings_widget import CalculationSettingsWidget
from .results_widget import ResultsWidget

__all__ = [
    "PersonDataWidget",
    "DrinksWidget", 
    "CalculationSettingsWidget",
    "ResultsWidget"
] 