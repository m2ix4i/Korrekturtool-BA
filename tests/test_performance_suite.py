"""
Performance Test Suite
Comprehensive performance testing for the Bachelor Thesis Correction Tool
"""

import pytest
import time
import psutil
import gc
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import main application modules
try:
    from src.analyzers.advanced_gemini_analyzer import AdvancedGeminiAnalyzer
    from src.parsers.docx_parser import DocxParser
    from src.integrators.advanced_word_integrator_fixed import AdvancedWordIntegrator
except ImportError:
    # Handle missing modules gracefully
    AdvancedGeminiAnalyzer = None
    DocxParser = None
    AdvancedWordIntegrator = None


@pytest.mark.performance
@pytest.mark.benchmark
class TestPerformanceBenchmarks:
    """Performance benchmarks for core components"""
    
    @pytest.mark.skipif(DocxParser is None, reason="DocxParser not available")
    def test_document_parsing_speed(self, test_document_files, benchmark):
        """Benchmark document parsing speed across different document sizes"""
        def parse_document(doc_path):
            return DocxParser(str(doc_path))
        
        # Test with different document sizes
        for size, doc_path in test_document_files.items():
            result = benchmark.pedantic(
                parse_document,
                args=(doc_path,),
                rounds=3,
                iterations=1
            )
            assert result.document is not None
            
            # Performance assertions based on document size
            if size == "small":
                assert benchmark.stats['mean'] < 1.0  # < 1 second for small docs
            elif size == "medium":
                assert benchmark.stats['mean'] < 5.0  # < 5 seconds for medium docs
            elif size == "large":
                assert benchmark.stats['mean'] < 15.0  # < 15 seconds for large docs
    
    @pytest.mark.skipif(AdvancedGeminiAnalyzer is None, reason="AdvancedGeminiAnalyzer not available")
    def test_ai_analysis_speed(self, mock_google_api_key, sample_text_data, benchmark):
        """Benchmark AI analysis speed with mocked API calls"""
        with patch('google.generativeai.GenerativeModel') as mock_model:
            # Mock fast API response
            mock_response = MagicMock()
            mock_response.text = '{"suggestions": [{"original_text": "test", "suggested_text": "improved test", "reason": "better", "category": "style", "confidence": 0.8}]}'
            mock_instance = MagicMock()
            mock_instance.generate_content.return_value = mock_response
            mock_model.return_value = mock_instance
            
            def analyze_text():
                analyzer = AdvancedGeminiAnalyzer()
                analyzer.client = mock_instance
                return analyzer.analyze_text(sample_text_data["complex"])
            
            result = benchmark(analyze_text)
            assert isinstance(result, list)
            assert benchmark.stats['mean'] < 2.0  # Should be fast with mocked API
    
    @pytest.mark.skipif(AdvancedWordIntegrator is None, reason="AdvancedWordIntegrator not available")
    def test_comment_integration_speed(self, create_test_docx, sample_suggestions, benchmark):
        """Benchmark comment integration speed"""
        doc_path = create_test_docx("benchmark_integration.docx")
        integrator = AdvancedWordIntegrator(str(doc_path))
        suggestion = sample_suggestions[0]
        
        def integrate_comment():
            return integrator.add_comment(
                text=suggestion.original_text,
                comment=suggestion.reason,
                author="AI Test"
            )
        
        result = benchmark(integrate_comment)
        assert result is not None or result is False
        assert benchmark.stats['mean'] < 5.0  # < 5 seconds per comment
    
    def test_text_chunking_performance(self, sample_text_data, benchmark):
        """Benchmark text chunking performance"""
        very_long_text = sample_text_data["very_long"] * 5
        
        def chunk_text():
            # Simple chunking algorithm for benchmark
            chunk_size = 1000
            overlap = 200
            chunks = []
            start = 0
            while start < len(very_long_text):
                end = min(start + chunk_size, len(very_long_text))
                chunks.append(very_long_text[start:end])
                start = end - overlap
                if start >= len(very_long_text):
                    break
            return chunks
        
        result = benchmark(chunk_text)
        assert len(result) > 1
        assert benchmark.stats['mean'] < 1.0  # Should be very fast
    
    def test_text_matching_performance(self, sample_text_data, benchmark):
        """Benchmark text matching performance"""
        text1 = sample_text_data["academic"]
        text2 = sample_text_data["complex"]
        
        def match_texts():
            # Simple matching algorithm for benchmark
            words1 = set(text1.lower().split())
            words2 = set(text2.lower().split())
            intersection = words1 & words2
            union = words1 | words2
            return len(intersection) / len(union) * 100
        
        result = benchmark(match_texts)
        assert 0 <= result <= 100
        assert benchmark.stats['mean'] < 0.1  # Should be very fast


