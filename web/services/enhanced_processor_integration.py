#!/usr/bin/env python3
"""
Enhanced Processor Integration Service
Integrates the new progress tracking system with existing processing tools
"""

import os
import sys
import logging
import uuid
from pathlib import Path
from typing import Optional, Callable, Dict, Any

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from main_complete_advanced import CompleteAdvancedKorrekturtool
from main_performance_optimized import PerformanceOptimizedKorrekturtool
from web.models.job import ProcessingMode, ProcessingResult
from web.utils.validators.secure_filename_generator import SecureFilenameGenerator
from web.services.enhanced_progress_tracker import get_web_progress_tracker
from src.utils.progress_adapters import create_progress_adapter

logger = logging.getLogger(__name__)


class EnhancedProcessorIntegration:
    """
    Enhanced processor integration with comprehensive progress tracking
    Replaces the basic ProcessorIntegration with advanced WebSocket-based progress updates
    """
    
    def __init__(self):
        self.web_progress_tracker = get_web_progress_tracker()
        self.current_job_id: Optional[str] = None
        self.current_tracker = None
    
    def process_document(
        self,
        input_file_path: str,
        processing_mode: ProcessingMode,
        categories: list,
        job_id: str,
        output_filename: Optional[str] = None
    ) -> ProcessingResult:
        """
        Process document with enhanced progress tracking
        
        Args:
            input_file_path: Path to input DOCX file
            processing_mode: Complete or Performance mode  
            categories: List of analysis categories
            job_id: Job identifier for progress tracking
            output_filename: Optional custom output filename
            
        Returns:
            ProcessingResult with processing details
        """
        try:
            self.current_job_id = job_id
            
            # Generate secure output path
            output_path = self._generate_output_path(input_file_path, output_filename)
            
            # Create enhanced progress tracker for this job
            estimated_duration = self.estimate_processing_time(processing_mode, categories)
            enhanced_tracker = self.web_progress_tracker.create_job_tracker(
                job_id=job_id,
                document_path=input_file_path,
                estimated_duration=estimated_duration
            )
            
            self.current_tracker = enhanced_tracker
            
            # Create progress adapter for the processing mode
            progress_adapter = create_progress_adapter(
                processing_mode.value,
                enhanced_tracker,
                job_id
            )
            
            # Process document based on mode
            if processing_mode == ProcessingMode.COMPLETE:
                result = self._process_with_complete_advanced(
                    input_file_path, output_path, categories, progress_adapter
                )
            else:
                result = self._process_with_performance_optimized(
                    input_file_path, output_path, categories, progress_adapter  
                )
            
            # Complete job tracking
            result_data = {
                'suggestions_found': result.total_suggestions,
                'comments_integrated': result.successful_integrations,
                'processing_time': result.processing_time_seconds,
                'output_file_id': result.output_file_id,
                'download_url': f"/api/v1/download/{result.output_file_id}"
            }
            
            self.web_progress_tracker.complete_job(job_id, True, result_data)
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing document {job_id}: {str(e)}")
            
            # Complete job with error
            if self.web_progress_tracker:
                self.web_progress_tracker.complete_job(
                    job_id, False, None, f"Processing failed: {str(e)}"
                )
            
            raise
    
    def _process_with_complete_advanced(
        self,
        input_path: str,
        output_path: str,
        categories: list,
        progress_adapter
    ) -> ProcessingResult:
        """Process document using CompleteAdvancedKorrekturtool with enhanced progress"""
        try:
            # Create original processor
            processor = CompleteAdvancedKorrekturtool()
            
            # Process with progress tracking
            success = progress_adapter.process_document_with_progress(
                input_path, output_path, processor
            )
            
            if not success:
                raise Exception("Complete advanced processing failed - check logs for details")
            
            # Extract results from processor
            stats = processor.performance_stats
            
            result = ProcessingResult(
                output_file_path=output_path,
                output_file_id=self._generate_file_id_from_path(output_path),
                total_suggestions=stats.get('total_suggestions', 0),
                successful_integrations=stats.get('successful_integrations', 0),
                processing_time_seconds=stats.get('end_time', 0) - stats.get('start_time', 0),
                cost_estimate=self._estimate_cost(stats.get('api_calls_made', 0)),
                performance_stats=stats
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error in complete advanced processing: {str(e)}")
            raise
    
    def _process_with_performance_optimized(
        self,
        input_path: str,
        output_path: str,
        categories: list,
        progress_adapter
    ) -> ProcessingResult:
        """Process document using PerformanceOptimizedKorrekturtool with enhanced progress"""
        try:
            # Create original processor
            processor = PerformanceOptimizedKorrekturtool()
            
            # Process with progress tracking
            success = progress_adapter.process_document_with_progress(
                input_path, output_path, processor
            )
            
            if not success:
                raise Exception("Performance optimized processing failed - check logs for details")
            
            # Extract results from performance dashboard
            dashboard = processor.performance_dashboard
            final_metrics = dashboard.get('final_metrics', {})
            optimization_stats = dashboard.get('optimization_stats', {})
            
            result = ProcessingResult(
                output_file_path=output_path,
                output_file_id=self._generate_file_id_from_path(output_path),
                total_suggestions=optimization_stats.get('batch', {}).get('total_suggestions', 0),
                successful_integrations=optimization_stats.get('integration', {}).get('comments_integrated', 0),
                processing_time_seconds=final_metrics.get('total_processing_time', 0),
                cost_estimate=self._estimate_cost_from_suggestions(
                    optimization_stats.get('batch', {}).get('total_suggestions', 0)
                ),
                performance_stats=dashboard
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error in performance optimized processing: {str(e)}")
            raise
    
    def _generate_output_path(self, input_path: str, custom_filename: Optional[str] = None) -> str:
        """Generate secure output file path"""
        from flask import current_app
        
        output_dir = Path(current_app.config.get('OUTPUT_FOLDER', 'outputs'))
        output_dir.mkdir(exist_ok=True)
        
        if custom_filename:
            # Sanitize custom filename
            generator = SecureFilenameGenerator()
            safe_filename = generator.sanitize_display_name(custom_filename)
            if not safe_filename.endswith('.docx'):
                safe_filename += '.docx'
            output_path = output_dir / safe_filename
        else:
            # Generate secure filename
            secure_name = SecureFilenameGenerator.generate()
            output_path = output_dir / secure_name
        
        return str(output_path)
    
    def _generate_file_id_from_path(self, file_path: str) -> str:
        """Generate file ID from output path"""
        filename = Path(file_path).stem  # Remove .docx extension
        return filename
    
    def _estimate_cost(self, api_calls: int) -> float:
        """Estimate processing cost based on API calls"""
        # Rough estimate: $0.0002 per API call for Gemini
        return api_calls * 0.0002
    
    def _estimate_cost_from_suggestions(self, suggestions: int) -> float:
        """Estimate cost from number of suggestions"""
        # Rough estimate: each suggestion represents ~1-2 API calls
        estimated_calls = suggestions * 1.5
        return estimated_calls * 0.0002
    
    def estimate_processing_time(self, processing_mode: ProcessingMode, categories: list) -> int:
        """Estimate processing time in seconds"""
        base_time = 60  # 1 minute base
        
        if processing_mode == ProcessingMode.COMPLETE:
            base_time = 90  # Complete mode is slower
        else:
            base_time = 45  # Performance mode is optimized
        
        # Add time per category
        category_time = len(categories) * 15
        
        return base_time + category_time
    
    def get_current_job_status(self) -> Optional[Dict[str, Any]]:
        """Get current job status from tracker"""
        if not self.current_tracker or not self.current_job_id:
            return None
        
        return self.current_tracker.get_job_info(self.current_job_id)
    
    def cleanup_job(self, job_id: str) -> None:
        """Clean up job resources"""
        try:
            self.web_progress_tracker.cleanup_job(job_id)
            
            if job_id == self.current_job_id:
                self.current_job_id = None
                self.current_tracker = None
                
            logger.info(f"Cleaned up job resources for {job_id}")
            
        except Exception as e:
            logger.error(f"Error cleaning up job {job_id}: {str(e)}")


# Compatibility class for existing code
class ProcessorIntegration(EnhancedProcessorIntegration):
    """
    Backward compatibility wrapper for existing ProcessorIntegration
    Delegates to EnhancedProcessorIntegration while maintaining the old interface
    """
    
    def __init__(self):
        super().__init__()
        self.progress_callback: Optional[Callable] = None
        self._legacy_job_id: Optional[str] = None
    
    def set_progress_callback(self, callback: Callable, job_id: str):
        """Set progress callback for job updates (legacy interface)"""
        self.progress_callback = callback
        self._legacy_job_id = job_id
    
    def process_document(
        self,
        input_file_path: str,
        processing_mode: ProcessingMode,
        categories: list,
        output_filename: Optional[str] = None
    ) -> ProcessingResult:
        """
        Legacy interface for processing documents
        Automatically generates job ID and uses enhanced tracking
        """
        # Generate job ID if not set by legacy callback
        job_id = self._legacy_job_id or str(uuid.uuid4())
        
        # Use enhanced processing
        return super().process_document(
            input_file_path=input_file_path,
            processing_mode=processing_mode,
            categories=categories,
            job_id=job_id,
            output_filename=output_filename
        )