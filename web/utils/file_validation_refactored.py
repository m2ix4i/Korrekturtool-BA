"""
Refactored file validation using focused validator classes
Following Sandi Metz principles for better separation of concerns
"""

import os
import logging
from typing import Tuple, Optional
from werkzeug.datastructures import FileStorage

from .validators import (
    FileExtensionValidator,
    FileSizeValidator,
    MimeTypeValidator,
    DocxStructureValidator,
    SecureFilenameGenerator
)

logger = logging.getLogger(__name__)


def validate_upload_file(file: FileStorage, max_size: int) -> Tuple[bool, str, Optional[dict]]:
    """
    Comprehensive file validation using focused validators
    
    Args:
        file: Werkzeug FileStorage object
        max_size: Maximum file size in bytes
        
    Returns:
        Tuple of (is_valid, error_message, file_info)
    """
    try:
        # Validate file presence
        is_valid, error_msg = _validate_file_presence(file)
        if not is_valid:
            return False, error_msg, None
        
        # Validate file extension
        is_valid, error_msg = _validate_file_extension(file.filename)
        if not is_valid:
            return False, error_msg, None
        
        # Validate file size
        file_size = _get_file_size(file)
        is_valid, error_msg = _validate_file_size(file_size, max_size)
        if not is_valid:
            return False, error_msg, None
        
        # Validate MIME type
        is_valid, error_msg = _validate_file_type(file)
        if not is_valid:
            return False, error_msg, None
        
        # Validate DOCX structure
        is_valid, error_msg = _validate_docx_structure(file)
        if not is_valid:
            return False, error_msg, None
        
        # Create file info
        file_info = _create_file_info(file, file_size)
        
        logger.info(f"File validation successful: {file.filename} ({file_size} bytes)")
        return True, "File validation successful", file_info
        
    except Exception as e:
        logger.error(f"Unexpected error during file validation: {str(e)}")
        return False, "Internal error during file validation", None


def _validate_file_presence(file: FileStorage) -> Tuple[bool, str]:
    """Validate file is present in request"""
    if not file or not file.filename:
        return False, "No file provided"
    return True, ""


def _validate_file_extension(filename: str) -> Tuple[bool, str]:
    """Validate file extension using focused validator"""
    validator = FileExtensionValidator({'docx'})
    return validator.validate(filename)


def _get_file_size(file: FileStorage) -> int:
    """Get file size by seeking to end"""
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    return file_size


def _validate_file_size(file_size: int, max_size: int) -> Tuple[bool, str]:
    """Validate file size using focused validator"""
    validator = FileSizeValidator()
    return validator.validate(file_size, max_size)


def _validate_file_type(file: FileStorage) -> Tuple[bool, str]:
    """Validate MIME type using focused validator"""
    validator = MimeTypeValidator()
    return validator.validate(file.stream)


def _validate_docx_structure(file: FileStorage) -> Tuple[bool, str]:
    """Validate DOCX structure using focused validator"""
    validator = DocxStructureValidator()
    return validator.validate(file.stream)


def _create_file_info(file: FileStorage, file_size: int) -> dict:
    """Create file metadata info dict"""
    generator = SecureFilenameGenerator()
    
    return {
        'original_filename': generator.sanitize_display_name(file.filename),
        'size': file_size,
        'secure_filename': generator.generate()
    }


def cleanup_file(file_path: str) -> bool:
    """Safely remove a file"""
    try:
        if os.path.exists(file_path):
            os.unlink(file_path)
            logger.info(f"File cleaned up: {file_path}")
            return True
        return False
    except Exception as e:
        logger.error(f"Error cleaning up file {file_path}: {str(e)}")
        return False