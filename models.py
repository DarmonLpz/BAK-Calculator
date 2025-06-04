from dataclasses import dataclass
from datetime import datetime
from enum import Enum

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
    height: int  # in cm
    weight: float  # in kg
    body_fat: float = 20.0  # Standardwert, falls nicht gesetzt
    bmi: float = 0.0
    
    def calculate_bmi(self) -> float:
        """Berechnet den BMI-Wert"""
        height_m = self.height / 100
        return self.weight / (height_m * height_m)

@dataclass
class Drink:
    name: str
    volume: float  # in ml
    alcohol_content: float  # in %
    time: datetime
    
    def get_alcohol_grams(self) -> float:
        """Berechnet die Alkoholmenge in Gramm"""
        # Alkohol hat eine Dichte von 0.789 g/ml
        return self.volume * (self.alcohol_content / 100) * 0.789

@dataclass
class CalculationSettings:
    models: list[BAKModel]  # Liste von Modellen für Vergleichsberechnung
    resorption_mode: ResorptionMode
    elimination_rate: float  # in ‰/h
    tolerance_factor: float = 1.0

@dataclass
class BACResult:
    peak_bac: float  # in ‰
    peak_time: datetime
    time_to_sober: datetime
    time_to_zero: datetime
    model: BAKModel

@dataclass 
class CalculationResults:
    """Sammelt alle Berechnungsergebnisse für verschiedene Modelle"""
    results: dict[BAKModel, BACResult]  # Ergebnisse pro Modell
    person: Person
    drinks: list[Drink]
    settings: CalculationSettings 