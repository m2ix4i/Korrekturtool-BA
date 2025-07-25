"""
Refactored ProgressTracker following Sandi Metz principles
Coordinates between single-purpose components using dependency injection
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from .job_state_manager import JobStateManager, JobInfo
from .websocket_broadcaster import WebSocketBroadcaster, WebSocketEmitter
from .progress_calculator import ProgressCalculator

logger = logging.getLogger(__name__)


class ProgressTracker:
    """
    Refactored ProgressTracker following Single Responsibility Principle
    
    ONLY responsible for:
    - Coordinating between JobStateManager, WebSocketBroadcaster, and ProgressCalculator
    - Providing a unified interface for progress tracking
    - Managing component interactions
    """
    
    def __init__(self, socketio: Optional[WebSocketEmitter] = None):
        self.state_manager = JobStateManager()
        self.calculator = ProgressCalculator()
        
        if socketio:
            self.broadcaster = WebSocketBroadcaster(socketio)
        else:
            self.broadcaster = None
            logger.warning("No SocketIO provided - broadcasting disabled")
        
        logger.info("ProgressTracker initialized with dependency injection")
    
    def start_job(self, job_id: str, stages: List[str], 
                  estimated_duration: Optional[int] = None) -> None:
        """Initialize job tracking"""
        try:
            job_info = self.state_manager.create_job(job_id, stages, estimated_duration)
            
            if self.broadcaster:
                self.broadcaster.broadcast_job_started(
                    job_id, stages, estimated_duration, 
                    job_info['start_time'].isoformat()
                )
            
            logger.info(f"Job {job_id} started with stages: {stages}")
            
        except Exception as e:
            logger.error(f"Error starting job {job_id}: {str(e)}")
            raise
    
    def update_progress(self, job_id: str, stage: str, progress: int, message: str,
                       stage_progress: Optional[int] = None) -> None:
        """Update and broadcast progress"""
        try:
            job_info = self.state_manager.update_job_progress(
                job_id, stage, progress, message, stage_progress
            )
            
            if not job_info:
                logger.warning(f"Progress update for unknown job: {job_id}")
                return
            
            if self.broadcaster:
                estimated_remaining = self.calculator.calculate_estimated_remaining(job_info)
                
                self.broadcaster.broadcast_progress_update(
                    job_id, stage, progress, job_info['stage_progress'],
                    message, estimated_remaining, job_info['last_update'].isoformat()
                )
            
            logger.debug(f"Job {job_id} progress: {progress}% - {stage}: {message}")
            
        except Exception as e:
            logger.error(f"Error updating progress for job {job_id}: {str(e)}")
            raise
    
    def complete_stage(self, job_id: str, stage: str) -> None:
        """Mark current stage as completed and advance to next stage"""
        try:
            next_stage = self.state_manager.advance_stage(job_id, stage)
            
            if self.broadcaster:
                self.broadcaster.broadcast_stage_completed(
                    job_id, stage, next_stage, datetime.utcnow().isoformat()
                )
            
            logger.info(f"Job {job_id} completed stage: {stage}, next: {next_stage}")
        
        except Exception as e:
            logger.error(f"Error completing stage for job {job_id}: {str(e)}")
            raise
    
    def complete_job(self, job_id: str, success: bool, 
                    result_data: Optional[Dict[str, Any]] = None) -> None:
        """Mark job complete and broadcast final status"""
        try:
            if not self.state_manager.complete_job(job_id, success):
                logger.warning(f"Job completion for unknown job: {job_id}")
                return
            
            job_info = self.state_manager.get_job(job_id)
            if not job_info:
                return
            
            if self.broadcaster:
                processing_time = f"{job_info['duration']:.1f} seconds"
                
                self.broadcaster.broadcast_job_completed(
                    job_id, success, processing_time, job_info['duration'],
                    job_info['end_time'].isoformat(), result_data
                )
            
            logger.info(f"Job {job_id} {'completed' if success else 'failed'} in {job_info['duration']:.1f}s")
            
            self._schedule_job_cleanup(job_id)
            
        except Exception as e:
            logger.error(f"Error completing job {job_id}: {str(e)}")
            raise
    
    def fail_job(self, job_id: str, error: str, stage: Optional[str] = None) -> None:
        """Mark job failed and broadcast error"""
        try:
            # Handle unknown jobs by still broadcasting failure
            if job_id not in self.state_manager.active_jobs:
                if self.broadcaster:
                    self.broadcaster.broadcast_job_failed(
                        job_id, error, stage or 'unknown', '0 seconds',
                        datetime.utcnow().isoformat()
                    )
                return
            
            self.state_manager.fail_job(job_id, error, stage)
            job_info = self.state_manager.get_job(job_id)
            
            if job_info and self.broadcaster:
                processing_time = f"{job_info['duration']:.1f} seconds"
                
                self.broadcaster.broadcast_job_failed(
                    job_id, error, stage or job_info['current_stage'],
                    processing_time, job_info['end_time'].isoformat()
                )
            
            logger.error(f"Job {job_id} failed in stage '{stage}': {error}")
            
            self._schedule_job_cleanup(job_id)
            
        except Exception as e:
            logger.error(f"Error failing job {job_id}: {str(e)}")
            raise
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get current job status in JSON-serializable format"""
        return self.state_manager.get_job_serializable(job_id)
    
    def cleanup_job(self, job_id: str) -> bool:
        """Remove job from active tracking"""
        return self.state_manager.remove_job(job_id)
    
    def get_active_jobs(self) -> List[str]:
        """Get list of active job IDs"""
        return self.state_manager.get_active_job_ids()
    
    def get_job_count(self) -> int:
        """Get number of active jobs"""
        return self.state_manager.get_job_count()
    
    def _schedule_job_cleanup(self, job_id: str, delay_minutes: int = 60) -> None:
        """Schedule job cleanup after delay"""
        # TODO: Implement actual delayed cleanup with proper task queue
        logger.info(f"Job {job_id} scheduled for cleanup in {delay_minutes} minutes")


# Singleton pattern for backward compatibility
_progress_tracker_instance = None

def get_progress_tracker() -> ProgressTracker:
    """Get the global progress tracker instance with dependency injection"""
    global _progress_tracker_instance
    if _progress_tracker_instance is None:
        try:
            from web.websocket import get_socketio
            socketio = get_socketio()
            _progress_tracker_instance = ProgressTracker(socketio)
        except ImportError:
            logger.warning("WebSocket unavailable - creating progress tracker without broadcasting")
            _progress_tracker_instance = ProgressTracker(None)
    
    return _progress_tracker_instance