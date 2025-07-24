"""
Refactored Progress emitter utility following Sandi Metz principles

Provides a generic interface for emitting progress updates during document processing
with proper separation of concerns and dependency injection.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from .stage_manager import StageManager
from .progress_calculator import ProgressCalculator
from .job_lifecycle_manager import JobLifecycleManager, ProgressTracker
from .processor_config_registry import ProcessorConfigRegistry

logger = logging.getLogger(__name__)


class ProgressEmitter:
    """
    Refactored progress emitter with separated concerns
    
    Coordinates between StageManager, ProgressCalculator, and JobLifecycleManager
    to provide a clean interface for progress tracking.
    """
    
    def __init__(self, job_id: str, progress_tracker: ProgressTracker):
        """
        Initialize progress emitter with dependency injection
        
        Args:
            job_id: Unique job identifier
            progress_tracker: Progress tracker instance (dependency injection)
        """
        self.job_id = job_id
        self.stage_manager = None
        self.progress_calculator = None
        self.lifecycle_manager = JobLifecycleManager(job_id, progress_tracker)
        
        logger.info(f"ProgressEmitter initialized for job {job_id}")
    
    def set_stages(self, stages: List[str], weights: Optional[Dict[str, float]] = None) -> None:
        """
        Define processing stages with optional weights
        
        Args:
            stages: List of stage names
            weights: Optional dictionary of stage weights
        """
        self._validate_stages(stages)
        
        # Use equal weights if not provided
        if weights is None:
            weights = self._create_equal_weights(stages)
        
        self._validate_weights(weights, stages)
        
        # Initialize components
        self.stage_manager = StageManager(stages)
        self.progress_calculator = ProgressCalculator(stages, weights)
        
        # Start job tracking
        estimated_duration = len(stages) * 30  # 30 seconds per stage average
        self.lifecycle_manager.start_job(stages, estimated_duration)
        
        logger.info(f"Job {self.job_id} stages set: {stages}")
    
    def start_stage(self, stage: str, message: Optional[str] = None) -> None:
        """
        Start new processing stage
        
        Args:
            stage: Stage name
            message: Optional message describing stage start
        """
        self._ensure_initialized()
        
        if not self._is_valid_stage_transition(stage):
            return
        
        self.stage_manager.set_current_stage(stage)
        
        # Calculate initial progress for this stage
        overall_progress = self._calculate_current_progress(0)
        start_message = message or f"Starting {stage} stage"
        
        self.lifecycle_manager.update_progress(stage, overall_progress, start_message, 0)
        logger.info(f"Job {self.job_id} starting stage: {stage}")
    
    def update_stage_progress(self, progress: int, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """
        Update current stage progress
        
        Args:
            progress: Stage progress (0-100)
            message: Progress message for user display
            details: Optional additional details for logging
        """
        self._ensure_initialized()
        
        if not self._validate_stage_update():
            return
        
        normalized_progress = self.progress_calculator.normalize_progress(progress)
        overall_progress = self._calculate_current_progress(normalized_progress)
        
        current_stage = self.stage_manager.get_current_stage()
        self.lifecycle_manager.update_progress(current_stage, overall_progress, message, normalized_progress)
        
        self._log_progress_update(progress, details)
    
    def complete_stage(self, message: Optional[str] = None) -> None:
        """
        Mark current stage complete and advance to next stage
        
        Args:
            message: Optional completion message
        """
        self._ensure_initialized()
        
        if not self._validate_stage_completion():
            return
        
        current_stage = self.stage_manager.get_current_stage()
        completion_message = message or f"Completed {current_stage} stage"
        
        # Update progress to 100% for current stage
        final_progress = self._calculate_current_progress(100)
        self.lifecycle_manager.update_progress(current_stage, final_progress, completion_message, 100)
        self.lifecycle_manager.complete_stage(current_stage)
        
        # Advance to next stage
        self.stage_manager.advance_to_next_stage()
        
        logger.info(f"Job {self.job_id} completed stage: {current_stage}")
    
    def complete_job(self, success: bool = True, result_data: Optional[Dict[str, Any]] = None,
                     message: Optional[str] = None) -> None:
        """
        Mark entire job complete
        
        Args:
            success: Whether job completed successfully
            result_data: Additional result data
            message: Optional completion message
        """
        self._ensure_initialized()
        
        self.lifecycle_manager.complete_job(success, result_data)
        status = "completed successfully" if success else "completed with errors"
        logger.info(f"Job {self.job_id} {status}")
    
    def fail_job(self, error: str, stage: Optional[str] = None) -> None:
        """
        Mark job as failed
        
        Args:
            error: Error message
            stage: Stage where error occurred
        """
        current_stage = stage
        if not current_stage and self.stage_manager:
            current_stage = self.stage_manager.get_current_stage()
        
        if self.lifecycle_manager:
            self.lifecycle_manager.fail_job(error, current_stage)
        
        logger.error(f"Job {self.job_id} failed: {error}")
    
    def get_current_status(self) -> Dict[str, Any]:
        """Get current progress status"""
        if not self.stage_manager or not self.progress_calculator:
            return {'job_id': self.job_id, 'initialized': False}
        
        return {
            'job_id': self.job_id,
            'current_stage': self.stage_manager.get_current_stage(),
            'current_stage_index': self.stage_manager.get_current_stage_index(),
            'total_stages': self.stage_manager.get_total_stage_count(),
            'initialized': True
        }
    
    # Private helper methods (extracted from large methods)
    
    def _ensure_initialized(self) -> None:
        """Ensure components are initialized"""
        if not self.stage_manager or not self.progress_calculator:
            raise RuntimeError(f"ProgressEmitter for job {self.job_id} not initialized - call set_stages() first")
    
    def _validate_stages(self, stages: List[str]) -> None:
        """Validate stages list"""
        if not stages:
            raise ValueError("Stages list cannot be empty")
        if len(set(stages)) != len(stages):
            raise ValueError("Stages list contains duplicates")
    
    def _validate_weights(self, weights: Dict[str, float], stages: List[str]) -> None:
        """Validate stage weights"""
        if set(weights.keys()) != set(stages):
            raise ValueError("Weights keys must match stages exactly")
        
        total_weight = sum(weights.values())
        if abs(total_weight - 1.0) > 0.01:
            raise ValueError(f"Weights must sum to 1.0, got {total_weight}")
    
    def _create_equal_weights(self, stages: List[str]) -> Dict[str, float]:
        """Create equal weights for all stages"""
        weight_per_stage = 1.0 / len(stages)
        return {stage: weight_per_stage for stage in stages}
    
    def _is_valid_stage_transition(self, stage: str) -> bool:
        """Validate stage transition"""
        if not self.stage_manager.is_valid_stage(stage):
            logger.warning(f"Starting unknown stage '{stage}' for job {self.job_id}")
            return False
        return True
    
    def _validate_stage_update(self) -> bool:
        """Validate stage update preconditions"""
        if not self.stage_manager.get_current_stage():
            logger.warning(f"Progress update without active stage for job {self.job_id}")
            return False
        return True
    
    def _validate_stage_completion(self) -> bool:
        """Validate stage completion preconditions"""
        if not self.stage_manager.get_current_stage():
            logger.warning(f"Stage completion without active stage for job {self.job_id}")
            return False
        return True
    
    def _calculate_current_progress(self, stage_progress: int) -> int:
        """Calculate overall progress including current stage"""
        completed_count = self.stage_manager.get_completed_stage_count()
        return self.progress_calculator.calculate_overall_progress(completed_count, stage_progress)
    
    def _log_progress_update(self, progress: int, details: Optional[Dict[str, Any]]) -> None:
        """Log progress update with optional details"""
        current_stage = self.stage_manager.get_current_stage()
        overall_progress = self._calculate_current_progress(progress)
        
        logger.debug(f"Job {self.job_id} stage '{current_stage}' progress: {progress}% (overall: {overall_progress}%)")
        
        if details:
            logger.debug(f"Job {self.job_id} progress details: {details}")


class ProgressEmitterFactory:
    """
    Factory for creating ProgressEmitter instances with proper configuration
    """
    
    @staticmethod
    def create(job_id: str, processor_type: str = 'basic', progress_tracker: Optional[ProgressTracker] = None) -> ProgressEmitter:
        """
        Create ProgressEmitter with processor-specific configuration
        
        Args:
            job_id: Job identifier
            processor_type: Type of processor configuration to use
            progress_tracker: Progress tracker instance (will be imported if None)
            
        Returns:
            Configured ProgressEmitter instance
        """
        # Get or create progress tracker
        if progress_tracker is None:
            progress_tracker = ProgressEmitterFactory._get_default_progress_tracker()
        
        emitter = ProgressEmitter(job_id, progress_tracker)
        
        # Configure stages from registry
        config = ProcessorConfigRegistry.get_config(processor_type)
        if config:
            emitter.set_stages(config.stages, config.weights)
        else:
            logger.warning(f"Unknown processor type '{processor_type}', using basic configuration")
            basic_config = ProcessorConfigRegistry.get_config('basic')
            emitter.set_stages(basic_config.stages, basic_config.weights)
        
        return emitter
    
    @staticmethod
    def create_custom(job_id: str, stages: List[str], weights: Optional[Dict[str, float]] = None, 
                     progress_tracker: Optional[ProgressTracker] = None) -> ProgressEmitter:
        """
        Create ProgressEmitter with custom configuration
        
        Args:
            job_id: Job identifier
            stages: Custom stages list
            weights: Optional custom weights
            progress_tracker: Progress tracker instance
            
        Returns:
            Configured ProgressEmitter instance
        """
        if progress_tracker is None:
            progress_tracker = ProgressEmitterFactory._get_default_progress_tracker()
        
        emitter = ProgressEmitter(job_id, progress_tracker)
        emitter.set_stages(stages, weights)
        return emitter
    
    @staticmethod
    def _get_default_progress_tracker() -> ProgressTracker:
        """Get default progress tracker instance"""
        try:
            from web.services.progress_tracker import get_progress_tracker
            return get_progress_tracker()
        except ImportError:
            logger.warning("Progress tracker not available - creating null tracker")
            return NullProgressTracker()


class NullProgressTracker:
    """Null object pattern for progress tracker when not available"""
    
    def start_job(self, job_id: str, stages: list, estimated_duration: Optional[int] = None) -> None:
        logger.info(f"NullProgressTracker: Job {job_id} started with stages {stages}")
    
    def update_progress(self, job_id: str, stage: str, progress: int, message: str, stage_progress: int) -> None:
        logger.info(f"NullProgressTracker: Job {job_id} progress {progress}% - {stage}: {message}")
    
    def complete_stage(self, job_id: str, stage: str) -> None:
        logger.info(f"NullProgressTracker: Job {job_id} completed stage {stage}")
    
    def complete_job(self, job_id: str, success: bool, result_data: Optional[Dict[str, Any]] = None) -> None:
        status = "completed" if success else "failed"
        logger.info(f"NullProgressTracker: Job {job_id} {status}")
    
    def fail_job(self, job_id: str, error: str, stage: Optional[str] = None) -> None:
        logger.error(f"NullProgressTracker: Job {job_id} failed in stage {stage}: {error}")