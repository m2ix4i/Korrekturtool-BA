"""
WebSocket event handlers for progress tracking
"""

import logging
from flask_socketio import emit, join_room, leave_room, disconnect
from flask import request

from web.websocket import get_socketio
from web.services.progress_tracker import get_progress_tracker

# Get instances
socketio = get_socketio()
progress_tracker = get_progress_tracker()
logger = logging.getLogger(__name__)

@socketio.on('connect')
def handle_connect():
    """
    Handle client connection
    
    Called when a WebSocket client connects to the server.
    """
    try:
        client_id = request.sid
        logger.info(f"Client connected: {client_id}")
        
        # Send connection confirmation
        emit('connected', {
            'message': 'Connected to progress tracking service',
            'client_id': client_id,
            'timestamp': progress_tracker._get_current_timestamp()
        })
        
    except Exception as e:
        logger.error(f"Error handling client connection: {str(e)}")
        emit('error', {
            'message': 'Connection error occurred',
            'error': str(e)
        })

@socketio.on('disconnect')
def handle_disconnect():
    """
    Handle client disconnection
    
    Called when a WebSocket client disconnects from the server.
    """
    try:
        client_id = request.sid
        logger.info(f"Client disconnected: {client_id}")
        
    except Exception as e:
        logger.error(f"Error handling client disconnection: {str(e)}")

@socketio.on('join_job')
def handle_join_job(data):
    """
    Join room for specific job updates
    
    Args:
        data: Dictionary containing 'job_id'
    """
    try:
        if not isinstance(data, dict) or 'job_id' not in data:
            emit('error', {
                'message': 'Invalid join_job request: job_id is required',
                'received_data': str(data)
            })
            return
        
        job_id = data['job_id']
        room = f"job_{job_id}"
        client_id = request.sid
        
        # Join the job-specific room
        join_room(room)
        
        logger.info(f"Client {client_id} joined room {room}")
        
        # Get current job status if available
        job_status = progress_tracker.get_job_status(job_id)
        
        # Send room join confirmation with current status
        response_data = {
            'message': f'Joined job tracking for {job_id}',
            'job_id': job_id,
            'room': room,
            'timestamp': progress_tracker._get_current_timestamp()
        }
        
        if job_status:
            response_data['current_status'] = job_status
        
        emit('job_joined', response_data)
        
    except Exception as e:
        logger.error(f"Error joining job room: {str(e)}")
        emit('error', {
            'message': 'Failed to join job tracking',
            'error': str(e),
            'job_id': data.get('job_id') if isinstance(data, dict) else 'unknown'
        })

@socketio.on('leave_job')
def handle_leave_job(data):
    """
    Leave job room
    
    Args:
        data: Dictionary containing 'job_id'
    """
    try:
        if not isinstance(data, dict) or 'job_id' not in data:
            emit('error', {
                'message': 'Invalid leave_job request: job_id is required',
                'received_data': str(data)
            })
            return
        
        job_id = data['job_id']
        room = f"job_{job_id}"
        client_id = request.sid
        
        # Leave the job-specific room
        leave_room(room)
        
        logger.info(f"Client {client_id} left room {room}")
        
        # Send room leave confirmation
        emit('job_left', {
            'message': f'Left job tracking for {job_id}',
            'job_id': job_id,
            'room': room,
            'timestamp': progress_tracker._get_current_timestamp()
        })
        
    except Exception as e:
        logger.error(f"Error leaving job room: {str(e)}")
        emit('error', {
            'message': 'Failed to leave job tracking',
            'error': str(e),
            'job_id': data.get('job_id') if isinstance(data, dict) else 'unknown'
        })

@socketio.on('get_job_status')
def handle_get_job_status(data):
    """
    Get current status of a specific job
    
    Args:
        data: Dictionary containing 'job_id'
    """
    try:
        if not isinstance(data, dict) or 'job_id' not in data:
            emit('error', {
                'message': 'Invalid get_job_status request: job_id is required',
                'received_data': str(data)
            })
            return
        
        job_id = data['job_id']
        job_status = progress_tracker.get_job_status(job_id)
        
        if job_status is None:
            emit('job_status_response', {
                'job_id': job_id,
                'found': False,
                'message': 'Job not found or has been cleaned up',
                'timestamp': progress_tracker._get_current_timestamp()
            })
        else:
            emit('job_status_response', {
                'job_id': job_id,
                'found': True,
                'status': job_status,
                'timestamp': progress_tracker._get_current_timestamp()
            })
        
        logger.debug(f"Sent job status for {job_id}: {'found' if job_status else 'not found'}")
        
    except Exception as e:
        logger.error(f"Error getting job status: {str(e)}")
        emit('error', {
            'message': 'Failed to get job status',
            'error': str(e),
            'job_id': data.get('job_id') if isinstance(data, dict) else 'unknown'
        })

@socketio.on('list_active_jobs')
def handle_list_active_jobs():
    """
    Get list of all active jobs
    """
    try:
        active_jobs = progress_tracker.get_active_jobs()
        job_count = progress_tracker.get_job_count()
        
        emit('active_jobs_response', {
            'active_jobs': active_jobs,
            'job_count': job_count,
            'timestamp': progress_tracker._get_current_timestamp()
        })
        
        logger.debug(f"Sent active jobs list: {job_count} jobs")
        
    except Exception as e:
        logger.error(f"Error listing active jobs: {str(e)}")
        emit('error', {
            'message': 'Failed to list active jobs',
            'error': str(e)
        })

@socketio.on('ping')
def handle_ping(data=None):
    """
    Handle ping request for connection health check
    
    Args:
        data: Optional ping data
    """
    try:
        emit('pong', {
            'message': 'Connection is healthy',
            'timestamp': progress_tracker._get_current_timestamp(),
            'echo': data
        })
        
    except Exception as e:
        logger.error(f"Error handling ping: {str(e)}")
        emit('error', {
            'message': 'Ping failed',
            'error': str(e)
        })

# Add the missing _get_current_timestamp method to progress_tracker for consistency
if not hasattr(progress_tracker, '_get_current_timestamp'):
    from datetime import datetime
    def _get_current_timestamp():
        return datetime.utcnow().isoformat()
    progress_tracker._get_current_timestamp = _get_current_timestamp

# Connection limit handling
@socketio.on_error_default
def default_error_handler(e):
    """
    Default error handler for WebSocket events
    
    Args:
        e: Exception that occurred
    """
    logger.error(f"WebSocket error: {str(e)}")
    emit('error', {
        'message': 'An error occurred while processing your request',
        'error': str(e),
        'timestamp': progress_tracker._get_current_timestamp()
    })

# Optional: Rate limiting for connection events
_connection_attempts = {}

def check_rate_limit(client_id, max_attempts=10, window_seconds=60):
    """
    Simple rate limiting for WebSocket connections
    
    Args:
        client_id: Client identifier
        max_attempts: Maximum attempts in time window
        window_seconds: Time window in seconds
        
    Returns:
        bool: True if within rate limit
    """
    import time
    current_time = time.time()
    
    if client_id not in _connection_attempts:
        _connection_attempts[client_id] = []
    
    # Clean old attempts
    _connection_attempts[client_id] = [
        timestamp for timestamp in _connection_attempts[client_id]
        if current_time - timestamp < window_seconds
    ]
    
    # Check if over limit
    if len(_connection_attempts[client_id]) >= max_attempts:
        return False
    
    # Add current attempt
    _connection_attempts[client_id].append(current_time)
    return True