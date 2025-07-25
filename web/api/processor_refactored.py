"""
Refactored document processing API following Sandi Metz principles
Uses dependency injection and single-purpose classes
"""

import logging
from typing import Optional

from web.services.job_repository import JobRepository
from web.utils.errors import ValidationError
from web.utils.error_builder import APIErrorBuilder
from .request_validator import ProcessingRequestValidator
from .processing_service import ProcessingService
from .download_service import DownloadService

logger = logging.getLogger(__name__)


class ProcessorController:
    """
    Processor controller following Single Responsibility Principle
    
    ONLY responsible for:
    - Coordinating between validator, service, and response building
    - HTTP request/response handling
    - Error handling and logging
    """
    
    def __init__(self, job_repository: Optional[JobRepository] = None):
        self.validator = ProcessingRequestValidator()
        self.processing_service = ProcessingService(job_repository)
        self.download_service = DownloadService(job_repository)
        logger.info("ProcessorController initialized with dependency injection")
    
    def process_document(self):
        """Handle document processing POST request"""
        try:
            request_data = self.validator.extract_and_validate()
            result = self.processing_service.start_processing(request_data)
            return APIErrorBuilder.success_response(result)
        except ValidationError as e:
            return self._handle_validation_error(e)
        except Exception as e:
            return self._handle_unexpected_error(e)
    
    def get_processing_status(self, job_id: str):
        """Get processing status for job ID"""
        try:
            job_data = self.processing_service.get_job_status(job_id)
            if not job_data:
                return APIErrorBuilder.not_found_error("Job not found")
            return APIErrorBuilder.success_response(job_data)
        except Exception as e:
            return self._handle_status_error(e)
    
    def download_result(self, file_id: str):
        """Download processed result file"""
        try:
            result = self.download_service.download_result(file_id)
            if result is None:
                return APIErrorBuilder.not_found_error("Processed file not found or not ready")
            return result
        except Exception as e:
            return self._handle_download_error(e)
    
    def cleanup_jobs(self, hours: int = 24) -> int:
        """Clean up old processing jobs"""
        try:
            return self.download_service.cleanup_old_jobs(hours)
        except Exception as e:
            logger.error(f"Error cleaning up jobs: {str(e)}")
            return 0
    
    def _handle_validation_error(self, error: ValidationError):
        """Handle validation error"""
        logger.error(f"Validation error: {str(error)}")
        return APIErrorBuilder.validation_error(str(error))
    
    def _handle_unexpected_error(self, error: Exception):
        """Handle unexpected processing error"""
        logger.error(f"Unexpected error during processing request: {str(error)}")
        return APIErrorBuilder.internal_error("Failed to start document processing")
    
    def _handle_status_error(self, error: Exception):
        """Handle status retrieval error"""
        logger.error(f"Error getting job status: {str(error)}")
        return APIErrorBuilder.internal_error("Failed to retrieve job status")
    
    def _handle_download_error(self, error: Exception):
        """Handle download error"""
        logger.error(f"Error downloading file: {str(error)}")
        return APIErrorBuilder.internal_error("Failed to download file")


# Global controller instance for Flask routes (dependency injection)
_controller_instance = None

def get_processor_controller(job_repository: Optional[JobRepository] = None) -> ProcessorController:
    """Get processor controller instance with dependency injection"""
    global _controller_instance
    if _controller_instance is None or job_repository is not None:
        _controller_instance = ProcessorController(job_repository)
    return _controller_instance


# Flask route functions using dependency injection
def process_document():
    """Flask route function for document processing"""
    controller = get_processor_controller()
    return controller.process_document()


def get_processing_status(job_id: str):
    """Flask route function for getting processing status"""
    controller = get_processor_controller()
    return controller.get_processing_status(job_id)


def download_result(file_id: str):
    """Flask route function for downloading results"""
    controller = get_processor_controller()
    return controller.download_result(file_id)


def init_processor(app):
    """Initialize processor with Flask app (for cleanup scheduling)"""
    # TODO: Set up periodic cleanup task using APScheduler or similar
    logger.info("Processor initialized with Flask app")


def cleanup_processing_jobs():
    """Clean up old processing jobs (compatibility function)"""
    controller = get_processor_controller()
    return controller.cleanup_jobs()