"""
DOCX structure validation
"""

import logging
import tempfile
import os
from zipfile import ZipFile, BadZipFile
from typing import Tuple
from .base_validator import BaseValidator

logger = logging.getLogger(__name__)


class DocxStructureValidator(BaseValidator):
    """Validates DOCX internal structure"""
    
    def __init__(self):
        self.required_files = {
            '[Content_Types].xml',
            '_rels/.rels',
            'word/document.xml'
        }
    
    def validate(self, file_stream) -> Tuple[bool, str]:
        """Validate DOCX file structure"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as temp_file:
            try:
                # Save file stream to temporary file
                file_stream.seek(0)
                temp_file.write(file_stream.read())
                temp_file.flush()
                
                # Validate structure
                is_valid, error_msg = self._validate_zip_structure(temp_file.name)
                return is_valid, error_msg
                
            finally:
                # Clean up temp file
                file_stream.seek(0)
                if os.path.exists(temp_file.name):
                    os.unlink(temp_file.name)
    
    def _validate_zip_structure(self, file_path: str) -> Tuple[bool, str]:
        """Validate internal ZIP structure of DOCX"""
        try:
            with ZipFile(file_path, 'r') as zip_file:
                zip_contents = set(zip_file.namelist())
                
                # Check required files
                missing_files = self.required_files - zip_contents
                if missing_files:
                    logger.warning(f"Missing required DOCX files: {missing_files}")
                    return False, "Invalid DOCX file structure"
                
                # Validate document.xml content
                if not self._validate_document_xml(zip_file):
                    return False, "Invalid DOCX file structure"
                
                return True, ""
                
        except BadZipFile:
            logger.warning("File is not a valid ZIP/DOCX file")
            return False, "Invalid DOCX file structure"
        except Exception as e:
            logger.error(f"Error validating DOCX structure: {str(e)}")
            return False, "Unable to validate DOCX structure"
    
    def _validate_document_xml(self, zip_file: ZipFile) -> bool:
        """Validate document.xml exists and is not empty"""
        try:
            document_xml = zip_file.read('word/document.xml')
            return len(document_xml) > 0
        except KeyError:
            logger.warning("Cannot read document.xml from DOCX file")
            return False