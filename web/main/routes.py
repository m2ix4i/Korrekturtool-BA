"""
Main application routes blueprint
"""

from flask import Blueprint, jsonify, send_from_directory
from web.utils.paths import PathHelper

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
    return send_from_directory(PathHelper.get_static_directory(), 'index.html')

@main_bp.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files"""
    return send_from_directory(PathHelper.get_static_directory(), filename)