"""
Universeller Analyzer für Trinkprotokoll-Analyse
Wählt automatisch zwischen Ollama und OpenAI basierend auf den Einstellungen
"""

import os
import json
import logging
from typing import Optional
from dataclasses import dataclass

from utils.ollama_analyzer import OllamaAnalyzer, DrinkingProtocol
from utils.openai_analyzer import OpenAIAnalyzer

logger = logging.getLogger(__name__)

class UniversalAnalyzer:
    """Universeller Analyzer für Trinkprotokoll-Analyse"""
    
    def __init__(self):
        self.settings = self._load_settings()
        self.ollama_analyzer = None
        self.openai_analyzer = None
        self._initialize_analyzers()
    
    def _load_settings(self) -> dict:
        """Lädt die API-Einstellungen"""
        settings_file = os.path.join(os.path.dirname(__file__), '..', '.api_settings')
        
        if os.path.exists(settings_file):
            try:
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                return settings
            except Exception as e:
                logger.error(f"Fehler beim Laden der Einstellungen: {e}")
        
        # Standardeinstellungen
        return {
            'provider': 'Ollama (Lokal)',
            'ollama_url': 'http://localhost:11434',
            'ollama_model': 'llama3.1',
            'openai_model': 'gpt-4o-mini'
        }
    
    def _initialize_analyzers(self):
        """Initialisiert die Analyzer basierend auf den Einstellungen"""
        try:
            # Ollama Analyzer initialisieren
            if 'ollama_url' in self.settings and 'ollama_model' in self.settings:
                self.ollama_analyzer = OllamaAnalyzer(
                    model_name=self.settings['ollama_model'],
                    base_url=self.settings['ollama_url']
                )
            
            # OpenAI Analyzer initialisieren (falls API-Key verfügbar)
            if 'openai_api_key' in self.settings and 'openai_model' in self.settings:
                # API-Key entschlüsseln
                from cryptography.fernet import Fernet
                key_file = os.path.join(os.path.dirname(__file__), '..', '.encryption_key')
                
                if os.path.exists(key_file):
                    with open(key_file, 'rb') as f:
                        encryption_key = f.read()
                    
                    cipher = Fernet(encryption_key)
                    try:
                        api_key = cipher.decrypt(self.settings['openai_api_key'].encode()).decode()
                        self.openai_analyzer = OpenAIAnalyzer(
                            api_key=api_key,
                            model=self.settings['openai_model']
                        )
                    except Exception as e:
                        logger.error(f"Fehler beim Entschlüsseln des API-Keys: {e}")
                        
        except Exception as e:
            logger.error(f"Fehler beim Initialisieren der Analyzer: {e}")
    
    def update_settings(self, new_settings: dict):
        """Aktualisiert die Einstellungen und reinitialisiert die Analyzer"""
        self.settings = new_settings
        self._initialize_analyzers()
    
    async def analyze_protocol(self, text: str) -> Optional[DrinkingProtocol]:
        """Analysiert Trinkprotokoll mit dem konfigurierten Analyzer"""
        provider = self.settings.get('provider', 'Ollama (Lokal)')
        
        if "OpenAI" in provider and self.openai_analyzer:
            logger.info("Verwende OpenAI für Protokoll-Analyse")
            return await self.openai_analyzer.analyze_protocol(text)
        
        elif "Ollama" in provider and self.ollama_analyzer:
            logger.info("Verwende Ollama für Protokoll-Analyse")
            return await self.ollama_analyzer.analyze_protocol(text)
        
        else:
            logger.error("Kein konfigurierter Analyzer verfügbar")
            return None
    
    async def test_connection(self) -> bool:
        """Testet die Verbindung zum konfigurierten Analyzer"""
        provider = self.settings.get('provider', 'Ollama (Lokal)')
        
        if "OpenAI" in provider and self.openai_analyzer:
            return await self.openai_analyzer.test_connection()
        
        elif "Ollama" in provider and self.ollama_analyzer:
            return await self.ollama_analyzer.test_connection()
        
        return False
    
    def get_provider_info(self) -> str:
        """Gibt Informationen über den aktuellen Provider zurück"""
        provider = self.settings.get('provider', 'Ollama (Lokal)')
        
        if "OpenAI" in provider:
            model = self.settings.get('openai_model', 'gpt-4o-mini')
            return f"OpenAI ({model})"
        
        elif "Ollama" in provider:
            model = self.settings.get('ollama_model', 'llama3.1')
            url = self.settings.get('ollama_url', 'http://localhost:11434')
            return f"Ollama ({model} @ {url})"
        
        return "Nicht konfiguriert"
    
    def is_configured(self) -> bool:
        """Prüft, ob ein Analyzer konfiguriert ist"""
        provider = self.settings.get('provider', 'Ollama (Lokal)')
        
        if "OpenAI" in provider:
            return self.openai_analyzer is not None
        elif "Ollama" in provider:
            return self.ollama_analyzer is not None
        
        return False 