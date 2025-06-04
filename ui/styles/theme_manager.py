from enum import Enum
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QFont, QFontDatabase
from PyQt6.QtWidgets import QApplication
import json
import os

class Theme(Enum):
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"

class Colors:
    """Zentrale Farbdefinitionen"""
    
    # Light Theme
    LIGHT = {
        'primary': '#2196F3',
        'primary_dark': '#1976D2',
        'primary_light': '#BBDEFB',
        'secondary': '#FF9800',
        'secondary_dark': '#F57C00',
        'secondary_light': '#FFE0B2',
        'background': '#FFFFFF',
        'surface': '#F5F5F5',
        'surface_variant': '#F0F4FA',
        'on_primary': '#FFFFFF',
        'on_secondary': '#FFFFFF',
        'on_background': '#1A1A1A',
        'on_surface': '#1A1A1A',
        'text_primary': '#212121',
        'text_secondary': '#757575',
        'text_disabled': '#BDBDBD',
        'divider': '#E0E0E0',
        'border': '#E0E0E0',
        'error': '#F44336',
        'warning': '#FF9800',
        'success': '#4CAF50',
        'info': '#2196F3',
        'disabled': '#F5F5F5',
        'hover': '#F0F0F0',
        'selected': '#E3F2FD'
    }
    
    # Dark Theme
    DARK = {
        'primary': '#2196F3',
        'primary_dark': '#1976D2',
        'primary_light': '#BBDEFB',
        'secondary': '#FF9800',
        'secondary_dark': '#F57C00',
        'secondary_light': '#FFE0B2',
        'background': '#121212',
        'surface': '#1E1E1E',
        'surface_variant': '#2D2D2D',
        'on_primary': '#FFFFFF',
        'on_secondary': '#000000',
        'on_background': '#FFFFFF',
        'on_surface': '#FFFFFF',
        'text_primary': '#FFFFFF',
        'text_secondary': '#B0B0B0',
        'text_disabled': '#666666',
        'divider': '#333333',
        'border': '#333333',
        'error': '#F44336',
        'warning': '#FF9800',
        'success': '#4CAF50',
        'info': '#2196F3',
        'disabled': '#2D2D2D',
        'hover': '#333333',
        'selected': '#1976D2'
    }

class FontManager:
    """Font-Management für konsistente Typografie"""
    
    # Font-Größen
    SIZES = {
        'caption': 10,
        'body2': 11,
        'body1': 12,
        'subtitle2': 13,
        'subtitle1': 14,
        'h6': 16,
        'h5': 18,
        'h4': 20,
        'h3': 24,
        'h2': 28,
        'h1': 32
    }
    
    # Font-Gewichte
    WEIGHTS = {
        'light': QFont.Weight.Light,
        'normal': QFont.Weight.Normal,
        'medium': QFont.Weight.Medium,
        'bold': QFont.Weight.Bold
    }
    
    @staticmethod
    def get_font(size_key: str = 'body1', weight: str = 'normal', family: str = 'Inter') -> QFont:
        """Erstellt einen Font mit den angegebenen Eigenschaften"""
        font = QFont(family)
        font.setPointSize(FontManager.SIZES.get(size_key, 12))
        font.setWeight(FontManager.WEIGHTS.get(weight, QFont.Weight.Normal))
        return font
    
    @staticmethod
    def load_custom_fonts():
        """Lädt benutzerdefinierte Schriftarten"""
        # In PyQt6 ist addApplicationFont eine statische Methode
        
        # Versuche Inter-Font zu laden (falls verfügbar)
        fonts_dir = os.path.join(os.path.dirname(__file__), '..', 'fonts')
        if os.path.exists(fonts_dir):
            for font_file in os.listdir(fonts_dir):
                if font_file.endswith(('.ttf', '.otf')):
                    font_path = os.path.join(fonts_dir, font_file)
                    QFontDatabase.addApplicationFont(font_path)

