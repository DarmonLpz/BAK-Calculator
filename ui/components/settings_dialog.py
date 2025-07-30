"""
Einstellungs-Dialog für API-Konfiguration
"""

import os
import json
import base64
from cryptography.fernet import Fernet
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QComboBox, QLineEdit, QPushButton, QGroupBox,
                             QMessageBox, QCheckBox, QFormLayout)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

class SettingsDialog(QDialog):
    """Dialog für API-Einstellungen"""
    
    settings_changed = pyqtSignal(dict)  # Signal für geänderte Einstellungen
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("API-Einstellungen")
        self.setModal(True)
        self.setMinimumWidth(400)
        
        # Verschlüsselungsschlüssel für API-Keys
        self.encryption_key = self._get_or_create_key()
        self.cipher = Fernet(self.encryption_key)
        
        self.setup_ui()
        self.load_settings()
        
    def _get_or_create_key(self):
        """Erstellt oder lädt den Verschlüsselungsschlüssel"""
        key_file = os.path.join(os.path.dirname(__file__), '..', '..', '.encryption_key')
        
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            # Neuen Schlüssel erstellen
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            return key
    
    def setup_ui(self):
        """Erstellt die Benutzeroberfläche"""
        layout = QVBoxLayout(self)
        
        # Titel
        title_label = QLabel("API-Konfiguration")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # API-Provider Auswahl
        provider_group = QGroupBox("API-Provider")
        provider_layout = QFormLayout(provider_group)
        
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["Ollama (Lokal)", "OpenAI (Cloud)"])
        self.provider_combo.currentTextChanged.connect(self.on_provider_changed)
        provider_layout.addRow("Provider:", self.provider_combo)
        
        layout.addWidget(provider_group)
        
        # OpenAI Einstellungen
        self.openai_group = QGroupBox("OpenAI Einstellungen")
        openai_layout = QFormLayout(self.openai_group)
        
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_edit.setPlaceholderText("sk-...")
        openai_layout.addRow("API-Key:", self.api_key_edit)
        
        self.model_combo = QComboBox()
        self.model_combo.addItems(["gpt-4o-mini", "gpt-4", "gpt-3.5-turbo"])
        openai_layout.addRow("Modell:", self.model_combo)
        
        layout.addWidget(self.openai_group)
        
        # Ollama Einstellungen
        self.ollama_group = QGroupBox("Ollama Einstellungen")
        ollama_layout = QFormLayout(self.ollama_group)
        
        self.ollama_url_edit = QLineEdit()
        self.ollama_url_edit.setText("http://localhost:11434")
        self.ollama_url_edit.setPlaceholderText("http://localhost:11434")
        ollama_layout.addRow("Server-URL:", self.ollama_url_edit)
        
        self.ollama_model_edit = QLineEdit()
        self.ollama_model_edit.setText("llama3.1")
        self.ollama_model_edit.setPlaceholderText("llama3.1")
        ollama_layout.addRow("Modell:", self.ollama_model_edit)
        
        layout.addWidget(self.ollama_group)
        
        # Test-Button
        test_layout = QHBoxLayout()
        self.test_button = QPushButton("Verbindung testen")
        self.test_button.clicked.connect(self.test_connection)
        test_layout.addWidget(self.test_button)
        
        layout.addLayout(test_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("Speichern")
        self.save_button.clicked.connect(self.save_settings)
        
        self.cancel_button = QPushButton("Abbrechen")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
        # Initiale Sichtbarkeit setzen
        self.on_provider_changed(self.provider_combo.currentText())
    
    def on_provider_changed(self, provider):
        """Behandelt Änderungen des API-Providers"""
        if "Ollama" in provider:
            self.openai_group.setVisible(False)
            self.ollama_group.setVisible(True)
        else:
            self.openai_group.setVisible(True)
            self.ollama_group.setVisible(False)
    
    def load_settings(self):
        """Lädt gespeicherte Einstellungen"""
        settings_file = os.path.join(os.path.dirname(__file__), '..', '..', '.api_settings')
        
        if os.path.exists(settings_file):
            try:
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                
                # Provider setzen
                provider = settings.get('provider', 'Ollama (Lokal)')
                index = self.provider_combo.findText(provider)
                if index >= 0:
                    self.provider_combo.setCurrentIndex(index)
                
                # OpenAI Einstellungen
                if 'openai_api_key' in settings:
                    encrypted_key = settings['openai_api_key']
                    try:
                        decrypted_key = self.cipher.decrypt(encrypted_key.encode()).decode()
                        self.api_key_edit.setText(decrypted_key)
                    except:
                        pass  # Verschlüsselter Key konnte nicht entschlüsselt werden
                
                model = settings.get('openai_model', 'gpt-4o-mini')
                index = self.model_combo.findText(model)
                if index >= 0:
                    self.model_combo.setCurrentIndex(index)
                
                # Ollama Einstellungen
                self.ollama_url_edit.setText(settings.get('ollama_url', 'http://localhost:11434'))
                self.ollama_model_edit.setText(settings.get('ollama_model', 'llama3.1'))
                
            except Exception as e:
                QMessageBox.warning(self, "Fehler", f"Einstellungen konnten nicht geladen werden: {e}")
    
    def save_settings(self):
        """Speichert die Einstellungen"""
        try:
            settings = {
                'provider': self.provider_combo.currentText(),
                'openai_model': self.model_combo.currentText(),
                'ollama_url': self.ollama_url_edit.text(),
                'ollama_model': self.ollama_model_edit.text()
            }
            
            # API-Key verschlüsselt speichern
            if self.api_key_edit.text().strip():
                encrypted_key = self.cipher.encrypt(self.api_key_edit.text().encode()).decode()
                settings['openai_api_key'] = encrypted_key
            
            settings_file = os.path.join(os.path.dirname(__file__), '..', '..', '.api_settings')
            with open(settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
            
            self.settings_changed.emit(settings)
            QMessageBox.information(self, "Erfolg", "Einstellungen wurden gespeichert!")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Einstellungen konnten nicht gespeichert werden: {e}")
    
    def test_connection(self):
        """Testet die API-Verbindung"""
        provider = self.provider_combo.currentText()
        
        if "OpenAI" in provider:
            self.test_openai_connection()
        else:
            self.test_ollama_connection()
    
    def test_openai_connection(self):
        """Testet OpenAI-Verbindung"""
        api_key = self.api_key_edit.text().strip()
        if not api_key:
            QMessageBox.warning(self, "Fehler", "Bitte geben Sie einen API-Key ein!")
            return
        
        try:
            import openai
            client = openai.OpenAI(api_key=api_key)
            
            # Einfacher Test
            response = client.chat.completions.create(
                model=self.model_combo.currentText(),
                messages=[{"role": "user", "content": "Hallo"}],
                max_tokens=10
            )
            
            QMessageBox.information(self, "Erfolg", "OpenAI-Verbindung erfolgreich!")
            
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"OpenAI-Verbindung fehlgeschlagen: {e}")
    
    def test_ollama_connection(self):
        """Testet Ollama-Verbindung"""
        try:
            import aiohttp
            import asyncio
            
            url = self.ollama_url_edit.text()
            model = self.ollama_model_edit.text()
            
            async def test():
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{url}/api/tags") as response:
                        if response.status == 200:
                            return True
                        return False
            
            # Einfacher Test (synchron)
            import requests
            try:
                response = requests.get(f"{url}/api/tags", timeout=5)
                if response.status_code == 200:
                    QMessageBox.information(self, "Erfolg", "Ollama-Verbindung erfolgreich!")
                else:
                    QMessageBox.critical(self, "Fehler", f"Ollama-Server antwortet mit Status {response.status_code}")
            except Exception as e:
                QMessageBox.critical(self, "Fehler", f"Ollama-Verbindung fehlgeschlagen: {e}")
                
        except ImportError:
            QMessageBox.warning(self, "Fehler", "aiohttp ist nicht installiert!")
    
    def get_settings(self):
        """Gibt die aktuellen Einstellungen zurück"""
        settings = {
            'provider': self.provider_combo.currentText(),
            'openai_model': self.model_combo.currentText(),
            'ollama_url': self.ollama_url_edit.text(),
            'ollama_model': self.ollama_model_edit.text()
        }
        
        if self.api_key_edit.text().strip():
            settings['openai_api_key'] = self.api_key_edit.text()
        
        return settings 