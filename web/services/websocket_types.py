"""
Type definitions for WebSocket and progress tracking
Improves type safety with Protocol and TypedDict
"""

from typing import Dict, List, Optional, Any, Protocol
from typing_extensions import TypedDict
from datetime import datetime


class WebSocketEmitter(Protocol):
    """Protocol for WebSocket emitter interface"""
    def emit(self, event: str, data: Dict[str, Any], room: Optional[str] = None) -> None: ...


class JobInfo(TypedDict, total=False):
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


class ProgressUpdateData(TypedDict):
    """Type-safe progress update message structure"""
    job_id: str
    stage: str
    progress: int
    stage_progress: int
    message: str
    estimated_remaining: Optional[str]
    timestamp: str


class JobStartedData(TypedDict):
    """Type-safe job started message structure"""
    job_id: str
    stages: List[str]
    estimated_duration: Optional[int]
    status: str
    timestamp: str


class JobCompletedData(TypedDict):
    """Type-safe job completed message structure"""
    job_id: str
    success: bool
    status: str
    processing_time: str
    duration_seconds: float
    timestamp: str


class JobFailedData(TypedDict):
    """Type-safe job failed message structure"""
    job_id: str
    success: bool
    error: str
    stage: str
    processing_time: str
    timestamp: str


class StageCompletedData(TypedDict):
    """Type-safe stage completed message structure"""
    job_id: str
    completed_stage: str
    next_stage: Optional[str]
    timestamp: str