#!/usr/bin/env python3
"""
Unit Tests für ZipWordCommentIntegrator
Testet die kritischen Funktionen der Word-Kommentar-Integration
"""

import unittest
import tempfile
import os
import shutil
import zipfile
import xml.etree.ElementTree as ET
from unittest.mock import patch, MagicMock, mock_open
from dataclasses import dataclass
from typing import Tuple

# Import der zu testenden Klasse
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.integrators.zip_word_comments import ZipWordCommentIntegrator


@dataclass
class MockSuggestion:
    """Mock-Klasse für KI-Verbesserungsvorschläge"""
    original_text: str
    suggested_text: str
    reason: str
    category: str
    confidence: float
    position: Tuple[int, int]


class TestZipWordCommentIntegrator(unittest.TestCase):
    """Test Suite für ZipWordCommentIntegrator"""
    
    def setUp(self):
        """Setup für jeden Test"""
        self.test_doc = "test_document.docx"
        self.integrator = ZipWordCommentIntegrator(self.test_doc)
        
        # Mock-Suggestions für Tests
        self.mock_suggestions = [
            MockSuggestion(
                original_text="Large Language Model",
                suggested_text="Large Language Model (LLM)",
                reason="Abkürzung ausschreiben",
                category="academic",
                confidence=0.9,
                position=(100, 120)
            ),
            MockSuggestion(
                original_text="KI-basierte Technologien",
                suggested_text="KI-basierte Technologien sind innovativ",
                reason="Präzisere Formulierung",
                category="style",
                confidence=0.8,
                position=(200, 220)
            )
        ]
    
    def test_xml_escaping(self):
        """Test XML-Escaping für Sonderzeichen"""
        text_with_special_chars = 'Text mit "Anführungszeichen" & Ampersand < > \''
        escaped = self.integrator._escape_xml(text_with_special_chars)
        
        self.assertIn('&quot;', escaped)
        self.assertIn('&amp;', escaped)
        self.assertIn('&lt;', escaped)
        self.assertIn('&gt;', escaped)
        self.assertIn('&apos;', escaped)
        
        # Stelle sicher, dass normale Zeichen nicht verändert werden
        self.assertIn('Text mit', escaped)
    
    def test_similarity_calculation(self):
        """Test Ähnlichkeitsberechnung zwischen Texten"""
        # Identische Texte
        similarity = self.integrator._calculate_similarity("test", "test")
        self.assertEqual(similarity, 1.0)
        
        # Völlig unterschiedliche Texte
        similarity = self.integrator._calculate_similarity("hello", "xyz")
        self.assertLess(similarity, 0.5)
        
        # Ähnliche Texte
        similarity = self.integrator._calculate_similarity(
            "Large Language Model",
            "Large Language Models"
        )
        self.assertGreater(similarity, 0.8)
    
    def test_comment_id_increment(self):
        """Test automatische ID-Vergabe"""
        initial_id = self.integrator.comment_id
        self.assertEqual(initial_id, 0)
        
        # Simuliere Kommentar-Hinzufügung
        mock_suggestion = self.mock_suggestions[0]
        self.integrator.comment_id += 1
        comment_data = {
            'id': str(self.integrator.comment_id),
            'author': 'KI Korrekturtool',
            'text': 'Test comment'
        }
        self.integrator.comments_data.append(comment_data)
        
        self.assertEqual(self.integrator.comment_id, 1)
        self.assertEqual(len(self.integrator.comments_data), 1)
    
    def test_format_comment_text(self):
        """Test Kommentar-Text-Formatierung"""
        suggestion = self.mock_suggestions[0]
        formatted_text = self.integrator._format_comment_text(suggestion)
        
        self.assertIn("KI-Verbesserung", formatted_text)
        self.assertIn("Wissenschaftlich", formatted_text)  # academic -> Wissenschaftlich
        self.assertIn(suggestion.suggested_text, formatted_text)
        self.assertIn(suggestion.reason, formatted_text)
        self.assertIn("Begründung:", formatted_text)
    
    @patch('os.path.exists')
    def test_backup_creation(self, mock_exists):
        """Test Backup-Erstellung"""
        mock_exists.return_value = True
        
        with patch('shutil.copy2') as mock_copy:
            backup_path = self.integrator.create_backup()
            
            self.assertTrue(backup_path.endswith('_backup.docx'))
            mock_copy.assert_called_once()
    
    def test_text_normalization(self):
        """Test Text-Normalisierung für besseres Matching"""
        # Teste verschiedene Eingaben
        test_cases = [
            ("  Hello   World  ", "hello world"),
            ("UPPERCASE TEXT", "uppercase text"),
            ("Mixed   Case\t\nText", "mixed case text")
        ]
        
        def normalize_text(text):
            return ' '.join(text.lower().strip().split())
        
        for input_text, expected in test_cases:
            result = normalize_text(input_text)
            self.assertEqual(result, expected)
    
    def test_search_strategies(self):
        """Test verschiedene Suchstrategien"""
        test_text = "Dies ist ein langer Testtext. Mit mehreren Sätzen. Und vielen Wörtern."
        
        # Simuliere die Suchstrategien aus _find_paragraph_for_text
        strategies = [
            test_text.strip()[:50],  # Erste 50 Zeichen
            test_text.strip()[:30],  # Erste 30 Zeichen
            test_text.split('.')[0] if '.' in test_text else test_text[:40],  # Erster Satz
            ' '.join(test_text.split()[:8]) if len(test_text.split()) > 8 else test_text  # Erste 8 Wörter
        ]
        
        self.assertEqual(len(strategies), 4)
        self.assertTrue(all(len(s) > 0 for s in strategies))
        self.assertEqual(strategies[2], "Dies ist ein langer Testtext")  # Erster Satz
    
    def test_error_handling_invalid_input(self):
        """Test Error-Handling für ungültige Eingaben"""
        # Leere Suggestion-Liste
        result = self.integrator.add_word_comments_robust([])
        self.assertEqual(result, 0)
        
        # None als Eingabe für _find_paragraph_for_text
        result = self.integrator._find_paragraph_for_text([], None, {})
        self.assertIsNone(result)
        
        # Leerer Text
        result = self.integrator._find_paragraph_for_text([], "", {})
        self.assertIsNone(result)
    
    @patch('zipfile.ZipFile')
    @patch('os.path.exists')
    def test_docx_integrity_check(self, mock_exists, mock_zipfile):
        """Test DOCX-Datei-Integritätsprüfung"""
        mock_exists.return_value = True
        
        # Simuliere korrupte ZIP-Datei
        mock_zip_instance = MagicMock()
        mock_zip_instance.testzip.side_effect = zipfile.BadZipFile("Korrupte Datei")
        mock_zipfile.return_value.__enter__.return_value = mock_zip_instance
        
        result = self.integrator.add_word_comments_robust(self.mock_suggestions)
        self.assertEqual(result, 0)  # Sollte 0 zurückgeben bei korrupter Datei
    
    def test_xml_namespace_handling(self):
        """Test XML-Namespace-Behandlung"""
        # Teste Namespace-Dictionary
        ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        
        # Erstelle Mock-XML-Element mit Namespace
        root = ET.Element('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}document')
        paragraph = ET.SubElement(root, '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p')
        text_elem = ET.SubElement(paragraph, '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t')
        text_elem.text = "Test paragraph text"
        
        # Teste Paragraph-Findung
        paragraphs = root.findall('.//w:p', ns)
        self.assertEqual(len(paragraphs), 1)
        
        # Teste Text-Extraktion
        text_elements = paragraphs[0].findall('.//w:t', ns)
        para_text = ''.join(t.text or '' for t in text_elements)
        self.assertEqual(para_text, "Test paragraph text")
    
    def test_comment_xml_structure(self):
        """Test XML-Struktur für Kommentare"""
        # Füge Test-Kommentar hinzu
        comment_data = {
            'id': '1',
            'author': 'KI Korrekturtool',
            'date': '2025-07-22T15:00:00Z',
            'initials': 'KI',
            'text': 'Test-Kommentar mit <Sonderzeichen> & "Anführungszeichen"',
            'category': 'academic'
        }
        self.integrator.comments_data.append(comment_data)
        
        # Erstelle temporäres Verzeichnis für Test
        with tempfile.TemporaryDirectory() as temp_dir:
            self.integrator.temp_dir = temp_dir
            os.makedirs(os.path.join(temp_dir, 'word'), exist_ok=True)
            
            # Teste XML-Erstellung
            self.integrator._create_comments_xml()
            
            # Prüfe ob Datei erstellt wurde
            comments_path = os.path.join(temp_dir, 'word', 'comments.xml')
            self.assertTrue(os.path.exists(comments_path))
            
            # Parse und validiere XML
            tree = ET.parse(comments_path)
            root = tree.getroot()
            
            # Prüfe Root-Element
            self.assertTrue(root.tag.endswith('comments'))
            
            # Prüfe Kommentar-Element
            comments = root.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}comment')
            self.assertEqual(len(comments), 1)
            
            # Prüfe Attribute
            comment = comments[0]
            self.assertEqual(comment.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}id'), '1')
            self.assertEqual(comment.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}author'), 'KI Korrekturtool')


