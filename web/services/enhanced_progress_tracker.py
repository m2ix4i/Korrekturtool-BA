#!/usr/bin/env python3
"""
Enhanced Progress Tracker Service for Web Interface
Integrates with existing WebSocket system and EnhancedProgressTracker
"""

import logging
from typing import Dict, Any, Optional
from web.services.progress_tracker import get_progress_tracker
from src.utils.progress_integration import EnhancedProgressTracker, ProgressUpdate, ProcessingStage

logger = logging.getLogger(__name__)


class WebProgressTracker:
    """
    Web-specific progress tracker that bridges EnhancedProgressTracker with WebSocket system
    """
    
    def __init__(self):
        self.websocket_tracker = get_progress_tracker()
        self.enhanced_tracker = None
        self.active_jobs: Dict[str, Dict[str, Any]] = {}
        logger.info("WebProgressTracker initialized")
    
    def create_job_tracker(self, job_id: str, document_path: str, 
                          estimated_duration: Optional[int] = None) -> EnhancedProgressTracker:
        """
        Create enhanced tracker for a job with WebSocket integration
        
        Args:
            job_id: Unique job identifier
            document_path: Path to document being processed
            estimated_duration: Estimated duration in seconds
            
        Returns:
            EnhancedProgressTracker instance configured for this job
        """
        try:
            # Create progress callback that forwards to WebSocket
            def progress_callback(update: ProgressUpdate):
                self._handle_progress_update(update)
            
            # Create enhanced tracker
            tracker = EnhancedProgressTracker(progress_callback=progress_callback)
            
            # Store job info
            self.active_jobs[job_id] = {
                'tracker': tracker,
                'document_path': document_path,
                'estimated_duration': estimated_duration
            }
            
            # Initialize WebSocket tracking with proper stages
            websocket_stages = [
                "initializing",
                "parsing", 
                "chunking",
                "analyzing",
                "formatting", 
                "integrating",
                "finalizing"
            ]
            
            self.websocket_tracker.start_job(
                job_id=job_id,
                stages=websocket_stages,
                estimated_duration=estimated_duration
            )
            
            # Start enhanced tracking
            tracker.start_job(job_id, document_path, estimated_duration)
            
            logger.info(f"Created job tracker for {job_id}")
            return tracker
            
        except Exception as e:
            logger.error(f"Error creating job tracker for {job_id}: {str(e)}")
            raise
    
    def get_job_tracker(self, job_id: str) -> Optional[EnhancedProgressTracker]:
        """Get enhanced tracker for job"""
        job_info = self.active_jobs.get(job_id)
        return job_info['tracker'] if job_info else None
    
    def complete_job(self, job_id: str, success: bool, 
                    result_data: Optional[Dict[str, Any]] = None,
                    error_message: Optional[str] = None) -> None:
        """
        Complete job tracking
        
        Args:
            job_id: Job identifier
            success: Whether job completed successfully
            result_data: Result data including metrics
            error_message: Error message if failed
        """
        try:
            # Complete enhanced tracking
            job_info = self.active_jobs.get(job_id)
            if job_info and 'tracker' in job_info:
                tracker = job_info['tracker']
                tracker.complete_job(job_id, success, result_data, error_message)
            
            # Complete WebSocket tracking
            if success:
                self.websocket_tracker.complete_job(job_id, success, result_data)
            else:
                self.websocket_tracker.fail_job(job_id, error_message or "Processing failed")
            
            logger.info(f"Completed job tracking for {job_id}: {'success' if success else 'failed'}")
            
        except Exception as e:
            logger.error(f"Error completing job tracking for {job_id}: {str(e)}")
            raise
    
    def cleanup_job(self, job_id: str) -> None:
        """Clean up job tracking resources"""
        try:
            # Cleanup enhanced tracker
            job_info = self.active_jobs.get(job_id)
            if job_info and 'tracker' in job_info:
                tracker = job_info['tracker']
                tracker.cleanup_job(job_id)
            
            # Cleanup WebSocket tracker
            self.websocket_tracker.cleanup_job(job_id)
            
            # Remove from active jobs
            if job_id in self.active_jobs:
                del self.active_jobs[job_id]
            
            logger.info(f"Cleaned up job tracking for {job_id}")
            
        except Exception as e:
            logger.error(f"Error cleaning up job tracking for {job_id}: {str(e)}")
    
    def _handle_progress_update(self, update: ProgressUpdate) -> None:
        """
        Handle progress update from EnhancedProgressTracker and forward to WebSocket
        
        Args:
            update: Progress update data
        """
        try:
            # Map ProcessingStage to WebSocket stage names
            stage_mapping = {
                ProcessingStage.INITIALIZING: "initializing",
                ProcessingStage.PARSING: "parsing",
                ProcessingStage.CHUNKING: "chunking", 
                ProcessingStage.ANALYZING: "analyzing",
                ProcessingStage.FORMATTING: "formatting",
                ProcessingStage.INTEGRATING: "integrating",
                ProcessingStage.FINALIZING: "finalizing",
                ProcessingStage.COMPLETED: "completed"
            }
            
            websocket_stage = stage_mapping.get(update.stage, update.stage.value)
            
            # Format message with additional context
            enhanced_message = update.message
            
            if update.current_item and update.total_items:
                enhanced_message += f" ({update.current_item})"
            
            if update.processing_rate:
                enhanced_message += f" - Rate: {update.processing_rate:.1f} items/sec"
            
            if update.estimated_remaining_seconds:
                remaining_str = self._format_time_remaining(update.estimated_remaining_seconds)
                enhanced_message += f" - ETA: {remaining_str}"
            
            # Update WebSocket tracker
            self.websocket_tracker.update_progress(
                job_id=update.job_id,
                stage=websocket_stage,
                progress=update.progress_percent,
                message=enhanced_message,
                stage_progress=update.stage_progress_percent
            )
            
            # Log detailed progress
            logger.debug(f"Progress update for {update.job_id}: {update.stage.value} "
                        f"{update.progress_percent}% - {update.message}")
            
        except Exception as e:
            logger.error(f"Error handling progress update: {str(e)}")
    
    def _format_time_remaining(self, seconds: int) -> str:
        """Format remaining time as human-readable string"""
        if seconds <= 0:
            return "0s"
        elif seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            minutes = seconds // 60
            return f"{minutes}m {seconds % 60}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes}m"
    
    def get_active_job_count(self) -> int:
        """Get number of active jobs"""
        return len(self.active_jobs)
    
    def get_active_job_ids(self) -> list:
        """Get list of active job IDs"""
        return list(self.active_jobs.keys())


# Global instance
_web_progress_tracker = None

def get_web_progress_tracker() -> WebProgressTracker:
    """Get global WebProgressTracker instance"""
    global _web_progress_tracker
    if _web_progress_tracker is None:
        _web_progress_tracker = WebProgressTracker()
    return _web_progress_tracker