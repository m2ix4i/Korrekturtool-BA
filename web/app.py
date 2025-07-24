#!/usr/bin/env python3
"""
Flask Web Application for German Bachelor Thesis Correction Tool
Provides web interface for the existing CLI-based correction system
"""

import os
import sys
from pathlib import Path
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import logging

# Add project root to path for imports (only when running directly)
if __name__ == '__main__':
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

# Import configuration and blueprints
from web.config import WebConfig
from web.main.routes import main_bp
from web.api.routes import api_bp
from web.utils.errors import create_error_response
from web.utils.directories import DirectoryManager
from web.websocket import init_websocket

# Load environment variables
load_dotenv()

def configure_logging():
    """Configure application logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def register_error_handlers(app):
    """Register global error handlers"""
    @app.errorhandler(404)
    def not_found(error):
        return create_error_response('Not found', 'The requested resource was not found', 404)
    
    @app.errorhandler(500)
    def internal_error(error):
        return create_error_response('Internal server error', 'An internal error occurred', 500)
    
    @app.errorhandler(413)
    def file_too_large(error):
        return create_error_response('File too large', 'The uploaded file exceeds the size limit', 413)

def create_app(config_class=WebConfig):
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Create necessary directories
    DirectoryManager.ensure_directories_exist(
        config_class.get_required_directories()
    )
    
    # Configure logging
    configure_logging()
    
    # Enable CORS for frontend integration
    CORS(app, origins=app.config.get('CORS_ORIGINS', ['http://localhost:3000']))
    
    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Initialize WebSocket
    socketio = init_websocket(app)
    
    return app, socketio

# Create the application instance
app, socketio = create_app()

if __name__ == '__main__':
    # Development server
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    print(f"🚀 Starting German Thesis Correction Tool Web Server with WebSocket support")
    print(f"📍 Server will be available at: http://localhost:{port}")
    print(f"🔧 Debug mode: {'ON' if debug else 'OFF'}")
    print(f"⚡ WebSocket support: ENABLED")
    
    socketio.run(
        app,
        host='0.0.0.0',
        port=port,
        debug=debug,
        use_reloader=debug
    )