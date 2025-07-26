"""
Error handling utilities
"""

from flask import jsonify


class ValidationError(Exception):
    """Exception raised for file validation errors"""
    pass


class FileProcessingError(Exception):
    """Exception raised for file processing errors"""
    pass


class ProcessingError(Exception):
    """Exception raised for document processing errors"""
    pass


def create_error_response(error_type: str, message: str, status_code: int, details=None):
    """
    Create standardized error response
    
    Args:
        error_type: Type of error (e.g., 'Not found', 'Internal server error')
        message: Human-readable error message
        status_code: HTTP status code
        details: Optional additional details for debugging (dict or None)
        
    Returns:
        Tuple of (JSON response, status code)
    """
    response_data = {
        'error': error_type,
        'message': message
    }
    
    if details:
        response_data['details'] = details
    
    return jsonify(response_data), status_code