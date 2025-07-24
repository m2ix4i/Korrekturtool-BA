"""
Main application routes blueprint
"""

from pathlib import Path
from flask import Blueprint, jsonify, send_from_directory

# Create main blueprint
main_bp = Blueprint('main', __name__)

@main_bp.route('/health')
def health_check():
    """Basic health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'German Thesis Correction Tool Web API',
        'version': '1.0.0'
    })

@main_bp.route('/')
def index():
    """Serve the main application page"""
    static_dir = Path(__file__).parent.parent / 'static'
    return send_from_directory(static_dir, 'index.html')

@main_bp.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files"""
    static_dir = Path(__file__).parent.parent / 'static'
    return send_from_directory(static_dir, filename)