"""
WebSocket initialization and configuration for progress tracking
"""

from flask_socketio import SocketIO
import logging

# Initialize SocketIO instance
socketio = SocketIO()

logger = logging.getLogger(__name__)

def init_websocket(app):
    """
    Initialize WebSocket with Flask application
    
    Args:
        app: Flask application instance
        
    Returns:
        SocketIO: Configured SocketIO instance
    """
    try:
        # Get CORS origins from app config
        cors_origins = app.config.get('CORS_ORIGINS', ['http://localhost:3000'])
        
        # Initialize SocketIO with the app
        socketio.init_app(
            app,
            cors_allowed_origins=cors_origins,
            logger=app.config.get('DEBUG', False),
            engineio_logger=app.config.get('DEBUG', False),
            ping_timeout=app.config.get('WEBSOCKET_PING_TIMEOUT', 60),
            ping_interval=app.config.get('WEBSOCKET_PING_INTERVAL', 25)
        )
        
        logger.info(f"WebSocket initialized with CORS origins: {cors_origins}")
        return socketio
        
    except Exception as e:
        logger.error(f"Failed to initialize WebSocket: {str(e)}")
        raise

def get_socketio():
    """
    Get the SocketIO instance
    
    Returns:
        SocketIO: The configured SocketIO instance
    """
    return socketio