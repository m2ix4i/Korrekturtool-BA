"""
Progress emitter utility for processing pipeline integration

Provides a generic interface for emitting progress updates during document processing
that can be used by any processor (CompleteAdvanced, PerformanceOptimized, etc.)
"""

import logging
from typing import List, Optional, Dict, Any, Callable
from datetime import datetime

logger = logging.getLogger(__name__)

class ProgressEmitter:
    """
    Generic progress emitter for processing pipeline integration
    
    Provides a clean interface for processors to emit progress updates
    without needing to know about WebSocket or progress tracking implementation details.
    """
    
    def __init__(self, job_id: str, progress_tracker=None):
        """
        Initialize progress emitter
        
        Args:
            job_id: Unique job identifier
            progress_tracker: Progress tracker instance (will be imported if None)
        """
        self.job_id = job_id
        self.stages: List[str] = []
        self.current_stage_index = 0
        self.current_stage = None
        self.stage_weights: Dict[str, float] = {}
        self.overall_progress = 0
        self.stage_progress = 0
        
        # Import progress tracker if not provided
        if progress_tracker is None:
            try:
                from web.services.progress_tracker import get_progress_tracker
                self.progress_tracker = get_progress_tracker()
            except ImportError:
                logger.warning("Progress tracker not available - progress updates will be logged only")
                self.progress_tracker = None
        else:
            self.progress_tracker = progress_tracker
        
        logger.info(f"ProgressEmitter initialized for job {job_id}")
    
    def set_stages(self, stages: List[str], weights: Optional[Dict[str, float]] = None) -> None:
        """
        Define processing stages with optional weights
        
        Args:
            stages: List of stage names (e.g., ["parsing", "analyzing", "integrating", "formatting"])
            weights: Optional dictionary of stage weights (defaults to equal weights)
        """
        self.stages = stages
        self.current_stage_index = 0
        self.current_stage = stages[0] if stages else None
        
        # Set stage weights (default to equal weights)
        if weights:
            self.stage_weights = weights
        else:
            weight_per_stage = 1.0 / len(stages) if stages else 1.0
            self.stage_weights = {stage: weight_per_stage for stage in stages}
        
        logger.info(f"Job {self.job_id} stages set: {stages}")
        
        # Initialize job in progress tracker
        if self.progress_tracker:
            # Calculate estimated duration based on typical processing times
            estimated_duration = len(stages) * 30  # 30 seconds per stage average
            self.progress_tracker.start_job(self.job_id, stages, estimated_duration)
    
    def start_stage(self, stage: str, message: Optional[str] = None) -> None:
        """
        Start new processing stage
        
        Args:
            stage: Stage name
            message: Optional message describing stage start
        """
        if stage not in self.stages:
            logger.warning(f"Starting unknown stage '{stage}' for job {self.job_id}")
            return
        
        self.current_stage = stage
        self.current_stage_index = self.stages.index(stage)
        self.stage_progress = 0
        
        # Calculate overall progress based on completed stages
        completed_weight = sum(
            self.stage_weights.get(self.stages[i], 0) 
            for i in range(self.current_stage_index)
        )
        self.overall_progress = int(completed_weight * 100)
        
        start_message = message or f"Starting {stage} stage"
        
        logger.info(f"Job {self.job_id} starting stage: {stage}")
        
        # Update progress tracker
        if self.progress_tracker:
            self.progress_tracker.update_progress(
                self.job_id, stage, self.overall_progress, start_message, 0
            )
    
    def update_stage_progress(self, progress: int, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """
        Update current stage progress
        
        Args:
            progress: Stage progress (0-100)
            message: Progress message for user display
            details: Optional additional details for logging
        """
        if not self.current_stage:
            logger.warning(f"Progress update without active stage for job {self.job_id}")
            return
        
        self.stage_progress = max(0, min(100, progress))
        
        # Calculate overall progress including current stage progress
        completed_weight = sum(
            self.stage_weights.get(self.stages[i], 0) 
            for i in range(self.current_stage_index)
        )
        current_stage_weight = self.stage_weights.get(self.current_stage, 0)
        current_stage_contribution = current_stage_weight * (self.stage_progress / 100)
        
        self.overall_progress = int((completed_weight + current_stage_contribution) * 100)
        
        logger.debug(f"Job {self.job_id} stage '{self.current_stage}' progress: {progress}% (overall: {self.overall_progress}%)")
        
        # Update progress tracker
        if self.progress_tracker:
            self.progress_tracker.update_progress(
                self.job_id, self.current_stage, self.overall_progress, message, self.stage_progress
            )
        
        # Log additional details if provided
        if details:
            logger.debug(f"Job {self.job_id} progress details: {details}")
    
    def complete_stage(self, message: Optional[str] = None) -> None:
        """
        Mark current stage complete and advance to next stage
        
        Args:
            message: Optional completion message
        """
        if not self.current_stage:
            logger.warning(f"Stage completion without active stage for job {self.job_id}")
            return
        
        completed_stage = self.current_stage
        completion_message = message or f"Completed {completed_stage} stage"
        
        # Mark stage progress as 100%
        self.stage_progress = 100
        
        # Update overall progress
        completed_weight = sum(
            self.stage_weights.get(self.stages[i], 0) 
            for i in range(self.current_stage_index + 1)
        )
        self.overall_progress = int(completed_weight * 100)
        
        logger.info(f"Job {self.job_id} completed stage: {completed_stage}")
        
        # Update progress tracker
        if self.progress_tracker:
            self.progress_tracker.update_progress(
                self.job_id, completed_stage, self.overall_progress, completion_message, 100
            )
            self.progress_tracker.complete_stage(self.job_id, completed_stage)
        
        # Advance to next stage if available
        if self.current_stage_index + 1 < len(self.stages):
            self.current_stage_index += 1
            self.current_stage = self.stages[self.current_stage_index]
            self.stage_progress = 0
        else:
            self.current_stage = None
    
    def complete_job(self, success: bool = True, result_data: Optional[Dict[str, Any]] = None,
                     message: Optional[str] = None) -> None:
        """
        Mark entire job complete
        
        Args:
            success: Whether job completed successfully
            result_data: Additional result data (download URL, metrics, etc.)
            message: Optional completion message
        """
        self.overall_progress = 100 if success else self.overall_progress
        completion_message = message or f"Job {'completed successfully' if success else 'completed with errors'}"
        
        logger.info(f"Job {self.job_id} {'completed successfully' if success else 'failed'}")
        
        # Update progress tracker
        if self.progress_tracker:
            self.progress_tracker.complete_job(self.job_id, success, result_data)
    
    def fail_job(self, error: str, stage: Optional[str] = None) -> None:
        """
        Mark job as failed
        
        Args:
            error: Error message
            stage: Stage where error occurred (defaults to current stage)
        """
        error_stage = stage or self.current_stage or 'unknown'
        
        logger.error(f"Job {self.job_id} failed in stage '{error_stage}': {error}")
        
        # Update progress tracker
        if self.progress_tracker:
            self.progress_tracker.fail_job(self.job_id, error, error_stage)
    
    def get_current_status(self) -> Dict[str, Any]:
        """
        Get current progress status
        
        Returns:
            Dictionary with current progress information
        """
        return {
            'job_id': self.job_id,
            'stages': self.stages,
            'current_stage': self.current_stage,
            'current_stage_index': self.current_stage_index,
            'overall_progress': self.overall_progress,
            'stage_progress': self.stage_progress,
            'stage_weights': self.stage_weights
        }


class ProcessorProgressAdapter:
    """
    Adapter class to easily integrate ProgressEmitter with existing processors
    
    Provides convenience methods and common processing stage patterns.
    """
    
    # Common stage definitions for different processor types
    COMPLETE_ADVANCED_STAGES = ["parsing", "chunking", "analyzing", "formatting", "integrating"]
    PERFORMANCE_OPTIMIZED_STAGES = ["system_analysis", "parsing", "batch_processing", "integrating", "dashboard"]
    BASIC_STAGES = ["parsing", "analyzing", "integrating"]
    
    # Default stage weights for different processing types
    STAGE_WEIGHTS = {
        "complete_advanced": {
            "parsing": 0.10,
            "chunking": 0.05, 
            "analyzing": 0.60,
            "formatting": 0.05,
            "integrating": 0.20
        },
        "performance_optimized": {
            "system_analysis": 0.05,
            "parsing": 0.10,
            "batch_processing": 0.65,
            "integrating": 0.15,
            "dashboard": 0.05
        },
        "basic": {
            "parsing": 0.15,
            "analyzing": 0.65,
            "integrating": 0.20
        }
    }
    
    @classmethod
    def create_for_complete_advanced(cls, job_id: str) -> ProgressEmitter:
        """Create progress emitter configured for CompleteAdvancedKorrekturtool"""
        emitter = ProgressEmitter(job_id)
        emitter.set_stages(cls.COMPLETE_ADVANCED_STAGES, cls.STAGE_WEIGHTS["complete_advanced"])
        return emitter
    
    @classmethod
    def create_for_performance_optimized(cls, job_id: str) -> ProgressEmitter:
        """Create progress emitter configured for PerformanceOptimizedKorrekturtool"""
        emitter = ProgressEmitter(job_id)
        emitter.set_stages(cls.PERFORMANCE_OPTIMIZED_STAGES, cls.STAGE_WEIGHTS["performance_optimized"])
        return emitter
    
    @classmethod
    def create_for_basic(cls, job_id: str) -> ProgressEmitter:
        """Create progress emitter configured for basic processing"""
        emitter = ProgressEmitter(job_id)
        emitter.set_stages(cls.BASIC_STAGES, cls.STAGE_WEIGHTS["basic"])
        return emitter
    
    @classmethod
    def create_custom(cls, job_id: str, stages: List[str], weights: Optional[Dict[str, float]] = None) -> ProgressEmitter:
        """Create progress emitter with custom stages and weights"""
        emitter = ProgressEmitter(job_id)
        emitter.set_stages(stages, weights)
        return emitter


# Convenience functions for easy integration
def create_progress_emitter(job_id: str, processor_type: str = "basic") -> ProgressEmitter:
    """
    Create progress emitter for specific processor type
    
    Args:
        job_id: Job identifier
        processor_type: Type of processor ("complete_advanced", "performance_optimized", "basic")
        
    Returns:
        Configured ProgressEmitter instance
    """
    if processor_type == "complete_advanced":
        return ProcessorProgressAdapter.create_for_complete_advanced(job_id)
    elif processor_type == "performance_optimized":
        return ProcessorProgressAdapter.create_for_performance_optimized(job_id)
    elif processor_type == "basic":
        return ProcessorProgressAdapter.create_for_basic(job_id)
    else:
        logger.warning(f"Unknown processor type '{processor_type}', using basic configuration")
        return ProcessorProgressAdapter.create_for_basic(job_id)


# Example usage for integration with existing processors
def example_processor_integration():
    """
    Example showing how to integrate ProgressEmitter with existing processors
    """
    job_id = "example_job_123"
    
    # Create progress emitter
    emitter = create_progress_emitter(job_id, "complete_advanced")
    
    try:
        # Parsing stage
        emitter.start_stage("parsing", "Loading and parsing document")
        # ... parsing logic ...
        emitter.update_stage_progress(50, "Extracting text content")
        # ... more parsing ...
        emitter.update_stage_progress(100, "Document structure analyzed")
        emitter.complete_stage("Document parsing completed")
        
        # Analyzing stage
        emitter.start_stage("analyzing", "Starting AI analysis")
        # ... analysis logic with progress updates ...
        emitter.update_stage_progress(25, "Processing grammar analysis")
        emitter.update_stage_progress(50, "Processing style analysis")
        emitter.update_stage_progress(75, "Processing clarity analysis")
        emitter.update_stage_progress(100, "AI analysis complete")
        emitter.complete_stage("AI analysis completed")
        
        # ... continue for other stages ...
        
        # Job completion
        emitter.complete_job(True, {
            "download_url": "/api/v1/download/example_job_123",
            "processing_time": "87 seconds",
            "comments_added": 42
        })
        
    except Exception as e:
        emitter.fail_job(str(e))
        raise