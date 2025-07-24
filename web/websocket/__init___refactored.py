"""
Refactored WebSocket initialization following Sandi Metz principles
Uses helper classes for better separation of concerns
"""

import logging
from flask import Flask
from flask_socketio import SocketIO
from .initialization_helper import initialize_websocket, get_websocket_initializer

logger = logging.getLogger(__name__)

# Initialize SocketIO instance through helper
socketio = None

def init_websocket(app: Flask) -> SocketIO:
    """
    Initialize WebSocket with Flask application using helper
    
    Args:
        app: Flask application instance
        
    Returns:
        SocketIO: Configured SocketIO instance
    """
    global socketio
    socketio = initialize_websocket(app)
    return socketio


def get_socketio() -> SocketIO:
    """
    Get the SocketIO instance
    
    Returns:
        SocketIO: The configured SocketIO instance
    """
    global socketio
    if socketio is None:
        initializer = get_websocket_initializer()
        socketio = initializer.get_socketio()
    return socketio