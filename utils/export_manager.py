"""
Export-Funktionen des BAK-Kalkulators (PDF, CSV, Excel, JSON).

Der PDF-Export ist als ansprechend gestalteter, gut verständlicher Bericht
aufgebaut: farbige Kopfzeile, Ergebnis-Box mit Ampel-Status, Klartext-
Interpretation, übersichtliche Tabellen, Diagramm und rechtliche Hinweise.
"""

from typing import Dict, Optional
import csv
import json
import os
from datetime import datetime

from PyQt6.QtWidgets import QFileDialog, QMessageBox, QWidget
from PyQt6.QtCore import QObject, pyqtSignal, QThread

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from models import ETHANOL_DENSITY, alcohol_grams

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                    TableStyle, Image)
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


# Farbschema (passt zum GUI-Theme)
PRIMARY = "#1976D2"
PRIMARY_LIGHT = "#E3F2FD"
GREY_HEAD = "#455A64"


def _bac_status(bac: float):
    """Liefert (Text, Ampel-Emoji, Hex-Farbe) zu einem BAK-Wert."""
    if bac <= 0.0:
        return "Nüchtern", "🟢", "#2E7D32"
    if bac < 0.3:
        return "Leicht alkoholisiert", "🟡", "#9E9D24"
    if bac < 0.5:
        return "Unter 0,5 ‰ – Restalkohol", "🟠", "#EF6C00"
    if bac < 1.1:
        return "Ordnungswidrigkeit (≥ 0,5 ‰)", "🔴", "#D84315"
    return "Absolut fahruntüchtig (≥ 1,1 ‰)", "🔴", "#B71C1C"


def _fmt_time(value) -> str:
    if isinstance(value, datetime):
        return value.strftime('%H:%M')
    return "--"


