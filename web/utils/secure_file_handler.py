#!/usr/bin/env python3
"""
Secure File Handler for Processing Pipeline
Provides comprehensive file security with path validation and integrity checks
"""

import os
import hashlib
import logging
import uuid
from pathlib import Path
from typing import Optional, Dict, Any
import shutil
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class SecureFileHandler:
    """
    Comprehensive file security handler with path validation and integrity checks
    """
    
    def __init__(self, base_directory: str):
        """
        Initialize secure file handler
        
        Args:
            base_directory: Base directory for file operations (sandbox)
        """
        self.base_directory = Path(base_directory).resolve()
        self.base_directory.mkdir(exist_ok=True)
        
        # Allowed file extensions (whitelist)
        self.allowed_extensions = {'.docx'}
        
        logger.info(f"SecureFileHandler initialized with base directory: {self.base_directory}")
    
    def validate_file_path(self, file_path: str) -> bool:
        """
        Validate file path against directory traversal attacks
        
        Args:
            file_path: File path to validate
            
        Returns:
            bool: True if path is safe
        """
        try:
            # Resolve path and check if it's within base directory
            resolved_path = Path(file_path).resolve()
            
            # Check if path is within base directory
            try:
                resolved_path.relative_to(self.base_directory)
            except ValueError:
                logger.warning(f"Path traversal attempt detected: {file_path}")
                return False
            
            # Check file extension
            if resolved_path.suffix.lower() not in self.allowed_extensions:
                logger.warning(f"Invalid file extension: {resolved_path.suffix}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating file path {file_path}: {str(e)}")
            return False
    
    def generate_secure_filename(self, original_filename: Optional[str] = None) -> str:
        """
        Generate secure UUID-based filename
        
        Args:
            original_filename: Original filename for extension extraction
            
        Returns:
            str: Secure filename with UUID
        """
        # Generate UUID for filename
        secure_id = str(uuid.uuid4())
        
        # Extract extension from original filename if provided
        if original_filename:
            original_path = Path(original_filename)
            extension = original_path.suffix.lower()
            if extension in self.allowed_extensions:
                return f"{secure_id}{extension}"
        
        # Default to .docx extension
        return f"{secure_id}.docx"
    
    def calculate_file_hash(self, file_path: str) -> Optional[str]:
        """
        Calculate SHA-256 hash of file for integrity verification
        
        Args:
            file_path: Path to file
            
        Returns:
            str: SHA-256 hash or None if error
        """
        try:
            if not self.validate_file_path(file_path):
                return None
            
            sha256_hash = hashlib.sha256()
            
            with open(file_path, "rb") as f:
                # Read file in chunks to handle large files
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            
            return sha256_hash.hexdigest()
            
        except Exception as e:
            logger.error(f"Error calculating hash for {file_path}: {str(e)}")
            return None
    
    def secure_file_move(self, source_path: str, destination_path: str) -> bool:
        """
        Securely move file with validation
        
        Args:
            source_path: Source file path
            destination_path: Destination file path
            
        Returns:
            bool: True if successful
        """
        try:
            # Validate both paths
            if not self.validate_file_path(destination_path):
                logger.error(f"Invalid destination path: {destination_path}")
                return False
            
            if not os.path.exists(source_path):
                logger.error(f"Source file does not exist: {source_path}")
                return False
            
            # Calculate hash before move for integrity check
            original_hash = None
            if os.path.exists(source_path):
                with open(source_path, "rb") as f:
                    original_hash = hashlib.sha256(f.read()).hexdigest()
            
            # Ensure destination directory exists
            dest_dir = Path(destination_path).parent
            dest_dir.mkdir(parents=True, exist_ok=True)
            
            # Move file
            shutil.move(source_path, destination_path)
            
            # Verify integrity after move
            if original_hash:
                new_hash = self.calculate_file_hash(destination_path)
                if new_hash != original_hash:
                    logger.error(f"File integrity check failed after move: {destination_path}")
                    # Try to remove corrupted file
                    try:
                        os.remove(destination_path)
                    except:
                        pass
                    return False
            
            logger.info(f"File securely moved: {source_path} -> {destination_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error moving file {source_path} to {destination_path}: {str(e)}")
            return False
    
    def secure_file_copy(self, source_path: str, destination_path: str) -> bool:
        """
        Securely copy file with validation
        
        Args:
            source_path: Source file path
            destination_path: Destination file path
            
        Returns:
            bool: True if successful
        """
        try:
            # Validate destination path
            if not self.validate_file_path(destination_path):
                logger.error(f"Invalid destination path: {destination_path}")
                return False
            
            if not os.path.exists(source_path):
                logger.error(f"Source file does not exist: {source_path}")
                return False
            
            # Ensure destination directory exists
            dest_dir = Path(destination_path).parent
            dest_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy file
            shutil.copy2(source_path, destination_path)
            
            # Verify integrity
            source_hash = None
            with open(source_path, "rb") as f:
                source_hash = hashlib.sha256(f.read()).hexdigest()
            
            dest_hash = self.calculate_file_hash(destination_path)
            
            if source_hash != dest_hash:
                logger.error(f"File integrity check failed after copy: {destination_path}")
                # Remove corrupted copy
                try:
                    os.remove(destination_path)
                except:
                    pass
                return False
            
            logger.info(f"File securely copied: {source_path} -> {destination_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error copying file {source_path} to {destination_path}: {str(e)}")
            return False
    
    def secure_delete(self, file_path: str) -> bool:
        """
        Securely delete file with validation and logging
        
        Args:
            file_path: File path to delete
            
        Returns:
            bool: True if successful
        """
        try:
            # Validate path
            if not self.validate_file_path(file_path):
                logger.error(f"Invalid file path for deletion: {file_path}")
                return False
            
            if not os.path.exists(file_path):
                logger.warning(f"File does not exist for deletion: {file_path}")
                return True  # Consider non-existent file as successfully deleted
            
            # Log file info before deletion
            file_stat = os.stat(file_path)
            file_hash = self.calculate_file_hash(file_path)
            
            # Delete file
            os.remove(file_path)
            
            # Audit log
            logger.info(f"File securely deleted: {file_path} (size: {file_stat.st_size}, hash: {file_hash})")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {str(e)}")
            return False
    
    def cleanup_old_files(self, max_age_hours: int = 24) -> int:
        """
        Clean up files older than specified age
        
        Args:
            max_age_hours: Maximum age in hours
            
        Returns:
            int: Number of files cleaned up
        """
        cleaned_count = 0
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        try:
            for file_path in self.base_directory.rglob("*"):
                if file_path.is_file():
                    # Check file age
                    file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    
                    if file_mtime < cutoff_time:
                        if self.secure_delete(str(file_path)):
                            cleaned_count += 1
            
            logger.info(f"Cleanup completed: {cleaned_count} files removed")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error during file cleanup: {str(e)}")
            return cleaned_count
    
    def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive file information
        
        Args:
            file_path: File path
            
        Returns:
            dict: File information or None if error
        """
        try:
            if not self.validate_file_path(file_path):
                return None
            
            if not os.path.exists(file_path):
                return None
            
            file_stat = os.stat(file_path)
            file_hash = self.calculate_file_hash(file_path)
            
            return {
                'path': file_path,
                'size': file_stat.st_size,
                'created': datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
                'modified': datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                'sha256': file_hash,
                'extension': Path(file_path).suffix.lower(),
                'is_valid': True
            }
            
        except Exception as e:
            logger.error(f"Error getting file info for {file_path}: {str(e)}")
            return None
    
    def verify_file_access(self, file_path: str, job_id: Optional[str] = None) -> bool:
        """
        Verify file access permissions (can be extended for job-based access control)
        
        Args:
            file_path: File path to verify
            job_id: Optional job ID for access control
            
        Returns:
            bool: True if access is allowed
        """
        try:
            # Basic path validation
            if not self.validate_file_path(file_path):
                return False
            
            # Check if file exists
            if not os.path.exists(file_path):
                return False
            
            # Check read permissions
            if not os.access(file_path, os.R_OK):
                logger.warning(f"No read access to file: {file_path}")
                return False
            
            # TODO: Add job-based access control if needed
            # if job_id:
            #     return self.verify_job_file_access(file_path, job_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error verifying file access for {file_path}: {str(e)}")
            return False


# Utility functions for common operations
def create_secure_handler(directory_type: str) -> SecureFileHandler:
    """
    Create secure file handler for specific directory type
    
    Args:
        directory_type: 'uploads', 'outputs', 'temp'
        
    Returns:
        SecureFileHandler instance
    """
    from flask import current_app
    
    base_dirs = {
        'uploads': current_app.config.get('UPLOAD_FOLDER', 'uploads'),
        'outputs': current_app.config.get('OUTPUT_FOLDER', 'outputs'),
        'temp': current_app.config.get('TEMP_FOLDER', 'temp')
    }
    
    base_dir = base_dirs.get(directory_type, directory_type)
    return SecureFileHandler(base_dir)


def validate_download_access(file_id: str, job_id: Optional[str] = None) -> bool:
    """
    Validate download access for a file
    
    Args:
        file_id: File identifier
        job_id: Optional job identifier for access control
        
    Returns:
        bool: True if download is allowed
    """
    try:
        handler = create_secure_handler('outputs')
        file_path = handler.base_directory / f"{file_id}.docx"
        
        return handler.verify_file_access(str(file_path), job_id)
        
    except Exception as e:
        logger.error(f"Error validating download access for {file_id}: {str(e)}")
        return False