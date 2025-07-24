"""
File upload API endpoint
Handles secure DOCX file uploads with comprehensive validation
"""

import os
import logging
from flask import request, current_app
from pathlib import Path

from web.utils.file_validation_refactored import validate_upload_file, cleanup_file
from web.utils.errors import ValidationError, FileProcessingError
from web.utils.error_builder import APIErrorBuilder

# Configure logging
logger = logging.getLogger(__name__)

def upload_file():
    """Handle file upload POST request following SRP"""
    try:
        file = _extract_file_from_request()
        file_info = _validate_file(file)
        saved_file_path = _save_file(file, file_info)
        return _create_success_response(file_info, saved_file_path)
    except ValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        return APIErrorBuilder.validation_error(str(e))
    except FileProcessingError as e:
        logger.error(f"File processing error: {str(e)}")
        return APIErrorBuilder.processing_error(str(e))
    except Exception as e:
        logger.error(f"Unexpected error during file upload: {str(e)}")
        return APIErrorBuilder.internal_error("An internal error occurred during file upload")

def _extract_file_from_request():
    """Extract file from request with validation"""
    if 'file' not in request.files:
        raise ValidationError('Please select a file to upload')
    return request.files['file']

def _validate_file(file):
    """Validate uploaded file and return file info"""
    max_size = current_app.config.get('MAX_CONTENT_LENGTH', 50 * 1024 * 1024)
    is_valid, error_message, file_info = validate_upload_file(file, max_size)
    
    if not is_valid:
        logger.warning(f"File validation failed: {error_message}")
        raise ValidationError(error_message)
    
    return file_info

def _save_file(file, file_info):
    """Save file to upload directory"""
    upload_dir = Path(current_app.config.get('UPLOAD_FOLDER', 'uploads'))
    upload_dir.mkdir(exist_ok=True)
    
    file_path = upload_dir / file_info['secure_filename']
    
    try:
        file.save(str(file_path))
        logger.info(f"File saved successfully: {file_path}")
        return file_path
    except Exception as e:
        if file_path.exists():
            cleanup_file(str(file_path))
        logger.error(f"Error saving file: {str(e)}")
        raise FileProcessingError('Failed to save uploaded file')

def _create_success_response(file_info, file_path):
    """Create standardized success response"""
    response_data = {
        'file_id': file_info['secure_filename'].replace('.docx', ''),
        'filename': file_info['original_filename'],
        'secure_filename': file_info['secure_filename'],
        'size': file_info['size'],
        'size_mb': round(file_info['size'] / (1024 * 1024), 2),
        'message': 'File uploaded successfully',
        'file_path': str(file_path)
    }
    
    logger.info(f"Upload successful: {file_info['original_filename']} -> {file_info['secure_filename']}")
    return APIErrorBuilder.success_response(response_data)

def get_upload_info():
    """Get information about upload configuration and limits"""
    try:
        max_size = current_app.config.get('MAX_CONTENT_LENGTH', 50 * 1024 * 1024)
        
        config_data = {
            'upload_config': {
                'max_file_size': max_size,
                'max_file_size_mb': round(max_size / (1024 * 1024), 2),
                'allowed_extensions': list(current_app.config.get('ALLOWED_EXTENSIONS', {'docx'})),
                'upload_endpoint': '/api/v1/upload',
                'supported_formats': ['Microsoft Word (.docx)']
            }
        }
        
        return APIErrorBuilder.success_response(config_data)
        
    except Exception as e:
        logger.error(f"Error getting upload info: {str(e)}")
        return APIErrorBuilder.internal_error('Failed to retrieve upload configuration')

def cleanup_upload(file_id):
    """Clean up uploaded file by file ID"""
    try:
        file_path = _get_file_path(file_id)
        
        if cleanup_file(str(file_path)):
            logger.info(f"File cleaned up successfully: {file_path}")
            return APIErrorBuilder.success_response({'message': 'File cleaned up successfully'})
        else:
            return APIErrorBuilder.file_not_found()
            
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")
        return APIErrorBuilder.cleanup_error()

def _get_file_path(file_id):
    """Reconstruct file path from file ID"""
    upload_dir = Path(current_app.config.get('UPLOAD_FOLDER', 'uploads'))
    return upload_dir / f"{file_id}.docx"