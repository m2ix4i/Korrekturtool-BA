"""
Error handling utilities
"""

from flask import jsonify


def create_error_response(error_type: str, message: str, status_code: int):
    """
    Create standardized error response
    
    Args:
        error_type: Type of error (e.g., 'Not found', 'Internal server error')
        message: Human-readable error message
        status_code: HTTP status code
        
    Returns:
        Tuple of (JSON response, status code)
    """
    return jsonify({
        'error': error_type,
        'message': message
    }), status_code