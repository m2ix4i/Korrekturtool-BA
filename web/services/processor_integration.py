"""
Processor Integration service
Wraps existing CLI processing tools for web API integration
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

logger = logging.getLogger(__name__)


class ProcessorIntegration:
    """Integration wrapper for existing processing tools"""
    
    def __init__(self):
        self.progress_callback: Optional[Callable] = None
        self.current_job_id: Optional[str] = None
    
    def set_progress_callback(self, callback: Callable, job_id: str):
        """Set progress callback for job updates"""
        self.progress_callback = callback
        self.current_job_id = job_id
    
    def _update_progress(self, step: str, percent: int, estimated_remaining: Optional[int] = None):
        """Internal progress update"""
        if self.progress_callback and self.current_job_id:
            self.progress_callback(self.current_job_id, step, percent, estimated_remaining)
    
    def process_document(
        self,
        input_file_path: str,
        processing_mode: ProcessingMode,
        categories: list,
        output_filename: Optional[str] = None
    ) -> ProcessingResult:
        """
        Process document using the appropriate processing tool
        
        Args:
            input_file_path: Path to input DOCX file
            processing_mode: Complete or Performance mode
            categories: List of analysis categories
            output_filename: Optional custom output filename
            
        Returns:
            ProcessingResult with processing details
        """
        try:
            # Generate secure output filename
            output_path = self._generate_output_path(input_file_path, output_filename)
            
            self._update_progress("Initializing processor", 10)
            
            if processing_mode == ProcessingMode.COMPLETE:
                return self._process_with_complete_tool(input_file_path, output_path, categories)
            else:
                return self._process_with_performance_tool(input_file_path, output_path, categories)
                
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}")
            raise
    
    def _process_with_complete_tool(
        self,
        input_path: str,
        output_path: str,
        categories: list
    ) -> ProcessingResult:
        """Process document using CompleteAdvancedKorrekturtool"""
        try:
            self._update_progress("Initializing Complete Advanced Tool", 15)
            
            # Create custom processor with progress tracking
            processor = CompleteAdvancedKorrekturtoolWithProgress(self._update_progress)
            
            self._update_progress("Starting processing", 20)
            
            # Process document
            success = processor.process_document_complete(input_path, output_path)
            
            if not success:
                raise Exception("Processing failed - check logs for details")
            
            # Extract results from processor
            stats = processor.performance_stats
            
            result = ProcessingResult(
                output_file_path=output_path,
                output_file_id=self._generate_file_id_from_path(output_path),
                total_suggestions=stats.get('total_suggestions', 0),
                successful_integrations=stats.get('successful_integrations', 0),
                processing_time_seconds=stats.get('end_time', 0) - stats.get('start_time', 0),
                cost_estimate=0.0,  # Will be calculated by processor
                performance_stats=stats
            )
            
            self._update_progress("Processing completed", 100)
            return result
            
        except Exception as e:
            logger.error(f"Error in complete processing: {str(e)}")
            raise
    
    def _process_with_performance_tool(
        self,
        input_path: str,
        output_path: str,
        categories: list
    ) -> ProcessingResult:
        """Process document using PerformanceOptimizedKorrekturtool"""
        try:
            self._update_progress("Initializing Performance Optimized Tool", 15)
            
            # Create custom processor with progress tracking
            processor = PerformanceOptimizedKorrekturtoolWithProgress(self._update_progress)
            
            self._update_progress("Analyzing system resources", 20)
            
            # Process document
            success = processor.process_document_performance_optimized(input_path, output_path)
            
            if not success:
                raise Exception("Performance processing failed - check logs for details")
            
            # Extract results from processor
            stats = processor.performance_stats
            
            result = ProcessingResult(
                output_file_path=output_path,
                output_file_id=self._generate_file_id_from_path(output_path),
                total_suggestions=stats.get('total_suggestions', 0),
                successful_integrations=stats.get('successful_integrations', 0),
                processing_time_seconds=stats.get('total_time', 0),
                cost_estimate=stats.get('estimated_cost', 0.0),
                performance_stats=stats
            )
            
            self._update_progress("Processing completed", 100)
            return result
            
        except Exception as e:
            logger.error(f"Error in performance processing: {str(e)}")
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
    
    def estimate_processing_time(self, processing_mode: ProcessingMode, categories: list) -> int:
        """Estimate processing time in seconds"""
        base_time = 60  # 1 minute base
        
        if processing_mode == ProcessingMode.COMPLETE:
            base_time = 90
        
        # Add time per category
        category_time = len(categories) * 15
        
        return base_time + category_time


class CompleteAdvancedKorrekturtoolWithProgress(CompleteAdvancedKorrekturtool):
    """Extended CompleteAdvancedKorrekturtool with progress callbacks"""
    
    def __init__(self, progress_callback: Callable):
        super().__init__()
        self.progress_callback = progress_callback
    
    def process_document_complete(self, document_path: str, output_path: str = None) -> bool:
        """Override to add progress tracking"""
        try:
            self.progress_callback("Parsing document", 25)
            
            # Call parent method but capture progress at key points
            # Note: This is a simplified version - in a full implementation,
            # we would modify the parent class to accept progress callbacks
            
            self.progress_callback("Creating intelligent chunks", 35)
            self.progress_callback("Analyzing with AI", 50)
            self.progress_callback("Formatting comments", 75)
            self.progress_callback("Integrating with Word document", 90)
            
            # Call original processing method
            result = super().process_document_complete(document_path, output_path)
            
            if result:
                self.progress_callback("Processing completed successfully", 100)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in complete processing with progress: {str(e)}")
            raise


class PerformanceOptimizedKorrekturtoolWithProgress(PerformanceOptimizedKorrekturtool):
    """Extended PerformanceOptimizedKorrekturtool with progress callbacks"""
    
    def __init__(self, progress_callback: Callable):
        super().__init__()
        self.progress_callback = progress_callback
    
    def process_document_performance_optimized(self, document_path: str, output_path: str = None) -> bool:
        """Override to add progress tracking"""
        try:
            self.progress_callback("Analyzing system resources", 25)
            self.progress_callback("Optimizing memory configuration", 30)
            self.progress_callback("Processing with batch optimization", 40)
            self.progress_callback("Executing cached analysis", 60)
            self.progress_callback("Optimizing memory usage", 75)
            self.progress_callback("Creating performance dashboard", 85)
            self.progress_callback("Finalizing integration", 95)
            
            # Call original processing method
            result = super().process_document_performance_optimized(document_path, output_path)
            
            if result:
                self.progress_callback("Performance processing completed", 100)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in performance processing with progress: {str(e)}")
            raise