"""
Request validation following Single Responsibility Principle
Handles ONLY request data validation and extraction
"""

import logging
from typing import Dict, Any, List
from flask import request

from web.utils.errors import ValidationError

logger = logging.getLogger(__name__)


class ProcessingRequestValidator:
    """
    Request validator following Single Responsibility Principle
    
    ONLY responsible for:
    - Validating request format and data
    - Extracting and normalizing request parameters
    - Ensuring data integrity
    """
    
    VALID_MODES = ['complete', 'optimized']
    VALID_CATEGORIES = ['grammar', 'style', 'clarity', 'academic']
    
    def extract_and_validate(self) -> Dict[str, Any]:
        """Extract and validate processing request"""
        self._validate_request_format()
        data = request.get_json()
        
        return {
            'file_id': self._validate_file_id(data),
            'processing_mode': self._validate_processing_mode(data),
            'categories': self._validate_categories(data),
            'output_filename': data.get('output_filename')
        }
    
    def _validate_request_format(self) -> None:
        """Validate basic request format"""
        if not request.is_json:
            raise ValidationError('Request must be JSON')
    
    def _validate_file_id(self, data: Dict[str, Any]) -> str:
        """Validate file_id parameter"""
        file_id = data.get('file_id')
        if not file_id:
            raise ValidationError('file_id is required')
        return file_id
    
    def _validate_processing_mode(self, data: Dict[str, Any]) -> str:
        """Validate processing_mode parameter"""
        processing_mode = data.get('processing_mode', 'complete')
        if processing_mode not in self.VALID_MODES:
            raise ValidationError(f'processing_mode must be one of: {self.VALID_MODES}')
        return processing_mode
    
    def _validate_categories(self, data: Dict[str, Any]) -> List[str]:
        """Validate categories parameter"""
        categories = data.get('categories', self.VALID_CATEGORIES)
        
        if not isinstance(categories, list):
            raise ValidationError('categories must be a list')
        
        invalid_categories = [cat for cat in categories if cat not in self.VALID_CATEGORIES]
        if invalid_categories:
            raise ValidationError(f'Invalid categories: {invalid_categories}')
        
        return categories