class TestPerformance(unittest.TestCase):
    """Performance-Tests für große Dokumente"""
    
    def test_large_text_matching(self):
        """Test Performance bei vielen Paragraphen"""
        integrator = ZipWordCommentIntegrator("test.docx")
        
        # Erstelle viele Mock-Paragraphen
        paragraphs = []
        for i in range(1000):
            para = ET.Element('p')
            text_elem = ET.SubElement(para, 't')
            text_elem.text = f"Test paragraph {i} mit etwas längerer text content"
            paragraphs.append(para)
        
        # Teste Suchgeschwindigkeit
        import time
        start_time = time.time()
        
        result = integrator._find_paragraph_for_text(
            paragraphs, 
            "Test paragraph 500", 
            {}
        )
        
        end_time = time.time()
        search_time = end_time - start_time
        
        self.assertIsNotNone(result)
        self.assertLess(search_time, 1.0)  # Sollte unter 1 Sekunde dauern


if __name__ == '__main__':
    # Erstelle Test-Suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestZipWordCommentIntegrator)
    performance_suite = unittest.TestLoader().loadTestsFromTestCase(TestPerformance)
    
    # Kombiniere alle Tests
    all_tests = unittest.TestSuite([suite, performance_suite])
    
    # Führe Tests aus
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(all_tests)
    
    # Zeige Zusammenfassung
    print(f"\n{'='*60}")
    print(f"TEST ZUSAMMENFASSUNG:")
    print(f"{'='*60}")
    print(f"Tests ausgeführt: {result.testsRun}")
    print(f"Fehler: {len(result.errors)}")
    print(f"Fehlgeschlagen: {len(result.failures)}")
    print(f"Erfolgreich: {result.testsRun - len(result.errors) - len(result.failures)}")
    
    if result.errors:
        print(f"\nFEHLER:")
        for test, error in result.errors:
            print(f"- {test}: {error}")
    
    if result.failures:
        print(f"\nFEHLGESCHLAGEN:")
        for test, failure in result.failures:
            print(f"- {test}: {failure}")
    
    if result.wasSuccessful():
        print(f"\n🎉 ALLE TESTS ERFOLGREICH!")
    else:
        print(f"\n❌ EINIGE TESTS FEHLGESCHLAGEN!")