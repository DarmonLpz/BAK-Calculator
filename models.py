"""
Datenmodelle des BAK-Kalkulators.

Hier sind alle zentralen Datenstrukturen sowie die gemeinsam genutzten
physikalischen Konstanten definiert. Wichtig: Die Dichte von Ethanol wird
hier EINMAL festgelegt und überall im Programm aus dieser Konstante bezogen,
damit Anzeige und Berechnung niemals auseinanderlaufen.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

# ---------------------------------------------------------------------------
# Physikalische Konstanten (einzige Quelle der Wahrheit)
# ---------------------------------------------------------------------------
# Dichte von reinem Ethanol bei 20 °C. In der deutschen forensischen Praxis
# (Widmark) wird traditionell mit 0,8 g/ml gerechnet. Dieser Wert wird im
# gesamten Programm verwendet.
ETHANOL_DENSITY: float = 0.8  # g/ml


def alcohol_grams(volume_ml: float, alcohol_percent: float) -> float:
    """Reine Alkoholmenge eines Getränks in Gramm.

    Formel: Volumen (ml) × Vol.-% / 100 × Dichte (g/ml)
    """
    try:
        return float(volume_ml) * (float(alcohol_percent) / 100.0) * ETHANOL_DENSITY
    except (TypeError, ValueError):
        return 0.0


class Gender(Enum):
    MALE = "männlich"
    FEMALE = "weiblich"


class BAKModel(Enum):
    WIDMARK = "Widmark"
    WATSON = "Watson"
    FORREST = "Forrest"
    SEIDL = "Seidl"


class ResorptionMode(Enum):
    FASTING = "Nüchtern"
    WITH_FOOD = "Mit Mahlzeit"


@dataclass
class Person:
    gender: Gender
    age: int
    height: int          # in cm
    weight: float        # in kg
    body_fat: float = 20.0   # Körperfettanteil in %
    drinking_habit: str = "Gelegentlich"

    def calculate_bmi(self) -> float:
        """Berechnet den BMI-Wert (kg/m²)."""
        if self.height <= 0:
            return 0.0
        height_m = self.height / 100
        return self.weight / (height_m * height_m)


@dataclass
class Drink:
    name: str
    volume: float            # in ml
    alcohol_content: float   # in Vol.-%
    time: datetime

    def get_alcohol_grams(self) -> float:
        """Reine Alkoholmenge dieses Getränks in Gramm."""
        return alcohol_grams(self.volume, self.alcohol_content)


@dataclass
class CalculationSettings:
    """Sämtliche vom Benutzer einstellbaren Berechnungsparameter."""
    models: list                      # Liste von BAKModel
    elimination_rate: float = 0.15    # in ‰/h
    resorption_deficit: float = 10.0  # in % (First-Pass / Resorptionsverlust)
    absorption_minutes: float = 30.0  # Resorptionsdauer bis Peak in Minuten
    meal_status: str = "Nüchtern"


@dataclass
class BACResult:
    """Ergebnis eines einzelnen Modells."""
    model: str
    peak_bac: float
    peak_time: datetime
    current_bac: float
    r_factor: float
    elimination_rate: float
    total_alcohol_g: float
    effective_alcohol_g: float
    bac_values: list = field(default_factory=list)
    time_to_05: datetime = None
    time_to_03: datetime = None
    time_to_00: datetime = None
    individual_contributions: list = field(default_factory=list)
