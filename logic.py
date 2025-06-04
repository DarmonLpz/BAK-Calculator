from datetime import datetime, timedelta
from typing import List
from models import Person, Drink, CalculationSettings, BACResult, BAKModel

class BACCalculator:
    def __init__(self):
        self.person = None
        self.drinks: List[Drink] = []
        self.settings = None
    
    def set_person(self, person: Person):
        """Setzt die Personendaten"""
        self.person = person
    
    def add_drink(self, drink: Drink):
        """Fügt ein Getränk hinzu"""
        self.drinks.append(drink)
    
    def set_settings(self, settings: CalculationSettings):
        """Setzt die Berechnungseinstellungen"""
        self.settings = settings
    
    def calculate_bac(self) -> List[BACResult]:
        """Berechnet die BAK nach allen ausgewählten Modellen"""
        if not all([self.person, self.drinks, self.settings]):
            raise ValueError("Nicht alle erforderlichen Daten sind vorhanden")
        
        results = []
        for model in BAKModel:
            if model == self.settings.model:
                result = self._calculate_single_model(model)
                results.append(result)
        
        return results
    
    def _calculate_single_model(self, model: BAKModel) -> BACResult:
        """Berechnet die BAK nach einem spezifischen Modell"""
        # Widmark-Formel als Basis
        total_alcohol = sum(drink.get_alcohol_grams() for drink in self.drinks)
        
        # Verteilungsfaktor r nach Widmark
        r = 0.7 if self.person.gender == "männlich" else 0.6
        
        # Körpergewicht in kg
        weight = self.person.weight
        
        # Maximale BAK
        peak_bac = (total_alcohol / (weight * r)) * 100
        
        # Zeitpunkt des Maximums (abhängig vom Resorptionsmodus)
        if self.settings.resorption_mode == "Nüchtern":
            peak_time = min(drink.time for drink in self.drinks) + timedelta(minutes=30)
        else:
            peak_time = min(drink.time for drink in self.drinks) + timedelta(minutes=60)
        
        # Berechnung der Rückkehrzeiten
        elimination_rate = self.settings.elimination_rate / 100  # Umrechnung in ‰/h
        
        # Zeit bis unter 0.3‰
        time_to_sober = peak_time + timedelta(hours=peak_bac / elimination_rate)
        
        # Zeit bis 0.0‰
        time_to_zero = peak_time + timedelta(hours=(peak_bac + 0.1) / elimination_rate)
        
        return BACResult(
            peak_bac=peak_bac,
            peak_time=peak_time,
            time_to_sober=time_to_sober,
            time_to_zero=time_to_zero,
            model=model
        )
    
    def get_bac_over_time(self, start_time: datetime, end_time: datetime, 
                         interval_minutes: int = 15) -> List[tuple]:
        """Berechnet den BAK-Verlauf über die Zeit"""
        if not all([self.person, self.drinks, self.settings]):
            raise ValueError("Nicht alle erforderlichen Daten sind vorhanden")
        
        time_points = []
        current_time = start_time
        while current_time <= end_time:
            time_points.append(current_time)
            current_time += timedelta(minutes=interval_minutes)
        
        bac_values = []
        for time_point in time_points:
            # Berechne BAK für jeden Zeitpunkt
            # (vereinfachte Berechnung, sollte je nach Modell angepasst werden)
            total_alcohol = sum(
                drink.get_alcohol_grams() 
                for drink in self.drinks 
                if drink.time <= time_point
            )
            
            r = 0.7 if self.person.gender == "männlich" else 0.6
            weight = self.person.weight
            
            bac = (total_alcohol / (weight * r)) * 100
            
            # Berücksichtige Abbau
            if time_point > min(drink.time for drink in self.drinks):
                hours_passed = (time_point - min(drink.time for drink in self.drinks)).total_seconds() / 3600
                elimination = hours_passed * (self.settings.elimination_rate / 100)
                bac = max(0, bac - elimination)
            
            bac_values.append((time_point, bac))
        
        return bac_values 