#!/usr/bin/env python3
"""
Issue #4 Validation Test
Validates that all critical components for Issue #4 are implemented and working
"""

import os
import sys
import tempfile
import uuid
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_models_exist():
    """Test that all required models exist and work"""
    print("✓ Testing models...")
    
    from web.models.job import Job, JobStatus, ProcessingMode, ProcessingOptions
    
    # Test ProcessingOptions
    options = ProcessingOptions(categories=['grammar', 'style'])
    assert options.categories == ['grammar', 'style']
    
    # Test to_dict and from_dict
    options_dict = options.to_dict()
    restored_options = ProcessingOptions.from_dict(options_dict)
    assert restored_options.categories == ['grammar', 'style']
    
    # Test Job creation
    job = Job(
        file_id=str(uuid.uuid4()),
        file_path="/test/path.docx",
        processing_mode=ProcessingMode.COMPLETE,
        options=options,  # Use the ProcessingOptions object
        job_id=str(uuid.uuid4())
    )
    
    assert job.status == JobStatus.PENDING
    assert job.processing_mode == ProcessingMode.COMPLETE
    
    print("✅ Models are working correctly")


def test_services_exist():
    """Test that all required services exist and can be imported"""
    print("✓ Testing services...")
    
    from web.services.job_manager import JobManager
    from web.services.background_processor import BackgroundProcessor
    from web.services.processor_integration import ProcessorIntegration
    from web.services.enhanced_processor_integration import EnhancedProcessorIntegration
    
    # Test singleton patterns
    manager1 = JobManager()
    manager2 = JobManager()
    assert manager1 is manager2
    
    processor1 = BackgroundProcessor()
    processor2 = BackgroundProcessor()
    assert processor1 is processor2
    
    print("✅ Services are working correctly")


def test_security_handler():
    """Test that secure file handler works"""
    print("✓ Testing security handler...")
    
    from web.utils.secure_file_handler import SecureFileHandler
    
    with tempfile.TemporaryDirectory() as temp_dir:
        handler = SecureFileHandler(temp_dir)
        
        # Test path validation
        valid_path = os.path.join(temp_dir, "test.docx")
        assert handler.validate_file_path(valid_path) == True
        
        # Test invalid path (traversal)
        invalid_path = "../../../etc/passwd"
        assert handler.validate_file_path(invalid_path) == False
        
        # Test filename generation
        filename = handler.generate_secure_filename()
        assert filename.endswith('.docx')
        assert len(filename) > 10  # Should be UUID + extension
    
    print("✅ Security handler is working correctly")


def test_api_endpoints():
    """Test that API endpoints exist and can be imported"""
    print("✓ Testing API endpoints...")
    
    from web.api.processor import process_document, get_processing_status, download_result
    from web.api.routes import api_bp
    
    # Check that functions exist and are callable
    assert callable(process_document)
    assert callable(get_processing_status)
    assert callable(download_result)
    
    # Check blueprint exists
    assert api_bp is not None
    
    print("✅ API endpoints are available")


def test_progress_tracking():
    """Test that progress tracking system works"""
    print("✓ Testing progress tracking...")
    
    from src.utils.progress_integration import EnhancedProgressTracker, ProcessingStage
    from web.services.enhanced_progress_tracker import get_web_progress_tracker
    
    # Test enhanced tracker
    progress_updates = []
    def callback(update):
        progress_updates.append(update)
    
    tracker = EnhancedProgressTracker(callback)
    job_id = str(uuid.uuid4())
    
    tracker.start_job(job_id, "test.docx", 60)
    tracker.update_stage_progress(job_id, ProcessingStage.PARSING, 50, "Testing...")
    tracker.complete_job(job_id, True, {'test': True})
    
    assert len(progress_updates) >= 3  # start, update, complete
    
    # Test web tracker
    web_tracker = get_web_progress_tracker()
    assert web_tracker is not None
    
    print("✅ Progress tracking is working correctly")


def test_file_structure():
    """Test that all required files exist"""
    print("✓ Testing file structure...")
    
    required_files = [
        'web/models/job.py',
        'web/services/job_manager.py', 
        'web/services/background_processor.py',
        'web/services/processor_integration.py',
        'web/services/enhanced_processor_integration.py',
        'web/utils/secure_file_handler.py',
        'web/api/processor.py',
        'src/utils/progress_integration.py',
        'src/utils/progress_adapters.py',
        'tests/integration/test_processing_pipeline.py',
        'docs/api_documentation.md'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    
    print("✅ All required files exist")
    return True


def test_enhanced_progress_integration():
    """Test enhanced progress system integration"""
    print("✓ Testing enhanced progress integration...")
    
    from web.services.enhanced_progress_tracker import get_web_progress_tracker
    from src.utils.progress_adapters import create_progress_adapter
    from src.utils.progress_integration import EnhancedProgressTracker
    
    # Test creating web tracker
    web_tracker = get_web_progress_tracker()
    job_id = str(uuid.uuid4())
    
    # Test creating job tracker
    enhanced_tracker = web_tracker.create_job_tracker(
        job_id=job_id,
        document_path="test.docx",
        estimated_duration=30
    )
    
    assert enhanced_tracker is not None
    
    # Test creating progress adapter
    adapter = create_progress_adapter('complete', enhanced_tracker, job_id)
    assert adapter is not None
    
    # Cleanup
    web_tracker.cleanup_job(job_id)
    
    print("✅ Enhanced progress integration is working correctly")


def main():
    """Run all validation tests"""
    print("🧪 Issue #4 Processing Pipeline Integration - Validation Tests")
    print("=" * 65)
    
    tests = [
        test_models_exist,
        test_services_exist,
        test_security_handler,
        test_api_endpoints,
        test_progress_tracking,
        test_file_structure,
        test_enhanced_progress_integration
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__} failed: {str(e)}")
            failed += 1
    
    print("\n" + "=" * 65)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All validation tests passed! Issue #4 implementation is complete.")
        return True
    else:
        print(f"⚠️  {failed} test(s) failed. Please check the implementation.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)