"""
WebSocket initialization helper following Single Responsibility Principle
Handles ONLY WebSocket setup and configuration
"""

import logging
from flask import Flask
from flask_socketio import SocketIO

logger = logging.getLogger(__name__)


class WebSocketInitializer:
    """
    WebSocket initializer following Single Responsibility Principle
    
    ONLY responsible for:
    - Configuring SocketIO instance
    - Registering event handlers
    - Setting up WebSocket middleware
    """
    
    def __init__(self):
        self.socketio = SocketIO()
        logger.info("WebSocketInitializer created")
    
    def initialize_with_app(self, app: Flask) -> SocketIO:
        """Initialize WebSocket with Flask application"""
        try:
            self._configure_socketio(app)
            self._register_event_handlers()
            
            logger.info("WebSocket initialized successfully")
            logger.info("WebSocket event handlers registered")
            return self.socketio
            
        except Exception as e:
            logger.error(f"Failed to initialize WebSocket: {str(e)}")
            raise
    
    def _configure_socketio(self, app: Flask) -> None:
        """Configure SocketIO with app settings"""
        cors_origins = app.config.get('CORS_ORIGINS', ['http://localhost:3000'])
        
        self.socketio.init_app(
            app,
            cors_allowed_origins=cors_origins,
            logger=app.config.get('DEBUG', False),
            engineio_logger=app.config.get('DEBUG', False),
            ping_timeout=app.config.get('WEBSOCKET_PING_TIMEOUT', 60),
            ping_interval=app.config.get('WEBSOCKET_PING_INTERVAL', 25)
        )
        
        logger.info(f"SocketIO configured with CORS origins: {cors_origins}")
    
    def _register_event_handlers(self) -> None:
        """Register WebSocket event handlers"""
        from . import progress  # Import to register handlers
        logger.debug("Progress event handlers imported")
    
    def get_socketio(self) -> SocketIO:
        """Get configured SocketIO instance"""
        return self.socketio


# Singleton instance for the application
_initializer = None

def get_websocket_initializer() -> WebSocketInitializer:
    """Get WebSocket initializer instance"""
    global _initializer
    if _initializer is None:
        _initializer = WebSocketInitializer()
    return _initializer


def initialize_websocket(app: Flask) -> SocketIO:
    """Initialize WebSocket with Flask app (convenience function)"""
    initializer = get_websocket_initializer()
    return initializer.initialize_with_app(app)