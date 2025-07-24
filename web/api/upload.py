"""
File upload API endpoint
Handles secure DOCX file uploads with comprehensive validation
"""

import os
import logging
from flask import request, jsonify, current_app
from werkzeug.utils import secure_filename
from pathlib import Path

from web.utils.file_validation import validate_upload_file, cleanup_file
from web.utils.errors import ValidationError, FileProcessingError

# Configure logging
logger = logging.getLogger(__name__)

def upload_file():
    """
    Handle file upload POST request
    
    Accepts multipart/form-data with 'file' field containing DOCX document
    
    Returns:
        JSON response with file metadata or error details
    """
    try:
        # Check if file is in request
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided',
                'message': 'Please select a file to upload'
            }), 400
        
        file = request.files['file']
        
        # Validate file
        max_size = current_app.config.get('MAX_CONTENT_LENGTH', 50 * 1024 * 1024)
        is_valid, error_message, file_info = validate_upload_file(file, max_size)
        
        if not is_valid:
            logger.warning(f"File validation failed: {error_message}")
            return jsonify({
                'success': False,
                'error': 'validation_failed',
                'message': error_message
            }), 400
        
        # Create upload directory if it doesn't exist
        upload_dir = Path(current_app.config.get('UPLOAD_FOLDER', 'uploads'))
        upload_dir.mkdir(exist_ok=True)
        
        # Save file with secure filename
        file_path = upload_dir / file_info['secure_filename']
        
        try:
            file.save(str(file_path))
            logger.info(f"File saved successfully: {file_path}")
            
            # Return success response with file metadata
            response_data = {
                'success': True,
                'file_id': file_info['secure_filename'].replace('.docx', ''),
                'filename': file_info['original_filename'],
                'secure_filename': file_info['secure_filename'],
                'size': file_info['size'],
                'size_mb': round(file_info['size'] / (1024 * 1024), 2),
                'message': 'File uploaded successfully',
                'file_path': str(file_path)
            }
            
            logger.info(f"Upload successful: {file_info['original_filename']} -> {file_info['secure_filename']}")
            return jsonify(response_data), 200
            
        except Exception as e:
            # Clean up file if save failed
            if file_path.exists():
                cleanup_file(str(file_path))
            
            logger.error(f"Error saving file: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'save_failed',
                'message': 'Failed to save uploaded file'
            }), 500
    
    except ValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'validation_error',
            'message': str(e)
        }), 400
    
    except FileProcessingError as e:
        logger.error(f"File processing error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'processing_error', 
            'message': str(e)
        }), 500
    
    except Exception as e:
        logger.error(f"Unexpected error during file upload: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': 'An internal error occurred during file upload'
        }), 500

def get_upload_info():
    """
    Get information about upload configuration and limits
    
    Returns:
        JSON response with upload configuration details
    """
    try:
        max_size = current_app.config.get('MAX_CONTENT_LENGTH', 50 * 1024 * 1024)
        
        return jsonify({
            'success': True,
            'upload_config': {
                'max_file_size': max_size,
                'max_file_size_mb': round(max_size / (1024 * 1024), 2),
                'allowed_extensions': list(current_app.config.get('ALLOWED_EXTENSIONS', {'docx'})),
                'upload_endpoint': '/api/v1/upload',
                'supported_formats': ['Microsoft Word (.docx)']
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting upload info: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': 'Failed to retrieve upload configuration'
        }), 500

def cleanup_upload(file_id):
    """
    Clean up uploaded file by file ID
    
    Args:
        file_id: File ID (UUID without extension)
        
    Returns:
        JSON response confirming cleanup
    """
    try:
        # Reconstruct file path
        upload_dir = Path(current_app.config.get('UPLOAD_FOLDER', 'uploads'))
        file_path = upload_dir / f"{file_id}.docx"
        
        if cleanup_file(str(file_path)):
            logger.info(f"File cleaned up successfully: {file_path}")
            return jsonify({
                'success': True,
                'message': 'File cleaned up successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'file_not_found',
                'message': 'File not found or already cleaned up'
            }), 404
            
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'cleanup_error',
            'message': 'Failed to clean up file'
        }), 500