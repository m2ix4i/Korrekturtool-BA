"""
Job model for processing task management
"""

import uuid
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import json


class JobStatus(Enum):
    """Job processing status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing" 
    COMPLETED = "completed"
    FAILED = "failed"


class ProcessingMode(Enum):
    """Processing mode enumeration"""
    COMPLETE = "complete"
    PERFORMANCE = "performance"


@dataclass
class ProcessingOptions:
    """Configuration options for processing"""
    categories: List[str]
    output_filename: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProcessingOptions':
        """Create from dictionary"""
        return cls(
            categories=data.get('categories', ['grammar', 'style', 'clarity', 'academic']),
            output_filename=data.get('output_filename')
        )


@dataclass
class ProcessingProgress:
    """Processing progress information"""
    current_step: str
    progress_percent: int
    estimated_remaining_seconds: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProcessingProgress':
        """Create from dictionary"""
        return cls(
            current_step=data.get('current_step', 'Unknown'),
            progress_percent=data.get('progress_percent', 0),
            estimated_remaining_seconds=data.get('estimated_remaining_seconds')
        )


@dataclass
class ProcessingResult:
    """Processing result information"""
    output_file_path: Optional[str] = None
    output_file_id: Optional[str] = None
    total_suggestions: int = 0
    successful_integrations: int = 0
    processing_time_seconds: float = 0.0
    cost_estimate: float = 0.0
    performance_stats: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProcessingResult':
        """Create from dictionary"""
        return cls(
            output_file_path=data.get('output_file_path'),
            output_file_id=data.get('output_file_id'),
            total_suggestions=data.get('total_suggestions', 0),
            successful_integrations=data.get('successful_integrations', 0),
            processing_time_seconds=data.get('processing_time_seconds', 0.0),
            cost_estimate=data.get('cost_estimate', 0.0),
            performance_stats=data.get('performance_stats')
        )


class Job:
    """Processing job model with state management"""
    
    def __init__(
        self,
        file_id: str,
        file_path: str,
        processing_mode: ProcessingMode,
        options: ProcessingOptions,
        job_id: Optional[str] = None
    ):
        self.job_id = job_id or str(uuid.uuid4())
        self.file_id = file_id
        self.file_path = file_path
        self.processing_mode = processing_mode
        self.options = options
        
        # Status tracking
        self.status = JobStatus.PENDING
        self.progress = ProcessingProgress(current_step="Initialized", progress_percent=0)
        self.result: Optional[ProcessingResult] = None
        self.error_message: Optional[str] = None
        
        # Timestamps
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        
        # Estimated processing time based on mode
        self.estimated_time_seconds = self._estimate_processing_time()
    
    def _estimate_processing_time(self) -> int:
        """Estimate processing time based on mode and options"""
        base_time = 60  # 1 minute base
        
        if self.processing_mode == ProcessingMode.COMPLETE:
            base_time = 90  # Complete mode takes longer
        
        # Add time for each category
        category_time = len(self.options.categories) * 15
        
        return base_time + category_time
    
    def start_processing(self):
        """Mark job as started"""
        self.status = JobStatus.PROCESSING
        self.started_at = datetime.now()
        self.progress = ProcessingProgress(
            current_step="Starting processing",
            progress_percent=5
        )
    
    def update_progress(self, step: str, percent: int, estimated_remaining: Optional[int] = None):
        """Update job progress"""
        self.progress = ProcessingProgress(
            current_step=step,
            progress_percent=min(percent, 99),  # Never show 100% until completed
            estimated_remaining_seconds=estimated_remaining
        )
    
    def complete_successfully(self, result: ProcessingResult):
        """Mark job as completed successfully"""
        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.now()
        self.result = result
        self.progress = ProcessingProgress(
            current_step="Completed",
            progress_percent=100
        )
    
    def fail_with_error(self, error_message: str):
        """Mark job as failed with error"""
        self.status = JobStatus.FAILED
        self.completed_at = datetime.now()
        self.error_message = error_message
        self.progress = ProcessingProgress(
            current_step="Failed",
            progress_percent=0
        )
    
    def get_elapsed_time(self) -> Optional[float]:
        """Get elapsed processing time in seconds"""
        if not self.started_at:
            return None
        
        end_time = self.completed_at or datetime.now()
        return (end_time - self.started_at).total_seconds()
    
    def is_expired(self, max_age_hours: int = 24) -> bool:
        """Check if job has expired (for cleanup)"""
        expiry_time = self.created_at + timedelta(hours=max_age_hours)
        return datetime.now() > expiry_time
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary for API responses"""
        data = {
            'job_id': self.job_id,
            'file_id': self.file_id,
            'processing_mode': self.processing_mode.value,
            'options': self.options.to_dict(),
            'status': self.status.value,
            'progress': self.progress.to_dict(),
            'estimated_time_seconds': self.estimated_time_seconds,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'elapsed_time_seconds': self.get_elapsed_time(),
            'error_message': self.error_message
        }
        
        if self.result:
            data['result'] = self.result.to_dict()
        
        return data
    
    def to_json(self) -> str:
        """Convert job to JSON string"""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Job':
        """Create job from dictionary (for deserialization)"""
        options = ProcessingOptions.from_dict(data['options'])
        processing_mode = ProcessingMode(data['processing_mode'])
        
        job = cls(
            file_id=data['file_id'],
            file_path=data.get('file_path', ''),
            processing_mode=processing_mode,
            options=options,
            job_id=data['job_id']
        )
        
        # Restore state
        job.status = JobStatus(data['status'])
        job.progress = ProcessingProgress.from_dict(data['progress'])
        job.estimated_time_seconds = data['estimated_time_seconds']
        job.error_message = data.get('error_message')
        
        # Restore timestamps
        job.created_at = datetime.fromisoformat(data['created_at'])
        if data.get('started_at'):
            job.started_at = datetime.fromisoformat(data['started_at'])
        if data.get('completed_at'):
            job.completed_at = datetime.fromisoformat(data['completed_at'])
        
        # Restore result if present
        if data.get('result'):
            job.result = ProcessingResult.from_dict(data['result'])
        
        return job
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Job':
        """Create job from JSON string"""
        data = json.loads(json_str)
        return cls.from_dict(data)