#!/usr/bin/env python3
"""
Enhanced Progress Tracking Integration for Processing Pipeline
Provides real-time progress updates via WebSocket during document processing
"""

import time
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ProcessingStage(Enum):
    """Processing pipeline stages"""
    INITIALIZING = "initializing"
    PARSING = "parsing"
    CHUNKING = "chunking"
    ANALYZING = "analyzing"
    FORMATTING = "formatting"
    INTEGRATING = "integrating"
    FINALIZING = "finalizing"
    COMPLETED = "completed"


@dataclass
class ProgressUpdate:
    """Progress update data structure"""
    job_id: str
    stage: ProcessingStage
    progress_percent: int
    stage_progress_percent: int
    message: str
    current_item: Optional[str] = None
    total_items: Optional[int] = None
    processing_rate: Optional[float] = None
    estimated_remaining_seconds: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class EnhancedProgressTracker:
    """
    Enhanced progress tracker that integrates with existing WebSocket system
    Provides granular progress updates for document processing pipeline
    """
    
    def __init__(self, progress_callback: Optional[Callable[[ProgressUpdate], None]] = None):
        """
        Initialize progress tracker
        
        Args:
            progress_callback: Optional callback function for progress updates
        """
        self.progress_callback = progress_callback
        self.active_jobs: Dict[str, Dict[str, Any]] = {}
        self.stage_weights = self._get_default_stage_weights()
        logger.info("EnhancedProgressTracker initialized")
    
    def _get_default_stage_weights(self) -> Dict[ProcessingStage, float]:
        """Get default weights for each processing stage"""
        return {
            ProcessingStage.INITIALIZING: 0.05,  # 5%
            ProcessingStage.PARSING: 0.10,       # 10%
            ProcessingStage.CHUNKING: 0.10,      # 10%
            ProcessingStage.ANALYZING: 0.60,     # 60% (most time-consuming)
            ProcessingStage.FORMATTING: 0.05,    # 5%
            ProcessingStage.INTEGRATING: 0.08,   # 8%
            ProcessingStage.FINALIZING: 0.02     # 2%
        }
    
    def start_job(self, job_id: str, document_path: str, estimated_duration: Optional[int] = None) -> None:
        """
        Start tracking a processing job
        
        Args:
            job_id: Unique job identifier
            document_path: Path to document being processed
            estimated_duration: Estimated total duration in seconds
        """
        try:
            stages = list(ProcessingStage)
            stages.remove(ProcessingStage.COMPLETED)  # Remove completed from active stages
            
            job_info = {
                'job_id': job_id,
                'document_path': document_path,
                'stages': stages,
                'current_stage': ProcessingStage.INITIALIZING,
                'current_stage_index': 0,
                'overall_progress': 0,
                'stage_progress': 0,
                'start_time': time.time(),
                'estimated_duration': estimated_duration,
                'stage_start_time': time.time(),
                'stage_metrics': {},
                'processing_stats': {
                    'chunks_processed': 0,
                    'total_chunks': 0,
                    'api_calls_made': 0,
                    'suggestions_found': 0,
                    'integrations_successful': 0
                }
            }
            
            self.active_jobs[job_id] = job_info
            
            # Send initial progress update
            self._send_progress_update(
                job_id=job_id,
                stage=ProcessingStage.INITIALIZING,
                progress_percent=0,
                stage_progress_percent=0,
                message="Initializing document processing..."
            )
            
            logger.info(f"Started tracking job {job_id}")
            
        except Exception as e:
            logger.error(f"Error starting job tracking {job_id}: {str(e)}")
            raise
    
    def update_stage_progress(self, job_id: str, stage: ProcessingStage, 
                            stage_progress: int, message: str,
                            current_item: Optional[str] = None,
                            total_items: Optional[int] = None,
                            metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Update progress within current stage
        
        Args:
            job_id: Job identifier
            stage: Current processing stage
            stage_progress: Progress within stage (0-100)
            message: Progress message
            current_item: Currently processing item (e.g., "chunk 5/20")
            total_items: Total items to process
            metadata: Additional metadata
        """
        try:
            if job_id not in self.active_jobs:
                logger.warning(f"Stage progress update for unknown job: {job_id}")
                return
            
            job_info = self.active_jobs[job_id]
            
            # Update job info
            job_info['current_stage'] = stage
            job_info['stage_progress'] = max(0, min(100, stage_progress))
            
            # Calculate overall progress
            overall_progress = self._calculate_overall_progress(job_info, stage, stage_progress)
            job_info['overall_progress'] = overall_progress
            
            # Calculate processing rate if applicable
            processing_rate = self._calculate_processing_rate(job_info, current_item, total_items)
            
            # Estimate remaining time
            estimated_remaining = self._estimate_remaining_time(job_info, overall_progress)
            
            # Update stats if metadata provided
            if metadata:
                job_info['processing_stats'].update(metadata)
            
            # Send progress update
            self._send_progress_update(
                job_id=job_id,
                stage=stage,
                progress_percent=overall_progress,
                stage_progress_percent=stage_progress,
                message=message,
                current_item=current_item,
                total_items=total_items,
                processing_rate=processing_rate,
                estimated_remaining_seconds=estimated_remaining,
                metadata=metadata
            )
            
            logger.debug(f"Job {job_id} stage progress: {stage.value} {stage_progress}% - {message}")
            
        except Exception as e:
            logger.error(f"Error updating stage progress for job {job_id}: {str(e)}")
            raise
    
    def advance_stage(self, job_id: str, next_stage: ProcessingStage, message: str) -> None:
        """
        Advance to next processing stage
        
        Args:
            job_id: Job identifier
            next_stage: Next stage to advance to
            message: Stage transition message
        """
        try:
            if job_id not in self.active_jobs:
                logger.warning(f"Stage advance for unknown job: {job_id}")
                return
            
            job_info = self.active_jobs[job_id]
            
            # Record stage completion time
            if 'stage_start_time' in job_info:
                stage_duration = time.time() - job_info['stage_start_time']
                job_info['stage_metrics'][job_info['current_stage'].value] = {
                    'duration': stage_duration,
                    'completed_at': time.time()
                }
            
            # Update to next stage
            job_info['current_stage'] = next_stage
            job_info['stage_progress'] = 0
            job_info['stage_start_time'] = time.time()
            
            # Update stage index
            if next_stage in job_info['stages']:
                job_info['current_stage_index'] = job_info['stages'].index(next_stage)
            
            # Calculate overall progress for stage start
            overall_progress = self._calculate_overall_progress(job_info, next_stage, 0)
            job_info['overall_progress'] = overall_progress
            
            # Send stage advance update
            self._send_progress_update(
                job_id=job_id,
                stage=next_stage,
                progress_percent=overall_progress,
                stage_progress_percent=0,
                message=message
            )
            
            logger.info(f"Job {job_id} advanced to stage: {next_stage.value}")
            
        except Exception as e:
            logger.error(f"Error advancing stage for job {job_id}: {str(e)}")
            raise
    
    def complete_job(self, job_id: str, success: bool, 
                    result_data: Optional[Dict[str, Any]] = None,
                    error_message: Optional[str] = None) -> None:
        """
        Mark job as completed
        
        Args:
            job_id: Job identifier
            success: Whether job completed successfully
            result_data: Job result data
            error_message: Error message if failed
        """
        try:
            if job_id not in self.active_jobs:
                logger.warning(f"Job completion for unknown job: {job_id}")
                return
            
            job_info = self.active_jobs[job_id]
            
            # Record completion time
            end_time = time.time()
            job_info['end_time'] = end_time
            job_info['total_duration'] = end_time - job_info['start_time']
            
            # Update final progress
            final_progress = 100 if success else job_info['overall_progress']
            final_stage = ProcessingStage.COMPLETED if success else job_info['current_stage']
            
            # Prepare completion message
            if success:
                message = f"Processing completed successfully in {job_info['total_duration']:.1f} seconds"
                if result_data and 'suggestions_found' in result_data:
                    message += f" - {result_data['suggestions_found']} suggestions generated"
            else:
                message = error_message or "Processing failed"
            
            # Send final progress update
            metadata = {
                'total_duration': job_info['total_duration'],
                'stage_metrics': job_info['stage_metrics'],
                'processing_stats': job_info['processing_stats']
            }
            
            if result_data:
                metadata.update(result_data)
            
            self._send_progress_update(
                job_id=job_id,
                stage=final_stage,
                progress_percent=final_progress,
                stage_progress_percent=100 if success else job_info['stage_progress'],
                message=message,
                metadata=metadata
            )
            
            logger.info(f"Job {job_id} {'completed' if success else 'failed'} in {job_info['total_duration']:.1f}s")
            
        except Exception as e:
            logger.error(f"Error completing job {job_id}: {str(e)}")
            raise
    
    def _calculate_overall_progress(self, job_info: Dict[str, Any], 
                                  current_stage: ProcessingStage, 
                                  stage_progress: int) -> int:
        """Calculate overall progress based on stage weights"""
        try:
            progress = 0.0
            
            # Add progress from completed stages
            for stage in job_info['stages']:
                if stage == current_stage:
                    # Add partial progress from current stage
                    stage_weight = self.stage_weights.get(stage, 0.1)
                    progress += stage_weight * (stage_progress / 100.0)
                    break
                else:
                    # Add full progress from completed stages
                    stage_weight = self.stage_weights.get(stage, 0.1)
                    progress += stage_weight
            
            return max(0, min(100, int(progress * 100)))
            
        except Exception as e:
            logger.error(f"Error calculating overall progress: {str(e)}")
            return job_info.get('overall_progress', 0)
    
    def _calculate_processing_rate(self, job_info: Dict[str, Any], 
                                 current_item: Optional[str], 
                                 total_items: Optional[int]) -> Optional[float]:
        """Calculate processing rate (items per second)"""
        try:
            if not current_item or not total_items:
                return None
            
            # Extract current item number if in format "item X/Y"
            if '/' in str(current_item):
                try:
                    current_num = int(str(current_item).split('/')[0].split()[-1])
                    elapsed = time.time() - job_info['start_time']
                    if elapsed > 0 and current_num > 0:
                        return current_num / elapsed
                except (ValueError, IndexError):
                    pass
            
            return None
            
        except Exception as e:
            logger.error(f"Error calculating processing rate: {str(e)}")
            return None
    
    def _estimate_remaining_time(self, job_info: Dict[str, Any], 
                               overall_progress: int) -> Optional[int]:
        """Estimate remaining processing time"""
        try:
            if overall_progress <= 0:
                return job_info.get('estimated_duration')
            
            elapsed = time.time() - job_info['start_time']
            
            if overall_progress >= 100:
                return 0
            
            # Estimate based on current progress
            estimated_total = elapsed * (100 / overall_progress)
            remaining = estimated_total - elapsed
            
            return max(0, int(remaining))
            
        except Exception as e:
            logger.error(f"Error estimating remaining time: {str(e)}")
            return None
    
    def _send_progress_update(self, job_id: str, stage: ProcessingStage,
                            progress_percent: int, stage_progress_percent: int,
                            message: str, current_item: Optional[str] = None,
                            total_items: Optional[int] = None,
                            processing_rate: Optional[float] = None,
                            estimated_remaining_seconds: Optional[int] = None,
                            metadata: Optional[Dict[str, Any]] = None) -> None:
        """Send progress update via callback"""
        try:
            if not self.progress_callback:
                return
            
            update = ProgressUpdate(
                job_id=job_id,
                stage=stage,
                progress_percent=progress_percent,
                stage_progress_percent=stage_progress_percent,
                message=message,
                current_item=current_item,
                total_items=total_items,
                processing_rate=processing_rate,
                estimated_remaining_seconds=estimated_remaining_seconds,
                metadata=metadata
            )
            
            self.progress_callback(update)
            
        except Exception as e:
            logger.error(f"Error sending progress update: {str(e)}")
    
    def get_job_info(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get current job information"""
        return self.active_jobs.get(job_id)
    
    def cleanup_job(self, job_id: str) -> None:
        """Remove job from tracking"""
        if job_id in self.active_jobs:
            del self.active_jobs[job_id]
            logger.info(f"Cleaned up job tracking for {job_id}")


class ProgressContext:
    """Context manager for progress tracking within processing stages"""
    
    def __init__(self, tracker: EnhancedProgressTracker, job_id: str, 
                 stage: ProcessingStage, total_items: int = 100):
        self.tracker = tracker
        self.job_id = job_id
        self.stage = stage
        self.total_items = total_items
        self.current_item = 0
        self.start_time = time.time()
    
    def __enter__(self):
        self.tracker.advance_stage(
            self.job_id, 
            self.stage, 
            f"Starting {self.stage.value}..."
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            # Completed successfully
            self.tracker.update_stage_progress(
                self.job_id,
                self.stage,
                100,
                f"Completed {self.stage.value}",
                total_items=self.total_items
            )
        else:
            # Failed
            logger.error(f"Stage {self.stage.value} failed: {exc_val}")
    
    def update(self, progress: int, message: str, **kwargs):
        """Update progress within this context"""
        self.current_item = kwargs.get('current_item', self.current_item + 1)
        
        self.tracker.update_stage_progress(
            self.job_id,
            self.stage,
            progress,
            message,
            current_item=f"item {self.current_item}/{self.total_items}",
            total_items=self.total_items,
            **kwargs
        )