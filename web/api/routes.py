"""
API routes blueprint
"""

from flask import Blueprint, jsonify
from web.utils.api_config import APIConfig

# Create API blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

@api_bp.route('/info')
def api_info():
    """API information endpoint"""
    return jsonify({
        'name': APIConfig.API_NAME,
        'version': APIConfig.API_VERSION,
        'description': APIConfig.API_DESCRIPTION,
        'endpoints': APIConfig.ENDPOINTS
    })