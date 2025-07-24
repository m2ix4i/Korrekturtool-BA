"""
Standardized API error response builder
Reduces duplication and ensures consistent error responses
"""

from flask import jsonify
from typing import Tuple


class APIErrorBuilder:
    """Standardized error response builder following DRY principle"""
    
    @staticmethod
    def validation_error(message: str) -> Tuple:
        """Create validation error response"""
        return jsonify({
            'success': False,
            'error': 'validation_error',
            'message': message
        }), 400
    
    @staticmethod
    def validation_failed(message: str) -> Tuple:
        """Create validation failed response"""
        return jsonify({
            'success': False,
            'error': 'validation_failed',
            'message': message
        }), 400
    
    @staticmethod
    def processing_error(message: str) -> Tuple:
        """Create processing error response"""
        return jsonify({
            'success': False,
            'error': 'processing_error',
            'message': message
        }), 500
    
    @staticmethod
    def save_failed(message: str = "Failed to save uploaded file") -> Tuple:
        """Create save failed error response"""
        return jsonify({
            'success': False,
            'error': 'save_failed',
            'message': message
        }), 500
    
    @staticmethod
    def internal_error(message: str = "An internal error occurred") -> Tuple:
        """Create internal error response"""
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': message
        }), 500
    
    @staticmethod
    def file_not_found(message: str = "File not found or already cleaned up") -> Tuple:
        """Create file not found error response"""
        return jsonify({
            'success': False,
            'error': 'file_not_found',
            'message': message
        }), 404
    
    @staticmethod
    def cleanup_error(message: str = "Failed to clean up file") -> Tuple:
        """Create cleanup error response"""
        return jsonify({
            'success': False,
            'error': 'cleanup_error',
            'message': message
        }), 500
    
    @staticmethod
    def no_file_provided(message: str = "No file provided") -> Tuple:
        """Create no file provided error response"""
        return jsonify({
            'success': False,
            'error': 'no_file_provided',
            'message': message
        }), 400
    
    @staticmethod
    def success_response(data: dict) -> Tuple:
        """Create standardized success response"""
        response_data = {'success': True}
        response_data.update(data)
        return jsonify(response_data), 200
    
    @staticmethod
    def not_found_error(message: str = "Resource not found") -> Tuple:
        """Create not found error response"""
        return jsonify({
            'success': False,
            'error': 'not_found',
            'message': message
        }), 404