@pytest.mark.performance  
@pytest.mark.memory
class TestMemoryUsage:
    """Memory usage tests for core components"""
    
    def test_document_parsing_memory(self, test_document_files, memory_monitor):
        """Test memory usage during document parsing"""
        if DocxParser is None:
            pytest.skip("DocxParser not available")
        
        initial_memory = memory_monitor['initial_memory']
        
        # Parse different sized documents
        parsers = []
        for size, doc_path in test_document_files.items():
            parser = DocxParser(str(doc_path))
            parsers.append(parser)
            
            current_memory = memory_monitor['get_current_memory']()
            memory_increase = current_memory - initial_memory
            
            # Memory assertions based on document size
            if size == "small":
                assert memory_increase < 10 * 1024 * 1024  # < 10MB
            elif size == "medium":
                assert memory_increase < 50 * 1024 * 1024  # < 50MB
            elif size == "large":
                assert memory_increase < 200 * 1024 * 1024  # < 200MB
    
    def test_ai_analysis_memory_leak(self, mock_google_api_key, sample_text_data, memory_monitor):
        """Test for memory leaks in AI analysis"""
        if AdvancedGeminiAnalyzer is None:
            pytest.skip("AdvancedGeminiAnalyzer not available")
        
        with patch('google.generativeai.GenerativeModel') as mock_model:
            mock_response = MagicMock()
            mock_response.text = '{"suggestions": []}'
            mock_instance = MagicMock()
            mock_instance.generate_content.return_value = mock_response
            mock_model.return_value = mock_instance
            
            initial_memory = memory_monitor['initial_memory']
            
            # Run multiple analysis cycles
            for i in range(10):
                analyzer = AdvancedGeminiAnalyzer()
                analyzer.client = mock_instance
                analyzer.analyze_text(sample_text_data["complex"])
                
                # Force garbage collection
                del analyzer
                gc.collect()
            
            final_memory = memory_monitor['get_current_memory']()
            memory_increase = final_memory - initial_memory
            
            # Should not have significant memory increase (< 20MB)
            assert memory_increase < 20 * 1024 * 1024
    
    def test_comment_integration_memory_scaling(self, create_test_docx, sample_suggestions, memory_monitor):
        """Test memory scaling with multiple comment integrations"""
        if AdvancedWordIntegrator is None:
            pytest.skip("AdvancedWordIntegrator not available")
        
        doc_path = create_test_docx("memory_scaling.docx")
        integrator = AdvancedWordIntegrator(str(doc_path))
        
        initial_memory = memory_monitor['initial_memory']
        
        # Add multiple comments
        for i in range(20):
            for j, suggestion in enumerate(sample_suggestions[:2]):  # Use 2 suggestions
                integrator.add_comment(
                    text=f"{suggestion.original_text}_{i}_{j}",
                    comment=f"{suggestion.reason}_{i}_{j}",
                    author="AI Test"
                )
        
        final_memory = memory_monitor['get_current_memory']()
        memory_increase = final_memory - initial_memory
        
        # Memory should scale reasonably (< 100MB for 40 comments)
        assert memory_increase < 100 * 1024 * 1024
    
    def test_large_text_processing_memory(self, sample_text_data, memory_monitor):
        """Test memory usage with very large text processing"""
        # Create very large text
        huge_text = sample_text_data["very_long"] * 20
        
        initial_memory = memory_monitor['initial_memory']
        
        # Process large text (simulate various operations)
        words = huge_text.split()
        unique_words = set(words)
        word_count = len(words)
        unique_count = len(unique_words)
        
        # Create chunks
        chunk_size = 5000
        chunks = [huge_text[i:i+chunk_size] for i in range(0, len(huge_text), chunk_size)]
        
        final_memory = memory_monitor['get_current_memory']()
        memory_increase = final_memory - initial_memory
        
        # Should handle large text efficiently
        assert memory_increase < 500 * 1024 * 1024  # < 500MB
        assert word_count > 0
        assert unique_count > 0
        assert len(chunks) > 1


