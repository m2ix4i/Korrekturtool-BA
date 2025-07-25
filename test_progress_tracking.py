#!/usr/bin/env python3
"""
Test script for enhanced progress tracking system
Tests the integration between WebSocket progress tracking and processing pipeline
"""

import os
import sys
import uuid
import time
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from web.services.enhanced_progress_tracker import get_web_progress_tracker
from src.utils.progress_integration import EnhancedProgressTracker, ProcessingStage
from src.utils.progress_adapters import create_progress_adapter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_enhanced_progress_tracker():
    """Test the EnhancedProgressTracker standalone"""
    print("\n=== Testing EnhancedProgressTracker ===")
    
    progress_updates = []
    
    def progress_callback(update):
        progress_updates.append(update)
        print(f"Progress: {update.stage.value} {update.progress_percent}% - {update.message}")
    
    # Create tracker
    tracker = EnhancedProgressTracker(progress_callback)
    
    # Test job lifecycle
    job_id = str(uuid.uuid4())
    document_path = "test_document.docx"
    
    # Start job
    tracker.start_job(job_id, document_path, estimated_duration=60)
    
    # Simulate processing stages
    stages = [
        (ProcessingStage.PARSING, "Parsing document..."),
        (ProcessingStage.CHUNKING, "Creating chunks..."),
        (ProcessingStage.ANALYZING, "Analyzing with AI..."),
        (ProcessingStage.FORMATTING, "Formatting comments..."),
        (ProcessingStage.INTEGRATING, "Integrating with Word..."),
        (ProcessingStage.FINALIZING, "Finalizing document...")
    ]
    
    for i, (stage, message) in enumerate(stages):
        tracker.advance_stage(job_id, stage, message)
        
        # Simulate progress within stage
        for progress in [25, 50, 75, 100]:
            tracker.update_stage_progress(
                job_id, stage, progress, f"{message} {progress}%",
                current_item=f"item {progress//25}/4",
                total_items=4
            )
            time.sleep(0.1)  # Brief pause
    
    # Complete job
    result_data = {'suggestions_found': 42, 'comments_integrated': 38}
    tracker.complete_job(job_id, True, result_data)
    
    print(f"✅ Test completed with {len(progress_updates)} progress updates")
    return len(progress_updates) > 0


def test_web_progress_tracker():
    """Test the WebProgressTracker integration"""
    print("\n=== Testing WebProgressTracker ===")
    
    web_tracker = get_web_progress_tracker()
    
    job_id = str(uuid.uuid4())
    document_path = "test_document.docx"
    
    try:
        # Create job tracker (this would normally integrate with WebSocket)
        enhanced_tracker = web_tracker.create_job_tracker(
            job_id=job_id,
            document_path=document_path,
            estimated_duration=30
        )
        
        # Simulate some processing
        enhanced_tracker.advance_stage(
            job_id, ProcessingStage.PARSING, "Starting document parsing..."
        )
        
        enhanced_tracker.update_stage_progress(
            job_id, ProcessingStage.PARSING, 50, "Parsing in progress...",
            current_item="page 5/10", total_items=10
        )
        
        enhanced_tracker.advance_stage(
            job_id, ProcessingStage.ANALYZING, "Starting AI analysis..."
        )
        
        enhanced_tracker.update_stage_progress(
            job_id, ProcessingStage.ANALYZING, 75, "Analyzing chunks...",
            current_item="chunk 15/20", total_items=20
        )
        
        # Complete job
        result_data = {'suggestions_found': 25, 'comments_integrated': 22}
        web_tracker.complete_job(job_id, True, result_data)
        
        print("✅ WebProgressTracker test completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ WebProgressTracker test failed: {str(e)}")
        return False
    finally:
        # Cleanup
        web_tracker.cleanup_job(job_id)


def test_mock_processing_with_adapter():
    """Test progress adapter with mock processing"""
    print("\n=== Testing Progress Adapter ===")
    
    web_tracker = get_web_progress_tracker()
    job_id = str(uuid.uuid4())
    document_path = "test_document.docx"
    
    try:
        # Create enhanced tracker
        enhanced_tracker = web_tracker.create_job_tracker(
            job_id=job_id,
            document_path=document_path,
            estimated_duration=45
        )
        
        # Create progress adapter
        adapter = create_progress_adapter('complete', enhanced_tracker, job_id)
        
        print("✅ Progress adapter created successfully")
        
        # Note: We can't easily test the full adapter without the actual processors
        # since they have complex dependencies. This tests the adapter creation.
        
        # Complete the job
        web_tracker.complete_job(job_id, True, {'test': True})
        
        return True
        
    except Exception as e:
        print(f"❌ Progress adapter test failed: {str(e)}")
        return False
    finally:
        # Cleanup
        web_tracker.cleanup_job(job_id)


def test_progress_context():
    """Test the ProgressContext context manager"""
    print("\n=== Testing ProgressContext ===")
    
    progress_updates = []
    
    def progress_callback(update):
        progress_updates.append(update)
        print(f"Context Progress: {update.stage.value} {update.progress_percent}% - {update.message}")
    
    tracker = EnhancedProgressTracker(progress_callback)
    job_id = str(uuid.uuid4())
    
    # Start job
    tracker.start_job(job_id, "test.docx", 30)
    
    try:
        # Test context manager
        from src.utils.progress_integration import ProgressContext
        
        with ProgressContext(tracker, job_id, ProcessingStage.ANALYZING, 10) as ctx:
            ctx.update(20, "Processing item 2...")
            time.sleep(0.1)
            ctx.update(50, "Processing item 5...")
            time.sleep(0.1)
            ctx.update(80, "Processing item 8...")
            time.sleep(0.1)
        
        # Complete job
        tracker.complete_job(job_id, True, {'test_context': True})
        
        print("✅ ProgressContext test completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ ProgressContext test failed: {str(e)}")
        return False


def main():
    """Run all progress tracking tests"""
    print("🧪 Testing Enhanced Progress Tracking System")
    print("=============================================")
    
    test_results = []
    
    # Run tests
    test_results.append(("EnhancedProgressTracker", test_enhanced_progress_tracker()))
    test_results.append(("WebProgressTracker", test_web_progress_tracker()))
    test_results.append(("ProgressAdapter", test_mock_processing_with_adapter()))
    test_results.append(("ProgressContext", test_progress_context()))
    
    # Show results
    print("\n📊 Test Results Summary")
    print("========================")
    
    passed = 0
    failed = 0
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:20} {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("\n🎉 All tests passed! Progress tracking system is working correctly.")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please check the implementation.")
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)