class ThemeManager(QObject):
    """Zentrale Theme-Verwaltung"""
    
    theme_changed = pyqtSignal(str)  # Theme-Name
    
    def __init__(self):
        super().__init__()
        self.current_theme = Theme.LIGHT
        self.colors = Colors.LIGHT
        self.settings_file = os.path.join(os.path.expanduser('~'), '.bak_calculator', 'theme_settings.json')
        
        # Erstelle Einstellungsverzeichnis
        os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
        
        # Lade gespeicherte Einstellungen
        self.load_settings()
        
        # Lade benutzerdefinierte Fonts
        FontManager.load_custom_fonts()
    
    def set_theme(self, theme: Theme):
        """Setzt das aktuelle Theme"""
        self.current_theme = theme
        
        if theme == Theme.LIGHT:
            self.colors = Colors.LIGHT
        elif theme == Theme.DARK:
            self.colors = Colors.DARK
        elif theme == Theme.AUTO:
            # Auto-Theme basierend auf Systemeinstellungen
            self.colors = self._get_system_theme()
        
        self.apply_theme()
        self.save_settings()
        self.theme_changed.emit(theme.value)
    
    def get_color(self, color_key: str) -> str:
        """Gibt eine Farbe für das aktuelle Theme zurück"""
        return self.colors.get(color_key, '#000000')
    
    def apply_theme(self):
        """Wendet das aktuelle Theme auf die Anwendung an"""
        app = QApplication.instance()
        if app:
            stylesheet = self._generate_stylesheet()
            app.setStyleSheet(stylesheet)
    
    def _generate_stylesheet(self) -> str:
        """Generiert das globale Stylesheet"""
        return f"""
        /* Globale Styles */
        QMainWindow {{
            background-color: {self.get_color('background')};
            color: {self.get_color('text_primary')};
        }}
        
        /* Buttons */
        QPushButton {{
            background-color: {self.get_color('primary')};
            color: {self.get_color('on_primary')};
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            font-weight: 500;
            min-width: 80px;
            min-height: 32px;
        }}
        
        QPushButton:hover {{
            background-color: {self.get_color('primary_dark')};
        }}
        
        QPushButton:pressed {{
            background-color: {self.get_color('primary_dark')};
        }}
        
        QPushButton:disabled {{
            background-color: {self.get_color('disabled')};
            color: {self.get_color('text_disabled')};
        }}
        
        /* Secondary Buttons */
        QPushButton[class="secondary"] {{
            background-color: {self.get_color('surface')};
            color: {self.get_color('text_primary')};
            border: 1px solid {self.get_color('border')};
        }}
        
        QPushButton[class="secondary"]:hover {{
            background-color: {self.get_color('hover')};
        }}
        
        /* Danger Buttons */
        QPushButton[class="danger"] {{
            background-color: {self.get_color('error')};
            color: {self.get_color('on_primary')};
        }}
        
        /* Input Fields */
        QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
            background-color: {self.get_color('surface')};
            color: {self.get_color('text_primary')};
            border: 1px solid {self.get_color('border')};
            border-radius: 4px;
            padding: 6px 12px;
            min-height: 24px;
        }}
        
        QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
            border-color: {self.get_color('primary')};
        }}
        
        QLineEdit:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled, QComboBox:disabled {{
            background-color: {self.get_color('disabled')};
            color: {self.get_color('text_disabled')};
        }}
        
        /* Labels */
        QLabel {{
            color: {self.get_color('text_primary')};
        }}
        
        QLabel[class="secondary"] {{
            color: {self.get_color('text_secondary')};
        }}
        
        QLabel[class="error"] {{
            color: {self.get_color('error')};
        }}
        
        QLabel[class="success"] {{
            color: {self.get_color('success')};
        }}
        
        /* Group Boxes */
        QGroupBox {{
            background-color: {self.get_color('surface')};
            border: 1px solid {self.get_color('border')};
            border-radius: 8px;
            margin-top: 12px;
            padding-top: 12px;
            font-weight: 600;
        }}
        
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 8px;
            color: {self.get_color('text_primary')};
        }}
        
        /* Tables */
        QTableWidget {{
            background-color: {self.get_color('background')};
            alternate-background-color: {self.get_color('surface')};
            gridline-color: {self.get_color('divider')};
            color: {self.get_color('text_primary')};
            border: 1px solid {self.get_color('border')};
            border-radius: 4px;
        }}
        
        QTableWidget::item {{
            padding: 8px;
            border-bottom: 1px solid {self.get_color('divider')};
        }}
        
        QTableWidget::item:selected {{
            background-color: {self.get_color('selected')};
        }}
        
        QHeaderView::section {{
            background-color: {self.get_color('surface_variant')};
            color: {self.get_color('text_primary')};
            padding: 8px;
            border: none;
            border-bottom: 2px solid {self.get_color('divider')};
            font-weight: 600;
        }}
        
        /* Tabs */
        QTabWidget::pane {{
            border: 1px solid {self.get_color('border')};
            border-radius: 4px;
            background-color: {self.get_color('background')};
        }}
        
        QTabBar::tab {{
            background-color: {self.get_color('surface')};
            color: {self.get_color('text_secondary')};
            padding: 8px 16px;
            margin-right: 2px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }}
        
        QTabBar::tab:selected {{
            background-color: {self.get_color('primary')};
            color: {self.get_color('on_primary')};
        }}
        
        QTabBar::tab:hover:!selected {{
            background-color: {self.get_color('hover')};
            color: {self.get_color('text_primary')};
        }}
        
        /* Sliders */
        QSlider::groove:horizontal {{
            border: 1px solid {self.get_color('border')};
            height: 4px;
            background: {self.get_color('surface')};
            border-radius: 2px;
        }}
        
        QSlider::handle:horizontal {{
            background: {self.get_color('primary')};
            border: 1px solid {self.get_color('primary_dark')};
            width: 18px;
            margin: -7px 0;
            border-radius: 9px;
        }}
        
        QSlider::handle:horizontal:hover {{
            background: {self.get_color('primary_dark')};
        }}
        
        /* Checkboxes and Radio Buttons */
        QCheckBox::indicator, QRadioButton::indicator {{
            width: 18px;
            height: 18px;
        }}
        
        QCheckBox::indicator:unchecked, QRadioButton::indicator:unchecked {{
            border: 2px solid {self.get_color('border')};
            background-color: {self.get_color('background')};
            border-radius: 3px;
        }}
        
        QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
            border: 2px solid {self.get_color('primary')};
            background-color: {self.get_color('primary')};
            border-radius: 3px;
        }}
        
        QRadioButton::indicator {{
            border-radius: 9px;
        }}
        
        QRadioButton::indicator:checked {{
            border-radius: 9px;
        }}
        
        /* Scroll Areas */
        QScrollArea {{
            border: 1px solid {self.get_color('border')};
            border-radius: 4px;
            background-color: {self.get_color('background')};
        }}
        
        /* Tooltips */
        QToolTip {{
            background-color: {self.get_color('surface_variant')};
            color: {self.get_color('text_primary')};
            border: 1px solid {self.get_color('border')};
            border-radius: 4px;
            padding: 4px 8px;
        }}
        """
    
    def _get_system_theme(self) -> dict:
        """Ermittelt das System-Theme (vereinfacht)"""
        # Vereinfachte Implementierung - in Realität würde man
        # Systemeinstellungen abfragen
        return Colors.LIGHT
    
    def save_settings(self):
        """Speichert die Theme-Einstellungen"""
        settings = {
            'theme': self.current_theme.value
        }
        
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            print(f"Fehler beim Speichern der Theme-Einstellungen: {e}")
    
    def load_settings(self):
        """Lädt die gespeicherten Theme-Einstellungen"""
        if not os.path.exists(self.settings_file):
            return
        
        try:
            with open(self.settings_file, 'r') as f:
                settings = json.load(f)
            
            theme_value = settings.get('theme', Theme.LIGHT.value)
            for theme in Theme:
                if theme.value == theme_value:
                    self.set_theme(theme)
                    break
        except Exception as e:
            print(f"Fehler beim Laden der Theme-Einstellungen: {e}")

# Globale Theme-Manager-Instanz
theme_manager = ThemeManager() 