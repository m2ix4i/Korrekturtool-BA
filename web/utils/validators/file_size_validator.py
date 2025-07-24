"""
File size validation
"""

from typing import Tuple
from .base_validator import BaseValidator


class FileSizeValidator(BaseValidator):
    """Validates file size limits"""
    
    def validate(self, file_size: int, max_size: int) -> Tuple[bool, str]:
        """Validate file size is within limits"""
        if file_size <= 0:
            return False, "File is empty"
        
        if file_size > max_size:
            max_size_mb = max_size // (1024 * 1024)
            return False, f"File too large. Maximum size: {max_size_mb}MB"
        
        return True, ""