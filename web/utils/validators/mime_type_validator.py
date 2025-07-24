"""
MIME type validation with Strategy pattern implementation
"""

import logging
from typing import Tuple
from abc import ABC, abstractmethod
from .base_validator import BaseValidator

# Try to import magic, fallback if not available
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
    logging.warning("python-magic not available, file type validation will use basic checks only")

logger = logging.getLogger(__name__)


class MimeDetectionStrategy(ABC):
    """Strategy interface for MIME type detection"""
    
    @abstractmethod
    def detect(self, file_stream) -> str:
        """Detect MIME type from file stream"""
        pass


class MagicDetector(MimeDetectionStrategy):
    """MIME type detection using python-magic"""
    
    def __init__(self):
        self.allowed_mime_types = {
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        }
    
    def detect(self, file_stream) -> str:
        """Detect MIME type using magic library"""
        current_pos = file_stream.tell()
        file_stream.seek(0)
        file_header = file_stream.read(2048)
        file_stream.seek(current_pos)
        
        return magic.from_buffer(file_header, mime=True)


class ZipSignatureDetector(MimeDetectionStrategy):
    """Fallback MIME type detection using ZIP signature"""
    
    def detect(self, file_stream) -> str:
        """Detect file type using ZIP signature"""
        current_pos = file_stream.tell()
        file_stream.seek(0)
        header = file_stream.read(4)
        file_stream.seek(current_pos)
        
        # Check for ZIP signature (DOCX files are ZIP archives)
        if header == b'PK\x03\x04':
            return 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        
        return 'unknown'


class MimeTypeValidator(BaseValidator):
    """Validates MIME type using Strategy pattern"""
    
    def __init__(self):
        self.allowed_mime_types = {
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        }
        self.detector = self._create_detector()
    
    def _create_detector(self) -> MimeDetectionStrategy:
        """Create appropriate MIME detector based on availability"""
        if MAGIC_AVAILABLE:
            return MagicDetector()
        else:
            return ZipSignatureDetector()
    
    def validate(self, file_stream) -> Tuple[bool, str]:
        """Validate file MIME type"""
        try:
            mime_type = self.detector.detect(file_stream)
            logger.debug(f"Detected MIME type: {mime_type}")
            
            if mime_type in self.allowed_mime_types:
                return True, ""
            else:
                return False, "Invalid file format. File does not appear to be a valid DOCX document"
                
        except Exception as e:
            logger.error(f"Error detecting file type: {str(e)}")
            return False, "Unable to validate file type"