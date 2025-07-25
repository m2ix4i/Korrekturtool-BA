"""
Progress emitter usage examples

This module contains examples demonstrating how to integrate ProgressEmitter
with existing processors. These examples are for documentation and testing purposes.
"""

import logging
from typing import Dict, Any
from src.utils.progress_emitter_refactored import ProgressEmitterFactory
from src.utils.processor_config_registry import ProcessorConfigRegistry

logger = logging.getLogger(__name__)


def complete_advanced_example():
    """
    Example showing how to integrate ProgressEmitter with CompleteAdvancedKorrekturtool
    """
    job_id = "example_complete_advanced_123"
    
    # Create progress emitter using factory
    emitter = ProgressEmitterFactory.create(job_id, "complete_advanced")
    
    try:
        # Parsing stage
        emitter.start_stage("parsing", "Loading and parsing document")
        # Simulate parsing work
        emitter.update_stage_progress(30, "Extracting document structure")
        emitter.update_stage_progress(60, "Processing text content")
        emitter.update_stage_progress(100, "Document structure analyzed")
        emitter.complete_stage("Document parsing completed")
        
        # Chunking stage  
        emitter.start_stage("chunking", "Creating intelligent text chunks")
        emitter.update_stage_progress(50, "Analyzing text boundaries")
        emitter.update_stage_progress(100, "Chunks created successfully")
        emitter.complete_stage("Text chunking completed")
        
        # Analyzing stage (most important stage)
        emitter.start_stage("analyzing", "Starting AI analysis")
        emitter.update_stage_progress(15, "Processing grammar analysis")
        emitter.update_stage_progress(35, "Processing style analysis")
        emitter.update_stage_progress(55, "Processing clarity analysis") 
        emitter.update_stage_progress(75, "Processing academic analysis")
        emitter.update_stage_progress(90, "Consolidating AI feedback")
        emitter.update_stage_progress(100, "AI analysis complete")
        emitter.complete_stage("AI analysis completed")
        
        # Formatting stage
        emitter.start_stage("formatting", "Formatting AI suggestions")
        emitter.update_stage_progress(50, "Applying comment templates")
        emitter.update_stage_progress(100, "Comments formatted")
        emitter.complete_stage("Comment formatting completed")
        
        # Integrating stage
        emitter.start_stage("integrating", "Integrating with Word document")
        emitter.update_stage_progress(25, "Creating Word XML structure")
        emitter.update_stage_progress(50, "Inserting comments into document")
        emitter.update_stage_progress(75, "Validating document integrity")
        emitter.update_stage_progress(100, "Integration complete")
        emitter.complete_stage("Word integration completed")
        
        # Job completion
        emitter.complete_job(True, {
            "download_url": f"/api/v1/download/{job_id}",
            "processing_time": "125 seconds",
            "comments_added": 67,
            "categories": ["grammar", "style", "clarity", "academic"]
        })
        
        logger.info(f"Complete advanced example finished for job {job_id}")
        
    except Exception as e:
        emitter.fail_job(str(e))
        logger.error(f"Complete advanced example failed: {e}")
        raise


def performance_optimized_example():
    """
    Example showing how to integrate ProgressEmitter with PerformanceOptimizedKorrekturtool
    """
    job_id = "example_performance_optimized_456"
    
    # Create progress emitter using factory
    emitter = ProgressEmitterFactory.create(job_id, "performance_optimized")
    
    try:
        # System analysis stage
        emitter.start_stage("system_analysis", "Analyzing system resources")
        emitter.update_stage_progress(50, "Checking available memory")
        emitter.update_stage_progress(100, "System configuration optimized")
        emitter.complete_stage("System analysis completed")
        
        # Parsing stage
        emitter.start_stage("parsing", "High-performance document parsing")
        emitter.update_stage_progress(40, "Loading document with memory optimization")
        emitter.update_stage_progress(80, "Extracting text with parallel processing")
        emitter.update_stage_progress(100, "Document parsed efficiently")
        emitter.complete_stage("Optimized parsing completed")
        
        # Batch processing stage (main processing work)
        emitter.start_stage("batch_processing", "Processing with batch optimization")
        emitter.update_stage_progress(10, "Initializing batch queues")
        emitter.update_stage_progress(25, "Processing batch 1/4")
        emitter.update_stage_progress(45, "Processing batch 2/4")
        emitter.update_stage_progress(65, "Processing batch 3/4")
        emitter.update_stage_progress(85, "Processing batch 4/4")
        emitter.update_stage_progress(95, "Consolidating batch results")
        emitter.update_stage_progress(100, "Batch processing complete")
        emitter.complete_stage("Batch processing completed")
        
        # Integrating stage
        emitter.start_stage("integrating", "Efficient Word integration")
        emitter.update_stage_progress(30, "Optimizing XML generation")
        emitter.update_stage_progress(70, "Streaming comments to document")
        emitter.update_stage_progress(100, "Integration optimized")
        emitter.complete_stage("Optimized integration completed")
        
        # Dashboard stage
        emitter.start_stage("dashboard", "Generating performance dashboard")
        emitter.update_stage_progress(50, "Collecting performance metrics")
        emitter.update_stage_progress(100, "Dashboard generated")
        emitter.complete_stage("Performance dashboard completed")
        
        # Job completion with performance metrics
        emitter.complete_job(True, {
            "download_url": f"/api/v1/download/{job_id}",
            "processing_time": "78 seconds",
            "comments_added": 52,
            "memory_usage": "450MB peak",
            "cache_hit_rate": 0.73,
            "performance_gain": "35% faster than standard processing"
        })
        
        logger.info(f"Performance optimized example finished for job {job_id}")
        
    except Exception as e:
        emitter.fail_job(str(e))
        logger.error(f"Performance optimized example failed: {e}")
        raise


