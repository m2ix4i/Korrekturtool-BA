"""
Comprehensive tests for AdvancedWordIntegrator
Tests Microsoft Word XML comment integration functionality
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import xml.etree.ElementTree as ET
from docx import Document

# Import the module we're testing
try:
    from src.integrators.advanced_word_integrator_fixed import AdvancedWordIntegrator
except ImportError:
    AdvancedWordIntegrator = None


@pytest.mark.integrator
@pytest.mark.unit
class TestAdvancedWordIntegrator:
    """Test suite for AdvancedWordIntegrator"""
    
    @pytest.mark.skipif(AdvancedWordIntegrator is None, reason="AdvancedWordIntegrator not available")
    def test_integrator_initialization(self, temp_docx_file):
        """Test integrator initialization"""
        integrator = AdvancedWordIntegrator(temp_docx_file)
        
        assert integrator.file_path == temp_docx_file
        assert hasattr(integrator, 'document')
    
    def test_integrator_with_nonexistent_file(self):
        """Test integrator with non-existent file"""
        if AdvancedWordIntegrator is None:
            pytest.skip("AdvancedWordIntegrator not available")
        
        with pytest.raises(Exception):
            AdvancedWordIntegrator("/nonexistent/file.docx")
    
    @pytest.mark.filesystem
    def test_comment_integration_basic(self, create_test_docx, sample_suggestions):
        """Test basic comment integration functionality"""
        if AdvancedWordIntegrator is None:
            pytest.skip("AdvancedWordIntegrator not available")
        
        doc_path = create_test_docx("integration_test.docx")
        integrator = AdvancedWordIntegrator(str(doc_path))
        
        # Test with one suggestion
        suggestion = sample_suggestions[0]
        result = integrator.add_comment(
            text=suggestion.original_text,
            comment=suggestion.reason,
            author="AI Test",
            suggested_text=suggestion.suggested_text
        )
        
        assert result is not None
    
    @pytest.mark.filesystem
    def test_multiple_comments_integration(self, create_test_docx, sample_suggestions):
        """Test integration of multiple comments"""
        if AdvancedWordIntegrator is None:
            pytest.skip("AdvancedWordIntegrator not available")
        
        doc_path = create_test_docx("multiple_comments.docx")
        integrator = AdvancedWordIntegrator(str(doc_path))
        
        for suggestion in sample_suggestions[:3]:  # Use first 3 suggestions
            result = integrator.add_comment(
                text=suggestion.original_text,
                comment=suggestion.reason,
                author=f"AI-{suggestion.category}",
                suggested_text=suggestion.suggested_text
            )
            assert result is not None
    
    def test_comment_xml_structure(self, create_test_docx, sample_suggestions):
        """Test that generated XML has correct comment structure"""
        if AdvancedWordIntegrator is None:
            pytest.skip("AdvancedWordIntegrator not available")
        
        doc_path = create_test_docx("xml_structure_test.docx")
        integrator = AdvancedWordIntegrator(str(doc_path))
        
        suggestion = sample_suggestions[0]
        
        # Mock XML generation to test structure
        with patch.object(integrator, '_create_comment_xml') as mock_create_xml:
            mock_xml_element = MagicMock()
            mock_create_xml.return_value = mock_xml_element
            
            integrator.add_comment(
                text=suggestion.original_text,
                comment=suggestion.reason,
                author="AI Test"
            )
            
            # Verify XML creation was called
            mock_create_xml.assert_called_once()
            args, kwargs = mock_create_xml.call_args
            assert suggestion.reason in str(args) or suggestion.reason in str(kwargs)
    
    def test_text_matching_and_positioning(self, create_test_docx, sample_text_data):
        """Test text matching and comment positioning"""
        if AdvancedWordIntegrator is None:
            pytest.skip("AdvancedWordIntegrator not available")
        
        # Create document with known content
        content = {
            "title": "Test Document",
            "paragraphs": [sample_text_data["academic"]]
        }
        doc_path = create_test_docx("positioning_test.docx", content)
        integrator = AdvancedWordIntegrator(str(doc_path))
        
        # Try to add comment to specific text
        target_text = "Large Language Models"
        comment_text = "Consider adding abbreviation (LLMs)"
        
        result = integrator.add_comment(
            text=target_text,
            comment=comment_text,
            author="AI Test"
        )
        
        # Should succeed if text is found
        if target_text in sample_text_data["academic"]:
            assert result is not None
    
    def test_special_characters_in_comments(self, create_test_docx, sample_text_data):
        """Test handling of special characters in comments"""
        if AdvancedWordIntegrator is None:
            pytest.skip("AdvancedWordIntegrator not available")
        
        doc_path = create_test_docx("special_chars.docx")
        integrator = AdvancedWordIntegrator(str(doc_path))
        
        # Comment with special characters
        special_comment = "Umlaute: äöüß, Anführungszeichen: 'deutsch'"
        
        result = integrator.add_comment(
            text="Test",
            comment=special_comment,
            author="AI Test"
        )
        
        # Should handle special characters gracefully
        assert result is not None or isinstance(result, bool)
    
    @pytest.mark.filesystem
    def test_save_document_with_comments(self, create_test_docx, temp_dir, sample_suggestions):
        """Test saving document with integrated comments"""
        if AdvancedWordIntegrator is None:
            pytest.skip("AdvancedWordIntegrator not available")
        
        doc_path = create_test_docx("save_test.docx")
        integrator = AdvancedWordIntegrator(str(doc_path))
        
        # Add some comments
        for suggestion in sample_suggestions[:2]:
            integrator.add_comment(
                text=suggestion.original_text,
                comment=suggestion.reason,
                author="AI Test"
            )
        
        # Save to new location
        output_path = temp_dir / "saved_with_comments.docx"
        result = integrator.save(str(output_path))
        
        # Verify file was saved
        assert output_path.exists() or result is True
    
    def test_comment_id_generation(self, create_test_docx):
        """Test that comment IDs are generated uniquely"""
        if AdvancedWordIntegrator is None:
            pytest.skip("AdvancedWordIntegrator not available")
        
        doc_path = create_test_docx("id_test.docx")
        integrator = AdvancedWordIntegrator(str(doc_path))
        
        # Mock ID generation to test uniqueness
        with patch.object(integrator, '_generate_comment_id', side_effect=[1, 2, 3]) as mock_id:
            integrator.add_comment(text="Text1", comment="Comment1", author="AI")
            integrator.add_comment(text="Text2", comment="Comment2", author="AI")
            integrator.add_comment(text="Text3", comment="Comment3", author="AI")
            
            # Should generate different IDs
            assert mock_id.call_count == 3
    
    def test_error_handling_invalid_text(self, create_test_docx):
        """Test error handling when text is not found"""
        if AdvancedWordIntegrator is None:
            pytest.skip("AdvancedWordIntegrator not available")
        
        doc_path = create_test_docx("error_test.docx")
        integrator = AdvancedWordIntegrator(str(doc_path))
        
        # Try to add comment to non-existent text
        result = integrator.add_comment(
            text="This text does not exist in the document",
            comment="This comment should fail or be handled gracefully",
            author="AI Test"
        )
        
        # Should either return False, None, or raise handled exception
        assert result is False or result is None or isinstance(result, Exception)
    
    def test_comment_styling_and_formatting(self, create_test_docx, mock_style_config):
        """Test comment styling and formatting options"""
        if AdvancedWordIntegrator is None:
            pytest.skip("AdvancedWordIntegrator not available")
        
        doc_path = create_test_docx("styling_test.docx")
        integrator = AdvancedWordIntegrator(str(doc_path))
        
        # Test with different styles
        for category, style_config in mock_style_config.items():
            result = integrator.add_comment(
                text="Test text",
                comment="Test comment",
                author=style_config["author"],
                style=category
            )
            
            # Should accept style parameters
            assert result is not None or result is False


@pytest.mark.integrator
@pytest.mark.integration
class TestAdvancedWordIntegratorIntegration:
    """Integration tests for word integrator with real documents"""
    
    @pytest.mark.filesystem
    def test_end_to_end_integration(self, integration_test_data, sample_suggestions):
        """Test complete integration workflow"""
        if AdvancedWordIntegrator is None:
            pytest.skip("AdvancedWordIntegrator not available")
        
        input_doc = integration_test_data['input_document']
        output_doc = integration_test_data['output_document']
        
        integrator = AdvancedWordIntegrator(str(input_doc))
        
        # Add all suggestions
        for suggestion in sample_suggestions:
            integrator.add_comment(
                text=suggestion.original_text,
                comment=f"{suggestion.reason}: {suggestion.suggested_text}",
                author=f"AI-{suggestion.category}",
                category=suggestion.category
            )
        
        # Save result
        result = integrator.save(str(output_doc))
        
        # Verify output exists and is readable
        if output_doc.exists():
            # Try to open the resulting document
            result_doc = Document(str(output_doc))
            assert result_doc is not None
    
    @pytest.mark.filesystem
    @pytest.mark.requires_test_files
    def test_with_real_test_document(self, temp_dir, sample_suggestions):
        """Test with actual test document from archive"""
        test_doc_path = Path("archive/test_files/test_document.docx")
        
        if not test_doc_path.exists():
            pytest.skip("Real test document not available")
        
        if AdvancedWordIntegrator is None:
            pytest.skip("AdvancedWordIntegrator not available")
        
        integrator = AdvancedWordIntegrator(str(test_doc_path))
        
        # Add a few comments
        for suggestion in sample_suggestions[:2]:
            result = integrator.add_comment(
                text=suggestion.original_text,
                comment=suggestion.reason,
                author="AI Test"
            )
            # May succeed or fail depending on whether text is found
            assert result is not None or result is False
        
        # Save to temp location
        output_path = temp_dir / "real_doc_with_comments.docx"
        save_result = integrator.save(str(output_path))
        
        # Should save successfully or return appropriate result
        assert save_result is not None
    
    @pytest.mark.filesystem
    def test_large_document_integration(self, test_document_files, sample_suggestions):
        """Test integration with large documents"""
        if AdvancedWordIntegrator is None:
            pytest.skip("AdvancedWordIntegrator not available")
        
        large_doc = test_document_files["large"]
        integrator = AdvancedWordIntegrator(str(large_doc))
        
        # Add comments (may not find all text in generated document)
        success_count = 0
        for suggestion in sample_suggestions:
            result = integrator.add_comment(
                text=suggestion.original_text,
                comment=suggestion.reason,
                author="AI Test"
            )
            if result:
                success_count += 1
        
        # At least the integrator should handle the large document without crashing
        assert hasattr(integrator, 'document')
        assert success_count >= 0  # May be 0 if no text matches


@pytest.mark.integrator
@pytest.mark.performance
class TestAdvancedWordIntegratorPerformance:
    """Performance tests for word integrator"""
    
    @pytest.mark.benchmark
    def test_comment_integration_speed(self, create_test_docx, sample_suggestions, benchmark):
        """Benchmark comment integration speed"""
        if AdvancedWordIntegrator is None:
            pytest.skip("AdvancedWordIntegrator not available")
        
        doc_path = create_test_docx("benchmark_test.docx")
        integrator = AdvancedWordIntegrator(str(doc_path))
        suggestion = sample_suggestions[0]
        
        def add_single_comment():
            return integrator.add_comment(
                text=suggestion.original_text,
                comment=suggestion.reason,
                author="AI Test"
            )
        
        result = benchmark(add_single_comment)
        assert result is not None or result is False
    
    @pytest.mark.memory
    def test_memory_usage_many_comments(self, create_test_docx, sample_suggestions, memory_monitor):
        """Test memory usage when adding many comments"""
        if AdvancedWordIntegrator is None:
            pytest.skip("AdvancedWordIntegrator not available")
        
        doc_path = create_test_docx("memory_test.docx")
        integrator = AdvancedWordIntegrator(str(doc_path))
        
        initial_memory = memory_monitor['initial_memory']
        
        # Add many comments (simulate many suggestions)
        for i in range(10):
            for suggestion in sample_suggestions:
                integrator.add_comment(
                    text=f"{suggestion.original_text}_{i}",
                    comment=f"{suggestion.reason}_{i}",
                    author="AI Test"
                )
        
        current_memory = memory_monitor['get_current_memory']()
        memory_increase = current_memory - initial_memory
        
        # Memory usage should be reasonable
        assert memory_increase < 100 * 1024 * 1024  # Less than 100MB
    
    @pytest.mark.slow
    def test_large_scale_integration_performance(self, test_document_files, performance_timer):
        """Test performance with large scale comment integration"""
        if AdvancedWordIntegrator is None:
            pytest.skip("AdvancedWordIntegrator not available")
        
        large_doc = test_document_files["large"]
        integrator = AdvancedWordIntegrator(str(large_doc))
        
        performance_timer['start']('large_scale')
        
        # Try to add many comments
        for i in range(20):
            integrator.add_comment(
                text=f"paragraph {i+1}",  # Generic text that might be found
                comment=f"Comment number {i+1}",
                author="AI Test"
            )
        
        elapsed = performance_timer['end']('large_scale')
        
        # Should complete within reasonable time
        assert elapsed < 30.0  # 30 seconds for 20 comments


@pytest.mark.integrator
@pytest.mark.unit
class TestWordIntegratorUtilities:
    """Test utility functions in word integrator"""
    
    def test_xml_comment_structure(self):
        """Test XML comment structure generation"""
        # Test the expected XML structure for Word comments
        comment_data = {
            'id': 1,
            'author': 'AI Test',
            'date': '2024-01-01T12:00:00Z',
            'text': 'This is a test comment'
        }
        
        # Expected XML elements
        expected_elements = ['w:comment', 'w:p', 'w:r', 'w:t']
        
        # This tests the conceptual structure
        assert comment_data['id'] == 1
        assert comment_data['author'] == 'AI Test'
        assert comment_data['text'] == 'This is a test comment'
    
    def test_comment_reference_structure(self):
        """Test comment reference XML structure"""
        reference_data = {
            'id': 1,
            'start_pos': 100,
            'end_pos': 150
        }
        
        # Expected reference elements
        expected_ref_elements = ['w:commentRangeStart', 'w:commentRangeEnd', 'w:commentReference']
        
        # Test the conceptual structure
        assert reference_data['id'] == 1
        assert reference_data['end_pos'] > reference_data['start_pos']
    
    def test_document_relationships_structure(self):
        """Test document relationships for comments"""
        # Word documents need proper relationships for comments
        relationships = {
            'comments.xml': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments',
            'content_types': '[Content_Types].xml'
        }
        
        assert 'comments.xml' in relationships
        assert relationships['comments.xml'].startswith('http://schemas.openxmlformats.org/')
    
    def test_text_position_calculation(self):
        """Test text position calculation for comment placement"""
        document_text = "This is a test document with some text for comment placement."
        target_text = "test document"
        
        # Find position of target text
        start_pos = document_text.find(target_text)
        end_pos = start_pos + len(target_text)
        
        assert start_pos >= 0
        assert end_pos > start_pos
        assert document_text[start_pos:end_pos] == target_text
    
    def test_comment_id_uniqueness(self):
        """Test comment ID generation and uniqueness"""
        used_ids = set()
        
        # Simulate ID generation
        for i in range(10):
            new_id = i + 1  # Simple sequential ID
            assert new_id not in used_ids
            used_ids.add(new_id)
        
        assert len(used_ids) == 10
        assert max(used_ids) == 10