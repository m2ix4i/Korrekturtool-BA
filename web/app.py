#!/usr/bin/env python3
"""
Flask Web Application for German Bachelor Thesis Correction Tool
Provides web interface for the existing CLI-based correction system
"""

import os
import sys
import signal
import socket
from pathlib import Path
from flask import Flask, jsonify, request, g
from flask_cors import CORS
from dotenv import load_dotenv
import logging
import time
from datetime import datetime

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
from web.utils.startup_validator import validate_startup_requirements, StartupValidationError
from web.websocket import init_websocket
from web.api.processor import init_processor

# Load environment variables
load_dotenv()

def configure_logging(debug_mode: bool = False):
    """Configure application logging with development enhancements"""
    # Set log level based on environment
    log_level = logging.DEBUG if debug_mode else logging.INFO
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('web_app.log') if not debug_mode else logging.NullHandler()
        ]
    )
    
    # Set specific logger levels for development
    if debug_mode:
        logging.getLogger('werkzeug').setLevel(logging.INFO)  # Flask request logs
        logging.getLogger('socketio').setLevel(logging.INFO)
        logging.getLogger('flask_cors').setLevel(logging.WARNING)
    
    # Create logger for this module
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured - Debug mode: {debug_mode}")
    
    return logger


def register_error_handlers(app):
    """Register enhanced global error handlers with development support"""
    logger = logging.getLogger(__name__)
    
    @app.errorhandler(404)
    def not_found(error):
        logger.warning(f"404 - Resource not found: {request.url}")
        return create_error_response(
            'Not found', 
            'The requested resource was not found', 
            404,
            details={'requested_url': request.url} if app.debug else None
        )
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"500 - Internal server error: {error}", exc_info=True)
        return create_error_response(
            'Internal server error', 
            'An internal error occurred',
            500,
            details={'error_type': type(error).__name__} if app.debug else None
        )
    
    @app.errorhandler(413)
    def file_too_large(error):
        max_size = app.config.get('MAX_CONTENT_LENGTH', 'unknown')
        logger.warning(f"413 - File too large, max size: {max_size}")
        return create_error_response(
            'File too large', 
            f'The uploaded file exceeds the size limit of {max_size} bytes',
            413,
            details={'max_size_bytes': max_size} if app.debug else None
        )
    
    @app.errorhandler(ImportError)
    def import_error(error):
        logger.error(f"Import error: {error}")
        return create_error_response(
            'Configuration error',
            'A required component could not be loaded. Please check your installation.',
            503,
            details={'missing_module': str(error)} if app.debug else None
        )
    
    @app.errorhandler(StartupValidationError)
    def startup_validation_error(error):
        logger.error(f"Startup validation error: {error.message}")
        return create_error_response(
            'Configuration error',
            error.message,
            503,
            details={'fix_suggestion': error.fix_suggestion} if error.fix_suggestion else None
        )
    
    # Add request timing for development
    if app.debug:
        @app.before_request
        def before_request():
            g.start_time = time.time()
        
        @app.after_request
        def after_request(response):
            if hasattr(g, 'start_time'):
                duration = round((time.time() - g.start_time) * 1000, 2)
                response.headers['X-Response-Time'] = f"{duration}ms"
                if duration > 1000:  # Log slow requests
                    logger.warning(f"Slow request: {request.method} {request.path} took {duration}ms")
            return response

