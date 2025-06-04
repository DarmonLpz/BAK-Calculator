import matplotlib.pyplot as plt
import matplotlib.dates as mdates

class BacPlotWidget:
    def __init__(self, fig, ax):
        self.fig = fig
        self.ax = ax

    def plot_bac_curve(self, times, bac_values, drink_times=None):
        """Zeichnet die BAK-Kurve"""
        self.ax.clear()
        
        # Hauptkurve
        self.ax.plot(times, bac_values, 'b-', linewidth=2, label='BAK')
        
        # Vertikale Linien für Drinkzeitpunkte
        if drink_times:
            for drink_time in drink_times:
                self.ax.axvline(x=drink_time, color='r', linestyle='--', alpha=0.5)
                # Zeitpunkt als Text über der Linie
                self.ax.text(drink_time, self.ax.get_ylim()[1], 
                           drink_time.strftime('%H:%M'),
                           rotation=90, va='top', ha='center',
                           color='r', alpha=0.7)
        
        # Horizontale Linien für Promillegrenzen
        self.ax.axhline(y=0.5, color='g', linestyle='--', alpha=0.5, label='0.5‰')
        self.ax.axhline(y=1.1, color='r', linestyle='--', alpha=0.5, label='1.1‰')
        
        # Achsenbeschriftungen
        self.ax.set_xlabel('Zeit')
        self.ax.set_ylabel('Blutalkoholkonzentration (‰)')
        self.ax.set_title('BAK-Verlauf')
        
        # X-Achse: Nur jede 2. Stunde beschriften
        self.ax.xaxis.set_major_locator(mdates.HourLocator(interval=2))
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        
        # Y-Achse: Bereich 0-2‰
        self.ax.set_ylim(0, 2)
        
        # Grid
        self.ax.grid(True, alpha=0.3)
        
        # Legende
        self.ax.legend()
        
        # X-Achsenbeschriftungen rotieren
        plt.setp(self.ax.get_xticklabels(), rotation=45, ha='right')
        
        # Layout anpassen
        self.fig.tight_layout()
        
        # Canvas aktualisieren
        self.canvas.draw() 