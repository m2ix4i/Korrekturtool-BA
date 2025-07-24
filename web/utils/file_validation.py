"""
File validation utilities for secure file upload handling
Provides comprehensive validation for DOCX files with security considerations
"""

import os
import uuid
import tempfile
import logging
from pathlib import Path
from typing import Tuple, Optional
from zipfile import ZipFile, BadZipFile
from werkzeug.datastructures import FileStorage

# Try to import magic, fallback if not available
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
    logging.warning("python-magic not available, file type validation will use basic checks only")

# Configure logging
logger = logging.getLogger(__name__)

# Security constants
MAX_FILENAME_LENGTH = 255
ALLOWED_EXTENSIONS = {'docx'}
ALLOWED_MIME_TYPES = {
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
}

# DOCX file structure requirements
REQUIRED_DOCX_FILES = {
    '[Content_Types].xml',
    '_rels/.rels',
    'word/document.xml'
}

class FileValidationError(Exception):
    """Custom exception for file validation errors"""
    pass

def validate_file_extension(filename: str) -> bool:
    """
    Validate file extension is allowed
    
    Args:
        filename: Name of the file to validate
        
    Returns:
        bool: True if extension is allowed, False otherwise
    """
    if not filename:
        return False
    
    # Get file extension (case insensitive)
    extension = Path(filename).suffix.lower().lstrip('.')
    return extension in ALLOWED_EXTENSIONS

def validate_file_type_magic(file_stream) -> bool:
    """
    Validate file type using magic numbers (not just extension)
    
    Args:
        file_stream: File-like object to validate
        
    Returns:
        bool: True if file type is valid DOCX, False otherwise
    """
    try:
        if not MAGIC_AVAILABLE:
            # Fallback to basic ZIP signature check
            current_pos = file_stream.tell()
            file_stream.seek(0)
            header = file_stream.read(4)
            file_stream.seek(current_pos)
            
            # Check for ZIP signature (DOCX files are ZIP archives)
            return header == b'PK\x03\x04'
        
        # Save current position
        current_pos = file_stream.tell()
        
        # Read first 2048 bytes for magic number detection
        file_stream.seek(0)
        file_header = file_stream.read(2048)
        
        # Restore position
        file_stream.seek(current_pos)
        
        # Use python-magic to detect MIME type
        mime_type = magic.from_buffer(file_header, mime=True)
        
        logger.debug(f"Detected MIME type: {mime_type}")
        return mime_type in ALLOWED_MIME_TYPES
        
    except Exception as e:
        logger.error(f"Error detecting file type: {str(e)}")
        return False

def validate_docx_structure(file_path: str) -> bool:
    """
    Validate DOCX file structure by checking internal ZIP structure
    
    Args:
        file_path: Path to the file to validate
        
    Returns:
        bool: True if DOCX structure is valid, False otherwise
    """
    try:
        with ZipFile(file_path, 'r') as zip_file:
            # Get list of files in the ZIP
            zip_contents = set(zip_file.namelist())
            
            # Check if required DOCX files are present
            missing_files = REQUIRED_DOCX_FILES - zip_contents
            if missing_files:
                logger.warning(f"Missing required DOCX files: {missing_files}")
                return False
            
            # Try to read the main document XML to ensure it's valid
            try:
                document_xml = zip_file.read('word/document.xml')
                if len(document_xml) == 0:
                    logger.warning("Document XML is empty")
                    return False
            except KeyError:
                logger.warning("Cannot read document.xml from DOCX file")
                return False
            
            return True
            
    except BadZipFile:
        logger.warning("File is not a valid ZIP/DOCX file")
        return False
    except Exception as e:
        logger.error(f"Error validating DOCX structure: {str(e)}")
        return False

def generate_secure_filename() -> str:
    """
    Generate a secure UUID-based filename
    
    Returns:
        str: Secure filename with .docx extension
    """
    secure_name = str(uuid.uuid4())
    return f"{secure_name}.docx"

def is_file_size_valid(file_size: int, max_size: int) -> bool:
    """
    Validate file size is within limits
    
    Args:
        file_size: Size of the file in bytes
        max_size: Maximum allowed size in bytes
        
    Returns:
        bool: True if file size is valid, False otherwise
    """
    return 0 < file_size <= max_size

def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe display (not for storage)
    
    Args:
        filename: Original filename
        
    Returns:
        str: Sanitized filename safe for display
    """
    if not filename:
        return "unnamed_file.docx"
    
    # Remove path components
    filename = os.path.basename(filename)
    
    # Limit length
    if len(filename) > MAX_FILENAME_LENGTH:
        name, ext = os.path.splitext(filename)
        filename = name[:MAX_FILENAME_LENGTH-len(ext)] + ext
    
    return filename

def validate_upload_file(file: FileStorage, max_size: int) -> Tuple[bool, str, Optional[dict]]:
    """
    Comprehensive file validation for upload
    
    Args:
        file: Werkzeug FileStorage object
        max_size: Maximum file size in bytes
        
    Returns:
        Tuple of (is_valid, error_message, file_info)
        file_info contains metadata if validation succeeds
    """
    try:
        # Check if file is present
        if not file or not file.filename:
            return False, "No file provided", None
        
        # Validate filename
        original_filename = sanitize_filename(file.filename)
        if not validate_file_extension(original_filename):
            return False, "Invalid file type. Only .docx files are allowed", None
        
        # Get file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        # Validate file size
        if not is_file_size_valid(file_size, max_size):
            if file_size == 0:
                return False, "File is empty", None
            else:
                return False, f"File too large. Maximum size: {max_size // (1024*1024)}MB", None
        
        # Validate file type using magic numbers
        if not validate_file_type_magic(file.stream):
            return False, "Invalid file format. File does not appear to be a valid DOCX document", None
        
        # Create temporary file for structure validation
        with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as temp_file:
            file.seek(0)
            temp_file.write(file.read())
            temp_file.flush()
            
            # Validate DOCX structure
            if not validate_docx_structure(temp_file.name):
                os.unlink(temp_file.name)
                return False, "Invalid DOCX file structure", None
            
            # Clean up temp file
            os.unlink(temp_file.name)
        
        # Reset file position for later use
        file.seek(0)
        
        # Create file info
        file_info = {
            'original_filename': original_filename,
            'size': file_size,
            'secure_filename': generate_secure_filename()
        }
        
        logger.info(f"File validation successful: {original_filename} ({file_size} bytes)")
        return True, "File validation successful", file_info
        
    except Exception as e:
        logger.error(f"Unexpected error during file validation: {str(e)}")
        return False, "Internal error during file validation", None

def cleanup_file(file_path: str) -> bool:
    """
    Safely remove a file
    
    Args:
        file_path: Path to file to remove
        
    Returns:
        bool: True if file was removed, False otherwise
    """
    try:
        if os.path.exists(file_path):
            os.unlink(file_path)
            logger.info(f"File cleaned up: {file_path}")
            return True
        return False
    except Exception as e:
        logger.error(f"Error cleaning up file {file_path}: {str(e)}")
        return False