from datetime import datetime, timedelta
from typing import List, Tuple
from models import Person, Drink, CalculationSettings, BACResult, BAKModel, Gender, ResorptionMode

class BACCalculator:
    def __init__(self):
        self.person = None
        self.drinks: List[Drink] = []
        self.settings = None
    
    def set_person(self, person: Person):
        self.person = person
    
    def add_drink(self, drink: Drink):
        self.drinks.append(drink)
    
    def set_settings(self, settings: CalculationSettings):
        self.settings = settings
    
    def calculate_bac(self) -> List[Tuple[datetime, float]]:
        """Berechnet den BAK-Verlauf über die Zeit"""
        if not all([self.person, self.drinks, self.settings]):
            raise ValueError("Nicht alle erforderlichen Daten sind vorhanden")
        
        # Sortiere Getränke nach Zeit
        sorted_drinks = sorted(self.drinks, key=lambda x: x.time)
        start_time = sorted_drinks[0].time
        end_time = start_time + timedelta(hours=24)  # 24 Stunden Vorhersage
        
        # Berechne Zeitpunkte im 15-Minuten-Intervall
        time_points = []
        current_time = start_time
        while current_time <= end_time:
            time_points.append(current_time)
            current_time += timedelta(minutes=15)
        
        # Berechne BAK für jeden Zeitpunkt
        bac_values = []
        for time_point in time_points:
            bac = self._calculate_bac_at_time(time_point)
            bac_values.append((time_point, bac))
        
        return bac_values
    
    def _calculate_bac_at_time(self, time_point: datetime) -> float:
        """Berechnet die BAK zu einem bestimmten Zeitpunkt"""
        # Berechne Gesamtalkoholmenge bis zu diesem Zeitpunkt
        total_alcohol = sum(
            drink.volume * (drink.alcohol_content / 100) * 0.8  # 0.8 g/ml Dichte von Alkohol
            for drink in self.drinks
            if drink.time <= time_point
        )
        
        # Berechne Verteilungsfaktor r
        r = self._calculate_distribution_factor()
        
        # Berechne Abbaurate
        elimination_rate = self._calculate_elimination_rate()
        
        # Berechne Resorptionszeit
        resorption_time = self._calculate_resorption_time()
        
        # Berücksichtige Resorptionsdefizit vor der Modellberechnung
        effective_alcohol = total_alcohol * (1 - self.settings.resorption_deficit / 100)
        
        # Berechne BAK nach dem gewählten Modell
        if self.settings.model == "Widmark":
            bac = self._calculate_widmark(effective_alcohol, r, elimination_rate, time_point)
        elif self.settings.model == "Watson":
            bac = self._calculate_watson(effective_alcohol, r, elimination_rate, time_point)
        elif self.settings.model == "Forrest":
            bac = self._calculate_forrest(effective_alcohol, r, elimination_rate, time_point)
        elif self.settings.model == "Seidl":
            bac = self._calculate_seidl(effective_alcohol, r, elimination_rate, time_point)
        else:
            raise ValueError(f"Unbekanntes Berechnungsmodell: {self.settings.model}")
        
        return max(0, bac)  # BAK kann nicht negativ sein
    
    def _calculate_distribution_factor(self) -> float:
        """Berechnet den Verteilungsfaktor r"""
        if hasattr(self.settings, 'model') and self.settings.model == "Watson":
            # Watson-Gleichung für Körperwasseranteil
            if self.person.gender == Gender.MALE:
                tbw = 2.447 - 0.09516 * self.person.age + 0.1074 * self.person.height + 0.3362 * self.person.weight
            else:
                tbw = -2.097 + 0.1069 * self.person.height + 0.2466 * self.person.weight
            return tbw / (0.8 * self.person.weight)
        else:
            # Standard-Widmark-Faktor
            return 0.7 if self.person.gender == Gender.MALE else 0.6
    
    def _calculate_elimination_rate(self) -> float:
        """Berechnet die Abbaurate in ‰/h"""
        if hasattr(self.settings, 'elimination_rate') and self.settings.elimination_rate == "Auto":
            base_rate = 0.15  # Standardwert
            # Anpassung nach Geschlecht
            if self.person.gender == Gender.FEMALE:
                base_rate *= 1.1
            # Anpassung nach Trinkgewohnheit
            if hasattr(self.person, 'drinking_habit') and self.person.drinking_habit == "Häufig":
                base_rate *= 1.25
            return base_rate
        else:
            return getattr(self.settings, 'manual_elimination_rate', 0.15) / 100  # Umrechnung in ‰/h
    
    def _calculate_resorption_time(self) -> float:
        """Berechnet die Resorptionszeit in Stunden"""
        if hasattr(self.settings, 'resorption_time') and self.settings.resorption_time == "Auto":
            return 1.0 if getattr(self.settings, 'meal_status', '') == "Nüchtern" else 1.5
        else:
            return 1.0  # Standardwert
    
    def _calculate_widmark(self, total_alcohol: float, r: float, elimination_rate: float, time_point: datetime) -> float:
        """Berechnet BAK nach der Widmark-Formel"""
        hours_passed = (time_point - self.drinks[0].time).total_seconds() / 3600
        return (total_alcohol / (r * self.person.weight)) - (elimination_rate * hours_passed)
    
    def _calculate_watson(self, total_alcohol: float, r: float, elimination_rate: float, time_point: datetime) -> float:
        """Berechnet BAK nach der Watson-Gleichung"""
        # Watson verwendet bereits den angepassten r-Wert
        return self._calculate_widmark(total_alcohol, r, elimination_rate, time_point)
    
    def _calculate_forrest(self, total_alcohol: float, r: float, elimination_rate: float, time_point: datetime) -> float:
        """Berechnet BAK nach dem Forrest-Modell"""
        # Berechne BMI
        bmi = self.person.weight / ((self.person.height / 100) ** 2)
        
        # Korrigiere r basierend auf BMI
        if bmi < 18.5:
            r_corrected = r * 1.15
        elif bmi <= 25:
            r_corrected = r
        elif bmi <= 30:
            r_corrected = r * 0.9
        else:
            r_corrected = r * 0.85
        
        return self._calculate_widmark(total_alcohol, r_corrected, elimination_rate, time_point)
    
    def _calculate_seidl(self, total_alcohol: float, r: float, elimination_rate: float, time_point: datetime) -> float:
        """Berechnet BAK nach dem Seidl-Modell"""
        # Kombiniere Watson und Forrest
        bmi = self.person.weight / ((self.person.height / 100) ** 2)
        
        if bmi < 18.5:
            r_corrected = r * 1.15
        elif bmi <= 25:
            r_corrected = r
        elif bmi <= 30:
            r_corrected = r * 0.9
        else:
            r_corrected = r * 0.85
        
        return self._calculate_widmark(total_alcohol, r_corrected, elimination_rate, time_point)
    
    def get_peak_bac(self) -> Tuple[datetime, float]:
        """Berechnet den maximalen BAK-Wert und den Zeitpunkt"""
        bac_values = self.calculate_bac()
        peak_time, peak_bac = max(bac_values, key=lambda x: x[1])
        return peak_time, peak_bac
    
    def get_time_to_sober(self, threshold: float = 0.3) -> datetime:
        """Berechnet den Zeitpunkt, zu dem die BAK unter einen bestimmten Wert fällt"""
        bac_values = self.calculate_bac()
        for time_point, bac in bac_values:
            if bac <= threshold:
                return time_point
        return bac_values[-1][0]  # Falls nicht erreicht, gib den letzten Zeitpunkt zurück 