"""
API routes blueprint
"""

from flask import Blueprint, jsonify, request, send_file
from web.utils.api_config import APIConfig
from web.api.upload import upload_file, get_upload_info, cleanup_upload
from web.api.processor import process_document, get_processing_status, download_result
from web.api.health import get_health_status, get_basic_info

# Create API blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

@api_bp.route('/info')
def api_info():
    """Enhanced API information endpoint with health summary"""
    return get_basic_info()

@api_bp.route('/health')
def health_check():
    """Comprehensive health check endpoint for localhost environment validation"""
    return get_health_status()

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

# Document processing endpoints
@api_bp.route('/process', methods=['POST'])
def process_docx_document():
    """Process uploaded DOCX document with AI analysis"""
    return process_document()

@api_bp.route('/status/<job_id>', methods=['GET'])
def get_job_status(job_id):
    """Get processing status for a specific job ID"""
    return get_processing_status(job_id)

@api_bp.route('/download/<file_id>', methods=['GET'])
def download_processed_file(file_id):
    """Download processed DOCX file"""
    return download_result(file_id)