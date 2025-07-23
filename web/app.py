#!/usr/bin/env python3
"""
Flask Web Application for German Bachelor Thesis Correction Tool
Provides web interface for the existing CLI-based correction system
"""

import os
import sys
from pathlib import Path
from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import logging

# Add parent directory to path to import existing modules
sys.path.append(str(Path(__file__).parent.parent))

# Import configuration
from web.config import WebConfig

# Load environment variables
load_dotenv()

def create_app(config_class=WebConfig):
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Enable CORS for frontend integration
    CORS(app, origins=app.config.get('CORS_ORIGINS', ['http://localhost:3000']))
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        """Basic health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'service': 'German Thesis Correction Tool Web API',
            'version': '1.0.0'
        })
    
    # API routes will be registered here
    @app.route('/api/v1/info')
    def api_info():
        """API information endpoint"""
        return jsonify({
            'name': 'German Thesis Correction Tool API',
            'version': '1.0.0',
            'description': 'Web API for automated German thesis correction with AI analysis',
            'endpoints': {
                'health': '/health',
                'info': '/api/v1/info',
                'upload': '/api/v1/upload (coming soon)',
                'process': '/api/v1/process (coming soon)',
                'status': '/api/v1/status/{job_id} (coming soon)',
                'download': '/api/v1/download/{file_id} (coming soon)'
            }
        })
    
    # Serve static files
    @app.route('/')
    def index():
        """Serve the main application page"""
        return send_from_directory('static', 'index.html')
    
    @app.route('/static/<path:filename>')
    def static_files(filename):
        """Serve static files"""
        return send_from_directory('static', filename)
    
    # Global error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found', 'message': 'The requested resource was not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error', 'message': 'An internal error occurred'}), 500
    
    @app.errorhandler(413)
    def file_too_large(error):
        return jsonify({'error': 'File too large', 'message': 'The uploaded file exceeds the size limit'}), 413
    
    return app

# Create the application instance
app = create_app()

if __name__ == '__main__':
    # Development server
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    print(f"🚀 Starting German Thesis Correction Tool Web Server")
    print(f"📍 Server will be available at: http://localhost:{port}")
    print(f"🔧 Debug mode: {'ON' if debug else 'OFF'}")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug,
        use_reloader=debug
    )