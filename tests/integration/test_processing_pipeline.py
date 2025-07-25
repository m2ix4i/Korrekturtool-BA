#!/usr/bin/env python3
"""
Integration tests for processing pipeline (Issue #4)
Tests the complete job lifecycle from creation to completion
"""

import os
import sys
import uuid
import time
import tempfile
import threading
from pathlib import Path
import pytest
from unittest.mock import Mock, patch

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from web.models.job import Job, JobStatus, ProcessingMode, ProcessingOptions
from web.services.job_manager import JobManager
from web.services.background_processor import BackgroundProcessor
from web.services.processor_integration import ProcessorIntegration
from web.utils.secure_file_handler import SecureFileHandler


class TestProcessingPipelineIntegration:
    """Integration tests for complete processing pipeline"""
    
    @pytest.fixture
    def temp_directories(self):
        """Create temporary directories for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            directories = {
                'uploads': temp_path / 'uploads',
                'outputs': temp_path / 'outputs', 
                'temp': temp_path / 'temp'
            }
            
            for dir_path in directories.values():
                dir_path.mkdir(exist_ok=True)
            
            yield directories
    
    @pytest.fixture
    def job_manager(self, temp_directories):
        """Create job manager with temporary storage"""
        with patch.dict(os.environ, {'JOB_STORAGE_PATH': str(temp_directories['temp'] / 'jobs.json')}):
            manager = JobManager()
            yield manager
            manager.stop()
    
    @pytest.fixture
    def background_processor(self, temp_directories):
        """Create background processor for testing"""
        processor = BackgroundProcessor()
        yield processor
        processor.stop()
    
    @pytest.fixture
    def secure_handler(self, temp_directories):
        """Create secure file handler for testing"""
        return SecureFileHandler(str(temp_directories['outputs']))
    
    @pytest.fixture
    def mock_document_file(self, temp_directories):
        """Create mock DOCX file for testing"""
        test_file = temp_directories['uploads'] / f"{uuid.uuid4()}.docx"
        
        # Create a minimal mock DOCX content
        test_content = b"Mock DOCX content for testing"
        with open(test_file, 'wb') as f:
            f.write(test_content)
        
        return str(test_file)
    
    def test_complete_job_lifecycle(self, job_manager, background_processor, mock_document_file):
        """Test complete job lifecycle from creation to completion"""
        
        # 1. Create job
        options = ProcessingOptions(
            categories=['grammar', 'style'],
            output_filename='test_output.docx'
        )
        
        job = job_manager.create_job(
            file_id=str(uuid.uuid4()),
            file_path=mock_document_file,
            processing_mode=ProcessingMode.COMPLETE,
            options=options.to_dict()
        )
        
        assert job is not None
        assert job.status == JobStatus.PENDING
        assert job.file_path == mock_document_file
        
        # 2. Start background processor
        background_processor.start()
        
        # 3. Submit job for processing
        success = background_processor.submit_job(job.job_id)
        assert success == True
        
        # 4. Wait for job to be picked up and started
        max_wait = 10  # seconds
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            updated_job = job_manager.get_job(job.job_id)
            if updated_job and updated_job.status == JobStatus.PROCESSING:
                break
            time.sleep(0.1)
        
        # Verify job was started
        processing_job = job_manager.get_job(job.job_id)
        assert processing_job.status == JobStatus.PROCESSING
        assert processing_job.started_at is not None
    
    def test_job_manager_thread_safety(self, job_manager, mock_document_file):
        """Test job manager thread safety with concurrent operations"""
        
        num_threads = 5
        num_jobs_per_thread = 3
        created_jobs = []
        
        def create_jobs():
            for i in range(num_jobs_per_thread):
                options = ProcessingOptions(categories=['grammar'])
                job = job_manager.create_job(
                    file_id=str(uuid.uuid4()),
                    file_path=mock_document_file,
                    processing_mode=ProcessingMode.COMPLETE,
                    options=options.to_dict()
                )
                created_jobs.append(job.job_id)
                time.sleep(0.01)  # Small delay to interleave operations
        
        # Create threads
        threads = [threading.Thread(target=create_jobs) for _ in range(num_threads)]
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Verify all jobs were created successfully
        expected_count = num_threads * num_jobs_per_thread
        assert len(created_jobs) == expected_count
        
        # Verify all jobs exist in manager
        for job_id in created_jobs:
            job = job_manager.get_job(job_id)
            assert job is not None
            assert job.status == JobStatus.PENDING
    
    def test_secure_file_handler_validation(self, secure_handler, temp_directories):
        """Test secure file handler path validation"""
        
        # Test valid paths
        valid_path = temp_directories['outputs'] / 'test.docx'
        assert secure_handler.validate_file_path(str(valid_path)) == True
        
        # Test path traversal attempts
        traversal_paths = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32\\config\\sam",
            str(temp_directories['outputs']) + "/../../../etc/passwd",
            "/etc/passwd",
            "C:\\Windows\\System32\\config\\sam"
        ]
        
        for bad_path in traversal_paths:
            assert secure_handler.validate_file_path(bad_path) == False
        
        # Test invalid extensions
        invalid_extension = temp_directories['outputs'] / 'test.exe'
        assert secure_handler.validate_file_path(str(invalid_extension)) == False
    
    def test_secure_file_operations(self, secure_handler, temp_directories):
        """Test secure file operations"""
        
        # Create test file
        test_content = b"Test file content for security validation"
        source_file = temp_directories['temp'] / 'source.docx'
        
        with open(source_file, 'wb') as f:
            f.write(test_content)
        
        # Test secure copy
        dest_file = temp_directories['outputs'] / 'destination.docx'
        success = secure_handler.secure_file_copy(str(source_file), str(dest_file))
        assert success == True
        assert dest_file.exists()
        
        # Verify file integrity
        with open(dest_file, 'rb') as f:
            copied_content = f.read()
        assert copied_content == test_content
        
        # Test file info
        file_info = secure_handler.get_file_info(str(dest_file))
        assert file_info is not None
        assert file_info['size'] == len(test_content)
        assert file_info['extension'] == '.docx'
        assert file_info['is_valid'] == True
        
        # Test secure delete
        success = secure_handler.secure_delete(str(dest_file))
        assert success == True
        assert not dest_file.exists()
    
    @patch('web.services.processor_integration.CompleteAdvancedKorrekturtool')
    def test_processor_integration_success(self, mock_processor_class, temp_directories):
        """Test processor integration with mocked processing tools"""
        
        # Setup mock
        mock_processor = Mock()
        mock_processor.process_document_complete.return_value = True
        mock_processor.performance_stats = {
            'start_time': time.time(),
            'end_time': time.time() + 60,
            'total_suggestions': 25,
            'successful_integrations': 22,
            'api_calls_made': 15
        }
        mock_processor_class.return_value = mock_processor
        
        # Create processor integration
        integration = ProcessorIntegration()
        
        # Test processing
        result = integration.process_document(
            input_file_path=str(temp_directories['uploads'] / 'test.docx'),
            processing_mode=ProcessingMode.COMPLETE,
            categories=['grammar', 'style'],
            output_filename='result.docx'
        )
        
        assert result is not None
        assert result.total_suggestions == 25
        assert result.successful_integrations == 22
        assert mock_processor.process_document_complete.called
    
    @patch('web.services.processor_integration.CompleteAdvancedKorrekturtool')
    def test_processor_integration_failure(self, mock_processor_class, temp_directories):
        """Test processor integration error handling"""
        
        # Setup mock to simulate failure
        mock_processor = Mock()
        mock_processor.process_document_complete.side_effect = Exception("Processing failed")
        mock_processor_class.return_value = mock_processor
        
        # Create processor integration
        integration = ProcessorIntegration()
        
        # Test processing failure
        with pytest.raises(Exception, match="Processing failed"):
            integration.process_document(
                input_file_path=str(temp_directories['uploads'] / 'test.docx'),
                processing_mode=ProcessingMode.COMPLETE,
                categories=['grammar', 'style'],
                output_filename='result.docx'
            )
    
    def test_error_handling_and_recovery(self, job_manager, background_processor, mock_document_file):
        """Test error handling and job failure scenarios"""
        
        # Create job with invalid file path
        options = ProcessingOptions(categories=['grammar'])
        job = job_manager.create_job(
            file_id=str(uuid.uuid4()),
            file_path="/nonexistent/file.docx",  # Invalid path
            processing_mode=ProcessingMode.COMPLETE,
            options=options.to_dict()
        )
        
        # Start background processor
        background_processor.start()
        
        # Submit job (should fail during processing)
        background_processor.submit_job(job.job_id)
        
        # Wait for job to fail
        max_wait = 10
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            updated_job = job_manager.get_job(job.job_id)
            if updated_job and updated_job.status == JobStatus.FAILED:
                break
            time.sleep(0.1)
        
        # Verify job failed gracefully
        failed_job = job_manager.get_job(job.job_id)
        assert failed_job.status == JobStatus.FAILED
        assert failed_job.error_message is not None
        assert "not found" in failed_job.error_message.lower()
    
    def test_concurrent_job_processing(self, job_manager, background_processor, mock_document_file):
        """Test concurrent job processing capabilities"""
        
        # Create multiple jobs
        job_ids = []
        for i in range(3):
            options = ProcessingOptions(categories=['grammar'])
            job = job_manager.create_job(
                file_id=str(uuid.uuid4()),
                file_path=mock_document_file,
                processing_mode=ProcessingMode.COMPLETE,
                options=options.to_dict()
            )
            job_ids.append(job.job_id)
        
        # Start background processor
        background_processor.start()
        
        # Submit all jobs
        for job_id in job_ids:
            success = background_processor.submit_job(job_id)
            assert success == True
        
        # Verify jobs are queued
        processor_status = background_processor.get_status()
        assert processor_status['queue_size'] >= len(job_ids) or processor_status['is_processing']
    
    def test_job_cleanup_and_maintenance(self, job_manager, temp_directories):
        """Test job cleanup and maintenance operations"""
        
        # Create job
        options = ProcessingOptions(categories=['grammar'])
        job = job_manager.create_job(
            file_id=str(uuid.uuid4()),
            file_path=str(temp_directories['uploads'] / 'test.docx'),
            processing_mode=ProcessingMode.COMPLETE,
            options=options.to_dict()
        )
        
        # Mark job as completed (simulate completion)
        job_manager.complete_job(job.job_id, Mock())
        
        # Test job exists
        assert job_manager.get_job(job.job_id) is not None
        
        # Test cleanup (with very short retention for testing)
        cleaned_count = job_manager.cleanup_expired_jobs(max_age_hours=0)
        assert cleaned_count >= 1
        
        # Verify job was cleaned up
        assert job_manager.get_job(job.job_id) is None
    
    def test_system_status_and_monitoring(self, job_manager, background_processor):
        """Test system status and monitoring capabilities"""
        
        # Test job manager status
        job_stats = job_manager.get_job_statistics()
        assert 'total_jobs' in job_stats
        assert 'jobs_by_status' in job_stats
        assert 'jobs_by_mode' in job_stats
        
        # Test background processor status
        processor_status = background_processor.get_status()
        assert 'is_running' in processor_status
        assert 'queue_size' in processor_status
        assert 'worker_thread_alive' in processor_status
    
    def teardown_method(self):
        """Cleanup after each test"""
        # Ensure background processors are stopped
        try:
            BackgroundProcessor().stop()
        except:
            pass


class TestSecurityFeatures:
    """Security-focused tests for the processing pipeline"""
    
    def test_file_access_control(self, temp_directories):
        """Test file access control mechanisms"""
        
        handler = SecureFileHandler(str(temp_directories['outputs']))
        
        # Create test file
        test_file = temp_directories['outputs'] / 'test.docx'
        test_file.write_text("test content")
        
        # Test valid access
        assert handler.verify_file_access(str(test_file)) == True
        
        # Test access to non-existent file
        assert handler.verify_file_access(str(temp_directories['outputs'] / 'nonexistent.docx')) == False
        
        # Test access outside base directory
        outside_file = temp_directories['temp'] / 'outside.docx'
        outside_file.write_text("outside content")
        assert handler.verify_file_access(str(outside_file)) == False
    
    def test_secure_filename_generation(self, temp_directories):
        """Test secure filename generation"""
        
        handler = SecureFileHandler(str(temp_directories['outputs']))
        
        # Test filename generation
        filename1 = handler.generate_secure_filename()
        filename2 = handler.generate_secure_filename()
        
        # Should be different
        assert filename1 != filename2
        
        # Should have .docx extension
        assert filename1.endswith('.docx')
        assert filename2.endswith('.docx')
        
        # Should be UUID format
        import uuid
        base1 = filename1.replace('.docx', '')
        try:
            uuid.UUID(base1)
            uuid_valid = True
        except ValueError:
            uuid_valid = False
        assert uuid_valid == True
    
    def test_file_integrity_validation(self, temp_directories):
        """Test file integrity validation"""
        
        handler = SecureFileHandler(str(temp_directories['outputs']))
        
        # Create test file
        test_content = b"Test content for integrity validation"
        test_file = temp_directories['outputs'] / 'integrity_test.docx'
        
        with open(test_file, 'wb') as f:
            f.write(test_content)
        
        # Calculate hash
        hash1 = handler.calculate_file_hash(str(test_file))
        assert hash1 is not None
        
        # Modify file and check hash changes
        with open(test_file, 'ab') as f:
            f.write(b" modified")
        
        hash2 = handler.calculate_file_hash(str(test_file))
        assert hash2 is not None
        assert hash1 != hash2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])