class ExportThread(QThread):
    """Thread für Export-Operationen, damit die GUI nicht einfriert."""

    progress_updated = pyqtSignal(int)
    export_finished = pyqtSignal(bool, str)

    def __init__(self, export_type: str, file_path: str, data: Dict):
        super().__init__()
        self.export_type = export_type
        self.file_path = file_path
        self.data = data

    def run(self):
        try:
            if self.export_type == 'pdf':
                self._export_pdf()
            elif self.export_type == 'csv':
                self._export_csv()
            elif self.export_type == 'excel':
                self._export_excel()
            elif self.export_type == 'json':
                self._export_json()
            self.export_finished.emit(True, f"Export erfolgreich: {self.file_path}")
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.export_finished.emit(False, f"Export-Fehler: {str(e)}")

    # ================================================================== #
    # PDF
    # ================================================================== #
    def _export_pdf(self):
        if not REPORTLAB_AVAILABLE:
            raise ImportError("ReportLab ist nicht installiert: pip install reportlab")

        self.progress_updated.emit(5)

        doc = SimpleDocTemplate(
            self.file_path, pagesize=A4,
            topMargin=1.5 * cm, bottomMargin=1.5 * cm,
            leftMargin=1.8 * cm, rightMargin=1.8 * cm,
            title="BAK-Bericht",
        )
        styles = getSampleStyleSheet()
        story = []

        h1 = ParagraphStyle('H1', parent=styles['Heading1'], fontSize=20,
                            textColor=colors.white, alignment=TA_CENTER,
                            spaceAfter=2, leading=24)
        sub = ParagraphStyle('Sub', parent=styles['Normal'], fontSize=10,
                             textColor=colors.HexColor("#E1F0FF"),
                             alignment=TA_CENTER)
        h2 = ParagraphStyle('H2', parent=styles['Heading2'], fontSize=13,
                            textColor=colors.HexColor(PRIMARY), spaceBefore=14,
                            spaceAfter=6)
        normal = ParagraphStyle('Body', parent=styles['Normal'], fontSize=10,
                                leading=14)

        # ---- Kopfzeile (farbiges Band) ----
        header = Table(
            [[Paragraph("BAK-Kalkulator – Auswertung", h1)],
             [Paragraph("Wissenschaftliche Schätzung der Blutalkoholkonzentration", sub)]],
            colWidths=[doc.width])
        header.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(PRIMARY)),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, -1), (-1, -1), 12),
        ]))
        story.append(header)
        story.append(Spacer(1, 6))
        story.append(Paragraph(
            f"Erstellt am {datetime.now().strftime('%d.%m.%Y um %H:%M')} Uhr",
            ParagraphStyle('date', parent=normal, alignment=TA_RIGHT,
                           textColor=colors.grey, fontSize=9)))
        story.append(Spacer(1, 8))

        results = self.data.get('results', {}) or {}
        self.progress_updated.emit(20)

        # ---- Ergebnis-Box mit Ampel-Status ----
        if results:
            self._add_summary_box(story, results, h2, normal)
        self.progress_updated.emit(35)

        # ---- Personendaten ----
        if 'person_data' in self.data:
            story.append(Paragraph("Personendaten", h2))
            story.append(self._person_table(self.data['person_data'], doc.width))

        self.progress_updated.emit(50)

        # ---- Getränke ----
        if self.data.get('drinks_data'):
            story.append(Paragraph("Konsumierte Getränke", h2))
            story.append(self._drinks_table(self.data['drinks_data'], doc.width))

        self.progress_updated.emit(62)

        # ---- Ergebnisse je Modell ----
        if results:
            story.append(Paragraph("Ergebnisse im Modellvergleich", h2))
            story.append(self._results_table(results, doc.width))

        self.progress_updated.emit(74)

        # ---- Diagramm ----
        chart_path = None
        chart_data = self.data.get('chart_data') or results
        if chart_data:
            chart_path = self.file_path.rsplit('.', 1)[0] + '_chart.png'
            self._create_chart_image(chart_path, chart_data)
            if os.path.exists(chart_path):
                story.append(Paragraph("BAK-Verlauf über die Zeit", h2))
                story.append(Image(chart_path, width=doc.width, height=doc.width * 0.55))
                story.append(Spacer(1, 4))
            else:
                chart_path = None

        self.progress_updated.emit(86)

        # ---- Rechtliche Grenzwerte ----
        story.append(Paragraph("Rechtliche Grenzwerte (Deutschland)", h2))
        story.append(self._legal_table(doc.width))

        # ---- Disclaimer ----
        story.append(Spacer(1, 14))
        disc = ParagraphStyle('disc', parent=normal, fontSize=9,
                              textColor=colors.HexColor("#B71C1C"),
                              backColor=colors.HexColor("#FFF3CD"),
                              borderPadding=8, leading=12)
        story.append(Paragraph(
            "<b>Wichtiger Hinweis:</b> Diese Berechnung ist eine Schätzung mit "
            "einer Unsicherheit von ±20–30 %. Sie dient ausschließlich der "
            "Information und ersetzt keine ärztliche oder forensische "
            "Blutuntersuchung. Fahren Sie niemals unter Alkoholeinfluss.", disc))

        doc.build(story)

        # Temporäres Diagramm-Bild erst nach dem Bauen entfernen
        if chart_path and os.path.exists(chart_path):
            try:
                os.remove(chart_path)
            except OSError:
                pass
        self.progress_updated.emit(100)

    # ------------------------------------------------------------------ #
    def _add_summary_box(self, story, results, h2, normal):
        currents = [r.get('current_bac', 0.0) for r in results.values()]
        peaks = [r.get('peak_bac', 0.0) for r in results.values()]
        avg_current = sum(currents) / len(currents) if currents else 0.0
        status, emoji, color = _bac_status(avg_current)

        latest_05 = max([r.get('time_to_05') for r in results.values()
                         if r.get('time_to_05')], default=None)
        latest_00 = max([r.get('time_to_00') for r in results.values()
                         if r.get('time_to_00')], default=None)
        first = next(iter(results.values()))

        box_style = ParagraphStyle('boxbig', parent=normal, fontSize=11, leading=16)
        lines = (
            f"<b>Status:</b> {status}<br/>"
            f"<b>Aktuelle BAK (Ø):</b> {avg_current:.2f} ‰&nbsp;&nbsp;|&nbsp;&nbsp;"
            f"<b>Maximum:</b> {min(peaks):.2f}–{max(peaks):.2f} ‰<br/>"
            f"<b>Reiner Alkohol:</b> {first.get('alcohol_grams', 0):.1f} g "
            f"aus {first.get('total_drinks', 0)} Getränk(en)<br/>"
            f"<b>Unter 0,5 ‰ ab:</b> {_fmt_time(latest_05)} Uhr&nbsp;&nbsp;|&nbsp;&nbsp;"
            f"<b>Nüchtern ab:</b> {_fmt_time(latest_00)} Uhr"
        )
        box = Table([[Paragraph(lines, box_style)]], colWidths=[None])
        box.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(PRIMARY_LIGHT)),
            ('LINEBEFORE', (0, 0), (0, -1), 4, colors.HexColor(color)),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        story.append(box)
        story.append(Spacer(1, 4))

    def _person_table(self, person, width):
        bmi = person.get('bmi')
        weight = person.get('weight', 0)
        height = person.get('height', 0)
        if not bmi and weight and height:
            bmi = weight / ((height / 100) ** 2)
        rows = [
            ['Geschlecht', person.get('gender', '–')],
            ['Alter', f"{person.get('age', '–')} Jahre"],
            ['Größe', f"{height} cm"],
            ['Gewicht', f"{weight} kg"],
            ['BMI', f"{bmi:.1f}" if bmi else '–'],
            ['Körperfettanteil', f"{person.get('body_fat', '–')} %"],
            ['Trinkgewohnheit', person.get('drinking_habit', '–')],
        ]
        t = Table(rows, colWidths=[width * 0.35, width * 0.65])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor(PRIMARY_LIGHT)),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#D0D7DE")),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ]))
        return t

    def _drinks_table(self, drinks, width):
        data = [['Getränk', 'Menge', 'Vol.-%', 'Datum/Zeit', 'Alkohol']]
        for d in drinks:
            grams = alcohol_grams(d['volume'], d['alcohol_content'])
            when = d['time'].strftime('%d.%m. %H:%M') if isinstance(d['time'], datetime) else str(d['time'])
            data.append([d['name'], f"{d['volume']:.0f} ml",
                         f"{d['alcohol_content']:.1f}", when, f"{grams:.1f} g"])
        return self._zebra_table(data, [width * 0.34, width * 0.14, width * 0.12,
                                        width * 0.24, width * 0.16])

    def _results_table(self, results, width):
        data = [['Modell', 'Max. BAK', 'Aktuell', 'Unter 0,5 ‰', 'Nüchtern']]
        for model, r in results.items():
            data.append([
                model,
                f"{r.get('peak_bac', 0):.2f} ‰",
                f"{r.get('current_bac', 0):.2f} ‰",
                _fmt_time(r.get('time_to_05')),
                _fmt_time(r.get('time_to_00')),
            ])
        return self._zebra_table(data, [width * 0.24, width * 0.19, width * 0.19,
                                        width * 0.19, width * 0.19])

    def _legal_table(self, width):
        data = [
            ['Ab BAK', 'Bedeutung'],
            ['0,3 ‰', 'Relative Fahruntüchtigkeit bei Ausfallerscheinungen (Straftat)'],
            ['0,5 ‰', 'Ordnungswidrigkeit: Bußgeld, Fahrverbot, Punkte (§ 24a StVG)'],
            ['1,1 ‰', 'Absolute Fahruntüchtigkeit – Straftat (§ 316 StGB)'],
            ['3,0 ‰', 'Lebensgefährliche Vergiftung – medizinischer Notfall'],
        ]
        return self._zebra_table(data, [width * 0.15, width * 0.85], align_left=True)

    def _zebra_table(self, data, col_widths, align_left=False):
        t = Table(data, colWidths=col_widths, repeatRows=1)
        style = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(GREY_HEAD)),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9.5),
            ('ALIGN', (1 if align_left else 0, 0), (-1, -1),
             'LEFT' if align_left else 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#D0D7DE")),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]
        for i in range(1, len(data)):
            if i % 2 == 0:
                style.append(('BACKGROUND', (0, i), (-1, i),
                              colors.HexColor("#F4F8FC")))
        t.setStyle(TableStyle(style))
        return t

    def _create_chart_image(self, file_path: str, chart_data: Dict):
        try:
            fig, ax = plt.subplots(figsize=(11, 6))
            palette = ['#1976D2', '#EF6C00', '#2E7D32', '#7B1FA2']
            max_bac = 0.0

            for i, (model, result) in enumerate(chart_data.items()):
                pts = result.get('bac_values') if isinstance(result, dict) else None
                if not pts:
                    continue
                times = [p[0] for p in pts]
                vals = [float(p[1]) for p in pts]
                max_bac = max(max_bac, max(vals) if vals else 0)
                ax.plot(times, vals, label=model, color=palette[i % len(palette)],
                        linewidth=2.2)

            for y, c, lbl in [(0.3, '#FBC02D', '0,3 ‰'), (0.5, '#EF6C00', '0,5 ‰'),
                              (1.1, '#C62828', '1,1 ‰')]:
                if max_bac > y * 0.6:
                    ax.axhline(y=y, color=c, linestyle='--', alpha=0.7, linewidth=1)
                    ax.text(0.005, y, lbl, transform=ax.get_yaxis_transform(),
                            color=c, fontsize=8, va='bottom')

            ax.set_xlabel('Uhrzeit')
            ax.set_ylabel('BAK (‰)')
            ax.set_ylim(0, max(max_bac * 1.15, 0.6))
            ax.grid(True, alpha=0.3)
            ax.legend(loc='upper right', fontsize=9)
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            fig.autofmt_xdate()
            fig.tight_layout()
            fig.savefig(file_path, dpi=150, bbox_inches='tight')
            plt.close(fig)
        except Exception as e:
            print(f"Fehler beim Erstellen des Diagramms: {e}")

    # ================================================================== #
    # CSV / Excel / JSON
    # ================================================================== #
    def _export_csv(self):
        self.progress_updated.emit(30)
        with open(self.file_path, 'w', newline='', encoding='utf-8-sig') as f:
            w = csv.writer(f, delimiter=';')
            w.writerow(['BAK-Kalkulator Export'])
            w.writerow(['Erstellt am', datetime.now().strftime('%d.%m.%Y %H:%M')])
            w.writerow([])

            if 'person_data' in self.data:
                p = self.data['person_data']
                w.writerow(['Personendaten'])
                w.writerow(['Geschlecht', p.get('gender', '')])
                w.writerow(['Alter', p.get('age', '')])
                w.writerow(['Größe (cm)', p.get('height', '')])
                w.writerow(['Gewicht (kg)', p.get('weight', '')])
                w.writerow(['Körperfett (%)', p.get('body_fat', '')])
                w.writerow(['Trinkgewohnheit', p.get('drinking_habit', '')])
                w.writerow([])

            if self.data.get('drinks_data'):
                w.writerow(['Getränke'])
                w.writerow(['Getränk', 'Menge (ml)', 'Vol.-%', 'Zeit', 'Alkohol (g)'])
                for d in self.data['drinks_data']:
                    grams = alcohol_grams(d['volume'], d['alcohol_content'])
                    when = d['time'].strftime('%d.%m.%Y %H:%M') if isinstance(d['time'], datetime) else str(d['time'])
                    w.writerow([d['name'], d['volume'], f"{d['alcohol_content']:.1f}",
                                when, f"{grams:.1f}"])
                w.writerow([])

            if self.data.get('results'):
                w.writerow(['Ergebnisse'])
                w.writerow(['Modell', 'Max. BAK (‰)', 'Aktuell (‰)',
                            'Unter 0,5‰', 'Unter 0,3‰', 'Nüchtern'])
                for model, r in self.data['results'].items():
                    w.writerow([model, f"{r.get('peak_bac', 0):.2f}",
                                f"{r.get('current_bac', 0):.2f}",
                                _fmt_time(r.get('time_to_05')),
                                _fmt_time(r.get('time_to_03')),
                                _fmt_time(r.get('time_to_00'))])
        self.progress_updated.emit(100)

    def _export_excel(self):
        try:
            import openpyxl
            from openpyxl.styles import Font, PatternFill
        except ImportError:
            raise ImportError("openpyxl ist nicht installiert: pip install openpyxl")

        self.progress_updated.emit(20)
        wb = openpyxl.Workbook()
        head_fill = PatternFill(start_color="455A64", end_color="455A64", fill_type="solid")
        head_font = Font(bold=True, color="FFFFFF")

        ws = wb.active
        ws.title = "Personendaten"
        if 'person_data' in self.data:
            p = self.data['person_data']
            ws['A1'] = "Personendaten"
            ws['A1'].font = Font(bold=True, size=14)
            for i, (k, v) in enumerate([
                ('Geschlecht', p.get('gender', '')), ('Alter', p.get('age', '')),
                ('Größe (cm)', p.get('height', '')), ('Gewicht (kg)', p.get('weight', '')),
                ('Körperfett (%)', p.get('body_fat', '')),
                ('Trinkgewohnheit', p.get('drinking_habit', ''))], start=3):
                ws[f'A{i}'] = k
                ws[f'B{i}'] = v
                ws[f'A{i}'].font = Font(bold=True)

        self.progress_updated.emit(50)
        if self.data.get('drinks_data'):
            wd = wb.create_sheet("Getränke")
            for c, h in enumerate(['Getränk', 'Menge (ml)', 'Vol.-%', 'Zeit', 'Alkohol (g)'], 1):
                cell = wd.cell(row=1, column=c, value=h)
                cell.font = head_font
                cell.fill = head_fill
            for row, d in enumerate(self.data['drinks_data'], start=2):
                grams = alcohol_grams(d['volume'], d['alcohol_content'])
                when = d['time'].strftime('%d.%m.%Y %H:%M') if isinstance(d['time'], datetime) else str(d['time'])
                wd.cell(row=row, column=1, value=d['name'])
                wd.cell(row=row, column=2, value=d['volume'])
                wd.cell(row=row, column=3, value=d['alcohol_content'])
                wd.cell(row=row, column=4, value=when)
                wd.cell(row=row, column=5, value=round(grams, 1))

        self.progress_updated.emit(80)
        if self.data.get('results'):
            wr = wb.create_sheet("Ergebnisse")
            for c, h in enumerate(['Modell', 'Max. BAK (‰)', 'Aktuell (‰)',
                                   'Unter 0,5‰', 'Nüchtern'], 1):
                cell = wr.cell(row=1, column=c, value=h)
                cell.font = head_font
                cell.fill = head_fill
            for row, (model, r) in enumerate(self.data['results'].items(), start=2):
                wr.cell(row=row, column=1, value=model)
                wr.cell(row=row, column=2, value=round(r.get('peak_bac', 0), 2))
                wr.cell(row=row, column=3, value=round(r.get('current_bac', 0), 2))
                wr.cell(row=row, column=4, value=_fmt_time(r.get('time_to_05')))
                wr.cell(row=row, column=5, value=_fmt_time(r.get('time_to_00')))

        wb.save(self.file_path)
        self.progress_updated.emit(100)

    def _export_json(self):
        self.progress_updated.emit(30)

        def serialize(obj):
            if isinstance(obj, dict):
                return {k: serialize(v) for k, v in obj.items()}
            if isinstance(obj, (list, tuple)):
                return [serialize(i) for i in obj]
            if isinstance(obj, datetime):
                return obj.isoformat()
            return obj

        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(serialize(self.data), f, indent=2, ensure_ascii=False)
        self.progress_updated.emit(100)


class ExportManager(QObject):
    """Manager für Export-Funktionen."""

    export_started = pyqtSignal()
    export_progress = pyqtSignal(int)
    export_finished = pyqtSignal(bool, str)

    def __init__(self, parent: QWidget = None):
        super().__init__()
        self.parent = parent
        self.export_thread: Optional[ExportThread] = None

    def _has_data(self, data: Dict) -> bool:
        if not data or not data.get('results'):
            QMessageBox.information(
                self.parent, "Keine Daten",
                "Es liegen noch keine Berechnungsergebnisse vor.\n\n"
                "Bitte geben Sie zuerst Personendaten und Getränke ein.")
            return False
        return True

    def export_to_pdf(self, data: Dict):
        if not self._has_data(data):
            return
        self._dialog_and_start('pdf', data, "PDF exportieren", "pdf",
                               "PDF Dateien (*.pdf)")

    def export_to_csv(self, data: Dict):
        if not self._has_data(data):
            return
        self._dialog_and_start('csv', data, "CSV exportieren", "csv",
                               "CSV Dateien (*.csv)")

    def export_to_excel(self, data: Dict):
        if not self._has_data(data):
            return
        self._dialog_and_start('excel', data, "Excel exportieren", "xlsx",
                               "Excel Dateien (*.xlsx)")

    def export_to_json(self, data: Dict):
        if not self._has_data(data):
            return
        self._dialog_and_start('json', data, "JSON exportieren", "json",
                               "JSON Dateien (*.json)")

    def _dialog_and_start(self, export_type, data, title, ext, filter_str):
        default_name = f"BAK_Bericht_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}"
        file_path, _ = QFileDialog.getSaveFileName(
            self.parent, title, default_name, filter_str)
        if file_path:
            self._start_export(export_type, file_path, data)

    def _start_export(self, export_type: str, file_path: str, data: Dict):
        if self.export_thread and self.export_thread.isRunning():
            QMessageBox.warning(self.parent, "Export läuft",
                                "Es läuft bereits ein Export. Bitte warten Sie.")
            return
        self.export_started.emit()
        self.export_thread = ExportThread(export_type, file_path, data)
        self.export_thread.progress_updated.connect(self.export_progress.emit)
        self.export_thread.export_finished.connect(self.export_finished.emit)
        self.export_thread.start()
