"""
API routes blueprint
"""

from flask import Blueprint, jsonify
from web.utils.api_config import APIConfig
from web.api.upload import upload_file, get_upload_info, cleanup_upload

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

# File upload endpoints
@api_bp.route('/upload', methods=['POST'])
def upload_docx_file():
    """Handle DOCX file upload with validation"""
    return upload_file()

@api_bp.route('/upload/info', methods=['GET'])
def get_upload_configuration():
    """Get upload limits and configuration details"""
    return get_upload_info()

@api_bp.route('/upload/<file_id>/cleanup', methods=['DELETE'])
def cleanup_uploaded_docx_file(file_id):
    """Clean up uploaded DOCX file by ID"""
    return cleanup_upload(file_id)