def create_app(config_class=WebConfig, validate_startup: bool = True):
    """Enhanced application factory pattern with startup validation"""
    logger = logging.getLogger(__name__)
    
    try:
        # Create Flask app
        app = Flask(__name__)
        app.config.from_object(config_class)
        
        # Configure logging first
        debug_mode = app.config.get('DEBUG', False)
        configure_logging(debug_mode)
        logger.info(f"Starting Flask application - Debug mode: {debug_mode}")
        
        # Run startup validation if requested
        if validate_startup:
            port = int(os.environ.get('PORT', 5000))
            logger.info("Running startup validation...")
            if not validate_startup_requirements(port):
                logger.error("Startup validation failed - see errors above")
                raise StartupValidationError("Critical startup validation failures detected")
            logger.info("Startup validation completed successfully")
        
        # Create necessary directories
        try:
            DirectoryManager.ensure_directories_exist(
                config_class.get_required_directories()
            )
            logger.info("Directory structure validated")
        except Exception as e:
            logger.error(f"Failed to create required directories: {e}")
            raise StartupValidationError(f"Directory creation failed: {e}")
        
        # Enable CORS for frontend integration
        cors_origins = app.config.get('CORS_ORIGINS', ['http://localhost:3000'])
        CORS(app, origins=cors_origins)
        logger.info(f"CORS configured for origins: {cors_origins}")
        
        # Register blueprints
        app.register_blueprint(main_bp)
        app.register_blueprint(api_bp)
        logger.info("Core blueprints registered")
        
        # Register test blueprint for development
        if debug_mode:
            try:
                from web.main.test_routes import test_bp
                app.register_blueprint(test_bp)
                logger.info("Development test blueprint registered")
            except ImportError as e:
                logger.warning(f"Test blueprint not available: {e}")
        
        # Register error handlers
        register_error_handlers(app)
        logger.info("Error handlers registered")
        
        # Initialize WebSocket
        try:
            socketio = init_websocket(app)
            logger.info("WebSocket support initialized")
        except Exception as e:
            logger.error(f"WebSocket initialization failed: {e}")
            raise StartupValidationError(f"WebSocket setup failed: {e}")
        
        # Initialize background processor
        try:
            init_processor(app)
            logger.info("Background processor initialized")
        except Exception as e:
            logger.warning(f"Background processor initialization failed: {e}")
            # Don't fail startup for background processor issues
        
        logger.info("Flask application created successfully")
        return app, socketio
        
    except StartupValidationError:
        # Re-raise startup validation errors
        raise
    except Exception as e:
        logger.error(f"Failed to create Flask application: {e}", exc_info=True)
        raise StartupValidationError(f"Application creation failed: {e}")

# Create the application instance (with validation by default)
try:
    app, socketio = create_app()
except StartupValidationError as e:
    print(f"❌ Application startup failed: {e.message}")
    if e.fix_suggestion:
        print(f"💡 Fix suggestion: {e.fix_suggestion}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected error during application startup: {e}")
    sys.exit(1)


def setup_signal_handlers():
    """Setup graceful shutdown signal handlers"""
    def signal_handler(signum, frame):
        print(f"\n🛑 Received signal {signum}, shutting down gracefully...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def print_startup_banner(port: int, debug: bool, host: str = "localhost"):
    """Print enhanced startup banner with development information"""
    print("\n" + "=" * 80)
    print("🎓 German Thesis Correction Tool - Web Server")
    print("=" * 80)
    print(f"🚀 Server Status: STARTING")
    print(f"📍 URL: http://{host}:{port}")
    print(f"🔧 Debug Mode: {'ON' if debug else 'OFF'}")
    print(f"⚡ WebSocket: ENABLED")
    print(f"🕒 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if debug:
        print(f"🛠️ Development Features:")
        print(f"   • Request timing headers enabled")
        print(f"   • Detailed error responses")
        print(f"   • Auto-reload on code changes")
        print(f"   • Development test routes available")
    
    print(f"🔗 Available Endpoints:")
    print(f"   • Main: http://localhost:{port}/")
    print(f"   • API Info: http://localhost:{port}/api/v1/info")
    print(f"   • Health Check: http://localhost:{port}/api/v1/health")
    
    if debug:
        print(f"   • Test Routes: http://localhost:{port}/test/")
    
    print("=" * 80)


def check_port_conflict(port: int) -> bool:
    """Check for port conflicts and suggest alternatives"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('localhost', port))
        return True
    except OSError:
        print(f"⚠️ Port {port} is already in use!")
        
        # Suggest alternative ports
        alternative_ports = [5001, 5002, 8000, 8080]
        for alt_port in alternative_ports:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('localhost', alt_port))
                print(f"💡 Alternative port available: {alt_port}")
                print(f"   Use: export PORT={alt_port} && python web/app.py")
                break
            except OSError:
                continue
        
        return False


if __name__ == '__main__':
    # Setup signal handlers for graceful shutdown
    setup_signal_handlers()
    
    # Get configuration
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    host = os.environ.get('HOST', '0.0.0.0')
    
    # Check for port conflicts
    if not check_port_conflict(port):
        print("❌ Cannot start server due to port conflict")
        sys.exit(1)
    
    # Print startup information
    print_startup_banner(port, debug, "localhost")
    
    try:
        # Start the server
        print("🔄 Starting server...")
        
        socketio.run(
            app,
            host=host,
            port=port,
            debug=debug,
            use_reloader=debug,
            log_output=debug
        )
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server startup failed: {e}")
        logging.getLogger(__name__).error(f"Server startup error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        print("👋 Server shutdown complete")