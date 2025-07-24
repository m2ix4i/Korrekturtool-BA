"""
API routes blueprint
"""

from flask import Blueprint, jsonify

# Create API blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

@api_bp.route('/info')
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