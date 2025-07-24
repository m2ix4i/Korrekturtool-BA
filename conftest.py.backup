import pytest
import os
import tempfile
import json
import shutil
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch
from typing import Dict, List, Any, Generator
from docx import Document
from docx.shared import Inches

# Import project modules for type hints and fixtures
from src.analyzers.advanced_gemini_analyzer import Suggestion, AdvancedGeminiAnalyzer
from src.parsers.docx_parser import DocumentChunk, DocxParser


# =============================================================================
# ENVIRONMENT AND API FIXTURES
# =============================================================================

@pytest.fixture(scope="session")
def test_env_setup():
    """Set up test environment variables at session level"""
    original_env = os.environ.copy()
    # Set test-specific environment variables
    os.environ['TESTING'] = 'true'
    os.environ['LOG_LEVEL'] = 'DEBUG'
    yield
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def mock_google_api_key():
    """Mock Google API Key für Tests"""
    original_key = os.environ.get('GOOGLE_API_KEY')
    os.environ['GOOGLE_API_KEY'] = 'test_api_key_for_testing_12345'
    yield 'test_api_key_for_testing_12345'
    if original_key:
        os.environ['GOOGLE_API_KEY'] = original_key
    else:
        os.environ.pop('GOOGLE_API_KEY', None)


@pytest.fixture
def real_api_key():
    """Real API key for integration tests - skip if not available"""
    api_key = os.environ.get('GOOGLE_API_KEY')
    if not api_key:
        pytest.skip("Real GOOGLE_API_KEY not available for integration test")
    return api_key


@pytest.fixture
def mock_gemini_client():
    """Mock Gemini API Client with configurable responses"""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "suggestions": [
            {
                "original_text": "Example text",
                "suggested_text": "Improved example text",
                "reason": "Better clarity",
                "category": "style",
                "confidence": 0.8
            }
        ]
    })
    mock_client.generate_content.return_value = mock_response
    return mock_client


# =============================================================================
# FILE SYSTEM AND DOCUMENT FIXTURES
# =============================================================================

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def temp_docx_file():
    """Create a temporary DOCX file for testing"""
    with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as f:
        temp_path = f.name
    yield temp_path
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def sample_docx_content():
    """Sample content for creating test DOCX files"""
    return {
        "title": "Test Document Title",
        "paragraphs": [
            "Dies ist der erste Absatz mit wichtigen Informationen über KI-Technologien.",
            "Der zweite Absatz enthält wissenschaftliche Erkenntnisse und Large Language Model Konzepte.",
            "Ein dritter Absatz mit grammatikalischen Herausforderungen und Stilproblemen.",
            "Der finale Absatz fasst die wichtigsten Punkte zusammen und bietet Ausblick.",
        ],
        "heading": "Wichtige Überschrift",
        "bullet_points": [
            "Erster Punkt der Liste",
            "Zweiter wichtiger Punkt", 
            "Dritter und letzter Punkt"
        ]
    }


@pytest.fixture
def create_test_docx(temp_dir, sample_docx_content):
    """Factory fixture to create test DOCX files with content"""
    def _create_docx(filename: str = "test_document.docx", custom_content: Dict = None) -> Path:
        content = custom_content or sample_docx_content
        file_path = temp_dir / filename
        
        doc = Document()
        
        # Add title
        title = doc.add_heading(content["title"], level=1)
        
        # Add heading
        if "heading" in content:
            doc.add_heading(content["heading"], level=2)
        
        # Add paragraphs
        for paragraph in content["paragraphs"]:
            doc.add_paragraph(paragraph)
        
        # Add bullet points if available
        if "bullet_points" in content:
            for point in content["bullet_points"]:
                doc.add_paragraph(point, style='List Bullet')
        
        doc.save(str(file_path))
        return file_path
    
    return _create_docx


