#!/usr/bin/env python3
"""
Unit Tests für GeminiAnalyzer
Testet die KI-Textanalyse und Suggestion-Generierung
"""

import unittest
import json
from unittest.mock import patch, MagicMock
import os
import sys

# Import der zu testenden Klasse
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.analyzers.gemini_analyzer import GeminiAnalyzer


class TestGeminiAnalyzer(unittest.TestCase):
    """Test Suite für GeminiAnalyzer"""
    
    def setUp(self):
        """Setup für jeden Test"""
        # Mock API-Key für Tests
        os.environ['GOOGLE_API_KEY'] = 'test_api_key_12345'
        self.analyzer = GeminiAnalyzer()
        
        # Mock-Response für API-Calls
        self.mock_api_response = {
            "suggestions": [
                {
                    "original_text": "Large Language Model",
                    "suggested_text": "Large Language Model (LLM)",
                    "reason": "Abkürzungen sollten bei der ersten Erwähnung ausgeschrieben werden",
                    "category": "academic",
                    "confidence": 0.9
                },
                {
                    "original_text": "KI-basierte Technologien",
                    "suggested_text": "KI-basierte Technologien bieten innovative Lösungen",
                    "reason": "Präzisere und informativere Formulierung",
                    "category": "style",
                    "confidence": 0.8
                }
            ]
        }
    
    def tearDown(self):
        """Cleanup nach jedem Test"""
        if 'GOOGLE_API_KEY' in os.environ:
            del os.environ['GOOGLE_API_KEY']
    
    def test_initialization(self):
        """Test Initialisierung des Analyzers"""
        self.assertEqual(self.analyzer.model, "gemini-1.5-flash")
        self.assertIsNotNone(self.analyzer.client)
        self.assertIn("academic", self.analyzer.categories)
        self.assertIn("style", self.analyzer.categories)
        self.assertIn("grammar", self.analyzer.categories)
        self.assertIn("clarity", self.analyzer.categories)
    
    def test_missing_api_key(self):
        """Test Verhalten ohne API-Key"""
        del os.environ['GOOGLE_API_KEY']
        
        with self.assertRaises(ValueError) as context:
            GeminiAnalyzer()
        
        self.assertIn("GOOGLE_API_KEY", str(context.exception))
    
    def test_category_mapping(self):
        """Test Kategorie-Mapping"""
        categories = self.analyzer.categories
        
        # Prüfe alle erwarteten Kategorien
        expected_categories = ["academic", "style", "grammar", "clarity"]
        for category in expected_categories:
            self.assertIn(category, categories)
            self.assertIn("name", categories[category])
            self.assertIn("description", categories[category])
    
    def test_json_extraction_valid(self):
        """Test JSON-Extraktion aus valider Response"""
        text_with_json = '''
        Hier ist die Analyse:
        ```json
        {
            "suggestions": [
                {
                    "original_text": "Test",
                    "suggested_text": "Besserer Test",
                    "reason": "Verbesserung",
                    "category": "style",
                    "confidence": 0.8
                }
            ]
        }
        ```
        Weitere Erklärungen...
        '''
        
        extracted = self.analyzer._extract_json_from_response(text_with_json)
        self.assertIsInstance(extracted, dict)
        self.assertIn("suggestions", extracted)
        self.assertEqual(len(extracted["suggestions"]), 1)
    
    def test_json_extraction_invalid(self):
        """Test JSON-Extraktion aus invalider Response"""
        invalid_responses = [
            "Keine JSON-Daten vorhanden",
            "```json\n{invalid json}\n```",
            "```json\n{\"incomplete\": \n```",
            ""
        ]
        
        for response in invalid_responses:
            result = self.analyzer._extract_json_from_response(response)
            self.assertIsNone(result)
    
    def test_suggestion_creation(self):
        """Test Suggestion-Objekt-Erstellung"""
        suggestion_data = {
            "original_text": "Test text",
            "suggested_text": "Improved test text", 
            "reason": "Better clarity",
            "category": "style",
            "confidence": 0.85
        }
        
        suggestion = self.analyzer._create_suggestion(suggestion_data, 10, 20)
        
        self.assertEqual(suggestion.original_text, "Test text")
        self.assertEqual(suggestion.suggested_text, "Improved test text")
        self.assertEqual(suggestion.reason, "Better clarity")
        self.assertEqual(suggestion.category, "style")
        self.assertEqual(suggestion.confidence, 0.85)
        self.assertEqual(suggestion.position, (10, 20))
    
    def test_suggestion_validation(self):
        """Test Validierung von Suggestion-Daten"""
        # Valide Suggestion
        valid_data = {
            "original_text": "Test",
            "suggested_text": "Better test",
            "reason": "Improvement",
            "category": "style",
            "confidence": 0.8
        }
        
        self.assertTrue(self.analyzer._validate_suggestion_data(valid_data))
        
        # Invalide Suggestions
        invalid_cases = [
            {},  # Leer
            {"original_text": ""},  # Leerer Text
            {"original_text": "Test"},  # Fehlende Felder
            {"original_text": "Test", "suggested_text": "", "reason": "x", "category": "style", "confidence": 0.8},  # Leerer suggested_text
            {"original_text": "Test", "suggested_text": "Better", "reason": "x", "category": "invalid", "confidence": 0.8},  # Ungültige Kategorie
            {"original_text": "Test", "suggested_text": "Better", "reason": "x", "category": "style", "confidence": 1.5},  # Ungültige Confidence
        ]
        
        for invalid_data in invalid_cases:
            self.assertFalse(self.analyzer._validate_suggestion_data(invalid_data))
    
    def test_cost_estimation(self):
        """Test Kostenschätzung"""
        test_text = "Dies ist ein Testtext für die Kostenschätzung."
        cost = self.analyzer.get_cost_estimate(test_text)
        
        self.assertIsInstance(cost, float)
        self.assertGreater(cost, 0)
        self.assertLess(cost, 1.0)  # Sollte unter $1 für kurzen Text sein
    
    def test_token_counting(self):
        """Test Token-Zählung"""
        test_texts = [
            "Kurzer Text",
            "Dies ist ein längerer Text mit mehr Wörtern und komplexeren Sätzen.",
            "a" * 1000  # Sehr langer Text
        ]
        
        for text in test_texts:
            tokens = self.analyzer._count_tokens(text)
            self.assertIsInstance(tokens, int)
            self.assertGreater(tokens, 0)
            # Längere Texte sollten mehr Tokens haben
            if len(text) > 100:
                self.assertGreater(tokens, 10)
    
    @patch('google.generativeai.GenerativeModel')
    def test_api_call_success(self, mock_model):
        """Test erfolgreichen API-Call"""
        # Mock API-Response
        mock_response = MagicMock()
        mock_response.text = json.dumps(self.mock_api_response)
        
        mock_instance = MagicMock()
        mock_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_instance
        
        # Erstelle neuen Analyzer mit Mock
        analyzer = GeminiAnalyzer()
        analyzer.client = mock_instance
        
        # Teste Analyse
        suggestions = analyzer.analyze_text("Test text for analysis")
        
        self.assertEqual(len(suggestions), 2)
        self.assertEqual(suggestions[0].category, "academic")
        self.assertEqual(suggestions[1].category, "style")
    
    @patch('google.generativeai.GenerativeModel')
    def test_api_call_failure(self, mock_model):
        """Test fehlgeschlagenen API-Call"""
        # Mock API-Exception
        mock_instance = MagicMock()
        mock_instance.generate_content.side_effect = Exception("API Error")
        mock_model.return_value = mock_instance
        
        analyzer = GeminiAnalyzer()
        analyzer.client = mock_instance
        
        # Sollte leere Liste zurückgeben bei Fehler
        suggestions = analyzer.analyze_text("Test text")
        self.assertEqual(len(suggestions), 0)
    
    def test_prompt_generation(self):
        """Test System- und User-Prompt-Generierung"""
        test_text = "Dies ist ein Testtext für die Analyse."
        context = "Wissenschaftliche Arbeit"
        
        system_prompt = self.analyzer._create_system_prompt()
        user_prompt = self.analyzer._create_user_prompt(test_text, context)
        
        # System Prompt Tests
        self.assertIn("Bachelorarbeit", system_prompt)
        self.assertIn("JSON", system_prompt)
        self.assertIn("academic", system_prompt)
        self.assertIn("style", system_prompt)
        
        # User Prompt Tests
        self.assertIn(test_text, user_prompt)
        self.assertIn(context, user_prompt)
        self.assertIn("original_text", user_prompt)
        self.assertIn("suggested_text", user_prompt)
    
    def test_empty_text_handling(self):
        """Test Behandlung von leerem Text"""
        empty_texts = ["", "   ", "\n\t\n", None]
        
        for empty_text in empty_texts:
            suggestions = self.analyzer.analyze_text(empty_text or "")
            self.assertEqual(len(suggestions), 0)
    
    def test_very_long_text_handling(self):
        """Test Behandlung von sehr langem Text"""
        # Generiere sehr langen Text (über Token-Limit)
        long_text = "Dies ist ein sehr langer Testtext. " * 1000
        
        # Sollte nicht abstürzen und valide Response liefern
        suggestions = self.analyzer.analyze_text(long_text)
        self.assertIsInstance(suggestions, list)
    
    def test_special_characters_handling(self):
        """Test Behandlung von Sonderzeichen"""
        special_text = 'Text mit "Anführungszeichen", <Klammern>, & Ampersand und Umlauten: äöü'
        
        # Sollte nicht abstürzen
        suggestions = self.analyzer.analyze_text(special_text)
        self.assertIsInstance(suggestions, list)
    
    def test_category_distribution(self):
        """Test gleichmäßige Kategorie-Verteilung"""
        # Simuliere Response mit verschiedenen Kategorien
        mixed_response = {
            "suggestions": [
                {"original_text": "test1", "suggested_text": "better1", "reason": "r1", "category": "academic", "confidence": 0.9},
                {"original_text": "test2", "suggested_text": "better2", "reason": "r2", "category": "style", "confidence": 0.8},
                {"original_text": "test3", "suggested_text": "better3", "reason": "r3", "category": "grammar", "confidence": 0.7},
                {"original_text": "test4", "suggested_text": "better4", "reason": "r4", "category": "clarity", "confidence": 0.85}
            ]
        }
        
        suggestions = []
        for i, suggestion_data in enumerate(mixed_response["suggestions"]):
            suggestion = self.analyzer._create_suggestion(suggestion_data, i*10, (i+1)*10)
            suggestions.append(suggestion)
        
        # Prüfe Kategorie-Verteilung
        categories = [s.category for s in suggestions]
        unique_categories = set(categories)
        
        self.assertEqual(len(unique_categories), 4)
        self.assertIn("academic", unique_categories)
        self.assertIn("style", unique_categories)
        self.assertIn("grammar", unique_categories)
        self.assertIn("clarity", unique_categories)


class TestAnalyzerIntegration(unittest.TestCase):
    """Integrations-Tests für GeminiAnalyzer"""
    
    @unittest.skipIf(not os.getenv('GOOGLE_API_KEY'), "Benötigt echten API-Key")
    def test_real_api_call(self):
        """Test mit echtem API-Call (nur bei verfügbarem API-Key)"""
        analyzer = GeminiAnalyzer()
        
        test_text = "KI-basierte Technologien werden in Zukunft eine wichtige Rolle spielen."
        suggestions = analyzer.analyze_text(test_text)
        
        self.assertIsInstance(suggestions, list)
        # Bei echtem API-Call können wir nicht die exakte Anzahl vorhersagen
        # aber es sollte eine valide Liste sein


if __name__ == '__main__':
    # Führe Tests aus
    unittest.main(verbosity=2)