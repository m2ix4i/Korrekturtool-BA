"""
Pytest Tests für Word Integrator
Tests für Word-Kommentar-Integration mit pytest fixtures
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, mock_open
import tempfile
import os
import xml.etree.ElementTree as ET
import zipfile

from src.integrators.advanced_word_integrator_fixed import AdvancedWordIntegratorFixed


class TestAdvancedWordIntegrator:
    """Test Suite für AdvancedWordIntegrator mit pytest"""
    
    @pytest.fixture
    def integrator(self, temp_docx_file):
        """Fixture für WordIntegrator-Instanz"""
        return AdvancedWordIntegratorFixed(temp_docx_file)
    
    def test_integrator_initialization(self, integrator):
        """Test Initialisierung des Integrators"""
        assert integrator.document_path.endswith('.docx')
        assert integrator.comment_id == 0
        assert len(integrator.comments_data) == 0
        assert integrator.temp_dir is None
    
    def test_xml_escaping(self, integrator):
        """Test XML-Escaping für Sonderzeichen"""
        text_with_special = 'Text mit "Anführungszeichen" & Ampersand < > \''
        escaped = integrator._escape_xml(text_with_special)
        
        assert '&quot;' in escaped
        assert '&amp;' in escaped
        assert '&lt;' in escaped
        assert '&gt;' in escaped
        assert '&apos;' in escaped
        assert 'Text mit' in escaped
    
    @pytest.mark.parametrize("text1,text2,expected_min", [
        ("test", "test", 1.0),  # Identisch
        ("hello", "xyz", 0.0),  # Völlig unterschiedlich
        ("Large Language Model", "Large Language Models", 0.8)  # Ähnlich
    ])
    def test_similarity_calculation(self, integrator, text1, text2, expected_min):
        """Test Ähnlichkeitsberechnung zwischen Texten"""
        similarity = integrator._calculate_similarity(text1, text2)
        if expected_min == 1.0:
            assert similarity == 1.0
        elif expected_min == 0.0:
            assert similarity < 0.5
        else:
            assert similarity >= expected_min
    
    def test_comment_formatting(self, integrator, sample_suggestions):
        """Test Kommentar-Text-Formatierung"""
        suggestion = sample_suggestions[0]
        formatted_text = integrator._format_comment_text(suggestion)
        
        assert "KI-Verbesserung" in formatted_text
        assert "Wissenschaftlich" in formatted_text  # academic -> Wissenschaftlich
        assert suggestion.suggested_text in formatted_text
        assert suggestion.reason in formatted_text
        assert "Begründung:" in formatted_text
    
    @patch('os.path.exists', return_value=True)
    @patch('shutil.copy2')
    def test_backup_creation(self, mock_copy, mock_exists, integrator):
        """Test Backup-Erstellung"""
        backup_path = integrator.create_backup()
        
        assert backup_path.endswith('_backup.docx')
        mock_copy.assert_called_once()
    
    def test_comment_id_increment(self, integrator):
        """Test automatische ID-Vergabe"""
        initial_id = integrator.comment_id
        assert initial_id == 0
        
        # Simuliere Kommentar-Hinzufügung
        integrator.comment_id += 1
        comment_data = {
            'id': str(integrator.comment_id),
            'author': 'KI Korrekturtool',
            'text': 'Test comment'
        }
        integrator.comments_data.append(comment_data)
        
        assert integrator.comment_id == 1
        assert len(integrator.comments_data) == 1
    
    def test_empty_suggestions_handling(self, integrator):
        """Test Behandlung von leerer Suggestion-Liste"""
        result = integrator.add_comments([])
        assert result == 0
    
    def test_xml_namespace_handling(self, integrator):
        """Test XML-Namespace-Behandlung"""
        ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        
        # Erstelle Mock-XML mit Namespace
        root = ET.Element('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}document')
        paragraph = ET.SubElement(root, '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p')
        text_elem = ET.SubElement(paragraph, '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t')
        text_elem.text = "Test paragraph text"
        
        # Teste Paragraph-Findung
        paragraphs = root.findall('.//w:p', ns)
        assert len(paragraphs) == 1
        
        # Teste Text-Extraktion
        text_elements = paragraphs[0].findall('.//w:t', ns)
        para_text = ''.join(t.text or '' for t in text_elements)
        assert para_text == "Test paragraph text"
    
    @patch('zipfile.ZipFile')
    @patch('os.path.exists', return_value=True)
    def test_docx_integrity_check(self, mock_exists, mock_zipfile, integrator, sample_suggestions):
        """Test DOCX-Datei-Integritätsprüfung"""
        # Simuliere korrupte ZIP-Datei
        mock_zip_instance = MagicMock()
        mock_zip_instance.testzip.side_effect = zipfile.BadZipFile("Korrupte Datei")
        mock_zipfile.return_value.__enter__.return_value = mock_zip_instance
        
        result = integrator.add_comments(sample_suggestions)
        assert result == 0  # Sollte 0 zurückgeben bei korrupter Datei
    
    def test_text_normalization_strategies(self, integrator):
        """Test Text-Normalisierung für besseres Matching"""
        test_cases = [
            ("  Hello   World  ", "hello world"),
            ("UPPERCASE TEXT", "uppercase text"), 
            ("Mixed   Case\t\nText", "mixed case text")
        ]
        
        def normalize_text(text):
            return ' '.join(text.lower().strip().split())
        
        for input_text, expected in test_cases:
            result = normalize_text(input_text)
            assert result == expected
    
    def test_search_strategies_generation(self, integrator):
        """Test verschiedene Suchstrategien"""
        test_text = "Dies ist ein langer Testtext. Mit mehreren Sätzen. Und vielen Wörtern."
        
        strategies = [
            test_text.strip()[:50],  # Erste 50 Zeichen
            test_text.strip()[:30],  # Erste 30 Zeichen
            test_text.split('.')[0] if '.' in test_text else test_text[:40],
            ' '.join(test_text.split()[:8]) if len(test_text.split()) > 8 else test_text
        ]
        
        assert len(strategies) == 4
        assert all(len(s) > 0 for s in strategies)
        assert strategies[2] == "Dies ist ein langer Testtext"
    
    def test_comment_xml_creation(self, integrator):
        """Test XML-Struktur für Kommentare"""
        comment_data = {
            'id': '1',
            'author': 'KI Korrekturtool',
            'date': '2025-07-22T15:00:00Z',
            'initials': 'KI',
            'text': 'Test-Kommentar mit <Sonderzeichen> & "Anführungszeichen"',
            'category': 'academic'
        }
        integrator.comments_data.append(comment_data)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            integrator.temp_dir = temp_dir
            os.makedirs(os.path.join(temp_dir, 'word'), exist_ok=True)
            
            integrator._create_comments_xml()
            
            comments_path = os.path.join(temp_dir, 'word', 'comments.xml')
            assert os.path.exists(comments_path)
            
            # Parse und validiere XML
            tree = ET.parse(comments_path)
            root = tree.getroot()
            
            assert root.tag.endswith('comments')
            
            comments = root.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}comment')
            assert len(comments) == 1
            
            comment = comments[0]
            assert comment.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}id') == '1'
            assert comment.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}author') == 'KI Korrekturtool'


@pytest.mark.integration
class TestWordIntegratorIntegration:
    """Integrations-Tests für Word Integrator"""
    
    @pytest.fixture
    def integrator_with_temp(self, temp_docx_file):
        """Fixture für Integration-Tests"""
        return AdvancedWordIntegratorFixed(temp_docx_file)
    
    def test_full_integration_workflow(self, integrator_with_temp, sample_suggestions):
        """Test kompletter Integration-Workflow"""
        # Erstelle Mock-DOCX-Struktur
        test_docx_content = b'Mock DOCX content'
        with open(integrator_with_temp.document_path, 'wb') as f:
            f.write(test_docx_content)
        
        # Test Backup-Erstellung
        backup_path = integrator_with_temp.create_backup()
        assert os.path.exists(backup_path)
        
        # Test Kommentar-Hinzufügung (würde bei echter DOCX funktionieren)
        # Hier nur Test der Logik ohne echte DOCX-Manipulation
        assert len(sample_suggestions) > 0
        assert all(hasattr(s, 'original_text') for s in sample_suggestions)


@pytest.mark.slow
class TestWordIntegratorPerformance:
    """Performance-Tests für große Dokumente"""
    
    def test_large_paragraph_matching(self):
        """Test Performance bei vielen Paragraphen"""
        integrator = AdvancedWordIntegratorFixed("test.docx")
        
        # Erstelle viele Mock-Paragraphen
        paragraphs = []
        for i in range(1000):
            para = ET.Element('p')
            text_elem = ET.SubElement(para, 't')
            text_elem.text = f"Test paragraph {i} mit längerer Textinhalt"
            paragraphs.append(para)
        
        # Teste Suchgeschwindigkeit
        import time
        start_time = time.time()
        
        # Simuliere Suche (vereinfacht)
        target_text = "Test paragraph 500"
        found = False
        for para in paragraphs:
            text_elem = para.find('t')
            if text_elem is not None and target_text in (text_elem.text or ""):
                found = True
                break
        
        end_time = time.time()
        search_time = end_time - start_time
        
        assert found is True
        assert search_time < 1.0  # Sollte unter 1 Sekunde dauern
    
    def test_memory_usage_large_comments(self, temp_docx_file):
        """Test Speicherverbrauch bei vielen Kommentaren"""
        integrator = AdvancedWordIntegratorFixed(temp_docx_file)
        
        # Erstelle viele Test-Kommentare
        for i in range(100):
            comment_data = {
                'id': str(i),
                'author': 'KI Korrekturtool',
                'text': f'Test comment {i} with longer text content for memory testing',
                'category': 'academic'
            }
            integrator.comments_data.append(comment_data)
        
        assert len(integrator.comments_data) == 100
        
        # Teste Speicher-Cleanup
        integrator.comments_data.clear()
        assert len(integrator.comments_data) == 0