@pytest.fixture
def test_document_files(temp_dir):
    """Create multiple test document files for comprehensive testing"""
    files = {}
    
    # Small document
    small_doc = Document()
    small_doc.add_paragraph("Short test document with minimal content.")
    small_path = temp_dir / "small_document.docx"
    small_doc.save(str(small_path))
    files["small"] = small_path
    
    # Medium document
    medium_doc = Document()
    medium_doc.add_heading("Medium Test Document", level=1)
    for i in range(5):
        medium_doc.add_paragraph(f"This is paragraph {i+1} with some content for testing purposes. It contains multiple sentences and various text patterns.")
    medium_path = temp_dir / "medium_document.docx"
    medium_doc.save(str(medium_path))
    files["medium"] = medium_path
    
    # Large document (for performance testing)
    large_doc = Document()
    large_doc.add_heading("Large Test Document", level=1)
    for i in range(50):
        large_doc.add_paragraph(f"This is a longer paragraph {i+1} for performance testing. " * 10)
    large_path = temp_dir / "large_document.docx"
    large_doc.save(str(large_path))
    files["large"] = large_path
    
    yield files


# =============================================================================
# DATA FIXTURES AND FACTORIES
# =============================================================================

@pytest.fixture
def sample_suggestions():
    """Sample suggestion objects for testing"""
    return [
        Suggestion(
            original_text="Large Language Model",
            suggested_text="Large Language Model (LLM)",
            reason="Abkürzung bei erster Erwähnung ausschreiben",
            category="academic",
            confidence=0.9,
            position=(100, 120)
        ),
        Suggestion(
            original_text="KI-basierte Technologien",
            suggested_text="KI-basierte Technologien bieten innovative Lösungen",
            reason="Präzisere und vollständigere Formulierung",
            category="style",
            confidence=0.8,
            position=(200, 240)
        ),
        Suggestion(
            original_text="Dies ist falsch",
            suggested_text="Dies ist korrekt",
            reason="Grammatikfehler korrigieren",
            category="grammar",
            confidence=0.95,
            position=(300, 317)
        ),
        Suggestion(
            original_text="Es ist nicht klar",
            suggested_text="Die Aussage ist mehrdeutig und sollte präzisiert werden",
            reason="Klarheit und Verständlichkeit verbessern",
            category="clarity",
            confidence=0.85,
            position=(400, 416)
        )
    ]


@pytest.fixture
def suggestion_factory():
    """Factory for creating custom suggestions"""
    def _create_suggestion(
        original_text: str = "Default text",
        suggested_text: str = "Improved text",
        reason: str = "Test reason",
        category: str = "style",
        confidence: float = 0.8,
        position: tuple = (0, 12)
    ) -> Suggestion:
        return Suggestion(
            original_text=original_text,
            suggested_text=suggested_text,
            reason=reason,
            category=category,
            confidence=confidence,
            position=position
        )
    return _create_suggestion


@pytest.fixture
def document_chunk_factory():
    """Factory for creating document chunks"""
    def _create_chunk(
        text: str = "Default chunk text",
        start_pos: int = 0,
        end_pos: int = None,
        paragraph_idx: int = 0,
        element_type: str = "paragraph"
    ) -> DocumentChunk:
        if end_pos is None:
            end_pos = len(text)
        return DocumentChunk(text, start_pos, end_pos, paragraph_idx, element_type)
    return _create_chunk


@pytest.fixture
def sample_text_data():
    """Various text samples for testing different scenarios"""
    return {
        "simple": "Dies ist ein einfacher Testtext.",
        "with_errors": "Dies ist ein Text mit Fehlern und schlächte Grammatik.",
        "academic": "Large Language Models stellen eine bedeutende Entwicklung in der KI-Forschung dar.",
        "complex": "Die Implementierung von Machine Learning Algorithmen in produktiven Umgebungen erfordert umfassende Kenntnisse der zugrundeliegenden mathematischen Konzepte sowie praktische Erfahrung mit den entsprechenden Software-Frameworks.",
        "german_special": "Umlaute und Sonderzeichen: äöüß, sowie Anführungszeichen „deutsche" und ‚einfache'.",
        "mixed_content": "Text mit Zahlen 123, URLs https://example.com und E-Mail test@example.com.",
        "empty": "",
        "whitespace_only": "   \n\t   ",
        "very_long": "Dies ist ein sehr langer Text. " * 100
    }


