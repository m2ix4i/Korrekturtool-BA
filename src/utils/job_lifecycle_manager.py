"""
Job lifecycle management component for progress tracking
Following Single Responsibility Principle - handles only job state transitions
"""

import logging
from typing import Optional, Dict, Any, Protocol

logger = logging.getLogger(__name__)


class ProgressTracker(Protocol):
    """Protocol defining the progress tracker interface"""
    def start_job(self, job_id: str, stages: list, estimated_duration: Optional[int] = None) -> None: ...
    def update_progress(self, job_id: str, stage: str, progress: int, message: str, stage_progress: int) -> None: ...
    def complete_stage(self, job_id: str, stage: str) -> None: ...
    def complete_job(self, job_id: str, success: bool, result_data: Optional[Dict[str, Any]] = None) -> None: ...
    def fail_job(self, job_id: str, error: str, stage: Optional[str] = None) -> None: ...


class JobLifecycleManager:
    """
    Manages job state transitions and lifecycle events
    
    Responsibility: Job start, completion, failure, and progress tracker coordination
    """
    
    def __init__(self, job_id: str, progress_tracker: ProgressTracker):
        """
        Initialize job lifecycle manager
        
        Args:
            job_id: Unique job identifier
            progress_tracker: Progress tracker instance
        """
        self.job_id = job_id
        self.progress_tracker = progress_tracker
        
        logger.debug(f"JobLifecycleManager initialized for job {job_id}")
    
    def start_job(self, stages: list, estimated_duration: Optional[int] = None) -> None:
        """
        Start job tracking
        
        Args:
            stages: List of processing stages
            estimated_duration: Estimated duration in seconds
        """
        try:
            self.progress_tracker.start_job(self.job_id, stages, estimated_duration)
            logger.info(f"Job {self.job_id} started with stages: {stages}")
        except Exception as e:
            logger.error(f"Error starting job {self.job_id}: {str(e)}")
            raise
    
    def update_progress(self, stage: str, overall_progress: int, message: str, stage_progress: int) -> None:
        """
        Update job progress
        
        Args:
            stage: Current stage name
            overall_progress: Overall progress percentage
            message: Progress message
            stage_progress: Stage-specific progress percentage
        """
        try:
            self.progress_tracker.update_progress(
                self.job_id, stage, overall_progress, message, stage_progress
            )
            logger.debug(f"Job {self.job_id} progress updated: {overall_progress}%")
        except Exception as e:
            logger.error(f"Error updating progress for job {self.job_id}: {str(e)}")
            raise
    
    def complete_stage(self, stage: str) -> None:
        """
        Mark stage as completed
        
        Args:
            stage: Stage name to complete
        """
        try:
            self.progress_tracker.complete_stage(self.job_id, stage)
            logger.info(f"Job {self.job_id} completed stage: {stage}")
        except Exception as e:
            logger.error(f"Error completing stage for job {self.job_id}: {str(e)}")
            raise
    
    def complete_job(self, success: bool = True, result_data: Optional[Dict[str, Any]] = None) -> None:
        """
        Mark job as completed
        
        Args:
            success: Whether job completed successfully
            result_data: Additional result data
        """
        try:
            self.progress_tracker.complete_job(self.job_id, success, result_data)
            status = "completed successfully" if success else "completed with errors"
            logger.info(f"Job {self.job_id} {status}")
        except Exception as e:
            logger.error(f"Error completing job {self.job_id}: {str(e)}")
            raise
    
    def fail_job(self, error: str, stage: Optional[str] = None) -> None:
        """
        Mark job as failed
        
        Args:
            error: Error message
            stage: Stage where error occurred
        """
        try:
            self.progress_tracker.fail_job(self.job_id, error, stage)
            logger.error(f"Job {self.job_id} failed: {error}")
        except Exception as e:
            logger.error(f"Error failing job {self.job_id}: {str(e)}")
            raise