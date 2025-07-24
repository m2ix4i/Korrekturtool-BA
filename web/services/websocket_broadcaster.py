"""
WebSocket broadcasting following Single Responsibility Principle
Handles ONLY WebSocket message broadcasting and room management
"""

import logging
from typing import Dict, Any, Optional, Protocol

logger = logging.getLogger(__name__)


class WebSocketEmitter(Protocol):
    """Protocol for WebSocket emitter interface"""
    def emit(self, event: str, data: Dict[str, Any], room: Optional[str] = None) -> None: ...


class WebSocketBroadcaster:
    """
    Handles WebSocket broadcasting following Single Responsibility Principle
    
    ONLY responsible for:
    - Broadcasting messages to WebSocket rooms
    - Managing job-specific room communication
    - Formatting broadcast messages
    """
    
    def __init__(self, socketio: WebSocketEmitter):
        self.socketio = socketio
        logger.info("WebSocketBroadcaster initialized")
    
    def broadcast_job_started(self, job_id: str, stages: list, 
                            estimated_duration: Optional[int], timestamp: str) -> None:
        """Broadcast job started event"""
        data = {
            'job_id': job_id,
            'stages': stages,
            'estimated_duration': estimated_duration,
            'status': 'started',
            'timestamp': timestamp
        }
        self._broadcast_to_job_room(job_id, 'job_started', data)
    
    def broadcast_progress_update(self, job_id: str, stage: str, progress: int,
                                stage_progress: int, message: str, 
                                estimated_remaining: Optional[str], timestamp: str) -> None:
        """Broadcast progress update event"""
        data = {
            'job_id': job_id,
            'stage': stage,
            'progress': progress,
            'stage_progress': stage_progress,
            'message': message,
            'estimated_remaining': estimated_remaining,
            'timestamp': timestamp
        }
        self._broadcast_to_job_room(job_id, 'progress_update', data)
    
    def broadcast_stage_completed(self, job_id: str, completed_stage: str,
                                next_stage: Optional[str], timestamp: str) -> None:
        """Broadcast stage completion event"""
        data = {
            'job_id': job_id,
            'completed_stage': completed_stage,
            'next_stage': next_stage,
            'timestamp': timestamp
        }
        self._broadcast_to_job_room(job_id, 'stage_completed', data)
    
    def broadcast_job_completed(self, job_id: str, success: bool, processing_time: str,
                              duration_seconds: float, timestamp: str,
                              result_data: Optional[Dict[str, Any]] = None) -> None:
        """Broadcast job completion event"""
        data = {
            'job_id': job_id,
            'success': success,
            'status': 'completed' if success else 'failed',
            'processing_time': processing_time,
            'duration_seconds': duration_seconds,
            'timestamp': timestamp
        }
        
        if result_data:
            data.update(result_data)
        
        event_name = 'job_completed' if success else 'job_failed'
        self._broadcast_to_job_room(job_id, event_name, data)
    
    def broadcast_job_failed(self, job_id: str, error: str, stage: str,
                           processing_time: str, timestamp: str) -> None:
        """Broadcast job failure event"""
        data = {
            'job_id': job_id,
            'success': False,
            'error': error,
            'stage': stage,
            'processing_time': processing_time,
            'timestamp': timestamp
        }
        self._broadcast_to_job_room(job_id, 'job_failed', data)
    
    def _broadcast_to_job_room(self, job_id: str, event: str, data: Dict[str, Any]) -> None:
        """Broadcast message to job-specific room"""
        try:
            room = f"job_{job_id}"
            self.socketio.emit(event, data, room=room)
            logger.debug(f"Broadcasted {event} to room {room}")
        except Exception as e:
            logger.error(f"Error broadcasting {event} to job {job_id}: {str(e)}")