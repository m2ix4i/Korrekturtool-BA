"""
Pytest Tests für AdvancedGeminiAnalyzer
Tests für moderne AI-Textanalyse mit pytest fixtures
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json
import os

from src.analyzers.advanced_gemini_analyzer import AdvancedGeminiAnalyzer


class TestAdvancedGeminiAnalyzer:
    """Test Suite für AdvancedGeminiAnalyzer mit pytest"""
    
    def test_analyzer_initialization(self, mock_google_api_key):
        """Test Initialisierung des Analyzers"""
        analyzer = AdvancedGeminiAnalyzer()
        
        assert analyzer.model == "gemini-1.5-flash"
        assert analyzer.client is not None
        assert len(analyzer.categories) == 4
        assert "academic" in analyzer.categories
        assert "style" in analyzer.categories
        assert "grammar" in analyzer.categories
        assert "clarity" in analyzer.categories
    
    def test_missing_api_key_raises_error(self):
        """Test dass fehlender API-Key einen Fehler wirft"""
        # Entferne API-Key temporär
        original_key = os.environ.pop('GOOGLE_API_KEY', None)
        
        with pytest.raises(ValueError, match="GOOGLE_API_KEY"):
            AdvancedGeminiAnalyzer()
        
        # Stelle API-Key wieder her
        if original_key:
            os.environ['GOOGLE_API_KEY'] = original_key
    
    def test_json_extraction_valid_response(self, mock_google_api_key):
        """Test JSON-Extraktion aus valider API-Response"""
        analyzer = AdvancedGeminiAnalyzer()
        
        response_text = '''
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
        '''
        
        result = analyzer._extract_json_from_response(response_text)
        
        assert isinstance(result, dict)
        assert "suggestions" in result
        assert len(result["suggestions"]) == 1
        assert result["suggestions"][0]["original_text"] == "Test"
    
    @pytest.mark.parametrize("invalid_response", [
        "Keine JSON-Daten",
        "```json\n{invalid json}\n```", 
        "```json\n{\"incomplete\": \n```",
        ""
    ])
    def test_json_extraction_invalid_responses(self, mock_google_api_key, invalid_response):
        """Test JSON-Extraktion mit verschiedenen invaliden Responses"""
        analyzer = AdvancedGeminiAnalyzer()
        result = analyzer._extract_json_from_response(invalid_response)
        assert result is None
    
    def test_suggestion_validation(self, mock_google_api_key):
        """Test Validierung von Suggestion-Daten"""
        analyzer = AdvancedGeminiAnalyzer()
        
        # Valide Suggestion
        valid_data = {
            "original_text": "Test",
            "suggested_text": "Better test",
            "reason": "Improvement",
            "category": "style",
            "confidence": 0.8
        }
        assert analyzer._validate_suggestion_data(valid_data) is True
        
        # Invalide Suggestions
        invalid_cases = [
            {},  # Leer
            {"original_text": ""},  # Leerer Text
            {"original_text": "Test"},  # Fehlende Felder
            {"original_text": "Test", "suggested_text": "", "reason": "x", "category": "style", "confidence": 0.8},
            {"original_text": "Test", "suggested_text": "Better", "reason": "x", "category": "invalid", "confidence": 0.8},
            {"original_text": "Test", "suggested_text": "Better", "reason": "x", "category": "style", "confidence": 1.5},
        ]
        
        for invalid_data in invalid_cases:
            assert analyzer._validate_suggestion_data(invalid_data) is False
    
    def test_cost_estimation(self, mock_google_api_key):
        """Test Kostenschätzung für API-Calls"""
        analyzer = AdvancedGeminiAnalyzer()
        test_text = "Dies ist ein Testtext für die Kostenschätzung."
        
        cost = analyzer.get_cost_estimate(test_text)
        
        assert isinstance(cost, float)
        assert cost > 0
        assert cost < 1.0  # Sollte unter $1 für kurzen Text sein
    
    def test_token_counting(self, mock_google_api_key):
        """Test Token-Zählung für verschiedene Textlängen"""
        analyzer = AdvancedGeminiAnalyzer()
        
        test_cases = [
            ("Kurzer Text", 5),  # Approximation
            ("Dies ist ein längerer Text mit mehr Wörtern.", 15),
            ("a" * 1000, 100)  # Sehr langer Text
        ]
        
        for text, min_expected_tokens in test_cases:
            tokens = analyzer._count_tokens(text)
            assert isinstance(tokens, int)
            assert tokens > 0
            if len(text) > 50:
                assert tokens > min_expected_tokens
    
    @patch('google.generativeai.GenerativeModel')
    def test_successful_analysis(self, mock_model, mock_google_api_key):
        """Test erfolgreiche Text-Analyse"""
        # Mock API-Response
        mock_response = Mock()
        mock_response.text = json.dumps({
            "suggestions": [
                {
                    "original_text": "Large Language Model",
                    "suggested_text": "Large Language Model (LLM)",
                    "reason": "Abkürzung ausschreiben",
                    "category": "academic",
                    "confidence": 0.9
                }
            ]
        })
        
        mock_instance = Mock()
        mock_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_instance
        
        analyzer = AdvancedGeminiAnalyzer()
        analyzer.client = mock_instance
        
        suggestions = analyzer.analyze_text("Test text for analysis")
        
        assert len(suggestions) == 1
        assert suggestions[0].category == "academic"
        assert suggestions[0].confidence == 0.9
    
    @patch('google.generativeai.GenerativeModel')
    def test_api_failure_handling(self, mock_model, mock_google_api_key):
        """Test Behandlung von API-Fehlern"""
        mock_instance = Mock()
        mock_instance.generate_content.side_effect = Exception("API Error")
        mock_model.return_value = mock_instance
        
        analyzer = AdvancedGeminiAnalyzer()
        analyzer.client = mock_instance
        
        suggestions = analyzer.analyze_text("Test text")
        assert len(suggestions) == 0
    
    @pytest.mark.parametrize("empty_text", ["", "   ", "\n\t\n", None])
    def test_empty_text_handling(self, mock_google_api_key, empty_text):
        """Test Behandlung von leerem/None Text"""
        analyzer = AdvancedGeminiAnalyzer()
        suggestions = analyzer.analyze_text(empty_text or "")
        assert len(suggestions) == 0
    
    def test_prompt_generation(self, mock_google_api_key):
        """Test System- und User-Prompt-Generierung"""
        analyzer = AdvancedGeminiAnalyzer()
        test_text = "Dies ist ein Testtext für die Analyse."
        context = "Wissenschaftliche Arbeit"
        
        system_prompt = analyzer._create_system_prompt()
        user_prompt = analyzer._create_user_prompt(test_text, context)
        
        # System Prompt Tests
        assert "Bachelorarbeit" in system_prompt
        assert "JSON" in system_prompt
        assert "academic" in system_prompt
        
        # User Prompt Tests
        assert test_text in user_prompt
        assert context in user_prompt
        assert "original_text" in user_prompt
    
    @pytest.mark.slow
    def test_performance_long_text(self, mock_google_api_key):
        """Test Performance mit langem Text"""
        analyzer = AdvancedGeminiAnalyzer()
        long_text = "Dies ist ein sehr langer Testtext. " * 500
        
        # Sollte nicht abstürzen
        suggestions = analyzer.analyze_text(long_text)
        assert isinstance(suggestions, list)
    
    def test_special_characters(self, mock_google_api_key):
        """Test Behandlung von Sonderzeichen"""
        analyzer = AdvancedGeminiAnalyzer()
        special_text = 'Text mit "Anführungszeichen", <Klammern>, & Ampersand und Umlauten: äöü'
        
        suggestions = analyzer.analyze_text(special_text)
        assert isinstance(suggestions, list)
    
    def test_multi_category_analysis(self, mock_google_api_key, sample_suggestions):
        """Test Multi-Kategorie-Analyse"""
        analyzer = AdvancedGeminiAnalyzer()
        
        # Simuliere verschiedene Kategorien
        categories = [s.category for s in sample_suggestions]
        unique_categories = set(categories)
        
        assert len(unique_categories) >= 1
        assert all(cat in analyzer.categories for cat in unique_categories)


@pytest.mark.integration
class TestAdvancedAnalyzerIntegration:
    """Integrations-Tests für AdvancedGeminiAnalyzer"""
    
    @pytest.mark.api
    @pytest.mark.skipif(not os.getenv('GOOGLE_API_KEY'), reason="Benötigt echten API-Key")
    def test_real_api_call(self):
        """Test mit echtem API-Call"""
        analyzer = AdvancedGeminiAnalyzer()
        test_text = "KI-basierte Technologien werden in Zukunft eine wichtige Rolle spielen."
        
        suggestions = analyzer.analyze_text(test_text)
        
        assert isinstance(suggestions, list)
        # Bei echtem API-Call variiert die Anzahl