def custom_processor_example():
    """
    Example showing how to create a custom processor configuration
    """
    job_id = "example_custom_789"
    
    # Register custom processor configuration
    ProcessorConfigRegistry.register(
        'custom_academic',
        stages=['preparation', 'academic_analysis', 'citation_check', 'finalization'],
        weights={
            'preparation': 0.15,
            'academic_analysis': 0.55,
            'citation_check': 0.20,
            'finalization': 0.10
        },
        estimated_duration_per_stage=45
    )
    
    # Create progress emitter with custom configuration
    emitter = ProgressEmitterFactory.create(job_id, "custom_academic")
    
    try:
        # Custom processing stages
        emitter.start_stage("preparation", "Preparing academic document analysis")
        emitter.update_stage_progress(100, "Academic preparation complete")
        emitter.complete_stage()
        
        emitter.start_stage("academic_analysis", "Deep academic analysis")
        emitter.update_stage_progress(25, "Analyzing argument structure")
        emitter.update_stage_progress(50, "Checking academic terminology")
        emitter.update_stage_progress(75, "Evaluating evidence quality")
        emitter.update_stage_progress(100, "Academic analysis complete")
        emitter.complete_stage()
        
        emitter.start_stage("citation_check", "Validating citations and references")
        emitter.update_stage_progress(50, "Checking citation format")
        emitter.update_stage_progress(100, "Citations validated")
        emitter.complete_stage()
        
        emitter.start_stage("finalization", "Finalizing academic review")
        emitter.update_stage_progress(100, "Academic review finalized")
        emitter.complete_stage()
        
        emitter.complete_job(True, {
            "download_url": f"/api/v1/download/{job_id}",
            "processing_time": "165 seconds",
            "academic_suggestions": 23,
            "citation_issues": 5
        })
        
        logger.info(f"Custom processor example finished for job {job_id}")
        
    except Exception as e:
        emitter.fail_job(str(e))
        logger.error(f"Custom processor example failed: {e}")
        raise


def error_handling_example():
    """
    Example showing proper error handling with ProgressEmitter
    """
    job_id = "example_error_handling_000"
    
    emitter = ProgressEmitterFactory.create(job_id, "basic")
    
    try:
        # Start processing
        emitter.start_stage("parsing", "Starting document parsing")
        emitter.update_stage_progress(30, "Parsing document structure")
        
        # Simulate an error during processing
        raise Exception("Simulated processing error for demonstration")
        
    except Exception as e:
        # Proper error handling
        emitter.fail_job(f"Processing failed: {str(e)}", "parsing")
        logger.error(f"Error handling example failed as expected: {e}")


if __name__ == "__main__":
    # Configure logging for examples
    logging.basicConfig(level=logging.INFO)
    
    print("Running ProgressEmitter examples...")
    
    try:
        print("1. Complete Advanced Example")
        complete_advanced_example()
        print("✓ Complete Advanced Example finished\n")
        
        print("2. Performance Optimized Example")  
        performance_optimized_example()
        print("✓ Performance Optimized Example finished\n")
        
        print("3. Custom Processor Example")
        custom_processor_example()
        print("✓ Custom Processor Example finished\n")
        
        print("4. Error Handling Example")
        error_handling_example()
        print("✓ Error Handling Example finished\n")
        
        print("All examples completed successfully!")
        
    except Exception as e:
        print(f"Example failed: {e}")
        raise