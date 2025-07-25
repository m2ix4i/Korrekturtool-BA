"""
Progress tracking service for WebSocket-based real-time progress updates
"""

import time
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from flask_socketio import emit
from web.websocket import get_socketio

logger = logging.getLogger(__name__)

class ProgressTracker:
    """
    Centralized progress tracking with WebSocket broadcasting
    
    Manages job progress state and broadcasts updates to connected WebSocket clients
    in job-specific rooms for efficient message routing.
    """
    
    def __init__(self):
        self.active_jobs: Dict[str, Dict[str, Any]] = {}
        self.socketio = get_socketio()
        logger.info("ProgressTracker initialized")
    
    def start_job(self, job_id: str, stages: List[str], estimated_duration: Optional[int] = None) -> None:
        """
        Initialize job tracking
        
        Args:
            job_id: Unique job identifier
            stages: List of processing stages (e.g., ["parsing", "analyzing", "integrating"])
            estimated_duration: Estimated total duration in seconds
        """
        try:
            job_info = {
                'job_id': job_id,
                'stages': stages,
                'current_stage_index': 0,
                'current_stage': stages[0] if stages else 'unknown',
                'overall_progress': 0,
                'stage_progress': 0,
                'status': 'started',
                'start_time': datetime.utcnow(),
                'estimated_duration': estimated_duration,
                'estimated_completion': datetime.utcnow() + timedelta(seconds=estimated_duration) if estimated_duration else None,
                'last_update': datetime.utcnow(),
                'messages': []
            }
            
            self.active_jobs[job_id] = job_info
            
            # Broadcast job started event
            self._broadcast_to_job(job_id, 'job_started', {
                'job_id': job_id,
                'stages': stages,
                'estimated_duration': estimated_duration,
                'status': 'started',
                'timestamp': job_info['start_time'].isoformat()
            })
            
            logger.info(f"Job {job_id} started with stages: {stages}")
            
        except Exception as e:
            logger.error(f"Error starting job {job_id}: {str(e)}")
            raise
    
    def update_progress(self, job_id: str, stage: str, progress: int, message: str, 
                       stage_progress: Optional[int] = None) -> None:
        """
        Update and broadcast progress
        
        Args:
            job_id: Job identifier
            stage: Current processing stage
            progress: Overall job progress (0-100)
            message: Progress message for user display
            stage_progress: Progress within current stage (0-100), optional
        """
        try:
            if job_id not in self.active_jobs:
                logger.warning(f"Progress update for unknown job: {job_id}")
                return
            
            job_info = self.active_jobs[job_id]
            job_info['current_stage'] = stage
            job_info['overall_progress'] = max(0, min(100, progress))
            job_info['last_update'] = datetime.utcnow()
            job_info['messages'].append({
                'timestamp': datetime.utcnow().isoformat(),
                'stage': stage,
                'message': message,
                'progress': progress
            })
            
            if stage_progress is not None:
                job_info['stage_progress'] = max(0, min(100, stage_progress))
            
            # Calculate estimated remaining time
            estimated_remaining = self._calculate_estimated_remaining(job_id)
            
            # Broadcast progress update
            progress_data = {
                'job_id': job_id,
                'stage': stage,
                'progress': progress,
                'stage_progress': job_info.get('stage_progress', 0),
                'message': message,
                'estimated_remaining': estimated_remaining,
                'timestamp': job_info['last_update'].isoformat()
            }
            
            self._broadcast_to_job(job_id, 'progress_update', progress_data)
            
            logger.debug(f"Job {job_id} progress: {progress}% - {stage}: {message}")
            
        except Exception as e:
            logger.error(f"Error updating progress for job {job_id}: {str(e)}")
            raise
    
    def complete_stage(self, job_id: str, stage: str) -> None:
        """
        Mark current stage as completed and advance to next stage
        
        Args:
            job_id: Job identifier
            stage: Stage that was completed
        """
        try:
            if job_id not in self.active_jobs:
                logger.warning(f"Stage completion for unknown job: {job_id}")
                return
            
            job_info = self.active_jobs[job_id]
            
            # Find current stage index and advance
            if stage in job_info['stages']:
                current_index = job_info['stages'].index(stage)
                job_info['current_stage_index'] = current_index + 1
                
                # Determine next stage
                if current_index + 1 < len(job_info['stages']):
                    next_stage = job_info['stages'][current_index + 1]
                    job_info['current_stage'] = next_stage
                else:
                    next_stage = None
                
                # Broadcast stage completion
                self._broadcast_to_job(job_id, 'stage_completed', {
                    'job_id': job_id,
                    'completed_stage': stage,
                    'next_stage': next_stage,
                    'timestamp': datetime.utcnow().isoformat()
                })
                
                logger.info(f"Job {job_id} completed stage: {stage}, next: {next_stage}")
        
        except Exception as e:
            logger.error(f"Error completing stage for job {job_id}: {str(e)}")
            raise
    
    def complete_job(self, job_id: str, success: bool, result_data: Optional[Dict[str, Any]] = None) -> None:
        """
        Mark job complete and broadcast final status
        
        Args:
            job_id: Job identifier
            success: Whether job completed successfully
            result_data: Additional result data (download URL, metrics, etc.)
        """
        try:
            if job_id not in self.active_jobs:
                logger.warning(f"Job completion for unknown job: {job_id}")
                return
            
            job_info = self.active_jobs[job_id]
            job_info['status'] = 'completed' if success else 'failed'
            job_info['end_time'] = datetime.utcnow()
            job_info['duration'] = (job_info['end_time'] - job_info['start_time']).total_seconds()
            
            # Broadcast job completion
            completion_data = {
                'job_id': job_id,
                'success': success,
                'status': job_info['status'],
                'processing_time': f"{job_info['duration']:.1f} seconds",
                'duration_seconds': job_info['duration'],
                'timestamp': job_info['end_time'].isoformat()
            }
            
            if result_data:
                completion_data.update(result_data)
            
            event_name = 'job_completed' if success else 'job_failed'
            self._broadcast_to_job(job_id, event_name, completion_data)
            
            logger.info(f"Job {job_id} {'completed' if success else 'failed'} in {job_info['duration']:.1f}s")
            
            # Schedule cleanup after delay
            self._schedule_job_cleanup(job_id)
            
        except Exception as e:
            logger.error(f"Error completing job {job_id}: {str(e)}")
            raise
    
    def fail_job(self, job_id: str, error: str, stage: Optional[str] = None) -> None:
        """
        Mark job failed and broadcast error
        
        Args:
            job_id: Job identifier
            error: Error message
            stage: Stage where error occurred
        """
        try:
            if job_id not in self.active_jobs:
                logger.warning(f"Job failure for unknown job: {job_id}")
                # Still broadcast the failure even if we don't have job info
                self._broadcast_to_job(job_id, 'job_failed', {
                    'job_id': job_id,
                    'success': False,
                    'error': error,
                    'stage': stage or 'unknown',
                    'timestamp': datetime.utcnow().isoformat()
                })
                return
            
            job_info = self.active_jobs[job_id]
            job_info['status'] = 'failed'
            job_info['error'] = error
            job_info['end_time'] = datetime.utcnow()
            job_info['duration'] = (job_info['end_time'] - job_info['start_time']).total_seconds()
            
            # Broadcast job failure
            failure_data = {
                'job_id': job_id,
                'success': False,
                'error': error,
                'stage': stage or job_info['current_stage'],
                'processing_time': f"{job_info['duration']:.1f} seconds",
                'timestamp': job_info['end_time'].isoformat()
            }
            
            self._broadcast_to_job(job_id, 'job_failed', failure_data)
            
            logger.error(f"Job {job_id} failed in stage '{stage or job_info['current_stage']}': {error}")
            
            # Schedule cleanup after delay
            self._schedule_job_cleanup(job_id)
            
        except Exception as e:
            logger.error(f"Error failing job {job_id}: {str(e)}")
            raise
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current job status
        
        Args:
            job_id: Job identifier
            
        Returns:
            Job status dictionary or None if job not found
        """
        if job_id not in self.active_jobs:
            return None
        
        job_info = self.active_jobs[job_id].copy()
        
        # Convert datetime objects to ISO strings for JSON serialization
        if 'start_time' in job_info:
            job_info['start_time'] = job_info['start_time'].isoformat()
        if 'end_time' in job_info:
            job_info['end_time'] = job_info['end_time'].isoformat()
        if 'estimated_completion' in job_info and job_info['estimated_completion']:
            job_info['estimated_completion'] = job_info['estimated_completion'].isoformat()
        if 'last_update' in job_info:
            job_info['last_update'] = job_info['last_update'].isoformat()
        
        return job_info
    
    def _broadcast_to_job(self, job_id: str, event: str, data: Dict[str, Any]) -> None:
        """
        Broadcast message to job-specific room
        
        Args:
            job_id: Job identifier
            event: WebSocket event name
            data: Event data
        """
        try:
            room = f"job_{job_id}"
            self.socketio.emit(event, data, room=room)
            logger.debug(f"Broadcasted {event} to room {room}")
        except Exception as e:
            logger.error(f"Error broadcasting {event} to job {job_id}: {str(e)}")
    
    def _calculate_estimated_remaining(self, job_id: str) -> Optional[str]:
        """
        Calculate estimated remaining time based on progress
        
        Args:
            job_id: Job identifier
            
        Returns:
            Estimated remaining time as human-readable string
        """
        try:
            job_info = self.active_jobs[job_id]
            current_progress = job_info['overall_progress']
            
            if current_progress <= 0:
                return None
            
            elapsed = (datetime.utcnow() - job_info['start_time']).total_seconds()
            
            if current_progress >= 100:
                return "0 seconds"
            
            # Estimate total time based on current progress
            estimated_total = elapsed * (100 / current_progress)
            remaining = estimated_total - elapsed
            
            if remaining <= 0:
                return "0 seconds"
            elif remaining < 60:
                return f"{int(remaining)} seconds"
            elif remaining < 3600:
                minutes = int(remaining / 60)
                return f"{minutes} minute{'s' if minutes != 1 else ''}"
            else:
                hours = int(remaining / 3600)
                minutes = int((remaining % 3600) / 60)
                return f"{hours}h {minutes}m"
                
        except Exception as e:
            logger.error(f"Error calculating remaining time for job {job_id}: {str(e)}")
            return None
    
    def _schedule_job_cleanup(self, job_id: str, delay_minutes: int = 60) -> None:
        """
        Schedule job cleanup after delay
        
        Args:
            job_id: Job identifier
            delay_minutes: Delay before cleanup in minutes
        """
        # For now, just log the cleanup intention
        # In a production system, this would use a task queue like Celery
        logger.info(f"Job {job_id} scheduled for cleanup in {delay_minutes} minutes")
        
        # TODO: Implement actual delayed cleanup
        # This could be done with:
        # 1. Celery delayed task
        # 2. APScheduler
        # 3. Simple threading.Timer (not recommended for production)
    
    def cleanup_job(self, job_id: str) -> bool:
        """
        Remove job from active tracking
        
        Args:
            job_id: Job identifier
            
        Returns:
            True if job was removed, False if not found
        """
        if job_id in self.active_jobs:
            del self.active_jobs[job_id]
            logger.info(f"Cleaned up job {job_id}")
            return True
        return False
    
    def get_active_jobs(self) -> List[str]:
        """
        Get list of active job IDs
        
        Returns:
            List of active job IDs
        """
        return list(self.active_jobs.keys())
    
    def get_job_count(self) -> int:
        """
        Get number of active jobs
        
        Returns:
            Number of active jobs
        """
        return len(self.active_jobs)

# Global progress tracker instance
_progress_tracker = None

def get_progress_tracker() -> ProgressTracker:
    """
    Get the global progress tracker instance
    
    Returns:
        ProgressTracker instance
    """
    global _progress_tracker
    if _progress_tracker is None:
        _progress_tracker = ProgressTracker()
    return _progress_tracker