# =============================================================================
# MOCK FIXTURES FOR EXTERNAL DEPENDENCIES
# =============================================================================

@pytest.fixture
def mock_genai():
    """Mock the entire google.generativeai module"""
    with patch('google.generativeai') as mock_genai:
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = json.dumps({
            "suggestions": [
                {
                    "original_text": "Test",
                    "suggested_text": "Improved test",
                    "reason": "Better wording",
                    "category": "style",
                    "confidence": 0.8
                }
            ]
        })
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        mock_genai.configure = Mock()
        yield mock_genai


@pytest.fixture
def mock_file_operations():
    """Mock file system operations"""
    with patch('builtins.open', mock=Mock()) as mock_open, \
         patch('os.path.exists', return_value=True) as mock_exists, \
         patch('os.makedirs') as mock_makedirs:
        yield {
            'open': mock_open,
            'exists': mock_exists,
            'makedirs': mock_makedirs
        }


# =============================================================================
# PERFORMANCE AND MEMORY FIXTURES
# =============================================================================

@pytest.fixture
def memory_monitor():
    """Monitor memory usage during tests"""
    import psutil
    import gc
    
    process = psutil.Process()
    initial_memory = process.memory_info().rss
    
    yield {
        'initial_memory': initial_memory,
        'get_current_memory': lambda: process.memory_info().rss,
        'get_memory_diff': lambda: process.memory_info().rss - initial_memory
    }
    
    # Cleanup
    gc.collect()


@pytest.fixture
def performance_timer():
    """Timer for performance testing"""
    import time
    
    times = {}
    
    def start_timer(name: str):
        times[name] = time.time()
    
    def end_timer(name: str) -> float:
        if name not in times:
            raise ValueError(f"Timer '{name}' not started")
        elapsed = time.time() - times[name]
        del times[name]
        return elapsed
    
    yield {
        'start': start_timer,
        'end': end_timer
    }


# =============================================================================
# INTEGRATION TEST FIXTURES
# =============================================================================

@pytest.fixture
def integration_test_data(temp_dir, sample_docx_content):
    """Complete test data setup for integration tests"""
    # Create test document
    doc_path = temp_dir / "integration_test.docx"
    doc = Document()
    doc.add_heading(sample_docx_content["title"], level=1)
    for paragraph in sample_docx_content["paragraphs"]:
        doc.add_paragraph(paragraph)
    doc.save(str(doc_path))
    
    # Expected output path
    output_path = temp_dir / "integration_test_output.docx"
    
    return {
        'input_document': doc_path,
        'output_document': output_path,
        'temp_dir': temp_dir,
        'content': sample_docx_content
    }


# =============================================================================
# CONFIGURATION AND SETTINGS FIXTURES
# =============================================================================

@pytest.fixture
def test_config():
    """Test configuration settings"""
    return {
        'api_timeout': 30,
        'max_retries': 3,
        'chunk_size': 1000,
        'overlap_size': 200,
        'categories': ['grammar', 'style', 'clarity', 'academic'],
        'confidence_threshold': 0.7,
        'max_suggestions_per_chunk': 10
    }


@pytest.fixture
def mock_style_config():
    """Mock style configuration for comment formatting"""
    return {
        "default": {
            "author": "AI Korrektor",
            "color": "#FF0000",
            "template": "{reason}: {suggested_text}"
        },
        "academic": {
            "author": "Academic AI",
            "color": "#0000FF", 
            "template": "[Academic] {reason}: {suggested_text}"
        },
        "grammar": {
            "author": "Grammar AI",
            "color": "#FF0000",
            "template": "[Grammar] {suggested_text}"
        }
    }


# =============================================================================
# CLEANUP AND UTILITY FIXTURES
# =============================================================================

@pytest.fixture(autouse=True)
def cleanup_temp_files():
    """Automatically cleanup temporary files after each test"""
    temp_files = []
    
    def register_temp_file(filepath):
        temp_files.append(filepath)
    
    yield register_temp_file
    
    # Cleanup
    for filepath in temp_files:
        try:
            if os.path.exists(filepath):
                os.unlink(filepath)
        except Exception:
            pass  # Ignore cleanup errors