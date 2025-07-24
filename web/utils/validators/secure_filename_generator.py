"""
Secure filename generation utilities
"""

import os
import uuid
from pathlib import Path


class SecureFilenameGenerator:
    """Generates secure filenames to prevent path traversal"""
    
    @staticmethod
    def generate() -> str:
        """Generate a secure UUID-based filename"""
        secure_name = str(uuid.uuid4())
        return f"{secure_name}.docx"
    
    @staticmethod
    def sanitize_display_name(filename: str, max_length: int = 255) -> str:
        """Sanitize filename for safe display (not for storage)"""
        if not filename:
            return "unnamed_file.docx"
        
        # Remove path components
        filename = os.path.basename(filename)
        
        # Limit length
        if len(filename) > max_length:
            name, ext = os.path.splitext(filename)
            filename = name[:max_length-len(ext)] + ext
        
        return filename