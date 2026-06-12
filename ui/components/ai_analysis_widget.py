"""
Widget für die KI-gestützte Analyse von Explorationstexten.

Der Anwender fügt eine frei formulierte Schilderung des Trinkverhaltens ein;
auf Knopfdruck extrahiert Claude daraus Getränke, Personendaten und den
gemessenen BAK-Wert. Das Ergebnis wird per Signal an das Hauptfenster
weitergereicht, das die Felder befüllt und die Berechnung anstößt.
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QTextEdit, QGroupBox)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QFont

from utils import ai_extractor


class ExtractionWorker(QThread):
    """Führt die KI-Extraktion im Hintergrund aus."""

    finished_ok = pyqtSignal(dict)
    failed = pyqtSignal(str)

    def __init__(self, text: str):
        super().__init__()
        self.text = text

    def run(self):
        try:
            result = ai_extractor.run_extraction(self.text)
            self.finished_ok.emit(result)
        except Exception as e:  # noqa: BLE001 - Fehler an die GUI melden
            self.failed.emit(str(e))


EXAMPLE_TEXT = (
    "Beispiel: \"Ich habe am Tatabend gegen 19:30 Uhr angefangen. Bis etwa "
    "22 Uhr habe ich vier Halbe Bier getrunken, danach noch drei Schnäpse. "
    "Ich bin männlich, 35 Jahre, 1,82 m und wiege 85 kg. Die Blutprobe um "
    "00:45 Uhr ergab 1,12 Promille (GC-FID).\""
)


class AiAnalysisWidget(QWidget):
    """Eingabe von Freitext und Anstoß der KI-Analyse."""

    # Liefert das normalisierte Extraktionsergebnis an das Hauptfenster
    extraction_ready = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self.setup_ui()
        self.refresh_status()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Titel + Erklärung
        title = QLabel("🤖 Konsumangaben aus Text analysieren")
        title.setFont(QFont("Inter", 18, QFont.Weight.Bold))
        layout.addWidget(title)

        intro = QLabel(
            "Fügen Sie die Schilderung des Trinkverhaltens ein (z. B. aus einer "
            "Exploration). Die KI filtert automatisch die Getränke, die "
            "Personendaten und – falls vorhanden – den gemessenen "
            "Blutalkoholwert samt Uhrzeit heraus, übernimmt sie in den Rechner "
            "und prüft die Plausibilität gegen den Messwert.")
        intro.setWordWrap(True)
        intro.setFont(QFont("Inter", 11))
        intro.setStyleSheet("color: #555;")
        layout.addWidget(intro)

        # Eingabe
        input_group = QGroupBox("Explorationstext")
        input_group.setFont(QFont("Inter", 13, QFont.Weight.Bold))
        input_layout = QVBoxLayout(input_group)
        self.text_input = QTextEdit()
        self.text_input.setFont(QFont("Inter", 12))
        self.text_input.setPlaceholderText(EXAMPLE_TEXT)
        self.text_input.setMinimumHeight(160)
        input_layout.addWidget(self.text_input)
        layout.addWidget(input_group)

        # Aktionsleiste
        action_layout = QHBoxLayout()
        self.status_label = QLabel("")
        self.status_label.setFont(QFont("Inter", 11))
        self.status_label.setWordWrap(True)
        action_layout.addWidget(self.status_label, 1)

        self.example_btn = QPushButton("Beispiel einfügen")
        self.example_btn.setFont(QFont("Inter", 11))
        self.example_btn.clicked.connect(self._insert_example)
        action_layout.addWidget(self.example_btn)

        self.analyze_btn = QPushButton("🤖 Mit KI analysieren")
        self.analyze_btn.setFont(QFont("Inter", 12, QFont.Weight.Bold))
        self.analyze_btn.setMinimumHeight(42)
        self.analyze_btn.setStyleSheet("""
            QPushButton { background-color: #6A1B9A; color: white; border: none;
                          border-radius: 8px; padding: 8px 20px; }
            QPushButton:hover { background-color: #571580; }
            QPushButton:disabled { background-color: #cccccc; color: #666; }
        """)
        self.analyze_btn.clicked.connect(self._on_analyze)
        action_layout.addWidget(self.analyze_btn)
        layout.addLayout(action_layout)

        # Ergebnis / Zusammenfassung
        result_group = QGroupBox("Erkannte Angaben")
        result_group.setFont(QFont("Inter", 13, QFont.Weight.Bold))
        result_layout = QVBoxLayout(result_group)
        self.result_view = QTextEdit()
        self.result_view.setReadOnly(True)
        self.result_view.setFont(QFont("Inter", 11))
        self.result_view.setPlaceholderText(
            "Hier erscheint nach der Analyse, was die KI erkannt hat.")
        result_layout.addWidget(self.result_view)
        layout.addWidget(result_group, 1)

    def refresh_status(self):
        """Zeigt an, ob die KI-Funktion einsatzbereit ist."""
        ok, msg = ai_extractor.ai_status()
        self.analyze_btn.setEnabled(ok)
        color = "#2E7D32" if ok else "#C62828"
        self.status_label.setText(msg)
        self.status_label.setStyleSheet(f"color: {color};")

    def _insert_example(self):
        self.text_input.setPlainText(EXAMPLE_TEXT.split('Beispiel: "', 1)[-1].rstrip('"'))

    def _on_analyze(self):
        ok, msg = ai_extractor.ai_status()
        if not ok:
            self.result_view.setHtml(f"<p style='color:#C62828;'>❌ {msg}</p>")
            return

        text = self.text_input.toPlainText().strip()
        if not text:
            self.result_view.setHtml(
                "<p style='color:#C62828;'>❌ Bitte geben Sie einen Text ein.</p>")
            return

        self.analyze_btn.setEnabled(False)
        self.analyze_btn.setText("⏳ KI analysiert …")
        self.result_view.setHtml("<p><i>Die KI analysiert den Text …</i></p>")

        self.worker = ExtractionWorker(text)
        self.worker.finished_ok.connect(self._on_success)
        self.worker.failed.connect(self._on_error)
        self.worker.start()

    def _on_success(self, result: dict):
        self.analyze_btn.setEnabled(True)
        self.analyze_btn.setText("🤖 Mit KI analysieren")
        self.result_view.setHtml(self._format_result(result))
        self.extraction_ready.emit(result)

    def _on_error(self, message: str):
        self.analyze_btn.setEnabled(True)
        self.analyze_btn.setText("🤖 Mit KI analysieren")
        self.result_view.setHtml(
            f"<p style='color:#C62828;'>❌ <b>Fehler bei der Analyse:</b><br>{message}</p>")

    @staticmethod
    def _format_result(result: dict) -> str:
        person = result.get("person", {})
        drinks = result.get("drinks", [])
        meas = result.get("measurement", {})
        summary = result.get("summary", "")

        html = ["<h3>✅ Erkannte Angaben</h3>"]

        # Person
        if person:
            parts = []
            if person.get("gender"):
                parts.append(person["gender"])
            if person.get("age"):
                parts.append(f"{person['age']} J.")
            if person.get("height"):
                parts.append(f"{person['height']} cm")
            if person.get("weight"):
                parts.append(f"{person['weight']:.0f} kg")
            html.append(f"<p><b>Person:</b> {', '.join(parts)}</p>")

        # Getränke
        if drinks:
            html.append("<p><b>Getränke:</b></p><ul>")
            for d in drinks:
                html.append(
                    f"<li>{d['time'].strftime('%d.%m. %H:%M')} – {d['name']}, "
                    f"{d['volume']:.0f} ml, {d['alcohol_content']:.1f} %</li>")
            html.append("</ul>")
        else:
            html.append("<p><b>Getränke:</b> keine erkannt</p>")

        # Messwert
        if meas.get("bac") is not None:
            when = (meas["datetime"].strftime('%d.%m.%Y %H:%M')
                    if meas.get("datetime") else "Zeit unbekannt")
            html.append(
                f"<p><b>Gemessene BAK:</b> {meas['bac']:.3f} ‰ "
                f"({when}{', ' + meas['method'] if meas.get('method') else ''})</p>")
        else:
            html.append("<p><b>Gemessene BAK:</b> nicht im Text gefunden</p>")

        if summary:
            html.append(f"<p style='color:#555;'><i>Hinweise der KI: {summary}</i></p>")

        html.append("<p style='color:#2E7D32;'>Die Angaben wurden in den Rechner "
                    "übernommen. Prüfen Sie sie im Tab „Eingabe“ und sehen Sie das "
                    "Ergebnis unter „Ergebnisse“ → „BAK-Controller“.</p>")
        return "".join(html)
