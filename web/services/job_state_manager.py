"""
Job state management following Single Responsibility Principle
Handles ONLY job state tracking and metadata management
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from typing_extensions import TypedDict

logger = logging.getLogger(__name__)


class JobInfo(TypedDict):
    """Type-safe job information structure"""
    job_id: str
    stages: List[str]
    current_stage_index: int
    current_stage: str
    overall_progress: int
    stage_progress: int
    status: str
    start_time: datetime
    estimated_duration: Optional[int]
    estimated_completion: Optional[datetime]
    last_update: datetime
    messages: List[Dict[str, Any]]
    end_time: Optional[datetime]
    duration: Optional[float]
    error: Optional[str]


class JobStateManager:
    """
    Manages job state and metadata following Single Responsibility Principle
    
    ONLY responsible for:
    - Creating and storing job information
    - Updating job progress and status
    - Retrieving job information
    - Managing job lifecycle states
    """
    
    def __init__(self):
        self.active_jobs: Dict[str, JobInfo] = {}
        logger.info("JobStateManager initialized")
    
    def create_job(self, job_id: str, stages: List[str], 
                   estimated_duration: Optional[int] = None) -> JobInfo:
        """Create new job with initial state"""
        job_info: JobInfo = {
            'job_id': job_id,
            'stages': stages,
            'current_stage_index': 0,
            'current_stage': stages[0] if stages else 'unknown',
            'overall_progress': 0,
            'stage_progress': 0,
            'status': 'started',
            'start_time': datetime.utcnow(),
            'estimated_duration': estimated_duration,
            'estimated_completion': self._calculate_completion_time(estimated_duration),
            'last_update': datetime.utcnow(),
            'messages': [],
            'end_time': None,
            'duration': None,
            'error': None
        }
        
        self.active_jobs[job_id] = job_info
        logger.info(f"Job {job_id} created with stages: {stages}")
        return job_info
    
    def update_job_progress(self, job_id: str, stage: str, progress: int, 
                           message: str, stage_progress: Optional[int] = None) -> Optional[JobInfo]:
        """Update job progress and add message"""
        if job_id not in self.active_jobs:
            return None
        
        job_info = self.active_jobs[job_id]
        job_info['current_stage'] = stage
        job_info['overall_progress'] = max(0, min(100, progress))
        job_info['last_update'] = datetime.utcnow()
        
        if stage_progress is not None:
            job_info['stage_progress'] = max(0, min(100, stage_progress))
        
        job_info['messages'].append({
            'timestamp': datetime.utcnow().isoformat(),
            'stage': stage,
            'message': message,
            'progress': progress
        })
        
        return job_info
    
    def advance_stage(self, job_id: str, completed_stage: str) -> Optional[str]:
        """Advance job to next stage, return next stage name or None"""
        if job_id not in self.active_jobs:
            return None
        
        job_info = self.active_jobs[job_id]
        
        if completed_stage in job_info['stages']:
            current_index = job_info['stages'].index(completed_stage)
            job_info['current_stage_index'] = current_index + 1
            
            if current_index + 1 < len(job_info['stages']):
                next_stage = job_info['stages'][current_index + 1]
                job_info['current_stage'] = next_stage
                return next_stage
            else:
                job_info['current_stage'] = 'completed'
                return None
        
        return None
    
    def complete_job(self, job_id: str, success: bool) -> bool:
        """Mark job as completed or failed"""
        if job_id not in self.active_jobs:
            return False
        
        job_info = self.active_jobs[job_id]
        job_info['status'] = 'completed' if success else 'failed'
        job_info['end_time'] = datetime.utcnow()
        job_info['duration'] = (job_info['end_time'] - job_info['start_time']).total_seconds()
        
        if success:
            job_info['overall_progress'] = 100
        
        return True
    
    def fail_job(self, job_id: str, error: str, stage: Optional[str] = None) -> bool:
        """Mark job as failed with error message"""
        if job_id not in self.active_jobs:
            return False
        
        job_info = self.active_jobs[job_id]
        job_info['status'] = 'failed'
        job_info['error'] = error
        job_info['end_time'] = datetime.utcnow()
        job_info['duration'] = (job_info['end_time'] - job_info['start_time']).total_seconds()
        
        return True
    
    def get_job(self, job_id: str) -> Optional[JobInfo]:
        """Get job information"""
        return self.active_jobs.get(job_id)
    
    def get_job_serializable(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job information in JSON-serializable format"""
        job_info = self.get_job(job_id)
        if not job_info:
            return None
        
        serializable = job_info.copy()
        serializable['start_time'] = job_info['start_time'].isoformat()
        serializable['last_update'] = job_info['last_update'].isoformat()
        
        if job_info['end_time']:
            serializable['end_time'] = job_info['end_time'].isoformat()
        if job_info['estimated_completion']:
            serializable['estimated_completion'] = job_info['estimated_completion'].isoformat()
        
        return serializable
    
    def remove_job(self, job_id: str) -> bool:
        """Remove job from tracking"""
        if job_id in self.active_jobs:
            del self.active_jobs[job_id]
            logger.info(f"Job {job_id} removed from tracking")
            return True
        return False
    
    def get_active_job_ids(self) -> List[str]:
        """Get list of active job IDs"""
        return list(self.active_jobs.keys())
    
    def get_job_count(self) -> int:
        """Get number of active jobs"""
        return len(self.active_jobs)
    
    def _calculate_completion_time(self, estimated_duration: Optional[int]) -> Optional[datetime]:
        """Calculate estimated completion time"""
        if estimated_duration:
            return datetime.utcnow() + timedelta(seconds=estimated_duration)
        return None