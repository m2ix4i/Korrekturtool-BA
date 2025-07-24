"""
File extension validation
"""

import os
from pathlib import Path
from typing import Tuple
from .base_validator import BaseValidator


class FileExtensionValidator(BaseValidator):
    """Validates file extensions"""
    
    def __init__(self, allowed_extensions: set = None):
        self.allowed_extensions = allowed_extensions or {'docx'}
    
    def validate(self, filename: str) -> Tuple[bool, str]:
        """Validate file extension is allowed"""
        if not filename:
            return False, "No filename provided"
        
        extension = Path(filename).suffix.lower().lstrip('.')
        
        if extension not in self.allowed_extensions:
            return False, f"Invalid file type. Only {', '.join(self.allowed_extensions)} files are allowed"
        
        return True, ""