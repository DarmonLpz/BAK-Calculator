"""
Berechnungs-Engine des BAK-Kalkulators.

Diese Datei enthält die EINZIGE, echte Berechnungslogik. Sie modelliert für
jedes Getränk eine eigene Resorptions- (linearer Anstieg bis zum Peak) und
eine Eliminationsphase (linearer Abbau nach Zero-Order-Kinetik). Die
Einzelkurven werden zur Gesamtkurve aufsummiert (Superposition).

Alle vom Benutzer gewählten Einstellungen (Eliminationsrate, Resorptions-
defizit, Resorptionsdauer, Mahlzeit) wirken sich direkt auf das Ergebnis aus.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from models import (
    Person, Drink, CalculationSettings, BAKModel, Gender,
    ETHANOL_DENSITY,
)


class BACCalculator:
    """Wissenschaftliche BAK-Berechnung mit Einzelgetränk-Pharmakodynamik."""

    # ------------------------------------------------------------------ #
    # Verteilungsfaktor r je Modell
    # ------------------------------------------------------------------ #
    @staticmethod
    def distribution_factor(model: BAKModel, person: Person) -> float:
        """Verteilungsfaktor r (L/kg) abhängig vom gewählten Modell."""
        is_male = person.gender == Gender.MALE

        if model == BAKModel.WIDMARK:
            # Klassische, feste Faktoren (Gullberg & Jones)
            r = 0.68 if is_male else 0.55

        elif model == BAKModel.WATSON:
            # Anthropometrisch über das Gesamtkörperwasser (TBW)
            if is_male:
                tbw = (2.447 - 0.09516 * person.age
                       + 0.1074 * person.height + 0.3362 * person.weight)
            else:
                tbw = (-2.097 + 0.1069 * person.height
                       + 0.2466 * person.weight)
            # Umrechnung TBW -> Widmark-r: Blut besteht zu ~80 % aus Wasser
            r = tbw / (0.8 * person.weight) if person.weight > 0 else 0.6

        elif model == BAKModel.FORREST:
            # Widmark-Basis mit Alters- und Körperfettkorrektur
            base = 0.68 if is_male else 0.55
            age_factor = max(0.80, 1.0 - 0.01 * max(0, person.age - 20))
            fat_factor = max(0.80, 1.0 - 0.01 * (person.body_fat - 20))
            r = base * age_factor * fat_factor

        elif model == BAKModel.SEIDL:
            # Originale Seidl-Regression (2000), Größe in cm, Gewicht in kg
            if is_male:
                r = 0.31608 - 0.004821 * person.weight + 0.004432 * person.height
            else:
                r = 0.31223 - 0.006446 * person.weight + 0.004466 * person.height
        else:
            r = 0.68 if is_male else 0.55

        # Auf physiologisch sinnvollen Bereich begrenzen
        return max(0.40, min(0.90, r))

    # ------------------------------------------------------------------ #
    # Hauptberechnung
    # ------------------------------------------------------------------ #
    def calculate(self, person: Person, drinks: List[Drink],
                  settings: CalculationSettings,
                  models: List[BAKModel],
                  now: Optional[datetime] = None) -> Dict[str, dict]:
        """Berechnet die Ergebnisse für alle gewählten Modelle.

        Rückgabe: ``{modellname: ergebnis_dict}``
        """
        if not person or not drinks or not models:
            return {}

        now = now or datetime.now()
        results: Dict[str, dict] = {}
        for model in models:
            results[model.value] = self._calculate_model(
                person, drinks, settings, model, now
            )
        return results

    # ------------------------------------------------------------------ #
    def _calculate_model(self, person, drinks, settings, model, now) -> dict:
        r = self.distribution_factor(model, person)
        elimination_rate = settings.elimination_rate          # ‰/h
        absorption_hours = max(settings.absorption_minutes, 1) / 60.0
        deficit_factor = max(0.0, 1.0 - settings.resorption_deficit / 100.0)

        total_alcohol = sum(d.get_alcohol_grams() for d in drinks)
        effective_alcohol = total_alcohol * deficit_factor

        # Einzelgetränk-Beiträge vorbereiten
        contributions = []
        for i, drink in enumerate(sorted(drinks, key=lambda d: d.time)):
            grams = drink.get_alcohol_grams() * deficit_factor
            peak_contrib = grams / (person.weight * r) if person.weight > 0 else 0.0
            contributions.append({
                'index': i,
                'name': drink.name,
                'grams': drink.get_alcohol_grams(),
                'effective_grams': grams,
                'consumption_time': drink.time,
                'peak_time': drink.time + timedelta(hours=absorption_hours),
                'peak_contribution': peak_contrib,
                'absorption_hours': absorption_hours,
            })

        first_time = min(c['consumption_time'] for c in contributions)
        last_time = max(c['consumption_time'] for c in contributions)

        def bac_at(t: datetime) -> float:
            """Gesamt-BAK zu einem beliebigen Zeitpunkt (Superposition)."""
            total = 0.0
            for c in contributions:
                if t < c['consumption_time']:
                    continue
                if t <= c['peak_time']:
                    # Resorptionsphase: linearer Anstieg auf den Peak
                    elapsed = (t - c['consumption_time']).total_seconds() / 3600
                    frac = elapsed / c['absorption_hours'] if c['absorption_hours'] > 0 else 1.0
                    total += c['peak_contribution'] * min(1.0, max(0.0, frac))
                else:
                    # Eliminationsphase: linearer Abbau ab dem Peak
                    hrs = (t - c['peak_time']).total_seconds() / 3600
                    total += max(0.0, c['peak_contribution'] - elimination_rate * hrs)
            return total

        # Zeitraster (5-Minuten-Schritte) für Diagramm und Kennzahlen
        start = first_time - timedelta(minutes=30)
        # Endzeitpunkt: bis sicher nüchtern, mindestens 2 h nach "jetzt"
        peak_total = sum(c['peak_contribution'] for c in contributions)
        sober_h = (peak_total / elimination_rate) if elimination_rate > 0 else 12
        end = max(now + timedelta(hours=2),
                  last_time + timedelta(hours=absorption_hours + sober_h + 1))

        bac_values = []
        step = timedelta(minutes=5)
        t = start
        while t <= end:
            bac_values.append((t, round(bac_at(t), 4)))
            t += step

        # Peak ermitteln
        peak_time, peak_bac = max(bac_values, key=lambda p: p[1])

        # Aktuelle BAK (direkt am Zeitpunkt "jetzt" ausgewertet)
        current_bac = bac_at(now) if start <= now <= end else 0.0

        # Zeitpunkte des Unterschreitens der Grenzwerte (nach dem Peak)
        time_to_05 = self._crossing_after(bac_values, peak_time, 0.5)
        time_to_03 = self._crossing_after(bac_values, peak_time, 0.3)
        time_to_00 = self._crossing_after(bac_values, peak_time, 0.005)

        # Einzelbeiträge zum Zeitpunkt "jetzt" (für die Detailanalyse)
        individual = []
        for c in contributions:
            cur = 0.0
            if now >= c['consumption_time']:
                if now <= c['peak_time']:
                    elapsed = (now - c['consumption_time']).total_seconds() / 3600
                    frac = elapsed / c['absorption_hours'] if c['absorption_hours'] > 0 else 1.0
                    cur = c['peak_contribution'] * min(1.0, max(0.0, frac))
                else:
                    hrs = (now - c['peak_time']).total_seconds() / 3600
                    cur = max(0.0, c['peak_contribution'] - elimination_rate * hrs)
            individual.append({
                'drink_number': c['index'] + 1,
                'name': c['name'],
                'alcohol_grams': c['grams'],
                'consumption_time': c['consumption_time'].strftime('%d.%m. %H:%M'),
                'peak_bac': c['peak_contribution'],
                'peak_time': c['peak_time'].strftime('%H:%M'),
                'current_contribution': cur,
                'resorption_duration': c['absorption_hours'],
            })

        elimination_time = (f"{current_bac / elimination_rate:.1f} Stunden"
                            if current_bac > 0 and elimination_rate > 0
                            else "Bereits nüchtern")

        return {
            'model': model.value,
            'peak_bac': round(peak_bac, 3),
            'peak_time': peak_time.strftime('%H:%M'),
            'peak_time_obj': peak_time,
            'current_bac': round(current_bac, 3),
            'r_factor': round(r, 3),
            'elimination_rate': round(elimination_rate, 3),
            'absorption_minutes': round(absorption_hours * 60),
            'resorption_deficit': settings.resorption_deficit,
            'meal_status': settings.meal_status,
            'alcohol_grams': round(total_alcohol, 1),
            'effective_alcohol_grams': round(effective_alcohol, 1),
            'person_weight': person.weight,
            'elimination_time': elimination_time,
            'time_to_05': time_to_05,
            'time_to_03': time_to_03,
            'time_to_00': time_to_00,
            'bac_values': bac_values,
            'individual_contributions': individual,
            'total_drinks': len(drinks),
            'calculation_details': {
                'verteilungsvolumen': (
                    f"{person.weight} kg × {r:.3f} = "
                    f"{person.weight * r:.1f} L Verteilungsvolumen"),
                'gesamtalkohol': (
                    f"{total_alcohol:.1f} g Reinalkohol, davon nach "
                    f"{settings.resorption_deficit:.0f}% Resorptionsdefizit "
                    f"{effective_alcohol:.1f} g wirksam"),
                'einzelgetraenke': (
                    f"{len(drinks)} Getränk(e) mit eigener Resorptions- und "
                    f"Eliminationskurve, summiert zur Gesamtkurve"),
            },
        }

    # ------------------------------------------------------------------ #
    @staticmethod
    def _crossing_after(bac_values, peak_time, threshold) -> Optional[datetime]:
        """Erster Zeitpunkt NACH dem Peak, an dem die BAK <= threshold ist."""
        for t, bac in bac_values:
            if t >= peak_time and bac <= threshold:
                return t
        return None