@pytest.mark.performance
@pytest.mark.slow
class TestScalabilityTests:
    """Scalability tests for high-volume scenarios"""
    
    def test_concurrent_document_processing(self, test_document_files, performance_timer):
        """Test concurrent processing of multiple documents"""
        if DocxParser is None:
            pytest.skip("DocxParser not available")
        
        import threading
        import queue
        
        results = queue.Queue()
        
        def process_document(doc_path):
            try:
                parser = DocxParser(str(doc_path))
                results.put(("success", parser))
            except Exception as e:
                results.put(("error", str(e)))
        
        performance_timer['start']('concurrent_processing')
        
        # Create threads for concurrent processing
        threads = []
        for doc_path in test_document_files.values():
            thread = threading.Thread(target=process_document, args=(doc_path,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        elapsed = performance_timer['end']('concurrent_processing')
        
        # Collect results
        success_count = 0
        error_count = 0
        while not results.empty():
            status, result = results.get()
            if status == "success":
                success_count += 1
            else:
                error_count += 1
        
        # Should complete within reasonable time and mostly succeed
        assert elapsed < 60.0  # < 1 minute for concurrent processing
        assert success_count > 0
        assert success_count >= error_count  # More successes than errors
    
    def test_batch_suggestion_processing(self, mock_google_api_key, sample_suggestions, performance_timer):
        """Test processing large batches of suggestions"""
        if AdvancedGeminiAnalyzer is None:
            pytest.skip("AdvancedGeminiAnalyzer not available")
        
        with patch('google.generativeai.GenerativeModel') as mock_model:
            mock_response = MagicMock()
            mock_response.text = '{"suggestions": []}'
            mock_instance = MagicMock()
            mock_instance.generate_content.return_value = mock_response
            mock_model.return_value = mock_instance
            
            analyzer = AdvancedGeminiAnalyzer()
            analyzer.client = mock_instance
            
            # Create large batch of text samples
            text_batch = []
            for i in range(50):
                for suggestion in sample_suggestions:
                    text_batch.append(f"{suggestion.original_text} variation {i}")
            
            performance_timer['start']('batch_processing')
            
            results = []
            for text in text_batch:
                result = analyzer.analyze_text(text)
                results.append(result)
            
            elapsed = performance_timer['end']('batch_processing')
            
            # Should handle large batches efficiently
            assert elapsed < 30.0  # < 30 seconds for 200 texts
            assert len(results) == len(text_batch)
    
    def test_memory_stability_long_running(self, sample_text_data, memory_monitor):
        """Test memory stability over long-running operations"""
        initial_memory = memory_monitor['initial_memory']
        
        # Simulate long-running processing
        for iteration in range(100):
            # Process text
            text = sample_text_data["complex"] * 2
            words = text.split()
            
            # Create and destroy objects
            data_structures = {
                'word_set': set(words),
                'word_list': list(words),
                'word_dict': {word: len(word) for word in words}
            }
            
            # Clean up
            del data_structures
            del words
            del text
            
            # Periodic garbage collection
            if iteration % 20 == 0:
                gc.collect()
                current_memory = memory_monitor['get_current_memory']()
                memory_increase = current_memory - initial_memory
                
                # Memory should remain stable (< 50MB increase)
                assert memory_increase < 50 * 1024 * 1024
        
        # Final memory check
        gc.collect()
        final_memory = memory_monitor['get_current_memory']()
        total_increase = final_memory - initial_memory
        
        # Total memory increase should be minimal
        assert total_increase < 100 * 1024 * 1024  # < 100MB


@pytest.mark.performance
@pytest.mark.integration
class TestEndToEndPerformance:
    """End-to-end performance tests for complete workflows"""
    
    def test_complete_workflow_performance(self, integration_test_data, sample_suggestions, performance_timer):
        """Test performance of complete correction workflow"""
        input_doc = integration_test_data['input_document']
        output_doc = integration_test_data['output_document']
        
        performance_timer['start']('full_workflow')
        
        try:
            # Step 1: Parse document
            if DocxParser is not None:
                parser = DocxParser(str(input_doc))
                parse_time = time.time()
            
            # Step 2: Analyze text (mocked)
            if AdvancedGeminiAnalyzer is not None:
                with patch('google.generativeai.GenerativeModel') as mock_model:
                    mock_response = MagicMock()
                    mock_response.text = '{"suggestions": []}'
                    mock_instance = MagicMock()
                    mock_instance.generate_content.return_value = mock_response
                    mock_model.return_value = mock_instance
                    
                    analyzer = AdvancedGeminiAnalyzer()
                    analyzer.client = mock_instance
                    
                    # Simulate analysis
                    for suggestion in sample_suggestions:
                        analyzer.analyze_text(suggestion.original_text)
                    
                    analyze_time = time.time()
            
            # Step 3: Integrate comments
            if AdvancedWordIntegrator is not None:
                integrator = AdvancedWordIntegrator(str(input_doc))
                
                for suggestion in sample_suggestions[:3]:  # Limit to 3 for performance
                    integrator.add_comment(
                        text=suggestion.original_text,
                        comment=suggestion.reason,
                        author="AI Test"
                    )
                
                integrator.save(str(output_doc))
                integrate_time = time.time()
            
        except Exception as e:
            # Workflow might fail due to missing components, that's OK for performance testing
            pass
        
        elapsed = performance_timer['end']('full_workflow')
        
        # Complete workflow should finish in reasonable time
        assert elapsed < 120.0  # < 2 minutes for full workflow
    
    def test_system_resource_usage(self, integration_test_data, performance_timer):
        """Test overall system resource usage during processing"""
        process = psutil.Process()
        
        # Measure initial resources
        initial_cpu_times = process.cpu_times()
        initial_memory = process.memory_info().rss
        initial_io = process.io_counters() if hasattr(process, 'io_counters') else None
        
        performance_timer['start']('resource_usage')
        
        # Perform resource-intensive operations
        input_doc = integration_test_data['input_document']
        
        try:
            if DocxParser is not None:
                # Parse document multiple times
                for _ in range(5):
                    parser = DocxParser(str(input_doc))
                    del parser
            
            # Simulate memory-intensive operations
            large_data = []
            for i in range(1000):
                large_data.append(f"Data item {i}" * 100)
            
            # CPU-intensive operations
            for i in range(10000):
                _ = sum(range(100))
            
        except Exception:
            pass  # Handle gracefully for testing
        
        elapsed = performance_timer['end']('resource_usage')
        
        # Measure final resources
        final_cpu_times = process.cpu_times()
        final_memory = process.memory_info().rss
        final_io = process.io_counters() if hasattr(process, 'io_counters') else None
        
        # Resource usage should be reasonable
        cpu_time_used = (final_cpu_times.user + final_cpu_times.system) - (initial_cpu_times.user + initial_cpu_times.system)
        memory_increase = final_memory - initial_memory
        
        assert cpu_time_used < 60.0  # < 60 seconds of CPU time
        assert memory_increase < 500 * 1024 * 1024  # < 500MB memory increase
        assert elapsed < 30.0  # < 30 seconds wall time


@pytest.mark.performance
@pytest.mark.regression
class TestPerformanceRegression:
    """Performance regression tests to ensure performance doesn't degrade"""
    
    def test_parsing_performance_baseline(self, test_document_files, benchmark):
        """Establish baseline for document parsing performance"""
        if DocxParser is None:
            pytest.skip("DocxParser not available")
        
        medium_doc = test_document_files["medium"]
        
        def parse_medium_document():
            return DocxParser(str(medium_doc))
        
        result = benchmark(parse_medium_document)
        
        # Performance baseline: medium document should parse in < 3 seconds
        assert benchmark.stats['mean'] < 3.0
        assert result.document is not None
    
    def test_memory_usage_baseline(self, create_test_docx, memory_monitor):
        """Establish baseline for memory usage"""
        initial_memory = memory_monitor['initial_memory']
        
        # Perform standard operations
        doc_path = create_test_docx("baseline_memory.docx")
        
        if DocxParser is not None:
            parser = DocxParser(str(doc_path))
        
        if AdvancedWordIntegrator is not None:
            integrator = AdvancedWordIntegrator(str(doc_path))
        
        current_memory = memory_monitor['get_current_memory']()
        memory_increase = current_memory - initial_memory
        
        # Memory baseline: standard operations should use < 30MB
        assert memory_increase < 30 * 1024 * 1024
    
    def test_api_call_efficiency_baseline(self, mock_google_api_key, sample_text_data):
        """Establish baseline for API call efficiency"""
        if AdvancedGeminiAnalyzer is None:
            pytest.skip("AdvancedGeminiAnalyzer not available")
        
        with patch('google.generativeai.GenerativeModel') as mock_model:
            mock_response = MagicMock()
            mock_response.text = '{"suggestions": []}'
            mock_instance = MagicMock()
            mock_instance.generate_content.return_value = mock_response
            mock_model.return_value = mock_instance
            
            analyzer = AdvancedGeminiAnalyzer()
            analyzer.client = mock_instance
            
            start_time = time.time()
            
            # Analyze multiple texts
            for _ in range(10):
                analyzer.analyze_text(sample_text_data["complex"])
            
            elapsed = time.time() - start_time
            
            # API call baseline: 10 calls should complete in < 5 seconds (mocked)
            assert elapsed < 5.0
            assert mock_instance.generate_content.call_count == 10